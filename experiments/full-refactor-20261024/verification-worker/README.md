# OpenShell workflow verification worker POC

Disposable experiment for the Jackin 6e266 workflow test worker. It does not invoke Jackin and has no host/Docker test-execution fallback. Docker is used only to build the pinned derived image and create the admitted bind-backed named-volume fixtures. OpenShell creates and deletes every sandbox attempt. The initial released-driver run remains the historical FAIL recorded below; the later tmpfs patch is a separate, pinned **EXPERIMENTAL PATCH** result.

## Reproduce

From the repository root:

```sh
experiments/full-refactor-20261024/verification-worker/gateway/setup.sh
experiments/full-refactor-20261024/verification-worker/prepare-fixtures.sh
experiments/full-refactor-20261024/verification-worker/build-image.sh
experiments/full-refactor-20261024/verification-worker/create-volumes.sh
```

Start the isolated gateway in a retained process session and capture its log:

```sh
experiments/full-refactor-20261024/verification-worker/gateway/run.sh \
  >> experiments/full-refactor-20261024/verification-worker/gateway/gateway.log 2>&1
```

In another terminal, build the small Rust control client and run the worker POC:

```sh
cd experiments/full-refactor-20261024/verification-worker/client
mise install
mise exec -- cargo build --offline
cd ../../../../
experiments/full-refactor-20261024/verification-worker/run-worker.sh
```

The released v0.1.5 Docker-driver path on OrbStack rejected the required structured tmpfs `Mount` request. The same engine accepted the exact `noexec`/`nosuid` options in a create-only `HostConfig.Tmpfs` control. A separate one-behavior patch passed focused driver tests and runtime option/size/noexec/admission checks; it is **PASS only for narrow tmpfs option translation**, with mechanism **EXPERIMENTAL PATCH**. Its base, branch, commit, exported diff and hash are recorded in `results/full-refactor-20261024/verification-worker/patch-tmpfs/`.

The complete verification worker remains **FAIL**. P10/P11 did not prove a complete read-only filesystem boundary. P14 used the exact P11 policy and found that, after create/mkdir/data-write/truncate/rename were denied in the first DAC-writable `/home` directory, chmod on a UID-1000-owned file succeeded. The probe stopped at that first violation; aliases, fork, setuid and later directories remain untested. P12/P13 both triggered OOM events but differed in outcome and sandbox survival. See `results/full-refactor-20261024/verification-worker/patch-tmpfs/result.md` and `results/full-refactor-20261024/verification-worker/landlock/result.md`.

## Configuration and boundary

- OpenShell CLI/gateway: v0.1.5, commit `bdb956f2cd65a635f1294fccf1d138d263bf650f`.
- Gateway identity: `jfr-20261024-verify`, endpoint `https://localhost:28630`, Docker driver, private XDG config/state under this directory, fresh CA/JWT/client identity, mTLS enabled.
- Gateway Docker config: bind-backed volumes enabled; resource admission stayed enabled; sandbox PID limit 64. No raw `type=bind` was sent in a sandbox request.
- Docker endpoint: OrbStack context, `unix:///Users/example/.orbstack/run/docker.sock`.
- Image: derived from Jackin’s frozen Python image digest, with an explicit UID/GID 1000 account and `/sandbox` workspace. Identity is in `results/image-final-identity.txt`.
- Inputs: disposable detached clone of the existing small Rust `runtime-probe` project plus a trusted test bundle. The exact host directories are validated against named-volume device options and workspace labels before attachment.
- Candidate/trusted mounts were requested read-only at `/sandbox/repo` and `/sandbox/checks`; the protected workspace root `/sandbox` itself is not replaced.
- Request CPU/memory: 1 CPU and 512 MiB; gateway PID cap 64. Intended tmpfs: `/tmp` 64 MiB with `noexec,nosuid`; `/build` 256 MiB with `nosuid`.
- No provider/account/agent credentials were attached. The only requested exec environment variable is `PYTHONDONTWRITEBYTECODE=1`.

## Result limits

OpenShell accepted create requests and deletion was acknowledged and confirmed for all three created sandbox IDs. None reached Ready. No test command ran inside a sandbox, so success/failure/timeout/cancellation, output bounds, network denial, read-only mounts/rootfs, tmpfs exhaustion, and effective CPU/memory/PID enforcement remain **NOT TESTED**. The valid API resource shape is `template.resources.limits.{cpu,memory}`. The first attempt used an invalid shape and was rejected before allocating a sandbox; it is retained only as request-debug evidence in the gateway log.

The offline policy hash receipt in `results/full-refactor-20261024/verification-worker/result.json` uses the same concatenation rules as Jackin `TestPolicy::freeze`, with this disposable host script and checkout as argv. It is not a Jackin run or a production evidence row. No result-binding behavior was exercised.

## Cleanup

Cleanup for this run is complete. `results/full-refactor-20261024/verification-worker/cleanup/cleanup-summary.md` lists the receipts and exact resources removed. The gateway inventories were empty before shutdown; the two dedicated gateways, private cert/config/state, exact candidate and trusted-bundle volumes, eight derived worker image tags, and generated helper binary were removed. Shared base images, shared build caches, fixture source, scripts and raw evidence remain. No broad container/image/cache prune was run. The scripts `cleanup-owned-gateways.sh`, `cleanup-owned-docker-resources.sh`, and `cleanup-private-state.py` describe the bounded cleanup actions used for this experiment; they have already been executed, and their exact one-run identities are preserved in the receipts.
