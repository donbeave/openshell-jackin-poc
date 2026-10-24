# Optional Docker engine ownership research

Research date: 2026-10-24. OpenShell release under test: v0.1.5, source `bdb956f2cd65a635f1294fccf1d138d263bf650f`.

## Mechanisms considered

| Mechanism | Evidence | Result and decision |
|---|---|---|
| Engine inside sandbox compute | Official pinned `docker:29.8.2-dind-rootless` image. First attempt with its actual entrypoint failed at process spawn: `Permission denied (os error 13)` because `/bin` interpreter path was not in the policy's read-only set. A second sandbox added only read-only `/bin` and `/sbin`; no added capability, writable path, privilege, user namespace grant, Docker grant, or client credential. OpenShell launched the entrypoint, then the canonical process exited status 1. It never became ready. The available OpenShell logs do not include the daemon's stderr, so the daemon-level cause is unresolved. | **BLOCKED** for rootless startup evidence on this configuration; not proof rootless Docker is universally unsupported. Exact resources and logs: `rootless-*`. No security weakening or repeated startup attempt. |
| OpenShell-managed companion engine | OpenShell v0.1.5 docs describe a gateway-selected compute driver and Docker daemon socket used by that driver. Config permits driver settings and approved, pre-existing labeled volume attachments; no documented per-sandbox companion create/adopt/inspect/recover/delete operation was found. | **NOT TESTED / missing upstream capability.** A managed companion needs a lifecycle API and owner mapping for daemon process, engine data, certificates, endpoints/ports, child resources, retry/recovery, and teardown. This is a subsystem; no extension implemented. |
| Small extension | Current documented driver extension point selects compute drivers; existing Docker driver provisions the sandbox container through its gateway daemon. No documented hook creates and binds one isolated inner engine to a sandbox lifecycle. | **NOT TESTED / likely architectural change.** Smallest upstream addition: driver-owned companion resource interface with immutable ID, per-instance auth, readiness, retention/recovery, and explicit deletion semantics. Stop until that interface exists. |
| External daemon forwarding | Dedicated disposable DinD engines A/B, separate mTLS identities, TCP endpoint, network policy, Docker/Compose, live bind, Testcontainers service data exchange and cleanup all exercised. | **PASS, EXTERNAL FIXTURE** for connectivity/workflow only. Engines, certificates, published ports, data and outer cleanup remain script/host-owned after sandbox stop/delete. This cannot satisfy native OpenShell engine ownership and cannot be counted as full replacement. |

## OpenShell upstream source review

- OpenShell issue #113, “Secure Docker daemon inside sandboxes”: https://github.com/NVIDIA/OpenShell/issues/113. Issue opened 2026-03-05, closed as duplicate. The text describes the absent in-sandbox daemon/socket/runtime and proposes rootless runtime, Sysbox, nested containerd/BuildKit, or remote Docker forwarding. GitHub shows no branch or pull request linked from this issue. This is proposal/research evidence, not implemented support.
- OpenShell Sandbox Runtimes: https://docs.nvidia.com/openshell/latest/how-it-works/sandboxes/runtimes. Docker compute uses the gateway's configured Docker socket; the sandbox is a container on that daemon host. The docs do not describe per-sandbox companion-engine ownership.
- OpenShell Gateway Configuration: https://docs.nvidia.com/openshell/latest/reference/gateway-config. Documents Docker driver socket and configuration, not a companion engine resource lifecycle.

The search was limited to the official docs, issue #113 and GitHub issue/PR search results for companion Docker daemon support. Absence in those sources is not an exhaustive proof that no private or unlinked work exists.

## Rootless evidence details

- Image: `docker:29.8.2-dind-rootless@sha256:c652fa9cebdaa3d655c33c6389c3c409f9a0fea6449c7d7c56c486fe71af0591`, linux/arm64, image identity in `rootless-image-identity.txt`; image user `rootless` (UID/GID 1000), entrypoint `/usr/local/bin/dockerd-entrypoint.sh`.
- Sandbox `jfr24rootless2`, immutable ID `bde30230-40d1-40e9-82fd-6ffcdf910c70`, failed before entrypoint process launch. It had no Docker grant, socket, client credentials, privileged/capability grant, or engine endpoint.
- Sandbox `jfr24rootless3`, immutable ID `8a756d2b-615e-4013-94c3-8cd4590c916a`, OpenShell create CLI exited 0 but sandbox phase became `Error`, condition `MainProcessFailed`, message `Canonical main process exited with status 1`. Its logs confirm `/usr/local/bin/dockerd-entrypoint.sh` launched, then the canonical process exited. Container stayed as OpenShell-managed sandbox runtime, but sandbox was not ready. No daemon-ready proof.
- Second policy differed only by read-only `/bin` and `/sbin` to admit the entrypoint's `/bin/sh` interpreter; still read-only, not writable. No capabilities were added. The one corrected launch is `experiments/full-replacement-20261024/docker/rootless-create.sh`, policy `rootless-ordinary.yaml`.
- The gateway log does not include rootless daemon stderr. Do not infer whether the next issue is namespace, filesystem, or daemon configuration.
