# Verification worker POC result

**Overall: FAIL** for the tested macOS 27.0.1 + OrbStack Linux/arm64 + OpenShell v0.1.5 Docker-driver profile. This is execution evidence for one specific runtime profile; it does not establish behavior on Docker Desktop, native Linux, VM, remote, or Kubernetes targets.

The derived image built successfully and a fresh isolated gateway authenticated over verified mutual TLS. OpenShell accepted each create request, but no sandbox became Ready. After moving mounts under the allowed `/sandbox` workspace and removing only Docker's redundant `rw` tmpfs flag, the OpenShell Docker driver's structured tmpfs `Mount` request failed with HTTP 400 `invalid option: nosuid`. A separate **create-only** Docker API control against the same engine and image succeeded with the exact required options through `HostConfig.Tmpfs`; it was never started and its exact container ID was removed. This narrows the failure to the OpenShell released structured-mount path on this engine. The experiment stopped without weakening the policy. No worker test command ran.

## Evidence

- Release and source: OpenShell v0.1.5, commit `bdb956f2cd65a635f1294fccf1d138d263bf650f`; Jackin source `6e266406b49da2ab3c55355f3b7d33d1643ee6cd`.
- Gateway: `https://localhost:28630`, identity `jfr-20261024-verify`, Docker driver, fresh experiment CA/client identity, verified mTLS, resource admission enabled, bind mounts enabled only to support the reviewed bind-backed named-volume path, gateway PID limit 64.
- Host Docker endpoint: OrbStack context, `unix:///Users/example/.orbstack/run/docker.sock`; Docker client 29.9.2, engine 29.8.2, Linux/arm64.
- Derived image: `jfr-20261024-verify-worker:baseline-python`, `sha256:9644b32c48960dee46b1b7f47b7ba15a7f57f61e1b821fa6a4ea9c916dc6d77c`, linux/arm64, UID/GID 1000. It adds passwd/group entries because the pinned base lacks `groupadd`; it adds no packages or credentials.
- Candidate source: disposable `runtime-probe` checkout at `aa24614607f52a98fd4894a1b02d355b219a9edc`; tree `20aa242142b7099eac398f15fe79cb105f22838a`.
- Tmpfs API control: `experiments/full-refactor-20261024/verification-worker/tmpfs-diagnostic/reproduce.sh` issued `docker create` only against the same image with `HostConfig.Tmpfs` values `/tmp=rw,noexec,nosuid,size=67108864` and `/build=rw,nosuid,size=268435456`. It succeeded (exit 0), saved `docker inspect` evidence, did not call `docker start`, removed the exact returned ID `345a28ace53dee4a7e32ec700c2a315a007b32e04d813fee60a82cec6e08c9d2` (exit 0), and confirmed subsequent inspect failed because the ID no longer exists. This proves Docker accepts this configuration path only; it does not prove runtime enforcement.
- Requested limits and policy: CPU 1, memory 512 MiB, PID cap 64; read-only candidate and trusted-bundle volumes; `/tmp` 64 MiB `noexec,nosuid`; `/build` 256 MiB `nosuid`; network disabled; no accounts or credentials.
- Gateway creation/errors/deletions: `experiments/full-refactor-20261024/verification-worker/results/gateway-attempt-events.log` and full `gateway/gateway.log`.
- Latest request/response and exit status: `results/worker.command.json`, `results/worker.stdout.json`, `results/worker.stderr.txt`, and `results/worker.exit-status` within the experiment directory.

## Attempt outcomes

| Sandbox | Outcome |
| --- | --- |
| `jfrv-20261024-w01` / `af2ebd7a-ed3f-463e-a9d8-6f49bac1d0a0` | FAIL: `/work/repo` was rejected because it replaces protected `/sandbox`; OpenShell deletion was confirmed. |
| `jfrv-20261024-w02` / `f8b6c9aa-a1ad-4b16-8e76-fc1e4297737a` | FAIL: Docker rejected tmpfs option `rw`; removed that redundant option because OpenShell tmpfs is writable by default; deletion confirmed. |
| `jfrv-20261024-w03` / `392de56a-9dec-47c2-ac17-76bdb07c0bf8` | FAIL: OpenShell's structured tmpfs `Mount` path was rejected with Docker API 400 `invalid option: nosuid`; required policy retained; deletion confirmed. |

## Harness note

The third attempt's raw Rust client process exit status is `0`, while its JSON body has `journey.error` and the gateway log records the sandbox entering Error. This exposed a harness bug: its top-level `ok` field reflected RPC acceptance/cleanup rather than the failed readiness journey. The harness was corrected so future runs derive the process result from the journey and cleanup result; the correction passed `cargo check --offline`, but was not runtime-rerun. The experiment result is therefore classified from the gateway's explicit provisioning failure, not the buggy process status. Raw evidence remains unchanged.

## Capability status

- **PASS / EXTERNAL FIXTURE:** pinned derived image build; exact candidate/bundle named-volume source validation; same-engine create-only validation of the exact tmpfs options through `HostConfig.Tmpfs`.
- **PASS / CONFIGURATION:** isolated gateway startup and verified mTLS; create request acceptance; OpenShell delete acknowledgement and confirmed deletion for all three sandbox IDs.
- **FAIL / RELEASED:** worker sandbox readiness under the required tmpfs policy using OpenShell v0.1.5's structured tmpfs `Mount` path on this OrbStack Docker engine. The same engine accepted the exact tmpfs policy through `HostConfig.Tmpfs`, so this is not evidence that the engine lacks the feature.
- **NOT TESTED:** runtime attachment, worker process execution, network/read-only enforcement, test outcome binding, timeout/cancellation, output truncation, tmpfs exhaustion, effective CPU/memory/PID limits, peak resource use, or successful development test.

The owned volumes and image remain for review. No created worker containers remain. `experiments/full-refactor-20261024/verification-worker/cleanup.sh` is a dry-run by default and verifies exact ownership before its optional `--apply` removal. Cleanup is not part of OpenShell's ownership evidence.

## Next smallest experiment

Try a one-behavior experimental OpenShell patch that routes validated tmpfs options through `HostConfig.Tmpfs` while leaving validation, named-volume mounts, policy values, and all other security settings unchanged. First preserve the released structured-mount failure. In the patch, require a positive create/readiness and functional `noexec`/`nosuid` negatives, plus a negative malformed-option or forbidden-target test. Keep this as **EXPERIMENTAL PATCH** evidence; if it needs broader driver redesign, stop and report the missing upstream interface. A separate engine profile can be tested later, but this same-engine control makes it the lower-cost next diagnostic.
