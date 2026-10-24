# Current full-refactor research handoff

**Verdict: NOT READY TO START THE FULL OPENSHELL REFACTOR.**

Read in order:

1. [Readiness report](READINESS_REPORT.md).
2. [Source inventory](SOURCE_INVENTORY.md) and its four independent audits/call-level records.
3. [User workflow contract](USER_WORKFLOW_CONTRACT.md).
4. [Responsibility map](RESPONSIBILITY_MAP.md) and [architecture decisions](ARCHITECTURE_DECISIONS.md).
5. [POC result index](POC_RESULTS.md), [target matrix](TARGET_MATRIX.md), [blockers](BLOCKERS.md) and [measurements](MEASUREMENTS_FOLLOWUP.md).
6. [Detailed refactor and release plan](REFACTOR_PLAN.md).
7. `results/full-refactor-20261024/` and `results/full-replacement-20261024/` for raw evidence/reviews, with matching experiment directories.
8. [Final decision review](results/full-refactor-20261024/final-decision-review.md) and [cleanup index](FOLLOWUP_CLEANUP.md).
9. [Publication security review](results/full-refactor-20261024/security-publication-review.md), including manually classified scanner findings and the historical-script warning.

Current Jackin pin6e supersedes the earlier41bad source group only through the recorded compatibility analysis. Architect7b and released OpenShellbdb remain pinned; two experimental OpenShell patches are separate from released support. Fresh setup is allowed; legacy migration is excluded. No Jackin product code was refactored.

The original baseline commit2315e6 and its documents/results remain intact. Its earlier “focused prototype” conclusion is historical, not the verdict for this full-refactor task. Follow this handoff rather than using the old narrow verdict as full replacement approval.

Do not execute old cleanup/restoration scripts. Read each current reproduction's ownership receipts, fresh unique namespace/PKI/port/path requirements and cleanup limitations. Generated checkouts, binaries, credentials, VM disks and build caches are not publication artifacts; source pins, patches, hashes and procedures reproduce them. Private raw local evidence is preserved separately from any public sanitization.
