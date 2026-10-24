# Immutable-ID DeleteSandbox experiment

## Scope

This bounded experiment tests one proposed OpenShell source capability: delete a sandbox by immutable object ID and keep request retries bound to that same ID. It does not prove stale Stop, Start, or Exec protection, engine ownership, or full Jackin replacement readiness.

## Pinned source and environment

- Released OpenShell: `v0.1.5`, base commit `bdb956f2cd65a635f1294fccf1d138d263bf650f`.
- Final experimental source commit: `95a1e7fe2bfc731ec21096dea0758fa7fc90a8db` on `jfr-guarded-delete`.
- Earlier strict server commit: `ed9b6045916647b31f3bbe0c14d652cf3b924f51`; later commits change only the SDK integration assertion to decode standard ErrorInfo. The gateway executable was rebuilt from the final commit.
- Final patch export: `immutable-delete.patch`, SHA-256 `78c1121e7e74cb719b76ec11069f7c3d426e40811d08a2b0b47aec56c77a587d`.
- Host: macOS, arm64 Apple Silicon. Rust `1.99.1`, mise `2026.10.18`, mbx `1.27.0`.
- Docker context: `orbstack`; client `29.9.2`, engine `29.8.2`, API `1.56`, Linux arm64.
- Final gateway binary: arm64 Mach-O, SHA-256 `ed2e461d0f3075e1e659cbdc3fecb8310f02d4d820833ec88caf6f3e7e3d4d4c`.
- Gateway config: Docker driver, mTLS enabled, HTTPS endpoint `127.0.0.1:28620`, identity and fresh state under `experiments/full-replacement-20261024/patch-delete/gatewayfresh/`, gateway ID and sandbox namespace `jfr-20261024-pdel-strict`.
- Comparison gateway: released OpenShell v0.1.5 at `127.0.0.1:28470`, separate client identity. The release comparison test only used a generated unique name and recorded ID.
- Sandbox image: `nvcr.io/nvidia/base/ubuntu@sha256:7e0f726d635d440d28a7f18e6498d3bdb76c7038bd4c90a090c21eb7c9f40686` (Linux arm64); command `/bin/sh -c 'sleep 600'`.

## Patch contract

The legacy name selector remains available. ID mode requires exactly one selector, an explicit selected workspace, and a parseable non-nil UUID `request_id`; retries must reuse the same request ID and full payload. ID mode rejects `allow_missing=true`. Workspace membership authorization happens before replay admission or target lookup. Replay admission is bound to the literal requested immutable ID without requiring that its row still exists; for a first execution, the handler then requires that the ID exist in the authorized workspace. Unknown IDs and IDs owned by another workspace return the same `NotFound`. A successful deletion retry replays the saved receipt; the same request ID with another target returns `FailedPrecondition` with Google `ErrorInfo` reason `REQUEST_ID_PAYLOAD_MISMATCH`.

The old released server ignores the unknown protobuf field but rejects the empty legacy `name` as `InvalidArgument`; the request does not degrade to deleting by name.

## Execution evidence

| Probe | Result | Mechanism | Evidence |
| --- | --- | --- | --- |
| Build patched gateway and CLI with locked deps | PASS | EXPERIMENTAL PATCH | `logs/strict-id-final-gateway-build.log` |
| Focused DeleteSandbox and replay unit tests | PASS, 5/5 | EXPERIMENTAL PATCH | `logs/strict-id-focused-server-tests.log` |
| Compile SDK integration fixture | PASS | EXPERIMENTAL PATCH | `logs/strict-id-sdk-integration-compile.log` |
| Patched mTLS gateway: ID delete, wait for removal, same-name replacement, replay same request, changed target conflict, valid foreign workspace vs absent ID, reject allow_missing | PASS, exit 0 | EXPERIMENTAL PATCH | `logs/strict-id-final-patched-runtime.log`, `logs/strict-id-gateway-runtime.log` |
| Released v0.1.5 mTLS gateway rejects new ID field with empty name; original remains; exact owned resource then removed by isolated name cleanup | PASS, exit 0 | RELEASED negative comparison + EXTERNAL FIXTURE cleanup | `logs/strict-id-final-release-runtime.log` |
| Final resource cleanup | PASS, no matching namespace containers or listener remained | EXPERIMENTAL PATCH | final patched test log and gateway runtime log |

The final patched runtime created original ID `95c7c454-c247-430c-9391-9889f2bdaa16` and same-name replacement ID `468b60f6-8ac0-40f2-b683-4fe4adf8a558`. First deletion returned `Accepted` (wire enum `2`); the test observed the original ID disappear before name reuse. A retry with the unchanged UUID and payload returned the saved original receipt (`openshell-replayed=true`), and the replacement remained present. Reusing that request ID with the replacement ID returned `FailedPrecondition` and decoded ErrorInfo reason `REQUEST_ID_PAYLOAD_MISMATCH`. Selecting a valid separately created workspace for the replacement ID returned the same `NotFound` as an absent ID. `allow_missing=true` returned `InvalidArgument` for both target cases. The test then removed the exact recorded sandbox IDs and temporary workspace through the API.

The released comparison created ID `a0494acf-3905-4a82-94ad-78cbf681fe33`; the new-format request returned `InvalidArgument` and the original sandbox remained present. Since the release has no ID delete API, test teardown first checked that its unique name still resolved to the recorded ID, deleted that exact name, checked the returned ID, and waited for deletion. This cleanup is non-atomic and relies on the isolated disposable comparison fixture having sole test authority and no concurrent name reuse; it is not an identity guarantee.

## Preserved failed attempts and recovery

- `logs/strict-id-patched-runtime.log`: initial invocation used relative TLS paths from Cargo's test working directory and failed before creating resources.
- `logs/strict-id-patched-runtime-retry.log`: first execution reached the changed-target conflict, but the test incorrectly searched for a machine reason in human-readable `Status.message()` and panicked before cleanup. That run created IDs `19194dd2-7e0a-47d5-8d88-766bd7099a73` and `5dda188b-2e41-4c34-91c7-dda4c2b1bee7`; the original was deleted in the test flow. The remaining recorded replacement ID `5dda188b-2e41-4c34-91c7-dda4c2b1bee7` was later removed by a one-off SDK cleanup helper using that exact ID, and `wait_deleted` confirmed removal. `logs/strict-id-owned-recovery-cleanup.log` records the operation. No prefix listing or broad deletion was used.
- `logs/strict-id-patched-runtime-v2.log`: harness assertion fixed to compare the human message; that run passed, but was superseded because the parent requested machine-readable Google ErrorInfo verification. The final run above decodes and verifies ErrorInfo.
- `revisions/` preserves the earlier `cfb1b7bf` patch/log/review artifacts and the intermediate `ed9b604` patch/build/runtime artifacts. They remain historical and are not the final result.

## Limits

This is an **EXPERIMENTAL PATCH**, not released OpenShell support. It proves immutable-ID DeleteSandbox only on this macOS/OrbStack Docker-driver setup. It does not cover Kubernetes, Linux, remote gateways, VMs, multi-gateway recovery, Stop/Start/Exec, a runtime generation token, or a managed dedicated engine. Native daemon ownership remains a separate OpenShell integration blocker.
