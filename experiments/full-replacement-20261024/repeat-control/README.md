# Fresh Rust control and session transport repeat

This repeat tests the released OpenShell v0.1.5 Rust API route on a fresh gateway and namespace. It does not test Capsule or the complete Jackin journey.

## Environment

- macOS ARM64 host, OrbStack Linux ARM64 Docker engine.
- OpenShell v0.1.5, commit `bdb956f2cd65a635f1294fccf1d138d263bf650f`.
- Gateway `jfr-20261024-rctl`, endpoint `https://localhost:28600`, fresh experiment CA, Docker `sandbox_label=jfr-20261024-rctl`.
- Rust client pins `openshell-sdk` to the OpenShell v0.1.5 commit, Tonic 0.14.6, Rust 1.99.1. It builds a Tonic `Channel` with `ClientTlsConfig` (private CA, expected hostname, client identity), then calls public `OpenShellClient::from_parts`. TLS verification remains enabled.
- Gateway resource admission remains enabled. No source patch, production component, provider credentials, or personal account data used.
- The pinned Ubuntu ARM64 image was already cached. No image build was part of this control repeat.

## Reproduce

From repository root:

```sh
sh experiments/full-replacement-20261024/repeat-control/gateway-rctl/setup.sh
sh experiments/full-replacement-20261024/repeat-control/gateway-rctl/run.sh
```

In another terminal, register the isolated mTLS client profile:

```sh
XDG_CONFIG_HOME="$PWD/experiments/full-replacement-20261024/repeat-control/gateway-rctl/config" \
XDG_STATE_HOME="$PWD/experiments/full-replacement-20261024/repeat-control/gateway-rctl/state" \
OPENSHELL_LOCAL_TLS_DIR="$PWD/experiments/full-replacement-20261024/repeat-control/gateway-rctl/certs" \
openshell gateway add https://localhost:28600 --local --name jfr-20261024-rctl
```

Build the client:

```sh
cd experiments/full-replacement-20261024/repeat-control
mise install
/Users/example/.local/bin/rust-build-guard -- mise exec -- cargo build --locked
```

Generate alternate test identities, then run TLS cases with the commands saved under `results/full-replacement-20261024/repeat-control/tls-*.json`. Run the lifecycle case:

```sh
experiments/full-replacement-20261024/repeat-control/target/debug/openshell-control-probe lifecycle \
  --endpoint https://localhost:28600 --server-name localhost \
  --ca experiments/full-replacement-20261024/repeat-control/gateway-rctl/certs/ca.crt \
  --cert experiments/full-replacement-20261024/repeat-control/gateway-rctl/certs/client/tls.crt \
  --key experiments/full-replacement-20261024/repeat-control/gateway-rctl/certs/client/tls.key \
  --name jfrctl24a \
  --image nvcr.io/nvidia/base/ubuntu@sha256:7e0f726d635d440d28a7f18e6498d3bdb76c7038bd4c90a090c21eb7c9f40686
```

The client emits JSON on stdout and exits nonzero when a required assertion fails. `lifecycle-repeat.json` preserves command arguments, status, stdout, stderr, runtime, image identity, and every per-operation outcome.

## Results

- **PASS, RELEASED:** valid client identity; authenticated Rust SDK calls; server-CA, hostname, missing-client, and untrusted-client-CA negative cases reject as expected.
- **PASS, RELEASED:** create retry with same request ID returned one sandbox ID; list/inspect/readiness, literal argv, separate stdout/stderr, exit status 23, stop/start/delete confirmation passed.
- **PASS, RELEASED:** non-TTY raw gRPC duplex carried 1 MiB stdout, separate stderr, split input frames including NUL, 500 ms receiver pause, EOF, and exit 0.
- **PASS, RELEASED:** disconnecting an execution stream then repeating its request ID did not run the marker twice. Server rejected replay because it does not store the output stream; command result recovery remains unavailable.
- **FAIL, RELEASED:** an old-context `StopSandbox` request by name stopped a newly created replacement with the same name. The response returned the replacement sandbox UUID. The API did not bind the mutation to the old UUID or generation.
- **NOT TESTED:** actual network loss of a create response. The create harness discarded its first successful response locally, then retried; do not label this as a lost network response.

A certificate with a different subject/OU, signed by the same test CA, authenticated as that distinct subject. This is a valid certificate under the configured trust anchor; it shows the test CA is the identity authority. No per-subject role restriction was tested.

This repeat does not establish Capsule protocol/account isolation, PTY resize, Jackin agent authentication, host workspace/Git semantics, profile enforcement, optional Docker development, or any target beyond macOS ARM64 + OrbStack Linux ARM64 Docker.

## Cleanup

Delete the two sandbox resources through the authenticated client and verify an empty sandbox list. The tested program did this by request; server logs and the final empty inventory are saved. Stop the gateway process with Ctrl-C. Then run `python3 experiments/full-replacement-20261024/repeat-control/cleanup-owned-fixture.py` to remove only this gateway's generated credentials, isolated XDG config/state, and test certificates. Keep the pinned source, lockfile, scripts, logs, JSON results, and image cache.
