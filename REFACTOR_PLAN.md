# Detailed full OpenShell refactor plan

This is a plan, not a Jackin implementation. Do not start the full refactor until the unresolved research gates in `READINESS_REPORT.md` are closed. Fresh setup is allowed; no old state/configuration importer or permanent legacy execution fallback is planned.

The per-call change list is [exhaustive-docker-calls.json](results/full-refactor-20261024/exhaustive-docker-calls.json), supplemented by the Apple, Capsule/account and workflow/fleet inventories linked from [SOURCE_INVENTORY.md](SOURCE_INVENTORY.md). Those records are part of this plan; the table below groups implementation work without replacing call-level ownership decisions.

## Phase 0 — Close research prerequisites

1. Prove the selected Candidate B with actual admitted agents/accounts, persistent private domains, shared project, exclusive control, host protocol, approved credential operation and recovery under one configuration. No production replacement Capsule or broker is built as a research shortcut.
2. Finish identity/generation-bound OpenShell operations. Review and test the Delete-only patch, including stable request-ID replay and scope semantics; do not treat it as a solution for Stop/Start/Exec.
3. Demonstrate a managed optional engine owner. If a companion/driver lifecycle subsystem is required, obtain that upstream capability before claiming full readiness. External forwarding is not the managed result.
4. Complete the no-network verification-worker boundary, including any narrowly scoped tmpfs patch and all negative/resource/process-lifetime cases.
5. Resolve the ordinary Cargo/nextest changed-binary workflow and image recipe/selected-agent reuse problems with executed solutions, keeping native failures.
6. Qualify every required target and remote authentication/image/storage path. Missing hosts, cluster or model credentials remain blockers, not future-scope relabeling.
7. Repeat the critical combined journeys independently from fresh resources. The independently repeated storage/Rust primitives are not this combined test.

## Phase 1 — Introduce explicit product records and interfaces

Change `crates/core/jackin-core/src/docker.rs` and the instance/resource model by responsibility, not by a mechanical DockerApi rename. Keep generic command/process/Git/hash helpers. Introduce the TargetRef, SandboxRef, DomainRef, SessionRef, ImageRecipeRef, ResourceReceipt and VerificationBinding described in [ARCHITECTURE_DECISIONS.md](ARCHITECTURE_DECISIONS.md).

Split interfaces:

- **ImageBuilder:** build/inspect/version metadata/cache/prune against an explicit builder. No agent run/exec/attach method.
- **OpenShellTargetClient:** verified transport, named reads with ID validation, identity/generation-bound mutations, streams/watch and explicit deletion receipts. Pagination and unavailable/unauthorized state are first-class.
- **ProjectState:** authorize/materialize Shared/Worktree/Clone and private persistent data using the target's selected mechanism.
- **SessionControl:** logical instance/domain/session mapping, operator lease, trusted protocol and host-action authorization over the proved transport.
- **ManagedDockerCapability:** request an explicitly managed per-instance engine, connect granted domains, and reconcile its owned resource receipts. This is not the old DinD runtime manager.
- **VerificationExecutor:** execute one frozen check in OpenShell, return bounded observations; workflow host service remains the result authority.

Each interface must represent uncertain outcome and partial inventory. No generic NOT_FOUND-to-purge conversion. Persist operation identity before side effects. Use new formats after fresh setup rather than preserving legacy Docker/Apple resource structs.

## Phase 2 — Replace image construction consumers, not the builder

| Current code | Action and reason | Dependency / release gate |
|---|---|---|
| `crates/adapters/jackin-image/src/{derived_image.rs,image_recipe.rs,agent_binary.rs,capsule_binary.rs}` | Retain builder/artifact resolution logic where valid; repair recipe identity to include selected agent/version/artifact, platform and actual role/plugin/tool inputs. Decouple privileged Capsule startup from Candidate B bootstrap. | Actual full role, two installed agent selections/versions, source change, forced/valid cache, all relevant installer routes. Existing installer/marketplace failures stay baseline defects. |
| `crates/services/jackin-runtime-image/src/image/{version.rs,validated.rs,prewarm_run.rs,sibling.rs}` | Replace direct `docker run` version execution with resolved metadata or a short OpenShell probe. Retain warming decisions after separating target image availability. | Missing-prefetch version path, malformed version/failure, immutable image and architecture verification. |
| `crates/services/jackin-runtime-cleanup-prune-images/src/prune_images.rs` | Keep narrow builder removal; replace role-container consumer scan with active and retained image references across targets. | Unused owned image pruned, active/recreatable images preserved; target outage prevents unsafe pruning. |
| `docker/construct`, `docker-bake.hcl`, image/packaging/CI tooling | Retain Docker/Buildx image construction and required Docker CLI tools; update generated bootstrap and artifacts. | Reproducible recipe/platform, no embedded credentials, default sandbox engine access still off. |

Store image config ID separately from OCI index/manifest digest. Use immutable references for runtime/recreation; a mutable local tag is not a remote transfer mechanism. Record target-store import/registry ownership and cleanup explicitly.

## Phase 3 — Replace execution, identity and storage

| Current code | Action | Required proof before deletion of old path |
|---|---|---|
| `jackin-runtime/src/runtime/{backend.rs,apple_container.rs,launch/launch_runtime/docker.rs}` | Remove Docker/Apple agent execution and incomplete backend dispatch; create/execute only through OpenShell. | Explicit startup/hooks, policy, application readiness, image/identity and errors; no fallback. |
| `jackin-runtime-backend-selection`; `jackin-runtime-launch-mounts/src/mounts.rs` selector; config runtime backend fields | Replace Docker/Apple selection with target/profile selection. | Fresh setup config, public option/schema changes documented, correct two-target selection. |
| `jackin-isolation/src/{materialize.rs,capture.rs}` and workspace planners | Retain Git policy/materialization where applicable; replace target storage/path mapping. Do not activate uncalled live capture accidentally. | Shared/Worktree/Clone, linked metadata, RO/symlink/permission/watch/concurrency, dirty/unpushed retention and recreation. |
| Instance manifest/resource state | Replace backend-specific container/VM handles with authority-scoped receipts and persistent data references. | Missing recovery data, generation change, interrupted publication, identity mismatch, explicit retain versus purge. No migration. |
| `jackin-runtime-docker-profile` policy helpers | Retain effective user intent/precedence; replace enforcement mapping with driver-qualified controls. Remove obsolete iptables/Docker flags only after proving equivalent active outcomes. | Open/restricted network, filesystem/identity/required capabilities, CPU/memory/PID/fd/tmpfs enforcement, unsupported grant fails clearly. Do not invent interactive sudo or activate uncalled readback. |

OpenShell owns sandbox processes; Jackin owns authorization and data retention. Local approved bind-backed volumes are an explicitly owned storage adaptation. VM/remote/Kubernetes need separately qualified storage; do not expose unrelated private directories to fit mount limits.

## Phase 4 — Replace session and credential transports

| Current code | Selected action | Gate |
|---|---|---|
| `jackin-runtime-attach-transport`, `jackin-runtime-host-attach`, `jackin-runtime-attach-{capsule-ready,sessions,inspect,running-gate}` | Replace direct Unix/Docker attach/exec fallback with the proved OpenShell canonical-session and control routes. | Same-process reconnect, binary/PTY, exact args/exit/streams, stale-generation input rejection, process versus client exit. |
| `jackin-runtime-session-control`, `jackin-runtime-snapshot`, `jackin-runtime-usage-relay` | Retain product models/provider semantics; replace every Docker command/tunnel and route by domain/SandboxRef. | Scoped session input/control, snapshot/events/usage, unavailable state/cancellation; no account-global leakage. |
| Capsule app/session/protocol modules | Reuse protocol/types/parsing and agent configuration where compatible. Remove PID1/root-wrapper assumptions from selected Candidate B path. Keep generic child ownership utilities; do not keep an agent-UID helper as trusted control. | Two agent domains + shell, operator take/release/focus/observe, child/grandchild ownership, host frames and real agent task. |
| `jackin-instance-agents`, account identity/admission/credential modules | Retain authorization, agent-specific config and revision decisions; replace publication/storage/transport and prove atomic visibility. | API key/profile/OAuth/GitHub/custom URL/model/effort, interrupted publication, revision/reconnect, refresh/expiry where supported. |
| `jackin-exec`/MCP/approval route | Retain binding/operator policy; replace Linux PID1/peer assumptions with a proved authenticated domain-origin route and isolated approved consumer. | Approval/denial/cancel/timeout/revocation/wrong-domain/no resolver; only approved consumer gets secret; masking is not containment. |

Current host protocol frames and desktop decisions remain product contracts. Clipboard/export/open/reveal must use authenticated origin and correct initiating desktop; raw PTY text cannot be interpreted as an authorized control message. No production multiplexer or credential broker is implemented in this research.

## Phase 5 — Replace optional engine and verification execution

- Remove `jackin-runtime-launch-dind` and `jackin-runtime-cleanup-dind-gc` as the old runtime sidecar manager after the managed OpenShell-compatible capability exists. Retain only reviewed generic parsing, readiness or certificate utilities behind the new owner, not the old role-container assumptions.
- Engine/domain attachment is explicit and absent by default. Record engine, CA, network, port, persistent-data and child ownership. Strong VM profiles must contain the claimed children inside the VM boundary; external container DinD does not meet that claim.
- In `jackin-workflow/src/verify.rs` retain frozen policy, candidate/bundle verification and result recording; replace Docker image ensure/run/wait/inspect/remove execution with the one-use OpenShell worker. Remove all host/direct-Docker fallback routes. Preserve the exact approved image/argv and bounded output/time/scratch/resources.
- Keep workflow service/event/review/repair semantics and `VerificationBinding` authoritative outside workers. A process exit, infrastructure timeout and uncertain cleanup are distinct results.

## Phase 6 — Replace management, recovery and fleet dependencies

Port `jackin-runtime-discovery`, launch slot/load cleanup/restore/account-identity helpers, cleanup absent/resolve/eject/prune guards, exit diagnosis and finalizers to the receipt/state model. Remove uncalled Docker-only slot/capture/readback foundations rather than carrying them as purported active guarantees. Preserve active metadata checkpoint/work preservation decisions.

Port `crates/apps/jackin/src/{app.rs,preflight.rs,cli/status.rs,cli/doctor.rs,cli/usage.rs,console/services/instances.rs,console/workflows.rs}` and the detailed inventory's remaining callsites. Separate builder/gateway/engine/host health. Keep meaningful local status when GitHub is unavailable. Extend the existing trusted host daemon/product state rather than creating a scheduler or generic controller.

Add explicit retain/stop/delete/recreate/purge transitions for every domain of a logical instance. Scope batch exile/prune to registered authorized targets. Preserve unavailable targets and uncertain effects. Test gateway restart, stale events, partial launch, simultaneous first/last entry, mount drift, keep-awake and desktop terminal restoration.

## Phase 7 — Remove obsolete backend paths and update packaging

Deletion is by resolved consumer, not crate name:

- Delete Docker role-container run/exec/attach/status/snapshot/usage/finalize/version-probe/verification execution code after its gate passes.
- Delete Apple CLI adapter/backend selection, image launch/attach/stop and incomplete finalize code; unused `remove/remove_with` is not an active user promise.
- Delete old Docker/Apple resource manifest variants and legacy import/default-backend fallback after fresh setup is documented.
- Delete old DinD role-container discovery/adoption/GC only after managed capability ownership is ready.
- Remove Bollard/DockerApi dependencies from production agent execution consumers; retain/rehome only the narrow builder or explicitly justified infrastructure operations.
- Keep generic process/reaping/command/Git/hash/parsing/product modules. Update packaging, operational scripts, build guards, CI and test fixtures so they no longer accidentally exercise a removed backend.

Run a final `rg`/callsite audit against the original inventories. Every retained direct Docker call must have one allowed owner: builder, explicit capability or OpenShell infrastructure. No hidden old backend remains behind a helper.

## Full release acceptance suite

The future rewritten product must pass **all** WF01–WF30 cases in [USER_WORKFLOW_CONTRACT.md](USER_WORKFLOW_CONTRACT.md), plus:

1. One coherent combined actual-role/two-account/shell/private/shared-storage/authenticated-code-task/credential-operation/session/recovery/failed-launch/cleanup journey per required target mechanism.
2. Every distinct supported installer, role admission, startup and authentication route; do not infer support from enum/setup entries or version output.
3. Stable request-ID retry, identity/generation guards, authorized absence before purge, pagination/incomplete inventory, version mismatch, certificate/token failure/renewal and output/backpressure bounds.
4. Default-off Docker plus managed engine lifecycle, online build/pull/registry auth, concurrent Compose/Testcontainers, two edits at same path, callbacks/ports/collision/exhaustion/reuse and cross-instance denial.
5. Frozen no-network/no-credential verification worker success/failure/timeout/abnormal exit/interrupted control, exact policy/result binding, process-group cleanup and negative resource/filesystem tests.
6. Local OrbStack and Docker Desktop separately, local Linux, VM sizes/mount limits/confinement, remote Linux/macOS image/storage/auth, Kubernetes storage/NetworkPolicy/image credentials and outage while another target remains usable.
7. Dirty/unpushed/uncertain work preservation, new-format state recreation, VM orderly/interrupted shutdown/flush outcomes, explicit purge guards and owned cleanup with unrelated resources protected.
8. Source/authority/storage/cleanup review and independent fresh combined replay, plus honest one/two-instance cost and cache measurements.

This research has not implemented the rewritten product and does not claim that product passed this release suite.
