> Earlier follow-up scope/candidate, preserved for history. The current fresh-setup full-refactor decision and architecture are in [READINESS_REPORT.md](READINESS_REPORT.md), [USER_WORKFLOW_CONTRACT.md](USER_WORKFLOW_CONTRACT.md), and [ARCHITECTURE_DECISIONS.md](ARCHITECTURE_DECISIONS.md). This table is not current runtime approval.

# Full replacement candidate architecture

Status: candidate under test, not a demonstrated complete design. Source/release freeze: `results/full-replacement-20261024/source-pins.json`. OpenShell is the only proposed execution system for agent sandboxes. No old Docker, Apple Container or custom agent-runtime adapter is retained. Docker may run gateway infrastructure, image builds and optional engines.

| Component | Owner | Authority and data | Proof status |
|---|---|---|---|
| Role/account/workspace selection and console | Jackin retained host logic | User authorization, role trust, supported agents, selected model/effort, UI and billing meaning | Source mapped; host-only mapping is not runtime PASS |
| Launch image builder | Jackin invokes Docker builder | Actual role source plus selected agent binaries, tools, hooks and plugins; image recipe/cache identity | Full Architect experiment pending; separate from sandbox Docker grant |
| Gateway and driver | OpenShell | Agent sandbox creation, process boundary, effective limits, runtime state | Isolated release gateway under test |
| Rust control client | Small experiment, future Jackin transport | Verified server CA/hostname and client identity through public SDK transport; immutable target identity | Under test; no insecure fallback |
| Capsule/session process | Jackin retained workload component | Account-isolated agent sessions, protocol, operator control, state/events and host-action authorization | Unchanged real binary/root isolation under test |
| Project and agent persistent state | Jackin retention owner; driver storage attachment | Canonical authorized source, Git mode, private account homes, retained metadata | Real host boundary unresolved; copies and plain named volumes do not prove live sharing |
| Optional dedicated engine | Jackin-owned infrastructure component behind OpenShell execution design | Separate per-instance daemon, CA/client keys, data, networks and ports; broad Docker authority only for granted sandbox | External fixture experiment; not native OpenShell ownership |
| Docker children | Dedicated engine | Child workloads remain outside agent policy unless separately constrained; preserve disclosed partial egress contract | No inherited-agent-policy claim |
| Resource ledger and explicit cleanup | Jackin retained lifecycle responsibility | Immutable gateway/sandbox/engine IDs, ownership labels, retained state and teardown intent | Small experiment manifests only; no production daemon manager |
| Platform prerequisites | Platform operator | Qualified local engine, VM driver, remote host or authorized cluster; storage and network enforcement | Each required target must pass separately |

Images reside in the explicitly selected builder engine and must reach each gateway by a tested local resolution, registry or transfer path. A local tag is never assumed remotely available. Credentials reside in disposable per-instance private storage or provider transport appropriate to the actual agent path; gateway mTLS, engine mTLS, model authentication and command-secret access remain separate.

OpenShell replaces old runtime create/inspect/list/execute/start/stop/delete and underlying sandbox process/transport enforcement. Jackin retains product decisions, Git mode materialization, account authorization, state/recipe ownership, session protocol, host-action authorization, lifecycle retention and optional infrastructure ownership. Those retained responsibilities do not justify retaining a second agent execution runtime.

No fork has been built or counted. A missing upstream primitive stays unresolved. The host-bind candidate must not rely on a missing admission check. Every required target needs one coherent combined journey; combining mutually incompatible successful primitives is insufficient.
