# Immutable-ID deletion patch run record

## Environment and versions

- Host: macOS Darwin 27.0, Apple M5 Max (arm64), 128 GiB memory; 2.0 TiB free at capture.
- OpenShell released base: `v0.1.5`, commit `bdb956f2cd65a635f1294fccf1d138d263bf650f`.
- Patch worktree: branch `jfr-guarded-delete`; patch commit `cfb1b7bf531fd1dff63db93658c3b11f47444678`, parent `bdb956f2cd65a635f1294fccf1d138d263bf650f`.
- Exported patch: `immutable-delete.patch`, SHA-256 `6b9a7bf23af3676322e55f45e92a4eb65ccc9e5639fbd86bd379638e620632e5`.
- Rust used for builds: `1.99.1`; mise `2026.10.18`; mbx `1.27.0`.
- Gateway A comparison reports `openshell-gateway 0.1.5`; patch gateway built from the worktree.
- mTLS remained enabled and certificate validation remained enabled. No secrets were saved in this record or the logs.
- Patch gateway ID/namespace: `jfr-20261024-pdel`, `127.0.0.1:28620`.
- Comparison gateway ID/namespace: release gateway A, `127.0.0.1:28470`; unique temporary test names only.
- Test image: `ubuntu:22.04`; command: `/bin/sh -c 'sleep 600'`.

## Build prerequisites

The first `mise exec -- cargo check --locked -p openshell-server -p openshell-cli -p openshell-sdk` attempt was rejected by the local Rust build guard because it did not match the required wrapper invocation. The exact accepted wrapper form then rejected the unmodified upstream `.cargo/config.toml` because its `[env] BINDGEN_EXTRA_CLANG_ARGS` can alter build outputs. The unchanged upstream value is `BINDGEN_EXTRA_CLANG_ARGS = "-I/usr/include/z3"`; its comment says this supplies the Z3 header include path. Both refusals were preserved; no guard was disabled and no Rust compiler override was set. Parent-authorized `mise exec -- cargo ...` was used with Rust 1.99.1 and mbx as Cargo provider. No source edits were made to the upstream `.cargo/config.toml`.

For this isolated build clone, `mise.toml`, `rust-toolchain.toml`, and `mise.lock` were temporarily set to the local current-stable Rust/mbx toolchain and are not part of the source patch. The exact upstream configuration files remain available in the neighboring `upstream-*.toml` backups and in the base commit.

## Results

| Test | Result | Execution evidence |
| --- | --- | --- |
| Patched server/SDK/CLI compile | PASS | `logs/cargo-check.log` |
| Patched gateway/CLI build | PASS | `logs/cargo-build.log` |
| Unit tests for matching ID, stale same-name replacement, invalid scope/selectors and missing ID behavior | PASS, 2 focused tests; 3 total matched with an existing persistence test | `logs/server-unit-tests.log` |
| Request replay fingerprint changes when `sandbox_id` changes | PASS | `logs/replay-fingerprint-test.log` |
| Patched gateway ID delete and same-name reuse | PASS | `logs/patched-gateway-runtime.log` |
| Wrong selected valid workspace | PASS, denied without mutation | Patched runtime log: a distinct valid workspace was created through `CreateWorkspace`; ID delete selected that authorized workspace for an ID owned by `default`, returned `NotFound`, and left the replacement present |
| Dual selector | PASS, `InvalidArgument`, no mutation | Patched runtime log |
| Released v0.1.5 receives new ID field with empty name | PASS, safe rejection | `logs/released-gateway-runtime.log`: `InvalidArgument`; original remained present |

Patched runtime observed the first deletion response as `Accepted` and then confirmed deletion by ID before creating the same-name replacement. Replaying deletion against the removed original ID returned `AlreadyAbsent`; the replacement ID remained present. The temporary workspace was created and deleted through API calls.

`logs/initial-name-reuse-unit-test.log` records an earlier unit-test iteration before the asynchronous deletion acknowledgement was accommodated. The final unit-test output is in `logs/server-unit-tests.log`.

## Cleanup and remaining gaps

The integration tests clean up their created sandboxes and temporary workspace through OpenShell API operations. The patch gateway process was stopped after evidence capture, and no `pdel` Docker containers remained. Generated patch gateway certificates and SQLite state stay under the ignored `experiments/full-replacement-20261024/patch-delete/gateway/` path. They are never publishable artifacts.

This proves only the experimental public immutable-ID DeleteSandbox addition. The released failure remains visible. No conclusion follows for stale Stop/Start/Exec requests, other releases, other gateway drivers, remote targets, or full Jackin replacement readiness.
