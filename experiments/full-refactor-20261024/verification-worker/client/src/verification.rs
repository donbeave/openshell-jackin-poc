use anyhow::{Context, Result, bail};
use base64::Engine as _;
use openshell_sdk::raw::{ExecSandboxRequest, proto};
use openshell_sdk::{DeleteOptions, EdgeAuthInterceptor, ListOptions, OpenShellClient};
use prost_types::{ListValue, Struct, Value as ProtoValue, value::Kind as ProtoKind};
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use std::{
    collections::{BTreeMap, HashMap},
    env, fs,
    time::{Duration, SystemTime, UNIX_EPOCH},
};
use tokio::time::timeout;
use tonic::transport::{Certificate, ClientTlsConfig, Endpoint, Identity};
use uuid::Uuid;

const MAX_BYTES_PER_STREAM: usize = 64 * 1024;
const TRUNCATION_MARKER: &[u8] = b"\n[truncated]";
const TEST_IMAGE: &str =
    "python@sha256:1b668429b3511ab407d8e00648891631b0b1a4d7e15e3ca70f38ab5b91ad4ab4";
const WRAPPER: &str = "import os,signal,subprocess,sys,time\ndeadline=float(sys.argv[1])\nargv=sys.argv[2:]\nremaining=deadline-time.time()\nif remaining <= 0: sys.exit(124)\ntry: child=subprocess.Popen(argv,start_new_session=True)\nexcept OSError as error:\n print(error,file=sys.stderr); sys.exit(125)\ntry: code=child.wait(timeout=remaining)\nexcept subprocess.TimeoutExpired:\n try: os.killpg(child.pid,signal.SIGKILL)\n except ProcessLookupError: pass\n child.wait(); sys.exit(124)\nsys.exit(code)";

fn arg(name: &str) -> Result<String> {
    let key = format!("--{name}");
    let args: Vec<String> = env::args().collect();
    let index = args
        .iter()
        .position(|item| item == &key)
        .context(format!("missing {key}"))?;
    args.get(index + 1)
        .cloned()
        .context(format!("missing value for {key}"))
}

fn json_proto(value: Value) -> Result<ProtoValue> {
    let kind = match value {
        Value::Null => ProtoKind::NullValue(0),
        Value::Bool(value) => ProtoKind::BoolValue(value),
        Value::Number(value) => ProtoKind::NumberValue(value.as_f64().context("non-f64 number")?),
        Value::String(value) => ProtoKind::StringValue(value),
        Value::Array(values) => ProtoKind::ListValue(ListValue {
            values: values
                .into_iter()
                .map(json_proto)
                .collect::<Result<Vec<_>>>()?,
        }),
        Value::Object(values) => ProtoKind::StructValue(Struct {
            fields: values
                .into_iter()
                .map(|(key, value)| Ok((key, json_proto(value)?)))
                .collect::<Result<BTreeMap<_, _>>>()?,
        }),
    };
    Ok(ProtoValue { kind: Some(kind) })
}

fn json_struct(value: Value) -> Result<Struct> {
    match value {
        Value::Object(fields) => Ok(Struct {
            fields: fields
                .into_iter()
                .map(|(k, v)| Ok((k, json_proto(v)?)))
                .collect::<Result<BTreeMap<_, _>>>()?,
        }),
        _ => bail!("expected object for protobuf Struct"),
    }
}

async fn client() -> Result<OpenShellClient> {
    let endpoint = arg("endpoint")?;
    let server_name = arg("server-name")?;
    let ca = fs::read(arg("ca")?).context("read test CA")?;
    let cert = fs::read(arg("cert")?).context("read test client certificate")?;
    let key = fs::read(arg("key")?).context("read test client key")?;
    let tls = ClientTlsConfig::new()
        .ca_certificate(Certificate::from_pem(ca))
        .domain_name(server_name)
        .identity(Identity::from_pem(cert, key));
    let channel = Endpoint::from_shared(endpoint)?
        .connect_timeout(Duration::from_secs(5))
        .timeout(Duration::from_secs(40))
        .tls_config(tls)?
        .connect()
        .await
        .context("verified mTLS connection")?;
    Ok(OpenShellClient::from_parts(
        channel,
        EdgeAuthInterceptor::noop(),
    ))
}

fn create_request(
    name: &str,
    image: &str,
    request_id: &str,
) -> Result<proto::CreateSandboxRequest> {
    let mounts = json!([
        {"type":"volume","source":"jfr24verify-candidate","target":"/sandbox/repo","read_only":true},
        {"type":"volume","source":"jfr24verify-bundle","target":"/sandbox/checks","read_only":true},
        {"type":"tmpfs","target":"/tmp","options":["noexec","nosuid"],"size_bytes":67108864},
        {"type":"tmpfs","target":"/build","options":["nosuid"],"size_bytes":268435456}
    ]);
    let template = proto::SandboxTemplate {
        image: image.to_string(),
        environment: HashMap::new(),
        driver_config: Some(json_struct(json!({"docker":{"mounts":mounts}}))?),
        resources: Some(json_struct(json!({"limits":{"cpu":"1","memory":"512Mi"}}))?),
        ..Default::default()
    };
    let labels = HashMap::from([
        (
            "jackin.poc.test-id".to_string(),
            "jfr-20261024-verification-worker".to_string(),
        ),
        (
            "jackin.poc.candidate-commit".to_string(),
            fs::read_to_string("../fixture/candidate-commit.txt")?
                .trim()
                .to_string(),
        ),
    ]);
    Ok(proto::CreateSandboxRequest {
        workspace_scope: Some(proto::workspace_selector("default")),
        spec: Some(proto::SandboxSpec {
            template: Some(template),
            command: vec!["/bin/sh".into(), "-c".into(), "sleep 3600".into()],
            restart_policy: proto::SandboxRestartPolicy::Never as i32,
            ..Default::default()
        }),
        name: name.to_string(),
        labels,
        annotations: HashMap::new(),
        await_main_process_attachment: false,
        workload_template: String::new(),
        request_id: request_id.to_string(),
        service_exposures: Vec::new(),
    })
}

#[derive(Default)]
struct Bounded {
    bytes: Vec<u8>,
    total: usize,
    truncated: bool,
}
impl Bounded {
    fn push(&mut self, data: &[u8]) {
        self.total += data.len();
        let limit = MAX_BYTES_PER_STREAM.saturating_sub(TRUNCATION_MARKER.len());
        let remaining = limit.saturating_sub(self.bytes.len());
        self.bytes
            .extend_from_slice(&data[..data.len().min(remaining)]);
        if self.total > self.bytes.len() {
            self.truncated = true;
        }
    }
    fn encoded(&self) -> String {
        let mut bytes = self.bytes.clone();
        if self.truncated {
            bytes.extend_from_slice(TRUNCATION_MARKER);
        }
        base64::engine::general_purpose::STANDARD.encode(bytes)
    }
}

struct ExecCapture {
    exit_code: i32,
    stdout: Bounded,
    stderr: Bounded,
}
async fn raw_exec(
    client: &OpenShellClient,
    name: &str,
    command: Vec<String>,
    deadline_secs: u64,
) -> Result<ExecCapture> {
    let duration = (deadline_secs > 0).then(|| prost_types::Duration {
        seconds: deadline_secs.min(i64::MAX as u64) as i64,
        nanos: 0,
    });
    let request = ExecSandboxRequest {
        workspace_scope: Some(proto::workspace_selector("default")),
        sandbox: name.into(),
        command,
        workdir: "/sandbox/repo".into(),
        environment: HashMap::from([("PYTHONDONTWRITEBYTECODE".into(), "1".into())]),
        execution_timeout: duration,
        stdin: Vec::new(),
        tty: false,
        cols: 0,
        rows: 0,
        no_login_shell: true,
        request_id: Uuid::new_v4().to_string(),
    };
    let mut grpc = client.raw_grpc();
    let response = timeout(
        Duration::from_secs(deadline_secs.saturating_add(20).max(40)),
        grpc.exec_sandbox(request),
    )
    .await
    .context("ExecSandbox RPC deadline")??;
    let mut stream = response.into_inner();
    let mut stdout = Bounded::default();
    let mut stderr = Bounded::default();
    for _ in 0..16384 {
        let event = timeout(Duration::from_secs(40), stream.message())
            .await
            .context("ExecSandbox stream deadline")??
            .context("ExecSandbox stream ended before exit")?;
        match event.payload {
            Some(proto::exec_sandbox_event::Payload::Stdout(chunk)) => stdout.push(&chunk.data),
            Some(proto::exec_sandbox_event::Payload::Stderr(chunk)) => stderr.push(&chunk.data),
            Some(proto::exec_sandbox_event::Payload::Exit(exit)) => {
                return Ok(ExecCapture {
                    exit_code: exit.exit_code,
                    stdout,
                    stderr,
                });
            }
            None => {}
        }
    }
    bail!("ExecSandbox exceeded 16384 response frames")
}

fn policy_hash(argv: &[String], timeout_secs: u64) -> String {
    let mut hash = Sha256::new();
    for part in argv {
        hash.update(part.as_bytes());
        hash.update([0]);
    }
    hash.update(TEST_IMAGE.as_bytes());
    hash.update(b"\0sandbox-wrapper-v1;watchdog-grace=5s;network=none;readonly-root;cap-drop=all;memory=536870912;cpus=1;pids=64;trusted-ro;candidate-ro;tmpfs=/tmp:64m,/build:256m;env=PYTHONDONTWRITEBYTECODE=1\0");
    hash.update(timeout_secs.to_be_bytes());
    format!("{:x}", hash.finalize())
}

fn frozen_host_argv(program: &str, mode: &str) -> Result<Vec<String>> {
    let script = fs::canonicalize(format!("../fixture/trusted-bundle/{mode}.py"))?;
    let repo = fs::canonicalize("../fixture/candidate")?;
    Ok(vec![
        program.to_string(),
        script.display().to_string(),
        repo.display().to_string(),
    ])
}

fn wrapped_command(program: &str, script: &str, timeout_secs: u64) -> Vec<String> {
    let deadline = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs_f64()
        + timeout_secs as f64
        + 5.0;
    vec![
        "/usr/local/bin/python3".into(),
        "-c".into(),
        WRAPPER.into(),
        format!("{deadline:.6}"),
        program.into(),
        script.into(),
        "/sandbox/repo".into(),
    ]
}

async fn run_case(
    client: &OpenShellClient,
    name: &str,
    mode: &str,
    expected: i32,
    request_timeout: u64,
    program: &str,
) -> Result<Value> {
    let argv = frozen_host_argv(program, mode)?;
    let container_argv = vec![
        program.to_string(),
        format!("/sandbox/checks/{mode}.py"),
        "/sandbox/repo".into(),
    ];
    let request = wrapped_command(program, &container_argv[1], request_timeout);
    let output = raw_exec(client, name, request, request_timeout).await?;
    anyhow::ensure!(
        output.exit_code == expected,
        "{mode}: expected exit {expected}, observed {}",
        output.exit_code
    );
    let structured = if mode == "success" {
        let report: Value = serde_json::from_slice(&output.stdout.bytes)
            .context("parse successful verification report")?;
        let checks = report
            .get("filesystem_checks")
            .context("missing filesystem checks")?;
        for path in [
            "/sandbox/repo/src/lib.rs",
            "/sandbox/checks/verify.py",
            "rootfs",
        ] {
            anyhow::ensure!(
                checks
                    .get(path)
                    .and_then(|value| value.get("denied"))
                    .and_then(Value::as_bool)
                    == Some(true),
                "write was not denied for {path}: {checks}"
            );
        }
        anyhow::ensure!(
            checks.get("tmp_write").and_then(Value::as_bool) == Some(true),
            "/tmp not writable: {checks}"
        );
        anyhow::ensure!(
            checks.get("build_write").and_then(Value::as_bool) == Some(true),
            "/build not writable: {checks}"
        );
        anyhow::ensure!(
            checks
                .get("tmp_noexec")
                .and_then(|value| value.get("denied"))
                .and_then(Value::as_bool)
                == Some(true),
            "/tmp executable file ran: {checks}"
        );
        anyhow::ensure!(
            report
                .get("network")
                .and_then(|value| value.get("denied_or_unroutable"))
                .and_then(Value::as_bool)
                == Some(true),
            "test network connect did not fail: {}",
            report["network"]
        );
        anyhow::ensure!(
            report.get("root_mount_read_only").and_then(Value::as_bool) == Some(true),
            "root mount is not read-only"
        );
        let security = &report["status_security"];
        anyhow::ensure!(
            security["NoNewPrivs"] == "1",
            "NoNewPrivs not set: {security}"
        );
        anyhow::ensure!(
            security["CapEff"] == "0000000000000000" && security["CapBnd"] == "0000000000000000",
            "capability set is not empty: {security}"
        );
        anyhow::ensure!(
            report["cgroup"]["memory.max"] == "536870912",
            "memory limit mismatch: {}",
            report["cgroup"]
        );
        anyhow::ensure!(
            report["cgroup"]["pids.max"] == "64",
            "pids limit mismatch: {}",
            report["cgroup"]
        );
        let cpu_max = report["cgroup"]["cpu.max"]
            .as_str()
            .context("missing cpu.max")?;
        anyhow::ensure!(
            cpu_max.split_whitespace().nth(1) == Some("100000"),
            "CPU quota is not one core: {cpu_max}"
        );
        Some(report)
    } else {
        None
    };
    Ok(
        json!({"mode":mode,"frozen_host_argv":argv,"container_argv":container_argv,"policy_hash_receipt":policy_hash(&argv,request_timeout),"production_result_record":false,"exit_code":output.exit_code,"expected_exit_code":expected,"stdout_base64":output.stdout.encoded(),"stderr_base64":output.stderr.encoded(),"stdout_bytes_total":output.stdout.total,"stderr_bytes_total":output.stderr.total,"stdout_truncated":output.stdout.truncated,"stderr_truncated":output.stderr.truncated,"stdout_retained_bytes":output.stdout.bytes.len()+if output.stdout.truncated {TRUNCATION_MARKER.len()} else {0},"stderr_retained_bytes":output.stderr.bytes.len()+if output.stderr.truncated {TRUNCATION_MARKER.len()} else {0},"verification_report":structured}),
    )
}

fn add_case(cases: &mut Vec<Value>, operation: &str, result: Result<Value>) {
    match result {
        Ok(details) => cases.push(json!({"operation":operation,"result":"PASS","details":details})),
        Err(error) => {
            cases.push(json!({"operation":operation,"result":"FAIL","error":format!("{error:#}")}))
        }
    }
}

async fn output_truncation_case(client: &OpenShellClient, name: &str) -> Result<Value> {
    let argv = frozen_host_argv("python3", "output")?;
    let output = raw_exec(
        client,
        name,
        wrapped_command("python3", "/sandbox/checks/output.py", 30),
        30,
    )
    .await?;
    anyhow::ensure!(output.exit_code == 0 && output.stdout.truncated && output.stderr.truncated);
    anyhow::ensure!(output.stdout.total == 128 * 1024 && output.stderr.total == 128 * 1024);
    anyhow::ensure!(output.stdout.bytes.len() + TRUNCATION_MARKER.len() == MAX_BYTES_PER_STREAM);
    anyhow::ensure!(output.stderr.bytes.len() + TRUNCATION_MARKER.len() == MAX_BYTES_PER_STREAM);
    Ok(
        json!({"mechanism":"bounded client collector (Jackin-retained result logic)","frozen_host_argv":argv,"container_argv":["python3","/sandbox/checks/output.py","/sandbox/repo"],"exit_code":output.exit_code,"stdout_total":output.stdout.total,"stderr_total":output.stderr.total,"per_stream_cap":MAX_BYTES_PER_STREAM,"stdout_marker":String::from_utf8_lossy(TRUNCATION_MARKER),"stdout_retained_bytes":output.stdout.bytes.len()+TRUNCATION_MARKER.len(),"stderr_retained_bytes":output.stderr.bytes.len()+TRUNCATION_MARKER.len(),"stdout_truncated":output.stdout.truncated,"stderr_truncated":output.stderr.truncated}),
    )
}

async fn tmpfs_mount_flags_case(client: &OpenShellClient, name: &str) -> Result<Value> {
    let command = vec![
        "/usr/local/bin/python3".to_string(),
        "-c".to_string(),
        r#"import json,pathlib
rows={}
for line in pathlib.Path('/proc/self/mountinfo').read_text().splitlines():
 fields=line.split()
 if fields[4] in ['/tmp','/build']:
  separator=fields.index('-')
  rows[fields[4]]={'mount_options':fields[5].split(','),'fs_type':fields[separator+1],'super_options':fields[separator+3].split(',')}
status=pathlib.Path('/proc/self/status').read_text()
nnp=next((line.split(':',1)[1].strip() for line in status.splitlines() if line.startswith('NoNewPrivs:')),'missing')
print(json.dumps({'mounts':rows,'NoNewPrivs':nnp},sort_keys=True))"#
            .to_string(),
    ];
    let output = raw_exec(client, name, command, 10).await?;
    anyhow::ensure!(output.exit_code == 0, "mountinfo probe exited {}", output.exit_code);
    let report: Value = serde_json::from_slice(&output.stdout.bytes)?;
    let tmp = &report["mounts"]["/tmp"];
    let build = &report["mounts"]["/build"];
    anyhow::ensure!(tmp["fs_type"] == "tmpfs", "/tmp is not tmpfs: {tmp}");
    anyhow::ensure!(build["fs_type"] == "tmpfs", "/build is not tmpfs: {build}");
    anyhow::ensure!(
        tmp["mount_options"].as_array().is_some_and(|options| {
            options.iter().any(|option| option == "noexec")
                && options.iter().any(|option| option == "nosuid")
        }),
        "/tmp missing noexec or nosuid in mountinfo: {tmp}"
    );
    anyhow::ensure!(
        build["mount_options"]
            .as_array()
            .is_some_and(|options| options.iter().any(|option| option == "nosuid")),
        "/build missing nosuid in mountinfo: {build}"
    );
    anyhow::ensure!(report["NoNewPrivs"] == "1", "NoNewPrivs is not set: {report}");
    Ok(json!({
        "mountinfo": report,
        "noexec": "functional negative tested separately by executing a disposable /tmp file and observing EACCES",
        "nosuid": "mount flag observed in mountinfo; functional setuid negative NOT TESTED because NoNewPrivs=1 also prevents setuid transitions and this experiment does not disable that boundary"
    }))
}

async fn check_pids(client: &OpenShellClient, name: &str) -> Result<Value> {
    let command = vec!["/usr/local/bin/python3".into(), "-c".into(), "import json,pathlib; print(json.dumps({'max':pathlib.Path('/sys/fs/cgroup/pids.max').read_text().strip(),'current':pathlib.Path('/sys/fs/cgroup/pids.current').read_text().strip()}))".into()];
    let response = client.exec(name, &command, Default::default()).await?;
    anyhow::ensure!(response.exit_code == 0);
    Ok(serde_json::from_slice(&response.stdout)
        .unwrap_or(json!({"raw":String::from_utf8_lossy(&response.stdout)})))
}

async fn interruption_probe(client: &OpenShellClient, name: &str) -> Result<Value> {
    let command = vec![
        "/usr/local/bin/python3".into(),
        "/sandbox/checks/interrupt-child.py".into(),
        "/sandbox/repo".into(),
    ];
    let request = ExecSandboxRequest {
        workspace_scope: Some(proto::workspace_selector("default")),
        sandbox: name.into(),
        command,
        workdir: "/sandbox/repo".into(),
        environment: HashMap::from([("PYTHONDONTWRITEBYTECODE".into(), "1".into())]),
        execution_timeout: None,
        stdin: Vec::new(),
        tty: false,
        cols: 0,
        rows: 0,
        no_login_shell: true,
        request_id: Uuid::new_v4().to_string(),
    };
    let mut grpc = client.raw_grpc();
    let response = grpc.exec_sandbox(request).await?;
    let stream = response.into_inner();
    let mut stdout: Vec<u8> = Vec::new();
    let mut stderr: Vec<u8> = Vec::new();
    // Poll the started marker independently, then disconnect the observation stream.
    tokio::time::sleep(Duration::from_millis(300)).await;
    let started = client
        .exec(
            name,
            &vec![
                "/usr/local/bin/python3".into(),
                "-c".into(),
                "import pathlib; print(pathlib.Path('/tmp/interrupt-started').read_text())".into(),
            ],
            Default::default(),
        )
        .await?;
    drop(stream);
    tokio::time::sleep(Duration::from_secs(6)).await;
    let after = client
        .exec(
            name,
            &vec![
                "/usr/local/bin/python3".into(),
                "-c".into(),
                "import pathlib; print(pathlib.Path('/tmp/interrupt-done').exists())".into(),
            ],
            Default::default(),
        )
        .await?;
    let still_running = String::from_utf8_lossy(&after.stdout).trim() == "True";
    let _ = (&mut stdout, &mut stderr);
    Ok(
        json!({"stream_disconnected_after_start":started.exit_code==0,"client_dropped_exec_stream":true,"completed_after_disconnect":still_running,"meaning":"disconnect is observation loss; no assumption it cancels the remote child"}),
    )
}

async fn run_created(
    client: &OpenShellClient,
    name: &str,
    sandbox_id: &str,
    request_id: &str,
    image: &str,
) -> Result<Value> {
    let ready = client.wait_ready(name, Duration::from_secs(120)).await?;
    anyhow::ensure!(ready.id == sandbox_id, "ready ID differs from create ID");
    let listed = client.list_all_sandboxes(ListOptions::default()).await?;
    let list_has_id = listed.iter().any(|sandbox| sandbox.id == sandbox_id);
    anyhow::ensure!(list_has_id, "created ID absent from list");
    let inspected = client.get_sandbox(name).await?;
    anyhow::ensure!(
        inspected.id == sandbox_id,
        "inspect ID differs from create ID"
    );

    let original_argv = frozen_host_argv("python3", "success")?;
    let original_timeout = 30;
    let mut cases = Vec::new();
    cases.push(json!({"operation":"create_list_inspect","result":"PASS","sandbox_id":sandbox_id,"request_id":request_id,"phase":format!("{:?}",ready.phase),"list_contains_id":list_has_id,"inspect_contains_same_id":true,"image":image,"resource_request":{"cpu_limit":"1","memory_limit":"512Mi"},"gateway_pid_limit":64,"mounts":[{"source":"jfr24verify-candidate","target":"/sandbox/repo","read_only":true},{"source":"jfr24verify-bundle","target":"/sandbox/checks","read_only":true},{"target":"/tmp","size_bytes":67108864,"options":["noexec","nosuid"]},{"target":"/build","size_bytes":268435456,"options":["nosuid"]}],"provider_count":0,"environment_allowlist":["PYTHONDONTWRITEBYTECODE=1"]}));

    add_case(
        &mut cases,
        "frozen_policy_success_and_boundaries",
        run_case(client, name, "success", 0, original_timeout, "python3").await,
    );
    add_case(
        &mut cases,
        "tmpfs_mount_flags_and_nnp_context",
        tmpfs_mount_flags_case(client, name).await,
    );
    add_case(
        &mut cases,
        "nonzero_result_and_separate_streams",
        run_case(client, name, "fail", 7, 30, "python3").await,
    );
    add_case(
        &mut cases,
        "missing_runtime",
        run_case(
            client,
            name,
            "missing-runtime",
            125,
            30,
            "/jfr/no-such-runtime",
        )
        .await,
    );
    add_case(
        &mut cases,
        "abnormal_exit",
        run_case(client, name, "abnormal-child", 250, 30, "python3").await,
    );
    add_case(
        &mut cases,
        "timeout_and_process_group",
        run_case(client, name, "timeout-child", 124, 2, "python3").await,
    );
    let pids_before = check_pids(client, name).await;
    let pids = run_case(client, name, "pids-fill", 0, 30, "python3").await;
    let pids_after = check_pids(client, name).await;
    cases.push(match (pids_before,pids_after,pids) {
        (Ok(before),Ok(after),Ok(details)) => json!({"operation":"pids_limit","result":"PASS","before":before,"after":after,"details":details}),
        (before,after,test) => json!({"operation":"pids_limit","result":"FAIL","before":before.err().map(|e|format!("{e:#}")),"after":after.err().map(|e|format!("{e:#}")),"error":test.err().map(|e|format!("{e:#}"))}),
    });
    for mode in ["tmpfs-fill-tmp", "tmpfs-fill-build"] {
        add_case(
            &mut cases,
            mode,
            run_case(client, name, mode, 0, 30, "python3").await,
        );
    }
    add_case(
        &mut cases,
        "bounded_output_truncation",
        output_truncation_case(client, name).await,
    );
    add_case(
        &mut cases,
        "cpu_limit_bounded_load",
        run_case(client, name, "cpu-load", 0, 10, "python3").await,
    );
    add_case(
        &mut cases,
        "memory_limit_bounded_load",
        run_case(client, name, "memory-limit", 0, 30, "python3").await,
    );
    match interruption_probe(client, name).await {
        Ok(details) => {
            cases.push(json!({"operation":"exec_disconnect","result":"OBSERVED","details":details}))
        }
        Err(error) => cases.push(
            json!({"operation":"exec_disconnect","result":"FAIL","error":format!("{error:#}")}),
        ),
    }

    let policy_receipt = json!({"argv":original_argv,"timeout_seconds":original_timeout,"image":TEST_IMAGE,"policy_hash":policy_hash(&original_argv,original_timeout),"provenance":"same byte-concatenation constants as Jackin TestPolicy::freeze at 6e266; receipt only, not a production run record"});
    Ok(
        json!({"gateway":"jfr-20261024-verify","endpoint":"https://localhost:28630","release":"OpenShell v0.1.5","commit":"bdb956f2cd65a635f1294fccf1d138d263bf650f","test_id":"jfr-20261024-verification-worker","candidate_commit":fs::read_to_string("../fixture/candidate-commit.txt")?.trim(),"candidate_tree":fs::read_to_string("../fixture/candidate-tree.txt")?.trim(),"trusted_bundle_hashes":fs::read_to_string("../results/trusted-bundle-hashes.txt")?,"policy_receipt":policy_receipt,"cases":cases}),
    )
}

pub async fn run() -> Result<Value> {
    let client = client().await?;
    let name = arg("name")?;
    let image = arg("image")?;
    let request_id = Uuid::new_v4().to_string();
    let request = create_request(&name, &image, &request_id)?;
    let mut grpc = client.raw_grpc();
    let created = grpc.create_sandbox(request).await?.into_inner();
    let sandbox_id = created
        .sandbox
        .context("create response omitted sandbox")?
        .metadata
        .context("sandbox omitted metadata")?
        .id;
    let journey = run_created(&client, &name, &sandbox_id, &request_id, &image).await;
    let cleanup = async {
        let deleted = client.delete_sandbox(&name, DeleteOptions::default()).await?;
        anyhow::ensure!(deleted.sandbox_id.as_deref() == Some(sandbox_id.as_str()), "delete ack ID differs");
        client.wait_deleted(&name, Duration::from_secs(60), Some(&sandbox_id)).await?;
        Ok::<_, anyhow::Error>(json!({"sandbox_id":sandbox_id,"outcome":format!("{:?}",deleted.outcome),"confirmed":true}))
    }.await;
    let cleanup_result = match cleanup {
        Ok(value) => value,
        Err(error) => json!({"confirmed":false,"error":format!("{error:#}")}),
    };
    let journey_result = match journey {
        Ok(value) => value,
        Err(error) => json!({"error":format!("{error:#}")}),
    };
    let journey_ok = journey_result.get("error").is_none()
        && journey_result
            .get("cases")
            .and_then(Value::as_array)
            .is_some_and(|cases| {
                cases.iter().all(|case| {
                    matches!(
                        case.get("result").and_then(Value::as_str),
                        Some("PASS" | "OBSERVED")
                    )
                })
            });
    let cleanup_ok = cleanup_result.get("confirmed").and_then(Value::as_bool) == Some(true);
    let overall_result = if journey_ok && cleanup_ok {
        "PASS"
    } else {
        "FAIL"
    };
    Ok(
        json!({"result":overall_result,"sandbox_id":sandbox_id,"request_id":request_id,"journey":journey_result,"cleanup":cleanup_result}),
    )
}
