# Required target matrix

Declared on 2026-10-24 before final combined experiments. These are required environments, not optional scope. A target is one gateway, compute driver, endpoint, workspace scope, platform, and configured VM size class. Different drivers use separate targets. Windows and general collaboration remain future design requirements.

| ID | Desktop/client | Compute target | Required coverage | Current evidence |
|---|---|---|---|---|
| T1 | macOS ARM64 | Local OrbStack Linux ARM64 Docker driver | Actual role, account domains, host project, sessions, worker, optional Docker, lifecycle | Prior primitive evidence; new isolated experiments in progress |
| T2 | macOS ARM64 | Local Docker Desktop Linux VM Docker driver | Host networking/bridge, real host mounts, image transfer, cleanup | NOT TESTED; no demonstrated separate Docker Desktop engine |
| T3 | Linux x86_64 | Local native Linux Docker driver | Native host paths, UID/files, session/process controls | BLOCKED; no disposable native Linux host supplied |
| T4 | macOS ARM64 | Local libkrun VM | Actual role mount layout, private/project separation, callbacks, durability, gateway size classes | Prior limited upload/build/stop-start only; full row NOT TESTED |
| T5 | Linux x86_64 | Local libkrun VM | Three-mount layout, permissions, callbacks, storage and size classes | BLOCKED; no disposable host supplied |
| T6 | Local desktop | Remote Linux container and VM gateways | Different-machine image delivery, remote project replica/conflict/export, authenticated fleet | BLOCKED; no authorized disposable remote endpoint supplied |
| T7 | Local desktop | Remote macOS ARM64 VM gateway | Remote delivery/storage, VM networking and correct-desktop host actions | BLOCKED; no authorized disposable remote endpoint supplied |
| T9 | macOS x86_64 | Local container gateway | Packaged client, terminal restoration, host mounts and ownership | BLOCKED; no disposable Intel Mac supplied |
| T10 | Linux ARM64 | Local native Linux Docker driver | Packaged client, UID/files and local process behavior | BLOCKED; no disposable native Linux ARM64 host supplied |
| T8 | macOS/Linux desktop | Kubernetes Linux compute | Controller prerequisites, enforced NetworkPolicy, PVC, imagePullSecrets, authenticated gateway | BLOCKED until disposable cluster/context supplied |

Desktop support baseline comes from Jackin source and current published packaging, not an assertion that every backend already works. Apple Container finalization is incomplete; OpenShell VM is a new required implementation mechanism. The binary preview/release policy in `.github/workflows/binary-preview.yml:82` publishes aarch64-apple-darwin, x86_64-apple-darwin, aarch64-unknown-linux-gnu, and x86_64-unknown-linux-gnu clients. Intel macOS and Linux ARM64 remain explicitly required desktop rows. This packaging evidence does not prove runtime qualification. Representative architecture selection: ARM64 for local desktop/container/VM, x86_64 for Linux/Kubernetes and the smaller VM mount budget.

Each passing target needs its own gateway identity, CA/auth reference, state directory, owner namespace, full inventory pagination, image digest/platform, project and private stores, cleanup receipt, and before/after unrelated-resource inventory. No copied archive is called a live host mount. Remote model is an explicit target-side project replica with export/conflict detection; live local-host semantics cannot be promised for remote targets without a proven synchronization mechanism.

Gateway-level VM sizing will use separately configured size-class targets. `--cpu`/`--memory` per-sandbox flags are not a sizing implementation for the reviewed VM driver. The exact role requires more than a project directory: private account directory, tool/cache directories where not baked into image, and worktree Git metadata. Consolidation may include only data authorized to the same domain; unrelated private directories cannot be co-mounted merely to fit the three x86_64 mounts. Actual layout and flush failures remain experiments, not source-backed passes.

Read-only final prerequisite discovery is retained in `evidence/target-discovery.json`: only two local gateway registrations were present, with no remote registrations. The kubectl, Helm and Apple Container entries were mise shims without an installed selected executable (`mise which` failed). No gateway registration or global selection was changed. This discovery does not authorize mutation of the pre-existing local gateways.
