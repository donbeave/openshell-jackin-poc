# Versions and evidence compatibility

Collected 2026-10-24. Raw API responses and commands are in `evidence/versions/`; installed tool and host evidence is in `evidence/environment.json`. Source checkouts are research copies, never the working Jackin checkout. No Jackin refactor is authorized or implemented.

| Repository | Reviewed reference | Current main observed | Use in this research |
|---|---|---|---|
| Jackin | `6e266406b49da2ab3c55355f3b7d33d1643ee6cd` | Same | Production source audit baseline |
| Architect | `7b72b38fe1d66e35c0931899c53bf3719592bbcc` | Same | Actual role build input |
| Research | `2315e6a278231854b3139b1ca32402777ff3cd01` | Same | Prior published archive; working directory itself has no `.git` |
| OpenShell | `v0.1.5`, `bdb956f2cd65a635f1294fccf1d138d263bf650f` | `f571c8e99c185804c39e837a2b70692e957de327` | All new runtime experiments stay on installed 0.1.5; main is source review only |

Available release records are saved, including draft flags. Jackin's latest observed published non-draft release is `jackin-dev-v0.1.52` (2026-09-13); the `preview-41bad147...` record is an unpublished draft, not an available release. Architect and the research repository returned no releases. OpenShell stable is `v0.1.5` (2026-10-20), with previous `v0.1.4`, `v0.1.3`, and a rolling prerelease `dev`. The API's dev target and publication timestamp do not identify current main. Never use `dev` as an experiment pin.

## Relevant changes

The prior product report read Jackin `41bad147...`; runtime POCs earlier read `7d4b8acea...`. The one commit from `41bad147...` to `6e266406...` changes child coordination, spooled process-group ownership, Capsule spawn/telemetry, Linux reaping and Darwin wait/reaper support. It affects 34 files, with 11,225 insertions and 181 deletions. Therefore the older source product analysis can guide unchanged role/account/workspace logic, but cannot prove the current process-lifetime behavior. New experiments must use an identified binary built from the required pin or explicitly remain version-limited. The installed host Capsule identifies `0.6.4+2b582a4`; it is not this pin. `--version` of a different binary is never promoted to evidence for `6e266406`.

OpenShell main is 49 commits ahead. The GitHub compare file list reaches its 300-file cap; a local pinned fetch and full diff-stat were also retained. Important changes include:

- `029fda684da8` moves CLI transport to the Rust SDK and adds SDK `ClientIdentity` mTLS support. Pinned 0.1.5 has no such SDK field and explicitly delegates mTLS to CLI legacy transport. This source change is promising, not executed compatibility evidence.
- `32f026442e4d` changes supervisor/compute connections to runtime-initiated transports across drivers. Mixed main/stable supervisor/driver binaries cannot be assumed compatible.
- `72ab4dd9ef59` and `9a85667d0d87` add Kubernetes shared-supervisor deployment/runtime changes. They do not establish a tested stable Kubernetes configuration here.
- `9152b6e4a172` lets VM boot a digest-pinned cached root disk without contacting registry. Stable registry-outage/recreation tests cannot borrow that behavior.
- `465324a8311a` fixes empty VM guest `/etc/hosts`; `20cb306d3ae8` changes Docker supervisor healthcheck cadence. Both affect operational assumptions and measurements.
- Latest runtime documentation changes default Docker/Podman UID fallback. Stable behavior must come from the stable source and executed image, not current documentation alone.

Full relevant diff is `evidence/versions/openshell-relevant-diff.patch`. No OpenShell patch has been applied. Upgrading any component requires an explicit compatibility experiment for runtime descriptors, protocol versions, authentication, exact streams, lifecycle, image/private storage, and policy enforcement before results are merged.

## Reused evidence

All 579 files listed in the original `ARCHIVE_MANIFEST.json` match their saved SHA-256 hashes (`evidence/archive-integrity.json`). New files are additive and not covered by that original manifest. Integrity verifies retained bytes, not correctness of the original experiment.

Read handoff, original readiness, capability matrix, decision, measurements, product contract, evidence audit, raw version/image/lifecycle/rootless/changed-binary results. Prior evidence remains scoped to macOS ARM64 with OrbStack Linux ARM64 engine, OpenShell 0.1.5, and its recorded images/policies. The limited VM result is distinct. None proves native Linux, Docker Desktop, remote Linux/macOS, Kubernetes, actual Architect, current Capsule, or an authenticated model session.

| Prior evidence | Result retained | Mechanism | Safe reuse and limit |
|---|---|---|---|
| `results/image/poc-final-build-matrix.json` | PASS | Released OpenShell feature / builder | Selected Claude version and image caching mechanics; small recipe, not Architect |
| `results/sdk-probe.json` | PASS | Configuration | Python mTLS/lifecycle; not Rust integration proof |
| `results/terminal/eof-sessions.json` | PASS | Configuration | Plain PTY input/resize/interrupt; not Capsule protocol |
| `results/repeat-final/native-same-path-v2.json` | FAIL | Released OpenShell feature | Rebuilt native network test fails PermissionDenied; no transparent resolution demonstrated |
| `results/native/native-identity-cycle-3-valid.json` | FAIL | Released OpenShell feature | Hash changed at resolved executable path; policy log reports executable changed |
| `results/policy-streams/events.json` | FAIL | Released OpenShell feature | Unrelated policy update closes established Docker/database streams |
| `results/alternatives/rootless-actual-startup.json` | FAIL | Released OpenShell feature | Rootless engine fails iptables permissions; native managed capability not proved |
| `results/native/testcontainers-success.json` | PASS | External service | First-run Redis data exchange only; repeated modified Testcontainers/concurrent unmodified project remain unproved |
| `results/ownership/after-delete.json` | FAIL | External service | External daemon and children survive sandbox deletion; script-owned cleanup distinct |
| `results/network/child-access-final.json` | FAIL for inheritance | External service | Child reaches endpoint denied to agent; no policy inheritance claim |
| `results/gateway-vm/` | PASS for limited slice | Configuration | VM agent version/offline build/upload retention only; not live host mounts or Docker children in VM |
| `results/agent-auth-availability.json` | NOT TESTED | Configuration | No test credential supplied; personal credential files not read |

Distinct output paths and Docker-child loopback execution remain successful workarounds only. They do not erase the failed native operation or establish ordinary Cargo/Testcontainers transparency. Prior independent Engine B repeats are useful repeats of those exact primitives; they are not the required fresh combined experiment.

## Measurements carried forward

`results/MEASUREMENTS.md` remains authoritative for sample definitions. Warm small v2 build 1.705 s, forced v2 30.908 s, version-change v2 24.847 s, final v3 75.029 s are different cache/recipe samples (n=1 each), not a single latency distribution. Prior VM first Ready observation about 72 s includes observation delay; CLI create response 0.765 s is not application readiness. Early idle samples: workload about 5.9 MiB, supervisor about 18.8 MiB, external engine about 64–65 MiB. Separate engine+children cgroup budget is not part of agent memory cap. No tail percentiles, current-Capsule baseline, three-domain cost, remote transfer cost, or combined authenticated startup cost is justified. Required missing measurements stay NOT TESTED.

## Source reproduction and final discovery

`experiments/metadata/fetch-sources.py` fetches missing exact source pins and preserves an existing differing checkout without reset. It was syntax-validated, not rerun over the retained source checkouts. `audits/dependency-declarations.json` records relevant lockfile versions and 102 Cargo manifest dependency declarations; declarations are not execution classifications. Per-action dispositions remain in the independently reviewed source ledger. Final local registration/tool discovery is in `evidence/target-discovery.json`; no disposable remote or Kubernetes target was discovered or authorized.
