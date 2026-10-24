mod verification;
use anyhow::{Context, Result, bail};
use base64::Engine as _;
use openshell_sdk::raw::{ExecSandboxRequest, proto};
use openshell_sdk::{
    DeleteOptions, EdgeAuthInterceptor, ExecOptions, ListOptions, OpenShellClient,
};
use prost::Message as _;
use serde::Serialize;
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use std::{collections::HashMap, env, fs, time::Duration};
use tokio::sync::mpsc;
use tokio::time::timeout;
use tokio_stream::wrappers::ReceiverStream;
use tonic::transport::{Certificate, ClientTlsConfig, Endpoint, Identity};
use uuid::Uuid;

#[derive(Serialize)]
struct Record {
    operation: String,
    ok: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    detail: Option<Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    error: Option<String>,
}

fn record(operation: &str, result: Result<Value>) -> Record {
    match result {
        Ok(detail) => Record {
            operation: operation.into(),
            ok: true,
            detail: Some(detail),
            error: None,
        },
        Err(error) => Record {
            operation: operation.into(),
            ok: false,
            detail: None,
            error: Some(format!("{error:#}")),
        },
    }
}

fn value<T: Serialize>(item: T) -> Result<Value> {
    Ok(serde_json::to_value(item)?)
}

fn arg(name: &str) -> Result<String> {
    let key = format!("--{name}");
    let args: Vec<String> = env::args().collect();
    let index = args
        .iter()
        .position(|item| item == &key)
        .with_context(|| format!("missing {key}"))?;
    args.get(index + 1)
        .cloned()
        .with_context(|| format!("missing value for {key}"))
}

fn optional_arg(name: &str) -> Option<String> {
    let key = format!("--{name}");
    let args: Vec<String> = env::args().collect();
    args.iter()
        .position(|item| item == &key)
        .and_then(|index| args.get(index + 1).cloned())
}

async fn connect_client() -> Result<OpenShellClient> {
    let endpoint = arg("endpoint")?;
    let server_name = arg("server-name")?;
    let ca_path = arg("ca")?;
    let cert_path = optional_arg("cert");
    let key_path = optional_arg("key");
    connect_client_to(
        &endpoint,
        &server_name,
        &ca_path,
        cert_path.as_deref(),
        key_path.as_deref(),
        30,
    )
    .await
}

async fn connect_client_to(
    endpoint: &str,
    server_name: &str,
    ca_path: &str,
    cert_path: Option<&str>,
    key_path: Option<&str>,
    request_timeout_seconds: u64,
) -> Result<OpenShellClient> {
    let ca = fs::read(ca_path).context("read CA certificate")?;
    let tls = ClientTlsConfig::new()
        .ca_certificate(Certificate::from_pem(ca))
        .domain_name(server_name.to_string());
    let tls = match (cert_path, key_path) {
        (Some(cert), Some(key)) => tls.identity(Identity::from_pem(
            fs::read(cert).context("read client certificate")?,
            fs::read(key).context("read client private key")?,
        )),
        (None, None) => tls,
        _ => bail!("--cert and --key must be supplied together"),
    };
    let channel = Endpoint::from_shared(endpoint.to_string())?
        .connect_timeout(Duration::from_secs(request_timeout_seconds.min(5)))
        .timeout(Duration::from_secs(request_timeout_seconds))
        .tls_config(tls)?
        .connect()
        .await
        .context("verified mTLS connection")?;
    Ok(OpenShellClient::from_parts(
        channel,
        EdgeAuthInterceptor::noop(),
    ))
}

async fn tls_probe() -> Result<Vec<Record>> {
    let mut records = Vec::new();
    let expect_allow = arg("expect")? == "allow";
    match connect_client().await {
        Ok(client) => {
            let health = client.health().await;
            let listing = client.list_all_sandboxes(ListOptions::default()).await;
            let current_user = client
                .raw_grpc()
                .get_current_user(proto::GetCurrentUserRequest {})
                .await;
            match (health, listing, current_user) {
                (Ok(health), Ok(sandboxes), Ok(user)) => {
                    let detail = json!({
                        "health_status": format!("{:?}", health.status),
                        "gateway_version": health.version,
                        "authenticated_list_allowed": true,
                        "visible_sandbox_count": sandboxes.len(),
                        "authenticated_subject": user.into_inner().subject
                    });
                    records.push(record("verified_mtls_and_authenticated_control_api", if expect_allow {
                        Ok(detail)
                    } else {
                        Err(anyhow::anyhow!("unexpectedly authenticated list_sandboxes"))
                    }));
                }
                (Ok(health), Err(error), _) => records.push(record("verified_mtls_and_authenticated_control_api", if expect_allow {
                    Err(error.into())
                } else {
                    Ok(json!({"health_is_public": format!("{:?}", health.status), "denied_at": "list_sandboxes", "reason": format!("{error:#}")}))
                })),
                (Ok(_), Ok(_), Err(error)) => records.push(record("verified_mtls_and_authenticated_control_api", if expect_allow {
                    Err(error.into())
                } else {
                    Ok(json!({"denied_at": "get_current_user", "reason": format!("{error:#}")}))
                })),
                (Err(error), _, _) => records.push(record("verified_mtls_and_authenticated_control_api", if expect_allow {
                    Err(error.into())
                } else {
                    Ok(json!({"denied_at": "health_rpc", "reason": format!("{error:#}")}))
                })),
            }
        }
        Err(error) => records.push(record(
            "verified_mtls_and_gateway_identity",
            if expect_allow {
                Err(error)
            } else {
                Ok(json!({"denied_at": "verified_mtls_handshake", "reason": format!("{error:#}")}))
            },
        )),
    }
    Ok(records)
}

fn interactive_start(
    sandbox: &str,
    command: Vec<String>,
    request_id: String,
) -> proto::ExecSandboxInput {
    proto::ExecSandboxInput {
        payload: Some(proto::exec_sandbox_input::Payload::Start(
            ExecSandboxRequest {
                workspace_scope: Some(proto::workspace_selector("default")),
                sandbox: sandbox.to_string(),
                command,
                workdir: String::new(),
                environment: HashMap::new(),
                execution_timeout: None,
                stdin: Vec::new(),
                tty: false,
                cols: 0,
                rows: 0,
                no_login_shell: true,
                request_id,
            },
        )),
    }
}

async fn duplex_probe(client: &OpenShellClient, sandbox: &str) -> Result<Value> {
    let mut grpc = client.raw_grpc();
    let (tx, rx) = mpsc::channel(4);
    tx.send(interactive_start(
        sandbox,
        vec![
            "/bin/sh".into(),
            "-c".into(),
            "printf 'out-start'; printf 'err-start' >&2; printf '%1048576s' ''; cat".into(),
        ],
        Uuid::new_v4().to_string(),
    ))
    .await
    .context("send interactive start")?;
    let response = grpc
        .exec_sandbox_interactive(ReceiverStream::new(rx))
        .await?;
    let mut stream = response.into_inner();
    let mut stdout = Vec::new();
    let mut stderr = Vec::new();
    let mut initial_out_seen = false;
    let mut initial_err_seen = false;
    for _ in 0..256 {
        if initial_out_seen && initial_err_seen {
            break;
        }
        let event = timeout(Duration::from_secs(10), stream.message())
            .await
            .context("initial output timeout")??
            .context("interactive stream ended before initial output")?;
        match event.payload {
            Some(proto::exec_sandbox_event::Payload::Stdout(chunk)) => {
                stdout.extend(&chunk.data);
                initial_out_seen |= stdout.windows(9).any(|x| x == b"out-start");
            }
            Some(proto::exec_sandbox_event::Payload::Stderr(chunk)) => {
                stderr.extend(&chunk.data);
                initial_err_seen |= stderr.windows(9).any(|x| x == b"err-start");
            }
            Some(proto::exec_sandbox_event::Payload::Exit(exit)) => {
                bail!("command exited early: {}", exit.exit_code)
            }
            None => {}
        }
    }
    anyhow::ensure!(
        initial_out_seen && initial_err_seen,
        "did not receive distinct initial stdout/stderr markers"
    );

    // Pause stream consumption while the child writes 1 MiB; resume afterward.
    tokio::time::sleep(Duration::from_millis(500)).await;
    tx.send(proto::ExecSandboxInput {
        payload: Some(proto::exec_sandbox_input::Payload::Stdin(
            b"split-".to_vec(),
        )),
    })
    .await
    .context("send first stdin frame")?;
    while !stdout.windows(6).any(|w| w == b"split-") {
        let event = timeout(Duration::from_secs(10), stream.message())
            .await
            .context("first stdin echo timeout")??
            .context("stream ended before first stdin echo")?;
        match event.payload {
            Some(proto::exec_sandbox_event::Payload::Stdout(chunk)) => stdout.extend(chunk.data),
            Some(proto::exec_sandbox_event::Payload::Stderr(chunk)) => stderr.extend(chunk.data),
            Some(proto::exec_sandbox_event::Payload::Exit(exit)) => {
                bail!("command exited early: {}", exit.exit_code)
            }
            None => {}
        }
    }
    tx.send(proto::ExecSandboxInput {
        payload: Some(proto::exec_sandbox_input::Payload::Stdin(
            b"frame\0tail".to_vec(),
        )),
    })
    .await
    .context("send second split/binary stdin frame")?;
    drop(tx); // Half-close input; `cat` must see EOF and exit.

    let mut exit_code = None;
    for _ in 0..512 {
        let event = timeout(Duration::from_secs(10), stream.message())
            .await
            .context("final stream timeout")??
            .context("stream ended without exit frame")?;
        match event.payload {
            Some(proto::exec_sandbox_event::Payload::Stdout(chunk)) => stdout.extend(chunk.data),
            Some(proto::exec_sandbox_event::Payload::Stderr(chunk)) => stderr.extend(chunk.data),
            Some(proto::exec_sandbox_event::Payload::Exit(exit)) => {
                exit_code = Some(exit.exit_code);
                break;
            }
            None => {}
        }
    }
    let echoed = b"split-frame\0tail";
    let stdout_tail = stdout.windows(echoed.len()).any(|w| w == echoed);
    let distinct_streams = stdout.windows(9).any(|w| w == b"out-start")
        && stderr.windows(9).any(|w| w == b"err-start");
    anyhow::ensure!(stdout_tail, "stdout missing exact split-frame/NUL echo");
    anyhow::ensure!(
        distinct_streams,
        "stdout/stderr markers were not kept separate"
    );
    anyhow::ensure!(
        exit_code == Some(0),
        "expected exit 0, observed {exit_code:?}"
    );
    let zero_start = b"out-start".len();
    let zero_end = zero_start + (1024 * 1024);
    anyhow::ensure!(
        stdout.len() == zero_end + echoed.len(),
        "unexpected stdout byte count: {} (expected {}; stderr bytes {}; exit code {:?}; stdout prefix {:?}; stderr prefix {:?})",
        stdout.len(),
        zero_end + echoed.len(),
        stderr.len(),
        exit_code,
        &stdout[..stdout.len().min(32)],
        &stderr[..stderr.len().min(32)]
    );
    anyhow::ensure!(
        stdout[zero_start..zero_end]
            .iter()
            .all(|byte| *byte == b' '),
        "space stream changed bytes"
    );
    let hash = Sha256::digest(&stdout);
    Ok(json!({
        "exit_code": exit_code,
        "stdout_len": stdout.len(),
        "child_space_output_bytes": 1024 * 1024,
        "stderr_base64": base64::engine::general_purpose::STANDARD.encode(stderr),
        "stdout_sha256": format!("{hash:x}"),
        "initial_stdout_and_stderr_before_input": true,
        "input_frames": ["split-", "frame\\0tail"],
        "half_close_eof_exit": true,
        "receiver_pause_ms": 500,
        "all_assertions_passed": true
    }))
}

async fn exec_case(
    client: &OpenShellClient,
    sandbox: &str,
    operation: &str,
    command: &[String],
    expected_exit: i32,
    expected_stdout: &[u8],
    expected_stderr: &[u8],
) -> Record {
    let result = client
        .exec(sandbox, command, ExecOptions::default())
        .await
        .map_err(Into::into)
        .and_then(|exec| {
            anyhow::ensure!(
                exec.exit_code == expected_exit,
                "expected exit {expected_exit}, got {}",
                exec.exit_code
            );
            anyhow::ensure!(
                exec.stdout == expected_stdout,
                "stdout bytes did not match expectation"
            );
            anyhow::ensure!(
                exec.stderr == expected_stderr,
                "stderr bytes did not match expectation"
            );
            value(json!({
                "exit_code": exec.exit_code,
                "stdout_base64": base64::engine::general_purpose::STANDARD.encode(exec.stdout),
                "stderr_base64": base64::engine::general_purpose::STANDARD.encode(exec.stderr)
            }))
        });
    record(operation, result)
}

fn create_request(name: &str, image: &str, request_id: &str) -> proto::CreateSandboxRequest {
    let labels = HashMap::from([("jackin-poc.test-id".to_string(), name.to_string())]);
    proto::CreateSandboxRequest {
        workspace_scope: Some(proto::workspace_selector("default")),
        spec: Some(proto::SandboxSpec {
            template: Some(proto::SandboxTemplate {
                image: image.to_string(),
                ..Default::default()
            }),
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
    }
}

async fn create_with_dedup(
    client: &OpenShellClient,
    name: &str,
    image: &str,
) -> Result<(String, Value)> {
    let request_id = Uuid::new_v4().to_string();
    let request = create_request(name, image, &request_id);
    let mut grpc = client.raw_grpc();
    let first = grpc.create_sandbox(request.clone()).await?.into_inner();
    drop(first); // Deliberately discard the response, then retry identical request ID and payload.
    let second = grpc.create_sandbox(request).await?.into_inner();
    let second_id = second
        .sandbox
        .context("retry create omitted sandbox")?
        .metadata
        .context("retry create omitted metadata")?
        .id;
    let list = client.list_sandboxes(ListOptions::default());
    let all = list.collect_all().await?;
    let matches: Vec<_> = all.iter().filter(|item| item.name == name).collect();
    anyhow::ensure!(
        matches.len() == 1,
        "same request ID retry created {} resources with same name",
        matches.len()
    );
    anyhow::ensure!(
        matches[0].id == second_id,
        "retry response ID differs from unique listed resource"
    );
    Ok((
        second_id.clone(),
        json!({
            "request_id": request_id,
            "first_response_discarded_by_harness": true,
            "retry_id": second_id,
            "one_resource_with_name": true,
            "idempotency_contract": "at-most-once request admission; harness discards acknowledgement after response, not a network packet drop"
        }),
    ))
}

async fn exec_lost_response_probe(client: &OpenShellClient, sandbox: &str) -> Result<Value> {
    let marker = format!("/tmp/jfr-20261024-once-{}", Uuid::new_v4());
    let request_id = Uuid::new_v4().to_string();
    let request = ExecSandboxRequest {
        workspace_scope: Some(proto::workspace_selector("default")),
        sandbox: sandbox.to_string(),
        command: vec![
            "/bin/sh".into(),
            "-c".into(),
            format!("printf x >> '{marker}'; printf READY; sleep 2; printf DONE"),
        ],
        workdir: String::new(),
        environment: HashMap::new(),
        execution_timeout: None,
        stdin: Vec::new(),
        tty: false,
        cols: 0,
        rows: 0,
        no_login_shell: true,
        request_id: request_id.clone(),
    };
    let mut grpc = client.raw_grpc();
    let mut stream = grpc.exec_sandbox(request.clone()).await?.into_inner();
    let mut first_stdout = Vec::new();
    for _ in 0..32 {
        let event = timeout(Duration::from_secs(10), stream.message())
            .await??
            .context("exec stream ended before READY")?;
        if let Some(proto::exec_sandbox_event::Payload::Stdout(chunk)) = event.payload {
            first_stdout.extend(chunk.data);
            if first_stdout.windows(5).any(|w| w == b"READY") {
                break;
            }
        }
    }
    anyhow::ensure!(
        first_stdout.windows(5).any(|w| w == b"READY"),
        "did not observe execution start"
    );
    drop(stream); // Disconnect before terminal completion; do not replay the prompt.
    tokio::time::sleep(Duration::from_millis(2200)).await;
    let duplicate = grpc.exec_sandbox(request).await;
    let duplicate_outcome = match duplicate {
        Ok(response) => {
            let mut duplicate_stream = response.into_inner();
            let mut events = 0u32;
            for _ in 0..32 {
                match timeout(Duration::from_secs(2), duplicate_stream.message()).await {
                    Ok(Ok(Some(_))) => events += 1,
                    Ok(Ok(None)) | Ok(Err(_)) | Err(_) => break,
                }
            }
            format!("accepted_stream_events={events}; output is not replay evidence")
        }
        Err(error) => format!("rejected_duplicate: {error}"),
    };
    let marker_read = client
        .exec(
            sandbox,
            &["/bin/sh".into(), "-c".into(), format!("cat '{marker}'")],
            ExecOptions::default(),
        )
        .await?;
    anyhow::ensure!(
        marker_read.exit_code == 0,
        "marker read failed: {}",
        marker_read.exit_code
    );
    anyhow::ensure!(
        marker_read.stdout == b"x",
        "duplicate request caused marker count/content {:?}",
        marker_read.stdout
    );
    Ok(json!({
        "request_id": request_id,
        "first_stream_disconnected_after": "READY, before terminal completion",
        "duplicate_outcome": duplicate_outcome,
        "marker_base64": base64::engine::general_purpose::STANDARD.encode(marker_read.stdout),
        "marker_written_once": true
    }))
}

async fn lifecycle_probe() -> Result<Vec<Record>> {
    let client = connect_client().await?;
    let name = arg("name")?;
    let image = arg("image")?;
    let mut records = vec![record(
        "authenticated_gateway_health",
        client.health().await.map(|health| {
            json!({"status": format!("{:?}", health.status), "version": health.version})
        }).map_err(Into::into),
    )];
    let id = match create_with_dedup(&client, &name, &image).await {
        Ok((id, detail)) => {
            records.push(record("create_same_request_id_retry", Ok(detail)));
            id
        }
        Err(error) => {
            records.push(record("create_same_request_id_retry", Err(error)));
            return Ok(records);
        }
    };
    let mut target_ok = true;

    records.push(record(
        "wait_ready",
        client.wait_ready(&name, Duration::from_secs(120)).await.map(|sandbox| {
            target_ok = sandbox.id == id;
            json!({"id": sandbox.id, "phase": format!("{:?}", sandbox.phase), "same_id": target_ok})
        }).map_err(Into::into),
    ));
    records.push(record(
        "get_inspect",
        client.get_sandbox(&name).await.map(|sandbox| {
            target_ok &= sandbox.id == id;
            json!({"id": sandbox.id, "name": sandbox.name, "phase": format!("{:?}", sandbox.phase), "same_id": target_ok})
        }).map_err(Into::into),
    ));
    records.push(record(
        "list",
        client.list_all_sandboxes(ListOptions::default()).await.map(|sandboxes| {
            let items: Vec<Value> = sandboxes.iter().map(|sandbox| {
                json!({"id": sandbox.id, "name": sandbox.name, "phase": format!("{:?}", sandbox.phase)})
            }).collect();
            json!({"items": items, "target_present_by_id": sandboxes.iter().any(|sandbox| sandbox.id == id)})
        }).map_err(Into::into),
    ));

    let literal = "space and \"quotes\" ; touch /tmp/jfr-20261024-should-not-exist";
    let literal_command = vec![
        "/bin/sh".into(),
        "-c".into(),
        "printf '%s' \"$1\"; test ! -e /tmp/jfr-20261024-should-not-exist".into(),
        "probe".into(),
        literal.into(),
    ];
    records.push(
        exec_case(
            &client,
            &name,
            "exec_literal_argv",
            &literal_command,
            0,
            literal.as_bytes(),
            b"",
        )
        .await,
    );
    let status_command = vec![
        "/bin/sh".into(),
        "-c".into(),
        "printf 'stdout-marker'; printf 'stderr-marker' >&2; exit 23".into(),
    ];
    records.push(
        exec_case(
            &client,
            &name,
            "exec_status_separate_streams",
            &status_command,
            23,
            b"stdout-marker",
            b"stderr-marker",
        )
        .await,
    );
    records.push(record(
        "interactive_duplex_binary_backpressure_eof",
        duplex_probe(&client, &name).await,
    ));
    records.push(record(
        "exec_disconnect_same_request_id_dedup",
        exec_lost_response_probe(&client, &name).await,
    ));

    records.push(record(
        "stop",
        client.stop_sandbox(&name).await.map(|sandbox| {
            target_ok &= sandbox.id == id;
            json!({"id": sandbox.id, "phase": format!("{:?}", sandbox.phase), "same_id": target_ok})
        }).map_err(Into::into),
    ));
    records.push(record(
        "start",
        client.start_sandbox(&name).await.map(|sandbox| {
            target_ok &= sandbox.id == id;
            json!({"id": sandbox.id, "phase": format!("{:?}", sandbox.phase), "same_id": target_ok})
        }).map_err(Into::into),
    ));
    records.push(record(
        "wait_ready_after_start",
        client.wait_ready(&name, Duration::from_secs(120)).await.map(|sandbox| {
            target_ok &= sandbox.id == id;
            json!({"id": sandbox.id, "phase": format!("{:?}", sandbox.phase), "same_id": target_ok})
        }).map_err(Into::into),
    ));
    // Capture an immutable old-context stop request while the original sandbox exists.
    // The released schema has only name + request ID, no sandbox ID or generation.
    let delayed_stop_request = proto::StopSandboxRequest {
        workspace_scope: Some(proto::workspace_selector("default")),
        name: name.clone(),
        request_id: Uuid::new_v4().to_string(),
    }
    .encode_to_vec();
    records.push(record(
        "delete_and_confirm_original_id",
        async {
            let deleted = client
                .delete_sandbox(&name, DeleteOptions::default())
                .await?;
            if deleted.sandbox_id.as_deref() != Some(id.as_str()) {
                bail!("delete acknowledgement did not identify original sandbox ID");
            }
            client
                .wait_deleted(&name, Duration::from_secs(60), Some(&id))
                .await?;
            Ok(json!({"id": id, "outcome": format!("{:?}", deleted.outcome), "confirmed": true}))
        }
        .await,
    ));
    records.push(stale_name_probe(&client, &name, &image, delayed_stop_request).await);
    Ok(records)
}

async fn duplex_only_probe() -> Result<Vec<Record>> {
    let endpoint = arg("endpoint")?;
    let server_name = arg("server-name")?;
    let ca = fs::read(arg("ca")?).context("read CA certificate")?;
    let cert = fs::read(arg("cert")?).context("read client certificate")?;
    let key = fs::read(arg("key")?).context("read client key")?;
    let tls = ClientTlsConfig::new()
        .ca_certificate(Certificate::from_pem(ca))
        .domain_name(server_name)
        .identity(Identity::from_pem(cert, key));
    let channel = Endpoint::from_shared(endpoint)?
        .connect_timeout(Duration::from_secs(5))
        .timeout(Duration::from_secs(30))
        .tls_config(tls)?
        .connect()
        .await
        .context("verified mTLS connection")?;
    let client = OpenShellClient::from_parts(channel, EdgeAuthInterceptor::noop());
    let name = arg("name")?;
    let image = arg("image")?;
    let (id, created) = create_with_dedup(&client, &name, &image).await?;
    let mut records = vec![record("create", Ok(created))];
    client.wait_ready(&name, Duration::from_secs(120)).await?;
    records.push(record(
        "interactive_duplex_binary_backpressure_eof",
        duplex_probe(&client, &name).await,
    ));
    let deleted = client
        .delete_sandbox(&name, DeleteOptions::default())
        .await?;
    anyhow::ensure!(
        deleted.sandbox_id.as_deref() == Some(id.as_str()),
        "delete acknowledgement identified a different sandbox"
    );
    client
        .wait_deleted(&name, Duration::from_secs(60), Some(&id))
        .await?;
    records.push(record("delete_confirmed", Ok(json!({"id": id}))));
    Ok(records)
}

async fn pty_read_until(
    stream: &mut tonic::Streaming<proto::ExecSandboxEvent>,
    output: &mut Vec<u8>,
    needle: &[u8],
) -> Result<()> {
    while !output.windows(needle.len()).any(|window| window == needle) {
        let event = timeout(Duration::from_secs(10), stream.message())
            .await
            .with_context(|| {
                format!(
                    "PTY output timeout waiting for {:?}; captured {} bytes, prefix {:?}",
                    String::from_utf8_lossy(needle),
                    output.len(),
                    &output[..output.len().min(96)]
                )
            })??
            .with_context(|| {
                format!(
                    "PTY stream ended before marker {:?}; captured {} bytes, prefix {:?}",
                    String::from_utf8_lossy(needle),
                    output.len(),
                    &output[..output.len().min(96)]
                )
            })?;
        match event.payload {
            Some(proto::exec_sandbox_event::Payload::Stdout(chunk)) => output.extend(chunk.data),
            Some(proto::exec_sandbox_event::Payload::Stderr(chunk)) => output.extend(chunk.data),
            Some(proto::exec_sandbox_event::Payload::Exit(exit)) => {
                bail!("PTY exited before marker with code {}", exit.exit_code)
            }
            None => {}
        }
    }
    Ok(())
}

async fn pty_probe(client: &OpenShellClient, sandbox: &str) -> Result<Value> {
    let mut grpc = client.raw_grpc();
    let (tx, rx) = mpsc::channel(8);
    let mut start = interactive_start(
        sandbox,
        vec![
            "/bin/sh".into(),
            "-c".into(),
            "stty size; printf 'PTY_READY\\n'; while :; do current=$(stty size); if [ \"$current\" = '37 101' ]; then printf 'PTY_RESIZED:%s\\n' \"$current\"; break; fi; sleep 0.1; done; IFS= read -r line; printf 'PTY_INPUT:%s\\n' \"$line\"; sleep 300".into(),
        ],
        Uuid::new_v4().to_string(),
    );
    if let Some(proto::exec_sandbox_input::Payload::Start(request)) = &mut start.payload {
        request.tty = true;
        request.cols = 80;
        request.rows = 24;
    }
    tx.send(start).await.context("send PTY start")?;
    let response = grpc
        .exec_sandbox_interactive(ReceiverStream::new(rx))
        .await?;
    let mut stream = response.into_inner();
    let mut output = Vec::new();
    let mut exit_code = None;
    pty_read_until(&mut stream, &mut output, b"PTY_READY").await?;
    tx.send(proto::ExecSandboxInput {
        payload: Some(proto::exec_sandbox_input::Payload::Resize(
            proto::ExecSandboxWindowResize {
                cols: 101,
                rows: 37,
            },
        )),
    })
    .await
    .context("send PTY resize")?;
    pty_read_until(&mut stream, &mut output, b"PTY_RESIZED:37 101").await?;
    tx.send(proto::ExecSandboxInput {
        payload: Some(proto::exec_sandbox_input::Payload::Stdin(
            b"input with spaces\n".to_vec(),
        )),
    })
    .await
    .context("send PTY text input")?;
    pty_read_until(&mut stream, &mut output, b"PTY_INPUT:input with spaces").await?;
    tx.send(proto::ExecSandboxInput {
        payload: Some(proto::exec_sandbox_input::Payload::Stdin(vec![0x03])),
    })
    .await
    .context("send PTY Ctrl-C")?;
    while exit_code.is_none() {
        let event = timeout(Duration::from_secs(10), stream.message())
            .await
            .context("PTY interrupt exit timeout")??
            .context("PTY stream ended without exit frame")?;
        match event.payload {
            Some(proto::exec_sandbox_event::Payload::Stdout(chunk)) => output.extend(chunk.data),
            Some(proto::exec_sandbox_event::Payload::Stderr(chunk)) => output.extend(chunk.data),
            Some(proto::exec_sandbox_event::Payload::Exit(exit)) => {
                exit_code = Some(exit.exit_code)
            }
            None => {}
        }
    }
    drop(tx);
    let mut reconnect = client.raw_grpc();
    let (reconnect_tx, reconnect_rx) = mpsc::channel(2);
    let reconnect_id = Uuid::new_v4().to_string();
    let mut reconnect_start = interactive_start(
        sandbox,
        vec!["/bin/sh".into(), "-c".into(), "printf PTY_NEW_EXEC".into()],
        reconnect_id,
    );
    if let Some(proto::exec_sandbox_input::Payload::Start(request)) = &mut reconnect_start.payload {
        request.tty = true;
        request.cols = 101;
        request.rows = 37;
    }
    reconnect_tx.send(reconnect_start).await?;
    let response = reconnect
        .exec_sandbox_interactive(ReceiverStream::new(reconnect_rx))
        .await?;
    let mut reconnect_stream = response.into_inner();
    let mut reconnect_output = Vec::new();
    let mut reconnect_exit = None;
    for _ in 0..32 {
        let event = timeout(Duration::from_secs(10), reconnect_stream.message())
            .await
            .context("new PTY exec response timeout")??
            .context("new PTY exec stream ended without event")?;
        match event.payload {
            Some(proto::exec_sandbox_event::Payload::Stdout(chunk)) => {
                reconnect_output.extend(chunk.data)
            }
            Some(proto::exec_sandbox_event::Payload::Stderr(chunk)) => {
                reconnect_output.extend(chunk.data)
            }
            Some(proto::exec_sandbox_event::Payload::Exit(exit)) => {
                reconnect_exit = Some(exit.exit_code);
                break;
            }
            None => {}
        }
    }
    drop(reconnect_tx);
    anyhow::ensure!(
        output
            .windows(b"PTY_READY".len())
            .any(|w| w == b"PTY_READY"),
        "initial PTY output missing"
    );
    anyhow::ensure!(
        output
            .windows(b"PTY_RESIZED:".len())
            .any(|w| w == b"PTY_RESIZED:"),
        "resize trap missing"
    );
    anyhow::ensure!(
        output.windows(b"37 101".len()).any(|w| w == b"37 101"),
        "PTY size was not updated to rows=37 cols=101"
    );
    anyhow::ensure!(
        output
            .windows(b"PTY_INPUT:input with spaces".len())
            .any(|w| w == b"PTY_INPUT:input with spaces"),
        "PTY text input missing"
    );
    anyhow::ensure!(exit_code.is_some(), "Ctrl-C did not produce an exit event");
    anyhow::ensure!(
        reconnect_output
            .windows(b"PTY_NEW_EXEC".len())
            .any(|w| w == b"PTY_NEW_EXEC"),
        "new PTY exec did not return its marker"
    );
    anyhow::ensure!(
        reconnect_exit == Some(0),
        "new PTY exec did not exit 0: {reconnect_exit:?}"
    );
    Ok(json!({
        "initial_window": {"rows":24,"cols":80},
        "resize_sent": {"rows":37,"cols":101},
        "resize_observed_by_stty": output.windows(b"37 101".len()).any(|w| w == b"37 101"),
        "text_input_received": true,
        "ctrl_c_exit_code": exit_code,
        "reconnect_behavior": "new ExecSandboxInteractive request; not process/session reattachment",
        "new_exec_exit_code": reconnect_exit,
        "pty_output_bytes": output.len()
    }))
}

async fn pty_only_probe() -> Result<Vec<Record>> {
    let client = connect_client().await?;
    let name = arg("name")?;
    let image = arg("image")?;
    let (id, created) = create_with_dedup(&client, &name, &image).await?;
    let mut records = vec![record("create", Ok(created))];
    client.wait_ready(&name, Duration::from_secs(120)).await?;
    records.push(record(
        "pty_resize_input_interrupt_reconnect",
        pty_probe(&client, &name).await,
    ));
    let deletion = async {
        let deleted = client
            .delete_sandbox(&name, DeleteOptions::default())
            .await?;
        anyhow::ensure!(
            deleted.sandbox_id.as_deref() == Some(id.as_str()),
            "delete ID mismatch"
        );
        client
            .wait_deleted(&name, Duration::from_secs(60), Some(&id))
            .await?;
        Ok::<(), anyhow::Error>(())
    }
    .await;
    records.push(record(
        "delete_confirmed",
        deletion.map(|_| json!({"id":id})),
    ));
    Ok(records)
}

async fn stale_delete_probe(client: &OpenShellClient, name: &str, image: &str) -> Record {
    let (original_id, _) = match create_with_dedup(client, name, image).await {
        Ok(created) => created,
        Err(error) => return record("stale_delete_after_reuse", Err(error)),
    };
    if let Err(error) = client.wait_ready(name, Duration::from_secs(120)).await {
        return record(
            "stale_delete_after_reuse",
            Err(anyhow::anyhow!("{error:#}")),
        );
    }
    let old_request = proto::DeleteSandboxRequest {
        workspace_scope: Some(proto::workspace_selector("default")),
        name: name.to_string(),
        allow_missing: false,
        request_id: Uuid::new_v4().to_string(),
    }
    .encode_to_vec();
    let old_request_id = match proto::DeleteSandboxRequest::decode(old_request.as_slice()) {
        Ok(request) => request.request_id,
        Err(error) => return record("stale_delete_after_reuse", Err(anyhow::anyhow!(error))),
    };
    let original_delete = client.delete_sandbox(name, DeleteOptions::default()).await;
    let original_delete_ok = match original_delete {
        Ok(deleted) if deleted.sandbox_id.as_deref() == Some(original_id.as_str()) => client
            .wait_deleted(name, Duration::from_secs(60), Some(&original_id))
            .await
            .is_ok(),
        _ => false,
    };
    if !original_delete_ok {
        return record(
            "stale_delete_after_reuse",
            Err(anyhow::anyhow!(
                "could not delete original and confirm by immutable ID"
            )),
        );
    }
    let (replacement_id, _) = match create_with_dedup(client, name, image).await {
        Ok(created) => created,
        Err(error) => return record("stale_delete_after_reuse", Err(error)),
    };
    if let Err(error) = client.wait_ready(name, Duration::from_secs(120)).await {
        let _ = client.delete_sandbox(name, DeleteOptions::default()).await;
        return record(
            "stale_delete_after_reuse",
            Err(anyhow::anyhow!("{error:#}")),
        );
    }
    let request = match proto::DeleteSandboxRequest::decode(old_request.as_slice()) {
        Ok(request) => request,
        Err(error) => return record("stale_delete_after_reuse", Err(anyhow::anyhow!(error))),
    };
    let mut grpc = client.raw_grpc();
    let old_delete = grpc.delete_sandbox(request).await;
    let (rpc_succeeded, response_id, error) = match old_delete {
        Ok(response) => {
            let response = response.into_inner();
            (true, Some(response.sandbox_id), None)
        }
        Err(error) => (false, None, Some(format!("{error:#}"))),
    };
    let replacement_absent = client
        .wait_deleted(name, Duration::from_secs(30), Some(&replacement_id))
        .await
        .is_ok();
    let cleanup_ok = if replacement_absent {
        true
    } else {
        let cleanup = async {
            let result = client
                .delete_sandbox(name, DeleteOptions::default())
                .await?;
            anyhow::ensure!(result.sandbox_id.as_deref() == Some(replacement_id.as_str()));
            client
                .wait_deleted(name, Duration::from_secs(60), Some(&replacement_id))
                .await?;
            Ok::<(), anyhow::Error>(())
        }
        .await;
        cleanup.is_ok()
    };
    let stale_delete_rejected = !replacement_absent;
    let detail = json!({
        "old_request_id": old_request_id,
        "request_bytes_captured_before_original_delete": true,
        "original_delete_confirmed": original_delete_ok,
        "replacement_id": replacement_id,
        "stale_delete_rpc_succeeded": rpc_succeeded,
        "stale_delete_rpc_response_sandbox_id": response_id,
        "stale_delete_rpc_error": error,
        "replacement_absent_after_old_request": replacement_absent,
        "stale_delete_rejected": stale_delete_rejected,
        "cleanup_confirmed": cleanup_ok
    });
    if replacement_absent {
        Record {
            operation: "stale_delete_after_reuse".into(),
            ok: false,
            detail: Some(detail),
            error: Some("preconstructed old-context delete removed same-name replacement".into()),
        }
    } else if !cleanup_ok {
        Record {
            operation: "stale_delete_after_reuse".into(),
            ok: false,
            detail: Some(detail),
            error: Some("replacement cleanup failed after stale delete check".into()),
        }
    } else {
        Record {
            operation: "stale_delete_after_reuse".into(),
            ok: true,
            detail: Some(detail),
            error: None,
        }
    }
}

async fn stale_delete_only_probe() -> Result<Vec<Record>> {
    let client = connect_client().await?;
    let name = arg("name")?;
    let image = arg("image")?;
    Ok(vec![stale_delete_probe(&client, &name, &image).await])
}

async fn watch_lifecycle(
    client: &OpenShellClient,
    target: &str,
    name: &str,
    expected_id: &str,
) -> Result<Value> {
    let mut grpc = client.raw_grpc();
    let request = proto::WatchSandboxRequest {
        workspace_scope: Some(proto::workspace_selector("default")),
        sandbox: name.to_string(),
        follow_status: true,
        follow_logs: false,
        follow_events: true,
        log_tail_lines: 0,
        event_tail: 0,
        stop_on_terminal: false,
        since_time: None,
        log_sources: Vec::new(),
        log_min_level: String::new(),
        resume_after_cursor: String::new(),
    };
    let response = grpc.watch_sandbox(request).await?;
    let mut stream = response.into_inner();
    let first = timeout(Duration::from_secs(5), stream.message())
        .await
        .context("watch initial event timeout")??
        .context("watch ended before first event")?;
    let first_event = stream_event_summary(target, first, expected_id);
    let stopped = client.stop_sandbox(name).await?;
    anyhow::ensure!(
        stopped.id == expected_id,
        "stop returned wrong target ID on {target}"
    );
    let started = client.start_sandbox(name).await?;
    anyhow::ensure!(
        started.id == expected_id,
        "start returned wrong target ID on {target}"
    );
    client.wait_ready(name, Duration::from_secs(120)).await?;

    let mut subsequent = Vec::new();
    let mut saw_ready_event = false;
    for _ in 0..8 {
        let received = timeout(Duration::from_secs(2), stream.message()).await;
        let Ok(Ok(Some(event))) = received else { break };
        let summary = stream_event_summary(target, event, expected_id);
        saw_ready_event |= summary["phase"] == "Ready";
        subsequent.push(summary);
        if saw_ready_event {
            break;
        }
    }
    let fresh = client.get_sandbox(name).await?;
    let fresh_phase = format!("{:?}", fresh.phase);
    let fresh_matches_target = fresh.id == expected_id && fresh_phase == "Ready";
    Ok(json!({
        "target": target,
        "name": name,
        "expected_sandbox_id": expected_id,
        "first_watch_event": first_event,
        "watch_events_after_stop_start": subsequent,
        "saw_ready_event_after_restart": saw_ready_event,
        "fresh_query": {"id": fresh.id, "phase": fresh_phase},
        "fresh_query_matches_target_ready": fresh_matches_target,
        "watch_event_is_observation_not_current_state": true
    }))
}

fn stream_event_summary(
    target: &str,
    event: proto::SandboxStreamEvent,
    expected_id: &str,
) -> Value {
    match event.payload {
        Some(proto::sandbox_stream_event::Payload::Sandbox(sandbox)) => {
            let id = sandbox
                .metadata
                .as_ref()
                .map(|metadata| metadata.id.clone())
                .unwrap_or_default();
            let phase = sandbox
                .status
                .as_ref()
                .and_then(|status| proto::SandboxPhase::try_from(status.phase).ok())
                .map(|phase| format!("{phase:?}"));
            json!({
                "target": target,
                "payload": "sandbox_snapshot",
                "sandbox_id": id,
                "phase": phase,
                "identity_matches_expected": id == expected_id,
                "cursor_present": !event.cursor.is_empty()
            })
        }
        Some(_) => {
            json!({"target": target, "payload": "non_snapshot_event", "cursor_present": !event.cursor.is_empty()})
        }
        None => {
            json!({"target": target, "payload": "empty", "cursor_present": !event.cursor.is_empty()})
        }
    }
}

async fn two_target_probe() -> Result<Vec<Record>> {
    let name = "jfrdup24";
    let image = "nvcr.io/nvidia/base/ubuntu@sha256:7e0f726d635d440d28a7f18e6498d3bdb76c7038bd4c90a090c21eb7c9f40686";
    let gateway_a = connect_client_to(
        "https://127.0.0.1:28470",
        "localhost",
        "../gateway-a/certs/ca.crt",
        Some("private/certs/control-client.crt"),
        Some("private/certs/control-client.key"),
        5,
    )
    .await?;
    let linux_gateway = connect_client_to(
        "https://192.168.139.147:18470",
        "192.168.139.147",
        "../targets/private/certs/jfr-linux-ca.crt",
        Some("../targets/private/certs/jfr-linux-client.crt"),
        Some("private/certs/control-vm.key"),
        5,
    )
    .await?;
    let user_a = gateway_a
        .raw_grpc()
        .get_current_user(proto::GetCurrentUserRequest {})
        .await?
        .into_inner()
        .subject;
    let user_linux = linux_gateway
        .raw_grpc()
        .get_current_user(proto::GetCurrentUserRequest {})
        .await?
        .into_inner()
        .subject;
    let (id_a, _) = create_with_dedup(&gateway_a, name, image).await?;
    let (id_linux, _) = match create_with_dedup(&linux_gateway, name, image).await {
        Ok(created) => created,
        Err(error) => {
            let _ = gateway_a
                .delete_sandbox(name, DeleteOptions::default())
                .await;
            return Err(error);
        }
    };
    gateway_a.wait_ready(name, Duration::from_secs(120)).await?;
    linux_gateway
        .wait_ready(name, Duration::from_secs(120))
        .await?;
    let get_a = gateway_a.get_sandbox(name).await?;
    let get_linux = linux_gateway.get_sandbox(name).await?;
    let list_a = gateway_a.list_all_sandboxes(ListOptions::default()).await?;
    let list_linux = linux_gateway
        .list_all_sandboxes(ListOptions::default())
        .await?;
    let matches_a = list_a.iter().filter(|sandbox| sandbox.name == name).count();
    let matches_linux = list_linux
        .iter()
        .filter(|sandbox| sandbox.name == name)
        .count();
    let target_a_watch =
        watch_lifecycle(&gateway_a, "gateway-a:jfr-20261024-a", name, &id_a).await?;
    let linux_watch = watch_lifecycle(
        &linux_gateway,
        "linux:192.168.139.147:18470",
        name,
        &id_linux,
    )
    .await?;
    let unavailable = connect_client_to(
        "https://127.0.0.1:28499",
        "localhost",
        "../gateway-a/certs/ca.crt",
        Some("private/certs/control-client.crt"),
        Some("private/certs/control-client.key"),
        5,
    )
    .await;
    let unavailable_state = match unavailable {
        Ok(_) => json!({"availability":"unexpectedly_reachable","instances_deleted":false}),
        Err(error) => {
            json!({"availability":"UNAVAILABLE","error":format!("{error:#}"),"instances_deleted":false})
        }
    };
    let deletion_a = async {
        let deleted = gateway_a
            .delete_sandbox(name, DeleteOptions::default())
            .await?;
        anyhow::ensure!(deleted.sandbox_id.as_deref() == Some(id_a.as_str()));
        gateway_a
            .wait_deleted(name, Duration::from_secs(60), Some(&id_a))
            .await?;
        Ok::<(), anyhow::Error>(())
    }
    .await;
    let deletion_linux = async {
        let deleted = linux_gateway
            .delete_sandbox(name, DeleteOptions::default())
            .await?;
        anyhow::ensure!(deleted.sandbox_id.as_deref() == Some(id_linux.as_str()));
        linux_gateway
            .wait_deleted(name, Duration::from_secs(60), Some(&id_linux))
            .await?;
        Ok::<(), anyhow::Error>(())
    }
    .await;
    Ok(vec![record(
        "two_gateways_duplicate_name_target_inventory_and_recovery",
        (|| -> Result<Value> {
            anyhow::ensure!(
                id_a != id_linux,
                "duplicate display names unexpectedly share immutable IDs"
            );
            anyhow::ensure!(
                get_a.id == id_a && get_linux.id == id_linux,
                "get routed to wrong target identity"
            );
            anyhow::ensure!(
                matches_a == 1 && matches_linux == 1,
                "expected one same-name instance in each target namespace"
            );
            anyhow::ensure!(
                get_a.phase == openshell_sdk::types::SandboxPhase::Ready
                    && get_linux.phase == openshell_sdk::types::SandboxPhase::Ready,
                "target status not Ready"
            );
            anyhow::ensure!(
                target_a_watch["fresh_query_matches_target_ready"] == true,
                "gateway A fresh query mismatch"
            );
            anyhow::ensure!(
                linux_watch["fresh_query_matches_target_ready"] == true,
                "Linux gateway fresh query mismatch"
            );
            anyhow::ensure!(
                deletion_a.is_ok() && deletion_linux.is_ok(),
                "cleanup did not confirm each owned sandbox"
            );
            Ok(json!({
                "targets": [
                    {"target":"gateway-a:jfr-20261024-a","endpoint":"https://127.0.0.1:28470","authenticated_subject":user_a,"display_name":name,"sandbox_id":id_a,"phase":format!("{:?}",get_a.phase),"list_count_same_name":matches_a,"watch":target_a_watch,"cleanup_confirmed":deletion_a.is_ok()},
                    {"target":"linux:192.168.139.147:18470","endpoint":"https://192.168.139.147:18470","authenticated_subject":user_linux,"display_name":name,"sandbox_id":id_linux,"phase":format!("{:?}",get_linux.phase),"list_count_same_name":matches_linux,"watch":linux_watch,"cleanup_confirmed":deletion_linux.is_ok()}
                ],
                "unreachable_target": unavailable_state,
                "two_targets_were_addressed_independently": true
            }))
        })(),
    )])
}

async fn stale_name_probe(
    client: &OpenShellClient,
    name: &str,
    image: &str,
    delayed_request: Vec<u8>,
) -> Record {
    let (replacement_id, _) = match create_with_dedup(client, name, image).await {
        Ok(created) => created,
        Err(error) => return record("stale_name_mutation_after_reuse", Err(error)),
    };
    if let Err(error) = client.wait_ready(name, Duration::from_secs(120)).await {
        let cleanup = client.delete_sandbox(name, DeleteOptions::default()).await;
        return record(
            "stale_name_mutation_after_reuse",
            Err(anyhow::anyhow!(
                "replacement did not become ready: {error:#}; cleanup result: {cleanup:?}"
            )),
        );
    }
    let request = match proto::StopSandboxRequest::decode(delayed_request.as_slice()) {
        Ok(request) => request,
        Err(error) => {
            return record(
                "stale_name_mutation_after_reuse",
                Err(anyhow::anyhow!(
                    "decode delayed old-context request: {error}"
                )),
            );
        }
    };
    let old_operation_id = request.request_id.clone();
    let mut grpc = client.raw_grpc();
    let stale_stop = grpc.stop_sandbox(request).await;

    let (stop_rpc_succeeded, stop_error, response_id) = match stale_stop {
        Ok(response) => {
            let response_id = response
                .into_inner()
                .sandbox
                .and_then(|sandbox| sandbox.metadata.map(|metadata| metadata.id));
            (true, None, response_id)
        }
        Err(error) => (false, Some(format!("{error:#}")), None),
    };
    let current = client.get_sandbox(name).await;
    let phase_after = current
        .as_ref()
        .map(|sandbox| format!("{:?}", sandbox.phase))
        .unwrap_or_else(|error| format!("inspect failed: {error:#}"));
    let current_id = current
        .as_ref()
        .map(|sandbox| sandbox.id.clone())
        .unwrap_or_default();
    let stale_mutation_rejected =
        current.is_ok() && current_id == replacement_id && phase_after != "Stopped";
    let delete_result = async {
        let deleted = client
            .delete_sandbox(name, DeleteOptions::default())
            .await?;
        anyhow::ensure!(
            deleted.sandbox_id.as_deref() == Some(replacement_id.as_str()),
            "replacement delete identified wrong sandbox"
        );
        client
            .wait_deleted(name, Duration::from_secs(60), Some(&replacement_id))
            .await?;
        Ok::<(), anyhow::Error>(())
    }
    .await;
    let cleanup_ok = delete_result.is_ok();
    let detail = json!({
        "old_context_request_id": old_operation_id,
        "request_bytes_captured_before_original_delete": true,
        "replacement_id": replacement_id,
        "stale_stop_rpc_succeeded": stop_rpc_succeeded,
        "stale_stop_rpc_error": stop_error,
        "stop_response_sandbox_id": response_id,
        "replacement_id_after": current_id,
        "replacement_phase_after": phase_after,
        "stale_mutation_rejected": stale_mutation_rejected,
        "replacement_cleanup_confirmed": cleanup_ok
    });
    let error = if !stale_mutation_rejected {
        Some("stale name-based stop affected replacement; API request has no immutable sandbox ID or runtime generation".to_string())
    } else if !cleanup_ok {
        Some(format!(
            "stale operation rejected but replacement cleanup failed: {:#}",
            delete_result.unwrap_err()
        ))
    } else {
        None
    };
    Record {
        operation: "stale_name_mutation_after_reuse".into(),
        ok: error.is_none(),
        detail: Some(detail),
        error,
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    let mode = env::args()
        .nth(1)
        .context("expected mode: tls, lifecycle, duplex, pty, stale-delete, two-target, verification-worker, verification-adversarial, verification-negative, verification-inspect, verification-list, or verification-delete")?;
    let records = match mode.as_str() {
        "tls" => tls_probe().await?,
        "lifecycle" => lifecycle_probe().await?,
        "duplex" => duplex_only_probe().await?,
        "pty" => pty_only_probe().await?,
        "stale-delete" => stale_delete_only_probe().await?,
        "two-target" => two_target_probe().await?,
        "verification-worker" => match verification::run().await {
            Ok(detail) => {
                let ok = detail.get("result").and_then(Value::as_str) == Some("PASS");
                vec![Record {
                    operation: "verification_worker".into(),
                    ok,
                    detail: Some(detail),
                    error: (!ok)
                        .then(|| "verification worker did not meet its execution contract".into()),
                }]
            }
            Err(error) => vec![record("verification_worker", Err(error))],
        },
        "verification-adversarial" => match verification::adversarial().await {
            Ok(detail) => {
                let ok = detail["execution"]["result"].as_str() == Some("PASS")
                    && detail["cleanup"]["confirmed"].as_bool() == Some(true);
                vec![Record {
                    operation: "verification_adversarial".into(),
                    ok,
                    detail: Some(detail),
                    error: (!ok)
                        .then(|| "adversarial worker confinement probe did not pass".into()),
                }]
            }
            Err(error) => vec![record("verification_adversarial", Err(error))],
        },
        "verification-negative" => match verification::negative().await {
            Ok(detail) => {
                let ok = detail.get("result").and_then(Value::as_str) == Some("PASS");
                vec![Record {
                    operation: "verification_negative".into(),
                    ok,
                    detail: Some(detail),
                    error: (!ok)
                        .then(|| "negative verification case did not deny the request".into()),
                }]
            }
            Err(error) => vec![record("verification_negative", Err(error))],
        },
        "verification-inspect" => match verification::inspect().await {
            Ok(detail) => vec![Record {
                operation: "verification_inspect".into(),
                ok: true,
                detail: Some(detail),
                error: None,
            }],
            Err(error) => vec![record("verification_inspect", Err(error))],
        },
        "verification-list" => match verification::list_for_cleanup().await {
            Ok(detail) => vec![Record {
                operation: "verification_list_for_cleanup".into(),
                ok: true,
                detail: Some(detail),
                error: None,
            }],
            Err(error) => vec![record("verification_list_for_cleanup", Err(error))],
        },
        "verification-delete" => match verification::delete().await {
            Ok(detail) => vec![Record {
                operation: "verification_delete".into(),
                ok: true,
                detail: Some(detail),
                error: None,
            }],
            Err(error) => vec![record("verification_delete", Err(error))],
        },
        _ => bail!("unknown mode {mode:?}"),
    };
    println!("{}", serde_json::to_string_pretty(&records)?);
    if records.iter().any(|item| !item.ok) {
        std::process::exit(1);
    }
    Ok(())
}
