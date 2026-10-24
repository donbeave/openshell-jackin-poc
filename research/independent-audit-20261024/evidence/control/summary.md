# OpenShell control and workflow worker POC

Scope: CLI-based control calls and the isolated workflow verification worker only. This is not evidence for Jackin's future Rust RPC transport, authenticated agent/account sessions, or the combined architecture.

## Environment and mechanism

- Jackin source: `6e266406b49da2ab3c55355f3b7d33d1643ee6cd`; worker baseline is `jackin-workflow/src/verify.rs`.
- OpenShell: CLI/gateway `0.1.5`, pinned source commit `bdb956f2cd65a635f1294fccf1d138d263bf650f`.
- Worker image: `python@sha256:1b668429b3511ab407d8e00648891631b0b1a4d7e15e3ca70f38ab5b91ad4ab4` (linux/arm64); gateway `jrr24-worker`, endpoint `https://127.0.0.1:18818`, workspace `default`, compute driver Docker. Runtime and supervisor image digests were not retained from Docker inspect before teardown; do not infer them from the worker image or gateway source version.
- Host: macOS ARM64 with OrbStack Docker engine. Details and exact commands live in the JSON evidence and scripts in `experiments/control/`.
- Mechanism: released OpenShell CLI and gateway, local mTLS, explicit gateway driver configuration. This did not test Jackin-side generated tonic RPC or protocol clients.

## Results

| Requirement | Result | Evidence |
|---|---|---|
| Exact argv, distinct stdout/stderr, exit code, binary stdin including NUL and non-UTF8 | PASS | [exec-roundtrip.json](exec-roundtrip.json) |
| Network deny plus positive control | PASS | See `policy-enforcement.json` |
| RO project/check bind mounts, Landlock denial, writable scratch, reported cgroup fields | PASS | See `policy-enforcement.json` |
| TLS server verification, wrong client CA rejection, client certificate renewal | PASS | See `tls-authentication.json` |
| Worker success/failure with actual OpenShell phase and exit status, input hashes unchanged | PASS | `../verification/jrr24-wpass02.json`, `../verification/jrr24-wfail03.json` |
| Jackin process-group timeout semantics | FAIL | `../verification/timeout-process-group.json` |
| CLI exec timeout cancels remote process | FAIL | [exec-cancellation.json](exec-cancellation.json) |
| Whole-sandbox delete as bounded worker termination | FAIL | `../verification/timeout-delete-worker.json` |
| Whole-sandbox deletion cleanup primitive | PASS for tested UUID-scoped container removal | `../verification/timeout-delete-worker.json` |
| CLI lost-response idempotency / caller-supplied request IDs | NOT TESTED | CLI help output captured in the experiment run; future generated RPC tests required |
| Atomic immutable identity precondition | FAIL | [identity-lifecycle.json](identity-lifecycle.json) |
| Name-only inventory not-found as sufficient host-data deletion proof | FAIL | [identity-lifecycle.json](identity-lifecycle.json) |
| Output cap | FAIL: CLI passed 100,000 bytes without a cap | [output-bound.json](output-bound.json) |
| Slow receiver, protocol cancellation, version mismatch, protocol retry | NOT TESTED | No evidence retained |

Exact scope: PASS rows cover only CLI bytes, the tested policy destination/paths, local TLS and fixture exit cases. `os.killpg(SIGKILL)` failed while its child continued. CLI timeout returned 124 while remote marker appeared later. Whole-sandbox deletion removed compute but did not report worker exit; it is therefore a failed complete termination contract with a successful cleanup primitive. Stale name stop affected a replacement. CLI emitted 100,000 bytes without a cap; slow receiver, version mismatch and protocol retries remain separately NOT TESTED. No generic NOT_FOUND permits deleting retained host data.

## Worker-policy configuration and limitations

The worker policy requires Landlock, runs UID/GID 1000, gives `/workspace` and `/jackin` read-only policy access, and allows `/tmp`, `/build`, and `/dev/null` writes. Fixture mounts for candidate and trusted check bundle were Docker read-only binds. The local gateway required `enable_bind_mounts=true`; resource admission was explicitly disabled. This is a configuration deviation and does not prove admitted durable-volume support.

The Docker runtime's `ReadonlyRootfs` field was false. A write to a mode-0777 path outside allowed Landlock paths was denied, and scratch writes succeeded, but a literal read-only root mount was not established. CPU, memory, and PID limits were observed in driver/container configuration; no stress overrun experiment established enforcement. Candidate/result binding is by frozen fixture content hashes, not a Git commit/tree proof. The verification worker therefore remains NOT READY.

## Decision

Do not select the CLI as Jackin's production control adapter. It demonstrates useful wire behavior, but does not provide stable caller request IDs, identity-preconditioned mutations, bounded output, or a reliable remote process-group timeout in these tests. Continue with the proposed generated tonic client plus authenticated TLS channel as an unproved implementation route, and require dedicated live tests. Required worker blockers include safe bounded termination with actual exit-state, immutable identity conditions or an equivalent proven ownership mechanism, strict root/scratch policy, and complete authorized cleanup evidence.

## Cleanup

The POC gateway and resource namespace were isolated. Per-resource cleanup evidence is in `final-cleanup.json` and `worker-group-cleanup.json`. The gateway process was already absent when the teardown script checked its PID; the original stop and port claims are marked invalid because their command results were not captured. The POC's generated state, XDG config, and ephemeral certificates/private keys were removed; see `gateway-teardown.json`. These experiments used no personal credentials and made no changes to Jackin source.
