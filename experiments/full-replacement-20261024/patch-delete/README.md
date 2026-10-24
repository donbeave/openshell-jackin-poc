# Immutable-ID deletion patch proof

This experiment tests one OpenShell source patch: public `DeleteSandbox` can target an immutable sandbox object ID. It does not change Stop, Start, Exec, other lifecycle operations, or Jackin.

## Baseline and artifacts

- OpenShell released base: `v0.1.5`, commit `bdb956f2cd65a635f1294fccf1d138d263bf650f`.
- Detached worktree branch: `jfr-guarded-delete` under `openshell/`, final source commit `95a1e7fe2bfc731ec21096dea0758fa7fc90a8db`.
- Gateway binary: arm64, SHA-256 `ed2e461d0f3075e1e659cbdc3fecb8310f02d4d820833ec88caf6f3e7e3d4d4c`, built from the final source commit with Rust `1.99.1` and mbx `1.27.0`.
- Patch gateway: mTLS on `127.0.0.1:28620`, own state/config/certificates under `gatewayfresh/`, namespace label `jfr-20261024-pdel-strict`.
- Released comparison gateway: OpenShell `v0.1.5` on `127.0.0.1:28470`; only short `po...` test names were created and removed.
- Image: `nvcr.io/nvidia/base/ubuntu@sha256:7e0f726d635d440d28a7f18e6498d3bdb76c7038bd4c90a090c21eb7c9f40686` (pinned Linux arm64 image); sandboxes use a disposable `sleep 600` command.
- The OpenShell gateway uses the configured Docker driver and local Docker engine to provision its sandbox resources. The Rust test client does not issue Docker API calls. OpenShell owns the sandbox records and engine children; successful test cleanup deletes sandboxes through OpenShell API calls.

The certificates under `gatewayfresh/certs/` are generated locally by `gatewayfresh/setup.sh`; never publish them. That directory is ignored by the parent repository. The test source contains no key material.

After the tests, `sh experiments/full-replacement-20261024/patch-delete/cleanup.sh` stops only a listener whose command line points at this experiment's `gatewayfresh/gateway.toml`, removes only this experiment's generated gateway keys/state/logs, and can be run repeatedly. It does not remove build caches or the shared Docker engine.

## Reproduce

From the parent POC repository root, create the detached source clone. `openshell/` is gitignored in this POC because it is a full local source clone; the exact patch is delivered separately as `results/full-replacement-20261024/patch-delete/immutable-delete.patch`.

```sh
POC_ROOT="$PWD"
PATCH_ROOT="$POC_ROOT/experiments/full-replacement-20261024/patch-delete"
git clone https://github.com/NVIDIA/OpenShell.git "$PATCH_ROOT/openshell"
git -C "$PATCH_ROOT/openshell" checkout --detach bdb956f2cd65a635f1294fccf1d138d263bf650f
git -C "$PATCH_ROOT/openshell" switch -c jfr-guarded-delete
git -C "$PATCH_ROOT/openshell" apply "$POC_ROOT/results/full-replacement-20261024/patch-delete/immutable-delete.patch"
cp "$PATCH_ROOT/tooling/mise.toml" "$PATCH_ROOT/openshell/mise.toml"
cp "$PATCH_ROOT/tooling/mise.lock" "$PATCH_ROOT/openshell/mise.lock"
cp "$PATCH_ROOT/tooling/rust-toolchain.toml" "$PATCH_ROOT/openshell/rust-toolchain.toml"
```

The overlay pins the run's current Rust/mbx versions and wrapper. It replaces only local tool configuration during reproduction; it is not part of the source patch.

```sh
sh experiments/full-replacement-20261024/patch-delete/gatewayfresh/setup.sh
sh experiments/full-replacement-20261024/patch-delete/gatewayfresh/run.sh
```

In another terminal, compile and run the focused tests:

```sh
cd experiments/full-replacement-20261024/patch-delete/openshell
mise exec -- cargo check --locked -p openshell-server -p openshell-cli -p openshell-sdk
mise exec -- cargo build --locked -p openshell-gateway -p openshell-cli
mise exec -- cargo test --locked -p openshell-server delete_by_ -- --nocapture
mise exec -- cargo test --locked -p openshell-server immutable_delete_target_is_part_of_replay_fingerprint -- --nocapture
```

Run the patched integration test using the generated patch-gateway client identity:

```sh
PDEL_ENDPOINT=https://localhost:28620 \
PDEL_SERVER_NAME=localhost \
PDEL_CA="$PWD/../gatewayfresh/certs/ca.crt" \
PDEL_CLIENT_CERT="$PWD/../gatewayfresh/certs/client/tls.crt" \
PDEL_CLIENT_KEY="$PWD/../gatewayfresh/certs/client/tls.key" \
PDEL_IMAGE=nvcr.io/nvidia/base/ubuntu@sha256:7e0f726d635d440d28a7f18e6498d3bdb76c7038bd4c90a090c21eb7c9f40686 \
mise exec -- cargo test --locked -p openshell-sdk --test delete_by_id_integration \
  patched_server_replays_id_delete_after_removal_and_name_reuse -- --ignored --exact --nocapture
```

The released-server check uses a separate existing release gateway and its own client identity:

```sh
PDEL_ENDPOINT=https://localhost:28470 \
PDEL_SERVER_NAME=localhost \
PDEL_CA="$PWD/../../gateway-a/certs/ca.crt" \
PDEL_CLIENT_CERT="$PWD/../../gateway-a/certs/client/tls.crt" \
PDEL_CLIENT_KEY="$PWD/../../gateway-a/certs/client/tls.key" \
PDEL_IMAGE=nvcr.io/nvidia/base/ubuntu@sha256:7e0f726d635d440d28a7f18e6498d3bdb76c7038bd4c90a090c21eb7c9f40686 \
mise exec -- cargo test --locked -p openshell-sdk --test delete_by_id_integration \
  released_server_rejects_new_empty_name_id_delete_without_deleting -- --ignored --exact --nocapture
```

The gateway must remain running for each integration command. The patched-server test deletes sandboxes by immutable ID, waits for removal, and deletes the temporary second workspace. The released server rejects ID requests, so its test cleanup verifies each unique test name still resolves to the recorded owned ID, then deletes that exact name and verifies the returned ID. This released-server cleanup is non-atomic and is safe only in the disposable comparison workspace with sole test authority and no concurrent creator reusing the test name. It does not prove an identity guarantee for name deletion. If a test process panics before its cleanup block, use `cleanup-owned/` with only the exact name/ID pairs recorded by that run; it sends ID-bound deletion requests and never scans by prefix.

For example, from `experiments/full-replacement-20261024/patch-delete/openshell`, recover an interrupted run using only its captured IDs:

```sh
PDEL_ENDPOINT=https://localhost:28620 \
PDEL_CA="$PWD/../gatewayfresh/certs/ca.crt" \
PDEL_CLIENT_CERT="$PWD/../gatewayfresh/certs/client/tls.crt" \
PDEL_CLIENT_KEY="$PWD/../gatewayfresh/certs/client/tls.key" \
mise exec -- cargo run --locked --manifest-path ../cleanup-owned/Cargo.toml -- \
  exact-run-name=<captured-id>
```

## Patch behavior and limits

The request accepts exactly one of `name` or `sandbox_id`. ID deletion requires an explicit workspace and a non-nil UUID `request_id` that callers must reuse unchanged on retry; `allow_missing` is rejected. Workspace membership is authorized before target lookup. A target whose stored workspace differs from the authorized selected workspace returns the same not-found result as an absent ID. The existing compute deletion-by-ID path supplies its ID-keyed mutation guard. Replay fingerprinting includes the new protobuf field and the target guard binds to the same immutable ID. The runtime check proves receipt replay after deletion and same-name reuse, and rejects a changed target under the same request ID with machine-readable Google `ErrorInfo`.

The SDK name-delete methods continue sending the legacy name and set `sandbox_id` empty. New SDK ID-delete methods send an empty name, explicit workspace, and immutable ID. An old server ignores the new protobuf field and rejects the empty name; it does not downgrade the call to name deletion.

This is an **EXPERIMENTAL PATCH**. Released OpenShell v0.1.5 has no public immutable-ID delete. This patch does not repair stale name-based Stop/Start/Exec operations or introduce an atomic compare-and-mutate API for them. It is not evidence that every lifecycle operation is ID-safe.
