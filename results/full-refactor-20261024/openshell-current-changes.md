# Released source versus observed main

Selected executed release remains v0.1.5, `bdb956f2cd65a635f1294fccf1d138d263bf650f`. Observed main is frozen separately at `f571c8e99c185804c39e837a2b70692e957de327`, 49 commits ahead. The GitHub comparison and first20 available release records are saved as `openshell-main-comparison.json` and `available-releases.json`. Architect has no GitHub release entries in that query; its commit remains the source authority. No main binary was built or tested here.

Relevant source changes requiring separate compatibility/runtime qualification:

- Gateway-initiated supervisor connections and per-sandbox supervisor state change the control/bootstrap path. They are not inferred fixes for the stable release's changed-binary or strict-worker results. [Connection change](https://github.com/NVIDIA/OpenShell/commit/32f026442e), [state isolation](https://github.com/NVIDIA/OpenShell/commit/ea13dfce41).
- Kubernetes shared-supervisor deployment/hosting changes lifecycle, resource budgeting and isolation assumptions. It does not qualify a cluster/PVC/NetworkPolicy target without execution. [Deployment](https://github.com/NVIDIA/OpenShell/commit/72ab4dd9ef), [hosting](https://github.com/NVIDIA/OpenShell/commit/9a85667d0d).
- CLI transport now uses the Rust SDK; the executed stable route used the public SDK with a caller-built verified channel. Do not transfer CLI behavior across these versions without rerunning. [Transport refactor](https://github.com/NVIDIA/OpenShell/commit/029fda684d).
- VM cached digest boot and guest loopback-name handling affect image/offline/network preparation. They do not establish host-sharing confinement or full VM behavior. [Cached digest boot](https://github.com/NVIDIA/OpenShell/commit/9152b6e4a1), [guest hosts](https://github.com/NVIDIA/OpenShell/commit/465324a831).
- Docker healthcheck cadence changes idle cost; it is not part of the stable idle sample. External compute-driver setup documentation is newer, but documentation is not a managed companion implementation. [Healthcheck](https://github.com/NVIDIA/OpenShell/commit/20cb306d3a), [external drivers](https://github.com/NVIDIA/OpenShell/commit/132c582349).
- Authorization audit events and TLS/dependency updates exist on main. No production security/readiness claim is made from the isolated stable tests.

The comparison does not list a change to the public `proto/openshell.proto` file. No executed main result demonstrates immutable-ID/generation mutation, a managed per-domain Docker companion or the full worker/session/account contract. The experimental patches remain based on the pinned release, not mixed with main. Required environments/accounts also remain unavailable. Main source inspection therefore does not change the full-refactor verdict.
