# Full OpenShell refactor readiness

**NOT READY TO START THE FULL OPENSHELL REFACTOR**

The complete source inventory, selected candidate architecture and detailed refactor/release plan are provided. The required research gate does not pass: changed session/account/credential assumptions, managed Docker ownership, strict verification-worker isolation, identity/generation safety, normal edited-network-binary development and required target coverage remain unresolved. No Jackin refactor was implemented.

## Scope and versions

- Jackin: `6e266406b49da2ab3c55355f3b7d33d1643ee6cd`; Architect: `7b72b38fe1d66e35c0931899c53bf3719592bbcc`.
- Original research baseline: `2315e6a278231854b3139b1ca32402777ff3cd01`; its original files/results remain unchanged.
- Executed stable OpenShell: v0.1.5, `bdb956f2cd65a635f1294fccf1d138d263bf650f`.
- Current source/release queries, observed main49-commit comparison, experiment pins and compatibility analysis are in `results/full-refactor-20261024/`. Main is not an executed result.
- Fresh setup is allowed. No legacy state/configuration migration is designed. New-design persistence/recovery remains mandatory. No unrelated reset or deletion is authorized.

The selected design uses OpenShell for agent and verification-worker execution. Docker remains the launch-time builder and an explicit optional capability. No old Docker/Apple execution fallback is retained in the plan. Source audit also found the independent Docker workflow worker, version probe, snapshots/session/usage/finalization/diagnostic paths and image consumer pruning; these are not hidden exceptions.

## Findings that determine the decision

1. **Current Capsule cannot supply its unchanged isolation path under supported released workload identity.** The actual6e Linux binary returns `capsule isolation wrapper must start as root`; policy rejects UID/GID0. Candidate B's separate sandboxes reconnect to the same canonical PTY and preserve independent deterministic processes, but full operator control, private persistent account state, protocol/host actions and authenticated agent/credential operations are unproved.
2. **Normal edited native network tests fail.** Real Testcontainers initially exchanged Redis data. Two rebuilt hashes at the same executable path were denied with `transparent_tcp_identity_unavailable`. The ordinary mise path also exposed incomplete tool preparation. No complete normal-command alternative was demonstrated; the earlier Docker loopback example is not substituted.
3. **External Docker works; managed ownership does not follow.** Dedicated-engine mTLS, online pull/build, Compose, logs/exec/stream, real host child binds and initial Testcontainers work. Engines survive sandbox deletion until fixture cleanup. No managed companion lifecycle was demonstrated; rootless startup did not establish it. Current requirements explicitly need a managed OpenShell-compatible owner, not the old DinD manager or an external fixture renamed as native support.
4. **Verification isolation is not equivalent yet.** A narrow tmpfs serialization patch allowed required sizes/noexec/nosuid through the Docker API. Worker primitives then ran, but default policy allowed an outside scratch write. Refined Landlock policy denied content writes while still allowing chmod of an out-of-grant UID-owned inode. That actual counterexample defeats the proposed read-only-root equivalence. OOM was enforced but outcomes/sandbox survival varied; unknown infrastructure outcome must not become a test pass.
5. **Resource identity needs more upstream support.** Released delayed Stop/Delete requests affected same-name replacements. The final Delete-only experimental patch95a1e7fe is built, runtime-tested and independently reviewed: stable request-ID replay and scope/fingerprint checks pass; old servers reject the new request safely. It does not fix Stop/Start/Exec or establish all generation-bound session actions.
6. **Image/role findings require separate product work.** Four real Architect agent paths ran preflight/version in OpenShell with explicit group/PATH/seed adaptations. Claude's required marketplace input and Codex's fallback installer fail independently of OpenShell. A fresh actual Amp request reused a Grok image with Amp absent, demonstrating selected-agent cache mismatch. Manual tag removal is not the final workflow.
7. **Required accounts and targets are missing.** No approved disposable live model-account fixtures were supplied. Docker Desktop, required native Linux/remote macOS/Linux and Kubernetes full journeys lack environments/evidence; Linux guest and packaged VM slices do not qualify them. VM host sharing failed with admission preserved, and confinement/role layout/size/shutdown behavior remains incomplete.

## What execution does establish

The public Rust SDK plus a caller-built verified Tonic channel supplies typed local and Linux-guest control, separate argv/output/exit, binary duplex, PTY resize/interrupt and duplicate prevention. Canonical-main-process attachment supplies a real same-PID reconnect primitive. Two gateways with duplicate names were attributed correctly, and an unreachable target stayed unavailable rather than deleted.

Administrator-prepared approved bind-backed volumes supply live local host edits, selected Shared/Clone/Worktree Git operations and retained bytes while admission remains enabled. Wrong-workspace/RO negatives and a fresh independent repeat passed. These are storage primitives with a trusted path/volume owner, not a complete materializer/private-domain lifecycle or VM confinement proof.

Actual full Architect-derived OpenCode, Amp, Kimi and Grok installation/hook/version slices passed after disclosed adaptations. They are not authenticated coding tasks. Measured component costs and limitations are in [MEASUREMENTS_FOLLOWUP.md](MEASUREMENTS_FOLLOWUP.md); command completion is not usable-agent readiness.

## Architecture and implementation plan

Select Candidate B: trusted host product/control/authorization, separate OpenShell session/account and shell sandboxes, explicitly authorized project sharing and separate private persistent state. Select a per-granted-domain managed companion owner for optional Docker; it is a required upstream dependency, not a demonstrated component. Use verified Rust control and immutable/generation-bound operations. Verification workers are separate no-account/no-network OpenShell sandboxes with trusted host policy/result ownership.

Detailed decisions/interfaces/resource owners: [ARCHITECTURE_DECISIONS.md](ARCHITECTURE_DECISIONS.md), [RESPONSIBILITY_MAP.md](RESPONSIBILITY_MAP.md). Exact crate/module replacement/deletion sequence and release gates: [REFACTOR_PLAN.md](REFACTOR_PLAN.md). This plan does not imply that an unwritten product passed its acceptance suite.

## Blockers and next work

[BLOCKERS.md](BLOCKERS.md) gives each affected workflow, failed assumption/missing proof, evidence, owner, proposed solution and smallest remaining experiment/change. [TARGET_MATRIX.md](TARGET_MATRIX.md) keeps every required environment visible. [USER_WORKFLOW_CONTRACT.md](USER_WORKFLOW_CONTRACT.md) defines WF01–WF30 and the explicit public command/JSON decisions.

The next decisive sequence is: qualify the missing identity/session/credential and managed-companion interfaces; provide approved test accounts/targets; prove the strict worker and normal edited-test solution; then run the actual combined two-account/shell/role/project/authenticated task/credential/session/recovery/teardown journey and independently replay it for every required target mechanism. No controller, scheduler, production broker or replacement Capsule is implemented to bypass those gates.

## Independent review and evidence limits

- Source coverage review closed the identified findings after correcting mixed resource owners, multiline/helper calls and inactive foundations. Its hashes and exact source references are retained.
- Authority/storage/cleanup review still finds the full architecture unproved; the worker addendum confirms that policy text and a single denial do not establish confinement equivalence.
- The Delete-only patch received a separate narrow code/log review after earlier versions failed replay/scope/cleanup review. The reviewer did not independently rerun it.
- Storage and Rust transport/lifecycle primitives were independently repeated from fresh state. The full combined journey was not, and is not counted as passed.
- The final cross-area decision review, [final-decision-review.md](results/full-refactor-20261024/final-decision-review.md), supports this NOT READY verdict after factual corrections. It is a source/evidence review, not an independent runtime rerun.
- Missing credentials, protocols, platforms, dimensions and measurements remain BLOCKED or NOT TESTED. Existing failures, overwritten-raw evidence limitation, fixture mistakes and procedural deviations remain disclosed in [POC_RESULTS.md](POC_RESULTS.md).

This is a readiness decision for the complete refactor. It does not claim production readiness or substitute a narrower readiness verdict.

## Merged independent audit

The [independent audit bundle](research/independent-audit-20261024/README.md) and its 207-record source inventory are now included alongside this later execution follow-up. Its workload-side process-group timeout and CLI cancellation negative cases remain valid for their recorded configuration. Its inconclusive PTY replay and earlier untested Rust/storage statements do not erase this report's later successful primitives. Conversely, the later primitives do not establish the complete domain/account/credential journey or erase a failed native operation. [RESEARCH_INDEX.md](RESEARCH_INDEX.md) records the comparison, patch boundaries and publication provenance. The full-replacement verdict remains NOT READY.
