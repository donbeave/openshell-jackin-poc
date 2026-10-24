# Independent final decision review

Reviewed the final research documents and their source/control/role/storage/worker evidence on 2026-10-24. This review performs no product changes or independent runtime rerun. Source pins are Jackin `6e266406b49da2ab3c55355f3b7d33d1643ee6cd`, Architect `7b72b38fe1d66e35c0931899c53bf3719592bbcc`, and released OpenShell v0.1.5 `bdb956f2cd65a635f1294fccf1d138d263bf650f`. The separate immutable-delete patch review applies only to final experimental commit `95a1e7fe2bfc731ec21096dea0758fa7fc90a8db`.

## Decision

**NOT READY TO START THE FULL OPENSHELL REFACTOR** is supported by the evidence. This is the required full-replacement decision, not approval for a reduced prototype. Required managed Docker ownership, account/session/credential boundaries, normal edited network-test execution, verification-worker isolation, identity/generation-safe operations and required target journeys remain unresolved. Any one of these is sufficient to prevent READY.

The documents select one coherent candidate architecture: trusted host product/authorization logic, separate OpenShell authority domains, explicitly authorized project sharing, separate private persistence, Docker image construction, a required managed companion capability, and separate OpenShell verification workers. Proposed components are clearly distinguished from executed support. The design does not retain the old Docker or Apple agent execution backend as fallback.

## Corrections requested

**Final disposition: the three factual corrections below are closed in the revised documents.** The historical findings remain to explain what was checked. `POC_RESULTS.md` and AD08 now record narrow tmpfs PASS at commit `68cfa648538a497acd4af2cf48424eda9834ba0f` with exported diff SHA256 `ff61fbd50e03e44d518dca339221cae9012f4eee4d8b24161ec320dfc4176a00`. They explicitly disclose that the historical executed gateway binary hash was not captured before cache garbage collection; a later rebuild is not substituted. The checked-out patch commit matches that pin. The worker cleanup report now distinguishes name-addressed deletion with identity checks from an atomic ID guard. `TARGET_MATRIX.md` separates Docker client 29.9.2 from engine 29.8.2.

1. **Medium — worker cleanup wording overstates the mutation guard.** `verification-worker/patch-tmpfs/result.md` says workers were “deleted with immutable IDs.” However, `experiments/full-refactor-20261024/verification-worker/patch-tmpfs/client/src/verification.rs:254` reads the name, compares its ID, then sends the released name-addressed `DeleteSandboxRequest` at line 274. Comparing the acknowledgement and checking subsequent inventory confirms the observed deleted identity; it is not an atomic immutable-ID precondition. Qualify this as disposable, sole-authority, unique-name cleanup with identity confirmation. Do not imply the separate Delete-only patch was present in the tmpfs gateway. The full design already correctly treats name-based mutation as unsafe under concurrent replacement.

2. **Low — narrow tmpfs patch result is stale in the summary.** `POC_RESULTS.md` marks the tmpfs serialization patch NOT TESTED, whereas `verification-worker/patch-tmpfs/result.md` records built/executed patched sandboxes, focused driver tests, noexec/size enforcement and admission/protected-target negatives as a narrow PASS. `ARCHITECTURE_DECISIONS.md` AD08 also calls it under test. Record narrow PASS / Experimental OpenShell patch with exact artifacts, while retaining the complete worker FAIL and any unfinished export/cleanup status separately. Successful option translation does not establish worker confinement.

3. **Low — local Docker engine version is inconsistent.** `TARGET_MATRIX.md` lists OrbStack engine 29.9.2. The recorded `results/full-replacement-20261024/environment.json` Docker version command reports Client 29.9.2 and Server 29.8.2. Use the server version applicable to each run, or explicitly document a subsequent engine change and its execution evidence. A client version must not be labeled the engine version.

These corrections do not change the NOT READY verdict. They matter because subsequent implementers must know which safety guarantees and version-specific results they can reuse.

## Scope and source coverage

The earlier independent source review closed its concrete findings after the inventory expanded to 137 operation rows and corrected callers, resource ownership, inactive foundations and released API assumptions. Its detailed history remains in `source-coverage-review.md`. In particular, the final plan explicitly covers the independent workflow verification worker, the `docker run` agent-version probe, direct status/session/snapshot/usage/diagnostic/finalization execution, image-consumer pruning and Docker management preflight. Builder/optional-engine/infrastructure operations remain separate from agent execution. Uncalled checkpoint capture, grant readback and Apple removal wrappers are not invented active guarantees. Six entrypoint cases are distinguished from twelve setup/adapter branches.

The reset allowance is applied correctly: no legacy importer or compatibility format is required, while new-design persistence/recovery is still mandatory. Windows and general collaboration remain visible future scope. Missing required desktops, native/remote hosts and Kubernetes remain blockers rather than being removed from the target matrix.

## Authority, storage and cleanup assessment

Candidate B's canonical PTY and deterministic-process results establish primitives, not the complete Capsule replacement. Account admission, private persistence, operator control, host protocol authorization, credential consumers, authenticated coding and their combined journey remain explicitly unproved. Treating an agent-UID helper as untrusted is correct. No unauthenticated terminal text is promoted to trusted desktop or credential authority.

Local admitted bind-backed volume results do not establish VM virtiofs confinement, remote live sharing or Kubernetes storage. The selected storage owner and additional path authorization are disclosed, with concurrency and lifecycle work unresolved. Remote checkout authority and explicit synchronization are distinguished from local live sharing.

External Docker connectivity is not reported as OpenShell-managed ownership. Engines and children survive until fixture cleanup; that is external ownership. Managed companion provision/adoption/recovery remains a required upstream dependency, and children are not claimed to inherit agent policy or an unrelated VM boundary.

The strict worker is correctly failed: P14 changes the mode of an out-of-grant UID-owned inode despite content-write denials. A narrowed content-write test cannot establish metadata immutability. OOM enforcement does not establish stable result/lifetime semantics. The tmpfs patch and Delete-only patch must stay separate until their combination is actually built and executed.

The immutable Delete patch's final static/log review is narrow: stable UUID replay, explicit workspace authorization, target fingerprint mismatch, same-name replacement survival and old-server fail-closed behavior were checked. It does not establish generation-bound Exec/Stop/Start or safe delayed session input. The final design correctly keeps those as blockers.

## Research and implementation gates

The refactor plan names retained product logic, new interfaces, replaced transports/storage/identity, removed backends and justified direct Docker operations. It gives release acceptance cases without claiming the unwritten product has passed them. The full combined role/two-account/shell/credential/session/storage/development/recovery journey has not run, and no independent repeat of that full journey is counted. Missing measurements and credentials remain unavailable rather than estimated as successful readiness.

The reviewed factual corrections are closed. No additional actionable overclaim was found in the revised final decision documents. Full-refactor readiness still requires the blocker experiments and upstream operations in `BLOCKERS.md`; no source audit, configuration value, proposed interface or successful isolated workaround substitutes for their required live evidence. This closes the independent decision review in support of NOT READY, not the unresolved readiness blockers.
