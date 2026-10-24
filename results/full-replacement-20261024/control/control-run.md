# Control and lifecycle proof of concept

Platform: macOS local gateway; OpenShell v0.1.5 at commit `bdb956f2cd65a635f1294fccf1d138d263bf650f`; gateway `jfr-20261024-a`, endpoint `https://127.0.0.1:28470`; namespace `jfr-20261024-a`. Client is a small Rust binary built against the released OpenShell SDK at that exact revision, using public `OpenShellClient::from_parts` with Tonic verified mTLS. Server CA, server name, and client certificate are all validated; no insecure TLS mode is available in the probe. The client key is an ignored experiment-only file. Sandbox image was `nvcr.io/nvidia/base/ubuntu@sha256:7e0f726d635d440d28a7f18e6498d3bdb76c7038bd4c90a090c21eb7c9f40686`, inspected as `linux/arm64` Ubuntu 24.04.

## Reproduction

From `experiments/full-replacement-20261024/control`:

```sh
mise exec -- cargo build --locked
./run-case.sh tls-valid tls --endpoint https://127.0.0.1:28470 --server-name localhost --ca ../gateway-a/certs/ca.crt --cert private/certs/control-client.crt --key private/certs/control-client.key --expect allow
./run-case.sh lifecycle-main lifecycle --endpoint https://127.0.0.1:28470 --server-name localhost --ca ../gateway-a/certs/ca.crt --cert private/certs/control-client.crt --key private/certs/control-client.key --name jfrctl241024 --image nvcr.io/nvidia/base/ubuntu@sha256:7e0f726d635d440d28a7f18e6498d3bdb76c7038bd4c90a090c21eb7c9f40686
```

The helper saves argv, stdout JSON, stderr, and exit status separately. The lifecycle name is deliberately within the release's 19-character limit. Results below are under this directory; the run used raw Tonic RPCs where request IDs and stream frames were required.

## TLS and API identity

`tls-valid`: PASS. Verified TLS plus the experiment client certificate succeeded; authenticated list and `GetCurrentUser` returned subject `jfr-control-20261024`. `tls-wrong-ca` and `tls-wrong-host`: expected denials at the verified TLS handshake. `tls-untrusted-client`: denied at mutual TLS. `tls-no-client`: public health returned `Healthy`, while authenticated list failed with `auth error: missing authorization header`. Each harness run exited 0 because the expected outcome matched.

`tls-wrong-ou` used a different CA-signed certificate with OU `invalid-user`. It was accepted as a different authenticated subject and permitted to list the same workspace. A denial was therefore NOT demonstrated. This is an identity-policy observation for this gateway configuration, not proof that OpenShell globally ignores roles or workspace authorization. The saved list output records only the count, not unrelated gateway sandbox rows.

## Lifecycle and execution

`lifecycle-main` exited 1 because two capability assertions failed; it still recorded all operations. Create with one UUID request ID, discard the first acknowledgement in the harness, then resend the identical request and payload: PASS, one named sandbox and the retry returned the same sandbox ID. This discards a response after receipt; it does not simulate a network packet loss. Wait-ready, get/inspect, list, argv with spaces/quotes/semicolon preserved as literal data, exit status `23` with separate stdout/stderr, stop, start with the same sandbox ID, delete and wait-deleted by the original ID: PASS. The unchanged API path preserved exit code and stdout/stderr separately.

Execution retry: the client disconnected its interactive stream after receiving `READY`, then retried with the same request ID. OpenShell rejected the duplicate because its execution had terminated and output was not stored; the marker file contained exactly one `x`. This is a successful no-replay/idempotency behavior after stream loss, not a replayable output guarantee.

Stale target: `lifecycle-stale-capture.stdout.json` captures a serialized `StopSandboxRequest` while the original sandbox still exists, deletes the original and confirms by ID, creates a replacement under the same name, then sends the unchanged serialized request. OpenShell accepted it and returned the replacement sandbox ID; the replacement changed from Ready to Stopped. The probe then deleted the replacement and confirmed cleanup. This is a reproducible stale-name mutation failure with a genuinely delayed, preconstructed request. Released `StopSandboxRequest`, `StartSandboxRequest`, and `DeleteSandboxRequest` each have workspace scope, name, and request ID, but no expected sandbox ID or generation. Their operation request ID deduplicates the mutation request; it does not bind it to the earlier resource identity. A Jackin caller therefore cannot safely replay delayed name-based stop/delete operations after name reuse without an upstream identity-guarded mutation or a retained single-owner lock that prevents reuse until all requests are fenced.

`stale-delete-before-patch.*` extends the stale-target proof: the client encoded a `DeleteSandboxRequest` while the original was ready, deleted and confirmed the original by ID, recreated the same name, then sent the exact preconstructed request bytes for the first time. The delete succeeded and its response identified the replacement ID; the replacement disappeared and was confirmed deleted. The probe reports expected FAIL for stale-target safety and confirms cleanup. The generated `DeleteSandboxResponse` comment says a same-name replacement is not part of the deletion, but this delayed first-admission request still removed it. This may mean that the comment protects replay of an already-admitted request, not a stale request constructed earlier but first delivered after replacement. Delete idempotency and target binding should be analyzed separately. Stale-start remains NOT TESTED.

## Interactive stream

`lifecycle-main` originally recorded a 25-byte stdout result because its fixture invoked external `dd` with stderr suppressed; this is a fixture failure, not a demonstrated OpenShell duplex limitation. It remains preserved. A separate corrected probe, `duplex-corrected.*`, used only a shell-builtin 1MiB output and passed: distinct stdout/stderr markers, split input frames with NUL, 500ms receiver pause, half-close EOF, exit 0, exact stdout byte count and SHA-256. The child was explicitly deleted and confirmed. This proves the tested non-TTY streaming contract for this Linux/arm64 guest image and local macOS gateway path; it does not establish PTY controls or arbitrary sustained-throughput behavior.

`pty-resize-interrupt-3.*` separately passes PTY startup and terminal control: initial `stty size` was 24 rows by 80 columns; the client sent resize to 37 by 101 and the child observed `37 101`; text containing spaces reached the shell; sending byte `0x03` produced exit code 130. The client then opened a new `ExecSandboxInteractive` with a new request ID, received `PTY_NEW_EXEC`, and exit 0. This is a new process execution, not reattachment to the interrupted process. Capsule-level session persistence, operator-control state, and process reattachment remain outside this test.

## Transport scope

The separate Linux gateway owner prepared `https://192.168.139.147:18470`, a private-IP listener with a matching SAN and distinct mTLS CA. A client key/CSR was generated locally and the issued client cert verified against its CA. `tls-linux-api.*` passes from this Rust client: verified mTLS, gateway health `Healthy`, authenticated list, and `GetCurrentUser` subject `jfr-control-vm-20261024`, OpenShell 0.1.5. This demonstrates Rust client control transport and identity at that endpoint. It does not prove the complete Linux lifecycle/workspace/runtime contract.

The interrupted second lifecycle repeat had created a Ready sandbox before the client was interrupted. I inspected only the experiment-owned name `jfrctl241024`, explicitly deleted it through `sh ../gateway-a/client.sh sandbox delete jfrctl241024`, and a subsequent get returned `sandbox not found`. The CLI reported deletion accepted before the get confirmed absence. This demonstrates explicit client recovery/cleanup after interruption, not automatic OpenShell cleanup at client termination. The detached repeat did not finish and remains NOT TESTED.

## Source facts and limits

The generated pinned protocol is at `experiments/full-replacement-20261024/control/target/debug/build/openshell-core-327eda7755ee44c6/out/openshell.v1.rs`; source checkout is Cargo's `openshell` checkout at revision `bdb956f`. `CreateSandboxRequest.request_id` is documented in the generated contract as a nonzero UUID with at-most-once admission and a 24-hour replay window. `ExecSandboxRequest.request_id` prevents relaunch; a terminal execution whose output was not stored is rejected on retry. These source facts are corroborated by the runtime duplicate probes above. The CLI supports JSON for create/get/list, but stop/start/delete reject `-o json`; that is a CLI-format limitation only. The Rust SDK raw API avoids human-output parsing.

No source patch or global gateway/client config change was made. No engine or Docker resource was created by this control probe.
