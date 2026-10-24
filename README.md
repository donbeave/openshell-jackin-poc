# OpenShell runtime proofs of concept for Jackin

**Start here:** [Agent handoff](AGENT_HANDOFF.md) · [Rewrite readiness](JACKIN_REWRITE_READINESS.md) · [Public-copy provenance](PUBLICATION.md)

Follow-up product analysis: [Jackin rewrite readiness](JACKIN_REWRITE_READINESS.md) maps the results to current Jackin user workflows. It distinguishes starting a focused prototype from committing to full runtime replacement; original experiment results below are preserved.

Read [DECISION.md](DECISION.md) and [CAPABILITY_MATRIX.md](CAPABILITY_MATRIX.md) first. The full requested contract is not ready; the demonstrated constrained approach is conditional. No Jackin repository was modified, and no production extension, controller, scheduler or daemon manager was built.

A **proof of concept** is a small experiment testing one requirement. A **dedicated engine** is a Docker daemon reserved for one test instance. An **external fixture** is a resource created outside OpenShell. A **workaround** changes the normal workflow. A **source patch** changes OpenShell code; none was applied here.

## Prerequisites and scope

The recorded run used macOS ARM64, an existing OrbStack Linux ARM64 engine, Docker client 29.9.2/engine 29.8.2, and published OpenShell v0.1.5 at commit `bdb956f2cd65a635f1294fccf1d138d263bf650f`. The CLI and `openshell-gateway` were already installed. Python 3.11+, uv, OpenSSL, and Docker Compose/buildx are needed on the host. VM probes additionally used the installed packaged VM driver/libkrun and Homebrew e2fsprogs; no custom kernel or cluster was built.

The user waived the local disk-threshold policy for this experiment. Shared caches were not pruned. Independent disk cleanup removed only recorded unused experiment tags and exited experiment orphans. See `results/disk-audit/`.

All resources use the `ojp-20261024` test ID. Before a new run, verify that this ID is unused or run the scoped cleanup. Do not reuse the names while another experiment instance is active. Use a new result directory or archive the existing evidence before replaying scripts that write fixed output filenames. Preserve original release results when trying any alternate release or source patch.

The separate local gateway uses `https://127.0.0.1:18770`; the separate VM gateway uses port 18771. Existing `openshell` and `openshell-vm` gateway registrations and their workloads were not reconfigured. All experiment CLI commands use `sh experiments/os.sh`, which selects isolated XDG state and credentials. Do not run them against your default gateway.

## Ordered reproduction

Commands assume the repository root. The result files contain the exact commands actually run, including preserved failures and corrections. The helper scripts are small experiment drivers, not a general test framework. Paths in the original run are absolute under `/Users/example/openshell-jackin-poc`; adjust experiment-owned path prefixes if replaying elsewhere.

```sh
uv venv experiments/sdk-venv
uv pip install --python experiments/sdk-venv/bin/python openshell==0.1.5
```

1. Read `results/sources/README.md`, `results/architect.source`, and `results/jackin.source`. They identify requirements only. The pinned OpenShell `.mdx` source snapshots are in `results/sources/`; source inspection is never a runtime test.
2. Prepare the separate gateway using `results/gateway/README.md` and `experiments/gateway/run-gateway.sh`. Generate new test-only certificates with `openshell-gateway generate-certs`, enable listener mTLS and launch JWT signing, retain `allow_driver_config = true` with resource admission enabled, and set Docker `sandbox_label = "ojp-20261024"`. The default namespace collided with another gateway during the first group; that failed group is retained.
3. Build the agent image **before** sandbox creation. The final frozen recipe is `experiments/image/Dockerfile.v3`, with build context `experiments/rust-project`. The original and intermediate recipes are also retained.

```sh
docker buildx build --load --progress=plain \
  --build-arg CLAUDE_VERSION=2.1.310 \
  -f experiments/image/Dockerfile.v3 \
  -t ojp-20261024-agent:2.1.310-poc-v3 experiments/rust-project

# Repeat unchanged, then force instruction re-execution; do not prune shared caches.
docker buildx build --load --progress=plain \
  --build-arg CLAUDE_VERSION=2.1.310 \
  -f experiments/image/Dockerfile.v3 \
  -t ojp-20261024-agent:2.1.310-poc-v3 experiments/rust-project
docker buildx build --load --no-cache --progress=plain \
  --build-arg CLAUDE_VERSION=2.1.310 \
  -f experiments/image/Dockerfile.v3 \
  -t ojp-20261024-agent:2.1.310-poc-v3 experiments/rust-project
```

Record build duration, cached instruction output and image ID each time. `--no-cache` does not remove cached base layers. The historical v2 warm/forced/version-change measurements are in `results/image/poc-final-build-matrix.json`; do not attribute them to the later v3 recipe. Build with `CLAUDE_VERSION=2.1.309` and a distinct tag to repeat the changed-agent test; run the actual version command inside its new sandbox.

4. Create the no-Docker sandbox with `experiments/denied.yaml`, a short unique name of at most 19 characters, `--no-auto-providers`, and an explicit main process. Use `experiments/sdk-probe.py` for the small public SDK lifecycle probe after installing `openshell==0.1.5` into an experiment venv. The independent SDK create/delete probe is under `experiments/repeat/`. `experiments/terminal-eof.py` records input, resize, Ctrl-C and Ctrl-D reconnect; see its fixed sandbox name before running it.
5. Create the two dedicated external engines. Read the script before running: they are privileged DinD **external fixtures** with their own data, trust material, CPU/memory caps and narrow outer port mappings. The workload does not receive the developer's Docker socket.

```sh
sh experiments/engines/setup.sh
python3 experiments/engines/probe.py
python3 experiments/engines/api-probes.py
python3 experiments/engines/seed-redis.py
```

Public image transfer uses `docker save`/`docker load` when needed. `seed-image.sh` is a small helper for that transfer. Nested registry egress had transient failures with the deliberately tiny ephemeral-port range; retain those failures rather than treating a seeded image as proof of registry access.

6. Start the selected instance using the approved project volume and explicit non-secret environment. Engine A's public API hostname is resolvable; the policy contains exact allowed ports and TCP TLS passthrough. Engine B uses separate keys/volume and API port 18777. Project volume ownership must match workload UID 1000; only change this disposable volume.

```sh
docker exec ojp-20261024-engine-a chown 1000:1000 /sandbox/ojp-project
sh experiments/os.sh sandbox create --name ojp-20261024-main \
  --from ojp-20261024-agent:2.1.310-poc-v3 \
  --policy experiments/engine.yaml \
  --driver-config-json '{"docker":{"mounts":[{"type":"volume","source":"ojp-20261024-engine-a-project","target":"/sandbox/ojp-project","read_only":false}]}}' \
  --env OJP_VALUE=harmless-value \
  --env DOCKER_HOST=tcp://host.docker.internal:18776 \
  --env DOCKER_TLS_VERIFY=1 \
  --env DOCKER_CERT_PATH=/workspace/ojp-tls/client \
  --env CARGO_HOME=/home/agent/.cargo \
  --env RUSTUP_HOME=/usr/local/rustup \
  --env MISE_DATA_DIR=/home/agent/.local/share/mise \
  --cpu 1 --memory 4Gi --no-auto-providers --detach \
  -- /opt/ojp-role-hook.sh sleep infinity
sh experiments/os.sh sandbox upload ojp-20261024-main \
  experiments/engines/private/engine-a/client /workspace/ojp-tls
sh experiments/os.sh sandbox exec ojp-20261024-main --no-login-shell -- docker version
```

Directory uploads append the local directory basename. The resulting TLS files are under `/workspace/ojp-tls/client`. Do not upload private keys into `results/`. Image ENTRYPOINT is replaced by OpenShell; the explicit main-process hook is necessary. Non-secret tool environment must be set explicitly. No real API credential is needed for these tests.

7. Test Docker operations from `experiments/docker-operations.py`, adjusting its fixed sandbox name if needed. Test live binds with the commands in `results/main/bind-files-owned.json`; agent and daemon both use `/sandbox/ojp-project`. Upload `experiments/compose` into that volume, then run:

```sh
sh experiments/os.sh sandbox upload --no-git-ignore \
  ojp-20261024-main experiments/compose /sandbox/ojp-project
sh experiments/os.sh sandbox exec ojp-20261024-main --no-login-shell -- \
  docker compose -p ojp-compose -f /sandbox/ojp-project/compose/compose.yaml up --build -d --wait
sh experiments/os.sh sandbox exec ojp-20261024-main --no-login-shell -- \
  docker compose -p ojp-compose -f /sandbox/ojp-project/compose/compose.yaml ps --format json
```

Read the returned automatic port instead of assuming the historical value. The fixture reserves A ports 18080–18084 and B ports 18085–18089; allow the fixed set before launch. The tested client endpoint is `host.docker.internal:<reported port>`. Remove the Compose application with `down -v --rmi local` before competing Testcontainers experiments use these few ports.

8. Upload the one Rust project to `/workspace`; use `mise exec -- cargo nextest run --offline` from `/workspace/rust-project`. Real Testcontainers uses `TESTCONTAINERS_HOST_OVERRIDE=host.docker.internal` and the supplied per-instance Docker TLS environment. Native egress additionally needs the actual resolved mbx executable path in the service rule. See `results/native/native-identity-baseline.json` and the two `*-cycle-*-valid.json` records for exact normal-build commands, paths, hashes and denials. The rebuild succeeds; the changed binary's subsequent protected network connection is denied. This does not mean all local Rust execution is denied. Preserve the failed native result before running the distinct-path or Docker-executed workaround. The canonical Testcontainers source includes the typed port and `IntoContainerPort` import; earlier compilation failures are retained.
9. Run `experiments/policy-streams.py` only on its named disposable sandbox after creating it. It starts a Docker stream and one persistent Redis connection, applies an unrelated update, then tests revocation separately. `experiments/policy-streams-control.py` is the no-change control. Neither reconnects automatically. Callback tests use an explicitly started server and `forward start 18100 <sandbox> --background`. Redirect the background forward's output to a file, rather than a captured pipe that can remain open in the SSH child.
10. Other methods: `experiments/engines/unix-socket.sh` creates the disposable Unix-socket fixture. Its approved socket/project volumes are mounted under `/sandbox`; client UID permissions are explicit. Rootless startup and Docker-executed Rust commands are in `results/alternatives/` and `results/native/`. Rootless startup failed without relaxing restrictions. The VM profile has separate setup/reproduction in `experiments/gateway-vm/` and `results/gateway-vm/README.md`.
11. Perform ownership observations **before fixture cleanup**. Stop/start and delete the OpenShell sandbox, inspect the dedicated daemon and its children, and compare exported result bytes. Primary evidence is in `results/ownership/`; the independent clean Engine B repeat is in `results/repeat-final/`.
12. Run `sh cleanup.sh` after all probes/reviews finish. It records and removes only experiment resources. The separate VM cleanup waits for its instance to disappear. Cleanup does not count as OpenShell-owned removal of the external engines.

## Evidence and measurements

`experiments/record.py <result-name> -- <command> ...` records command, UTC, monotonic duration, status, stdout and stderr. Treat the recorded status and output as authoritative: some scripts return 0 even when an individual method failed. Inspect the individual assertions and rows. Original failures include invalid gateway configuration, missing provider profile, incompatible image identity/tool homes/linker, fixture path/permission errors, and namespace interference; successful corrections do not erase them.

See `results/MEASUREMENTS.md`, the full matrix, and independent review. Three pre-existing Docker sandboxes were found stopped before cleanup; their initial termination cause remains unproven. The early shared namespace is a plausible cause, and the incident and approved restoration are documented in `results/collateral/gateway-analysis.md` and `results/collateral/restore-originals-execution.json`. The three original sandbox IDs are unchanged and all three now report Ready and pass harmless exec. Only harmless provider values were used. Generated TLS/JWT private files are disposable fixture state outside saved results and are removed at cleanup. OAuth/OIDC and authenticated model operations remain untested. TCP was sufficient for these fixtures; UDP is untested.
