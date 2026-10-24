# Required target qualification matrix

Declared before final experiments; selected sources are in `results/full-refactor-20261024/source-pins.json`. A target is one gateway, driver, endpoint, workspace and platform. New distributed requirements are separate from current desktop behavior. No unavailable required target is removed from scope.

| Target | OS / architecture / engine / driver / control | Applicable live evidence | Complete required journey result | Missing proof / prerequisite |
|---|---|---|---|---|
| Local macOS + OrbStack | macOS 27.0.1 ARM64; Docker client 29.9.2, host OrbStack Linux ARM64 engine 29.8.2; OpenShell Docker driver 0.1.5; verified mTLS | Rust control/duplex/PTY/idempotency, canonical-process reconnect, actual-role agent version/hook slices, host-backed named-volume Git primitives, bounded CPU/memory, external-engine Docker/Compose/initial Testcontainers | FAIL | Required edited native Testcontainers fails; managed optional engine, full account/session/credential/host protocol and combined journey unproved. Selected image GID0 needs explicit adaptation. Released worker tmpfs fails; patches separate. |
| Local macOS + Docker Desktop | Required distinct desktop engine/driver target | `target-prerequisites.json`: desktop-linux context absent | BLOCKED | Docker Desktop environment and independent full image/storage/auth/session/engine/policy/recovery journey. OrbStack results do not qualify it. |
| Local Linux host | Required distinct native-host configuration; architecture/engine to qualify | No authorized native Linux host supplied | BLOCKED | Qualified host, gateway bootstrap and full contract. Added Linux guest below is not silently relabeled native. |
| Added OrbStack-hosted Linux guest | Ubuntu 24.04.5 ARM64; own Docker 29.1.3; OpenShell Docker driver 0.1.5; private-IP verified mTLS | Fresh guest, release asset verification, image built in guest engine, approved volume retention/recreation, two-gateway Rust inventory/control; cleanup complete | NOT TESTED | Full actual role/account/session/workspace/Docker/policy/recovery journey. Local build in destination is not proof of host-built image transfer. Listener rebind broke old supervisors; documented grpc_endpoint fixed new sandboxes. |
| Packaged OpenShell VM | macOS ARM64 host; packaged VM driver 0.1.5; gateway-level 2 vCPU/2048 MiB sizing; verified mTLS | Host-Docker-built local image delivered, ARM64 guest UID/GID1000/caps0/NNP1, workspace grant; admission-preserving bind rejected; cleanup complete | FAIL | Required live host sharing/confinement, actual role/private account layout, different size selection, callbacks/service access, managed engine/children VM boundary, persistence/flush/recovery and combined journey. |
| Remote Linux | Required authorized separate host/gateway; chosen remote checkout authority | No authorized host supplied | BLOCKED | Bootstrap/auth/renewal, image absent remotely then delivered, storage/conflict/export, agent/session, engine, limits, outage/recovery/cleanup. Linux guest control is not this profile. |
| Remote macOS | Required authorized separate host/gateway and driver | No authorized host supplied | BLOCKED | Same full contract plus actual macOS process/host permissions where relevant. Local VM is not remote macOS. |
| Kubernetes | Required existing authorized cluster, gateway/controller, PVC/storage, enforced NetworkPolicy and image credentials | kubectl current-context absent | BLOCKED | No cluster created. Pod startup alone would not prove storage, egress, authenticated session, role/account, optional engine or recovery contract. |
| Windows | Future | None | NOT TESTED | Future design, not claimed. |
| General agent collaboration | Future product scope, not a target | Independent parallel fixtures only | NOT TESTED | No collaboration capability inferred. |

## Identity, sizing and storage rules

- Each gateway has separate credentials, state and ownership namespace. Two-gateway Rust tests used duplicate display names with distinct immutable sandbox IDs and correct target attribution; unavailable target stayed unavailable rather than deleted.
- VM sizing is gateway-level in the reviewed driver. Different requested sizes require explicitly qualified size-specific targets/configuration or upstream support; unsupported generic per-sandbox CPU/memory flags are not a solution.
- VM mount limits are architecture-dependent: three mounts on x86_64, 32 on ARM64. The actual multi-mount role/private-state layout is unproved. Do not expose a broad private directory to reduce mount count.
- Local host-backed volume proof is a Docker storage adaptation with admission enabled and exact host-side authorization. It does not establish VM virtiofs confinement or Kubernetes storage semantics.
- Remote source authority is the remote durable checkout. Explicit Git synchronization/export does not provide automatic live desktop sharing; conflict behavior must be tested.
- Strong VM claims must identify the processes inside the boundary. An agent VM using external container DinD leaves daemon/children outside the agent VM.

## Evidence and cleanup

Execution: `results/full-replacement-20261024/targets/`, `control/two-target-control.*`, `workspace/`, `repeat/`, `repeat-control/`, and current-role results under `results/full-refactor-20261024/agents/`. Compatibility limits are explicit in `results/full-refactor-20261024/compatibility.md`.

The target experiment's Linux guest and packaged VM resources were removed by recorded ownership/ID checks after dependent control tests. Its cleanup records distinguish OpenShell-owned removal from fixture-owned volume/gateway/image/machine removal. Unowned host inventory drift occurred during concurrent work; it is recorded and not attributed to an unproven actor. No claim of byte-identical unrelated inventory is made.
