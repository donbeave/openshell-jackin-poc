# Readiness decision

**NOT READY TO START THE FULL OPENSHELL REFACTOR**

The research gate fails. Released OpenShell 0.1.5 supplies useful sandbox, terminal and authenticated local control primitives, but the full replacement has required failed and unproved capabilities. No Jackin refactor was made. No Docker or Apple execution fallback is proposed. “Ready for a focused prototype” is not the result of this work.

This report is the full-replacement assessment. Original archived reports remain historical evidence with their narrower conclusions; this report does not convert them into parity proofs.

## Deliverables

| Deliverable | Artifact | Qualification |
|---|---|---|
| Runtime source inventory | [Source inventory](audits/SOURCE_INVENTORY.md), [per-site JSON](audits/source-inventory.json), [independent audits](audits/INDEPENDENT_AUDITS.md) | Static coverage independently passed: 207 canonical direct records, 10 cross-cutting records, 19 infrastructure records, one separate incomplete Apple-finalize behavior, and 1,266 reconciled broad matches. This is not runtime qualification. |
| User workflow contract | [Workflow contract](WORKFLOW_CONTRACT.md) | Source-traced current behavior, inactive foundations, new target requirements and public command changes; current-pin full live baseline not run |
| Responsibility map/interfaces | [Architecture](ARCHITECTURE.md) | Owner/identity/target/domain/storage/transport/image/lifecycle records and subsystem actions |
| Architecture decisions | [Architecture](ARCHITECTURE.md) | Candidate A current root mechanism fails; Candidate B proposed, authority/session/managed capability gates unproved; not an accepted complete execution design |
| POCs/raw evidence | [POC results](POC_RESULTS.md), `experiments/`, `evidence/` | Fresh isolated experiments; exact pins, failures/deviations, scoped cleanup; earlier 579-file archive integrity checked |
| Target matrix | [Required targets](TARGET_MATRIX.md) | Missing required desktops/remote/Kubernetes remain in scope and blocked |
| Refactor sequence/deletion/retained Docker ledger | [Refactor plan](REFACTOR_PLAN.md) | Twelve implementation stages gated behind research closure; 43 future release acceptance cases, not product test passes |
| Version compatibility | [Versions/evidence analysis](VERSIONS_AND_EVIDENCE.md) | Current main/releases and relevant 49 OpenShell commits reviewed; stable and main results not mixed |

## Decisive new execution findings

1. OpenShell rejects root workload UID/GID. Current Capsule's trusted per-account UID-switching mechanism requires root before dropping identity. This Candidate A path is incompatible under the tested released settings. Exact current-pin Capsule binary/transport was not executed; no broader impossibility claim is made.
2. The actual Architect Claude plugin layer fails at a declared Tailrocks marketplace because `.claude-plugin/marketplace.json` is absent. A reduced role is a workaround, not the required actual role image.
3. A checksum-verified selected Claude 2.1.309 input passed through the current native installer block but build output reports 2.1.310. Selected-version installation needs correction/proof. Metadata-less exact-version fallback remains unproved.
4. Local verified-mTLS CLI exec preserves literal arguments, independent stdout/stderr/status and binary stdin including NUL. It does not establish the proposed generated Rust RPC path, remote authentication, stable request replay, protocol mismatch or bounded streams.
5. Same-name replacement changes UUID/generation, yet a stale name-based stop acts on the replacement. A client identity read is not an atomic mutation guard. Never-reused canonical names under trusted namespace ownership are proposed, not yet proved as a complete strategy.
6. The existing verification timeout wrapper gets `PermissionError` from `os.killpg`; its child survives. CLI timeout also leaves remote work running. Deleting the entire sandbox removes compute but does not return worker process exit status, so it does not satisfy the full termination/result contract.
7. The worker fixture used explicit binds with resource admission disabled and had `ReadonlyRootfs=false`; Landlock denied a tested otherwise writable path. These are separate findings, not proof of the intended admitted-storage and literal RO-root design. Actual resource overrun, complete scratch semantics and immutable candidate/check result binding remain unqualified.

Raw findings and experiment boundaries are linked in [POC results](POC_RESULTS.md). Historical direct-Docker role hook/version diagnostics were caught by independent review, excluded from runtime evidence and disabled for replay. No pass is based on them.

## Blocking items

Every item below includes the workflow, failed/missing assumption, evidence, proposed solution and smallest next proof. A source proposal or unavailable environment is not a pass.

### B01 — Capsule/session architecture

- Workflow: multiple agent/account sessions plus generic shell, input ownership, persistent attach/reconnect and host actions.
- Missing capability: Candidate A's root UID-switching path fails supported OpenShell policy. Candidate B has no proved trusted host authority/session interface across the required domains.
- Evidence: `evidence/capsule/a-root-policy.json`, `RESULTS.md`; pinned Capsule isolation source; only two independent Alpine filesystems and one generic PTY were exercised.
- Proposed solution: complete Candidate B with trusted admission/operator/usage decisions outside workloads, account and shell sandboxes separate, same-UID helper limited to untrusted session I/O; reuse protocol/UI/authorization logic.
- Smallest remaining experiment: two admitted agent account domains and separate shell, real supported agent sessions; start/bytes/resize/signal/exit/list/disconnect/reconnect; control arbitration, child/grandchild/reaper failures and current host-frame replay. No production multiplexer should be built to hide the uncertainty.

### B02 — Actual role and selected agent installation

- Workflow: build selected role and agent version at launch, with tools/plugins/hooks working.
- Failed assumption: full Architect plugin installation succeeds and native artifact selection fixes the installed version.
- Evidence: `evidence/role/full-recipe-marketplace-failure.log`, `build-2.1.309.log`, `external-source-pins.json`; full failing generated Dockerfile and hash retained.
- Proposed solution: correct/pin role marketplace inputs or publish valid marketplace metadata; use an exact-version installation path with digest-bound metadata. Preserve actual tools/hooks.
- Smallest remaining experiment: rebuild the full unchanged-outcome role with corrected pinned dependencies, assert selected 2.1.309 then 2.1.310 during build and through OpenShell, test no-prefetched-metadata path, cold/reuse/forced/content matrix and explicit role bootstrap. No reduced-role pass substitutes.

### B03 — Accounts, credentials and usable authenticated coding

- Workflow: account selection, permission/revision admission, agent-specific auth/history/plugins/model configuration, scoped usage, approved credential MCP operation.
- Missing capability: no real authenticated two-account/domain run or credential publication/approval/refresh/usage channel proof. Current revocation is admission/reconnect enforcement, not immediate termination.
- Evidence: source traces in workflow contract; original `results/agent-auth-availability.json`; new POCs used no agent/model/GitHub credentials. Disposable test-account request is unanswered.
- Proposed solution: retain existing account authorization/staging logic with domain-bound authenticated host transport and per-domain private stores. Approved secret reaches only the approved consumer in its admitted account domain; disclosure by that consumer remains possible.
- Smallest remaining experiment: one real coding task, second admitted account and separate shell; interrupted config publication, wrong domain/workspace/revision/stale identity denials, usage unavailable/cancel, GitHub auth separate, harmless-secret approval/denial/cancel/timeout/revocation and intended MCP response.

### B04 — Production Rust control and resource identity

- Workflow: every launch, attach, status and lifecycle operation across targets.
- Failed/missing assumption: Rust CLI primitives equal complete Rust control route; name-based actions are identity safe; CLI cancellation/output/retry surface meets product needs.
- Evidence: `evidence/control/{exec-roundtrip,identity-lifecycle,exec-cancellation,output-bound,tls-authentication}.json`. Stale stop affects replacement; remote work survives CLI timeout; output uncapped. Stable SDK has no mTLS client identity; main has a source-only change.
- Proposed solution: generated pinned RPC clients/custom verified tonic channel (or a newly justified route after equivalent tests). Unique never-reused canonical names with persisted intent/stable IDs and sole trusted allocator; require server-side UUID preconditions if independent actors can reuse names.
- Smallest remaining experiment: real Rust local/remote mTLS positive/failure/renewal, complete pagination, stable request replay after lost response, protocol mismatch, bounded slow streams/cancel, same-name adversarial race under the selected authority strategy, authorized async deletion completion. Generic NOT_FOUND never authorizes retained-data purge.

### B05 — Local/VM project/private storage and persistence

- Workflow: Shared/Worktree/Clone, host editing/watch, retained work and ordinary recreation.
- Missing capability: actual role mount layout, private-store separation, file/Git/path semantics and durable recovery under the chosen target mechanism.
- Evidence: prior successful shared Docker volume was agent-to-daemon, not live host checkout; current worker uses direct binds with admission disabled; prior VM upload/compile/stop-start is narrow. VM mount budget and size semantics source-only beyond that slice.
- Proposed solution: admitted canonical project storage plus per-domain private stores; VM directory layout respects three x86_64/32 ARM64 mounts and gateway size classes; explicit committed publication/flush outcome.
- Smallest remaining experiment: actual host checkout in all three modes with bidirectional watch/RO/Git links/permissions/spaces/symlinks/concurrency, multiple mounts, stop/start and recreate retained data; orderly/interrupted VM shutdown and flush failure. Preserve data under unknown dirty/unpushed/session state.

### B06 — Optional managed Docker and normal compiled development

- Workflow: optional Docker/Buildx/Compose/Testcontainers in selected sandboxes; Docker absent by default; repeated ordinary Cargo/nextest edits.
- Failed/missing assumption: released OpenShell-compatible managed daemon/companion ownership exists and supports the complete concurrent workflow; changed executable network identity remains usable after rebuild.
- Evidence: prior rootless startup fails iptables; external mTLS engine passes selected Docker operations but survives sandbox deletion, children lack agent policy and killed tests leave children. Native same-path network integrity denial remains reproduced. Issue #113 is proposal/history, not released proof.
- Proposed solution: select and prove an owned OpenShell-compatible engine per authorized domain; separate agent/engine/child network/resource boundaries and receipts. An upstream change may be needed; no pinned patch exists. Do not retain old DinD manager as an unnamed workaround or disable integrity enforcement.
- Smallest remaining experiment/change: demonstrate one released in-compute/managed-companion mechanism or pinned small upstream patch with owned cleanup; two concurrent instances using the same unmodified Testcontainers project, repeated same-path rebuild/data exchange, online pulls/ports/path mapping and cross-domain engine denial; disabled-domain positive-control denial. If managed ownership requires a controller-sized extension, retain blocker.

### B07 — Verification worker bounded termination and isolation

- Workflow: independent trusted workflow verification and recorded result.
- Failed/missing assumption: current timeout wrapper can terminate its whole process group, and an equivalent full worker isolation/exit contract is available.
- Evidence: `evidence/verification/timeout-process-group.json`, `timeout-delete-worker.json`; `ReadonlyRootfs=false`, admitted-storage deviation and untested resource overrun; fixture hashes do not prove Git commit/tree/check-policy binding.
- Proposed solution: tested OpenShell-owned worker termination with observed terminal process state, or safe ownership-aware upstream signal operation. Keep policy/results trusted; credential-free pinned worker; no Docker/host execution fallback.
- Smallest remaining experiment/change: immutable candidate snapshot/check bundle bound to commit/tree/policy/image, success/failure/timeout/abnormal/unavailable/interrupted-control cases; prove group/grandchild kill and actual exit, no network, RO root/source/checks, bounded CPU/memory/PIDs/tmp/noexec/nosuid/output/deadline and complete cleanup. A blanket negative-PID allow rule is not an acceptable unreviewed patch.

### B08 — Image delivery and safe cache ownership

- Workflow: launch/reconnect/recreate on local, remote, VM and Kubernetes targets; safe image prune.
- Missing capability: full-role exact digest delivery/auth/platform/interrupted transfer and per-target retention are proved.
- Evidence: prior same-engine presence and limited VM import; new role-image ID attempt fails IdentityResolutionFailed; remote/private registry transfer untested. Older upstream issue #2676 reports authenticated pull failure but is not a stable-version execution result. One unused own workaround tag was safely removed; that is not global target-image prune proof.
- Proposed solution: digest/platform-bound builder output and authenticated delivery receipt per target, image cache ownership separate, active/retained references protect recreation. Use a qualified registry/preload route rather than assume Docker login propagates.
- Smallest remaining experiment: push/pull full image to a different authorized machine and Kubernetes, invalid credential/missing architecture/image/interrupted transfer; reconnect/recreate with registry unavailable as required; prune unused while preserving active/retained digest.

### B09 — Required target and fleet coverage

- Workflow: one useful view of instances across local container/VM, remote Linux/macOS and Kubernetes; correct desktop host actions.
- Missing capability: required environments/authenticated endpoints and selected remote storage/synchronization model qualified.
- Evidence: `TARGET_MATRIX.md`; only OrbStack local runtime and old limited macOS VM slice have execution. No disposable remote endpoints/cluster or alternate desktop hosts supplied.
- Proposed solution: independent target configs/credentials/inventories/state/ownership namespaces; VM size-class gateways; remote target-side replicas with explicit synchronization/conflict/export; Kubernetes qualified CNI/storage/controller/auth.
- Smallest remaining experiment: representative rows on every required target, image delivery between machines, remote Shared synchronization or explicit unresolved workflow change, callbacks/desktop routing, enforced Kubernetes NetworkPolicy/PVC/image auth and one-target outage while another remains usable. Do not remove rows to obtain readiness.

### B10 — Lifecycle, preservation, management and profile enforcement

- Workflow: hardline/eject/exile/purge/prune/prewarm, status/doctor, first-entry/last-exit/keep-awake and safe retained work.
- Missing capability: new state machine/ownership receipts survive meaningful transition failures, and every requested profile restriction is effectively enforced.
- Evidence: static production Docker/Apple and hold guards; live name-race failure; limited scoped cleanup. Normal hold creation/checkpoint capture and grant readback remain foundations without production callers found. No complete launch fault matrix or builder-down management test.
- Proposed solution: trusted new-format lifecycle and scope-aware reconciliation; preserve unknown work; separate builder/gateway/engine health; explicit admission/limits per domain and aggregate policy without pretending reservation is hard runtime enforcement.
- Smallest remaining experiment: fail every effect boundary including gateway restart/partial creation/lost events, verify dirty/unpushed/failed-inspection preservation and holds, builder down with reachable target, prewarm single adoption/mount drift, first/last concurrency; allowed/denied network/filesystem/privilege/resource operations under each representative profile.

### B11 — Critical combined replay and costs

- Workflow: actual role, two real accounts, shell, coding/edit/build/test, credential/usage, persistent session I/O, disconnect/reconnect, retained recovery, failed-launch cleanup, optional Docker and independent worker together.
- Missing capability: those mechanisms work together under one configuration and repeat from fresh resources.
- Evidence: isolated POCs only; actual role/current Capsule/accounts/managed Docker/worker gates fail or remain unproved. No combined run exists. Historical measurements have n/cache limitations and cannot be summed into a domain architecture benchmark.
- Proposed solution: close B01–B10, then one ownership-receipt combined fixture using existing binaries/protocols; independent fresh replay, no production controller.
- Smallest remaining experiment: full combination and fresh replay on qualified target mechanisms, recording all requested latencies, CPU/memory/idle/domain/VM/engine/child/concurrency/stop/cleanup/disk/cache costs and current Jackin comparison where practical. Additional per-domain sandboxes/supervisors, VMs and engines are real cost categories; no unmeasured numerical estimate is claimed.

## Reviews, cleanup and limits

Source coverage and authority/storage/cleanup were reviewed by separate agents. Both first reviews failed. Final static source coverage passed after manual action/caller tracing, broad reconciliation and correction of classification/alias defects. Authority/storage/cleanup and full replacement readiness remain unpassed. Findings were preserved; action records, timeout identities, status taxonomy, role probe exclusion and cleanup scripts were corrected. Re-review outcomes and remaining blockers are in the audit record. No review is an approval to start a full refactor while required evidence remains absent.

Owned gateways used isolated state/certs/labels. Parent final read-only observations found no listeners on their four ports after replay and no containers/volumes in their exact namespaces (`evidence/final-scoped-observation-after-replay.json`). The control teardown initially inferred a stop and curl result without recording commands; those original claims are explicitly invalidated, and no earlier stopping actor is inferred from current absence. Trusted runtime/supervisor image digests were not captured by the control fixture and remain an evidence gap. Capsule and control/worker final inventories confirm owned compute removal; generated credentials/state removed. The role fixture removed one unused own workaround tag; the disk keeper subsequently removed three additional own consumer-free role-image tags. It also removed 584,827,248 bytes of downloaded installer payloads with manifests/URLs/hashes retained. Active/foreign consumers, shared caches and the separately named role base were preserved. Shared bases/caches and foreign workloads remain protected. Concurrent foreign inventory changes have no proved causal attribution to this research; no unrelated mutation was issued. Disk cleanup ran in parallel as requested, preserving active/user data and keeping the 2 TB hard gate clear.

The full replacement objective remains unchanged. Source-only decisions can preserve unchanged product logic, but new runtime/transport/storage/identity/credential/platform assumptions cannot pass without execution. Missing accounts or targets are blockers, and an unwritten product has not passed the release suite.
