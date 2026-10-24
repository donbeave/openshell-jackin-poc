# Measurements

These are single-run proof-of-concept measurements, not benchmarks. Shared caches were retained. Failed attempts remain in the individual JSON records. Image `started_utc` fields written by the build helper were captured after the command; monotonic `seconds` is the duration used below. Do not use that helper field as an exact start time.

## Environment

macOS 27.0.1 build 26A434, Darwin 27.0.0, ARM64 Apple M5 Max, 18 logical CPUs, 137,438,953,472 bytes RAM (128 GiB). Initial free disk was 2,007,956,910,080 bytes (the adjacent initial probes vary slightly). Docker client 29.9.2; OrbStack Linux ARM64 engine 29.8.2. See `environment.json` and the recorded disk checks. The local disk-threshold policy was explicitly waived by the user; shared cache pruning was not used.

## Image builds

| Build | Duration | Cache condition and result | Evidence |
| --- | --- | --- | --- |
| First small image attempt | 16.509 s | Failed npm CLI copy layout; retained | `image/build-2.1.310-cold.json` |
| Corrected first small image | 18.875 s | First successful derived recipe; host base layers partly cached | `image/build-2.1.310-retry.json` |
| Construct-based v2 image | 25.886 s | New recipe; existing base/tool download caches | `image/poc-final-v2.json` |
| Unchanged v2 recipe | 1.705 s | Build instructions reused cache; no shared cache eviction | `image/poc-final-build-matrix.json` |
| Forced v2 rebuild | 30.908 s | `--no-cache`; base image layers remain cached | Same matrix |
| Actual agent version change to 2.1.309 | 24.847 s | Same recipe/tooling, changed npm agent version | Same matrix + sandbox version record |
| Final Rust-ready v3 | 75.029 s | Added compiler/linker dependencies and locked-project prefetch; warm host image cache | `image/poc-v3-buildessential-prefetch.json` |

The warm/forced v2 build manifests have different recorded IDs; cache reuse is established by cached instruction output, not by asserting identical manifest IDs. The v3 recipe is a later distinct experiment. No fully empty host-image/build cache was created, and the v2 numbers are not v3 cold/warm results.

## Readiness and first development test

| Measurement | Observed duration | Definition and cache condition |
| --- | --- | --- |
| First container sandbox create command | 0.765 s | CLI completion, local image present; **not** an independently polled readiness time |
| First independent Ready observation | 7.044 s after create request | Basic get showed Ready; includes manual delay, so this is an observation bound rather than isolated provisioning latency |
| Warm SDK sandbox start | 0.700 s | SDK response contained phase Ready; same image and retained workspace |
| Primary sandbox warm start | 1.292 s | CLI start plus subsequent retained-file/Docker checks; image cached |
| First successful native development test | 174.024 s after first create request | Rust compile/run passed; includes uploads, tool-home correction and unrelated interactive probes, not pure build time |
| VM first Ready observation | about 72 s | VM profile runtime/image disks initially cold; source Docker image already cached |
| VM create to successful offline compile | about 122 s | Includes env diagnosis and file upload; same local v3 image |

| Dedicated daemon readiness | Duration | Criterion |
| --- | --- | --- |
| cold | 0.413 s | First successful mTLS Docker info; host image cached; fresh empty daemon data |
| warm | 1.474 s | First successful mTLS Docker info; host image cached; same daemon data retained |

The daemon timing fixture used a fresh dedicated engine, distinct generated trust root, pinned Docker 29.8.2 DinD image, 1 CPU/512 MiB limit, and loopback-only published API port 18779. Cold means empty daemon data with host image layers already present. Warm means restart of the same fixture with its data retained; shutdown/restart overhead is included. Commands, failed readiness polls if any, authenticated response and exact fixture removal are in `measurements/daemon-authenticated-readiness.json`. Its cleanup was script-owned. Earlier startup-log listener timing (0.292 s) and an empty Engine B restart (1.572 s) are supplemental and are not substituted for authenticated cold readiness.

The Docker-executed Rust workaround compiled and ran the native loopback test in about 51.08 s cold, with a warm execution around 0.365 s. It changed execution location and returned a file by explicit copy. These are not measurements of native external-network compatibility.

## Resource use

`resources-idle.json` sampled the early container profile: basic agent approximately 5.9 MiB, its separate supervisor approximately 18.8 MiB, and each idle dedicated engine approximately 64–65 MiB. These are snapshots, not guaranteed steady-state baselines.

`measurements/rust-agent-peak.json` read cgroup `memory.peak`: 1,915,482,112 bytes, with 175,132,672 bytes current and a 4 GiB cap. `measurements/engine-a-peak.json` recorded a 4 GiB cgroup peak at the 4 GiB cap; that ancestor includes image loading, daemon, builders and child containers. The samples were taken during/after the experiments, so peaks are not attributed solely to one operation. No whole-machine peak or combined VM host/guest utilization was measured.

The separate 64 MiB agent test killed a 128 MiB allocation (status 137); `memory.events` changed from zero kills to `oom_kill 1`. The supervisor is outside that agent cap. Dedicated engines had separate 2 CPU/4 GiB ancestor caps; a child reported 0.5 CPU/128 MiB. These are separate budgets. VM effective configuration was 2 vCPUs/2048 MiB, not the ignored `--cpu 1` request.

## Cleanup

VM instance deletion removed its overlay and exact instance processes, leaving about 6.2 GiB of experiment-owned prepared-image cache until the VM fixture script removed it. The VM profile directory dropped from about 6.3 GiB allocated runtime state to about 40 KiB of retained scripts/config/log evidence. The previous preview VM remained active.

The independent disk helper removed 12 exited experiment orphan containers and 10 unused experiment image tags, after recording exact IDs and volume references. Top-level cleanup removed remaining experiment sandboxes, external engines and their children, approved project/socket volumes, identified channel volumes, experiment image tags, generated keys and local SDK venv. These removals were not shared-cache pruning. See `cleanup/execution.json`, `disk-audit/`, and final inventories.

Top-level cleanup free-space observations: before 2,037,538,013,184 bytes; after 2,045,334,794,240 bytes. Concurrent writes prevent attributing this difference solely to cleanup.

## Material limitation of the environment run

Three pre-existing OpenShell Docker sandboxes were running in the first inventory and were later found stopped (exit 137 at 22:14:39 UTC). The first test gateway temporarily used their default Docker namespace; later controlled tests proved cross-gateway namespace interference and the unique-label configuration removed it. The initial termination actor is not proven because the first gateway startup log was not retained. These stops predate final cleanup. See `collateral/gateway-analysis.md`; restoration was separately authorized under the original experiment-only mutation limit. Guarded original-gateway stop/start and post-restoration exec checks passed for the same three IDs; see `collateral/restore-originals-execution.json` and `collateral/restoration-verification.json`. This collateral effect is not hidden by the successful isolated runs.

The final disk-helper audit additionally found and removed 12 unreferenced `openshell-supervisor-*` volumes tied by exact sandbox UUID/namespace/managed-by/backend labels to the old experiment instances. They were missed by the first mounted-volume inventory. Their labels, no-reference checks and removal statuses are retained in `disk-audit/supervisor-volume-cleanup.json`; no contents were read. Final audit found no experiment tags, containers, volumes, listeners or generated private keys. Shared public image/build caches remain.
