# Two-gateway Rust control probe

## Setup and reproduction

This probe used two separately configured, verified-mTLS Rust clients and a 5-second Tonic request timeout. It did not use or modify global client configuration.

- Gateway A: `https://127.0.0.1:28470`, identity `jfr-20261024-a`, CA `experiments/full-replacement-20261024/gateway-a/certs/ca.crt`, client subject `jfr-control-20261024`.
- Linux guest gateway: `https://192.168.139.147:18470`, identity `jfr-20261024-linux`, separate CA `experiments/full-replacement-20261024/targets/private/certs/jfr-linux-ca.crt`, client subject `jfr-control-vm-20261024`.
- OpenShell v0.1.5 at `bdb956f2cd65a635f1294fccf1d138d263bf650f` on both. Image: `nvcr.io/nvidia/base/ubuntu@sha256:7e0f726d635d440d28a7f18e6498d3bdb76c7038bd4c90a090c21eb7c9f40686`.

From `experiments/full-replacement-20261024/control`:

```sh
mise exec -- cargo build --locked
./run-case.sh two-target-control two-target
```

Raw command, stdout, stderr, and exit status are in `two-target-control.command.json`, `.stdout.json`, `.stderr.txt`, and `.exit-status`. The run exited 0.

## Results

Both targets accepted the identical display name `jfrdup24`, but returned separate immutable sandbox IDs: Gateway A `24791e1a-7046-4491-ba29-adcf7b0a41e1`, Linux `cd185ec2-57fb-433f-b697-b15730aeb8c5`. Each independently returned exactly one matching name in its list, the correct ID in get/inspect, and Ready status. `GetCurrentUser` subjects differed as expected. This demonstrates that the Rust client independently selects targets by explicit endpoint and trust identity; it does not implement target inventory or a routing service.

For both targets, a raw WatchSandbox status stream was opened before stop/start. Events were tagged with the target and sandbox ID. Stop and start were followed by event snapshots showing `Stopping`, `Stopped`, and `Starting`; the bounded event read had not yet seen Ready. A fresh `GetSandbox` query then returned the expected immutable ID and Ready status on each gateway. This directly demonstrates that recent event observations can lag current state and must not be shown as current without a fresh query or reconciliation.

An intentionally unreachable endpoint, `https://127.0.0.1:28499`, failed with connection refused within the configured 5-second bound. Its result was represented as `UNAVAILABLE`, with `instances_deleted:false`; the probe did not infer deletion from a failed connection.

Both probe-created sandboxes were deleted by their captured immutable IDs and `wait_deleted` confirmed cleanup on each gateway. No other target resources were inspected or modified.

## Scope

PASS for explicit two-endpoint Rust control, distinct mTLS client identities, same-name target separation, per-target list/get/status, watch-event attribution, fresh-state query after lifecycle events, and unavailable-target representation. This does not prove the complete Linux or remote-host Jackin runtime profile, nor Kubernetes or multi-replica gateway recovery.
