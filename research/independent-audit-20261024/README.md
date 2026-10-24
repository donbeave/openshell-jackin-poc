> **Scope note:** this is the independently reviewed audit snapshot. Read the [merged research index](../../RESEARCH_INDEX.md) and [consolidated readiness report](../../READINESS_REPORT.md) for later execution proofs and the current overall decision. Earlier NOT TESTED entries remain accurate for this snapshot, not a claim that the later experiments never ran.

# Jackin full OpenShell replacement research

**NOT READY TO START THE FULL OPENSHELL REFACTOR**

Start with [the readiness report](READINESS_REPORT.md). It records failed capabilities, missing proof, proposed solutions and the smallest remaining experiments. This directory is additive research; Jackin product sources were not refactored. Original archive reports and failures remain unchanged.

| Artifact | Purpose |
|---|---|
| [Objective](OBJECTIVE.md) | Full requested scope and research gate |
| [Source inventory](audits/SOURCE_INVENTORY.md) / [JSON](audits/source-inventory.json) | Per-operation actions, callers, owners, changes, evidence and release tests; review coverage explicitly qualified |
| [Independent audits](audits/INDEPENDENT_AUDITS.md) | Four independent first audits plus separate source and authority/storage/cleanup review findings |
| [Workflow contract](WORKFLOW_CONTRACT.md) | Current source behavior, inactive foundations, new target requirements and proposed public changes |
| [Architecture candidate](ARCHITECTURE.md) | Full-scope responsibility map, records/interfaces and unresolved decisions |
| [POC results](POC_RESULTS.md) | Narrow passing primitives, preserved failures and all unproved required mechanisms |
| [Required targets](TARGET_MATRIX.md) | Required desktop/container/VM/remote/Kubernetes coverage; unavailable rows not dropped |
| [Refactor plan](REFACTOR_PLAN.md) | Implementation stages, removal/retained-Docker ledger and 43 future release cases |
| [Versions and evidence](VERSIONS_AND_EVIDENCE.md) | Source/release pins, compatibility analysis and prior evidence reuse limits |

New execution evidence is under `evidence/{capsule,role,control,verification}/`; scripts are under `experiments/`. Read each case's limitations before replay. Generated credentials and runtime state are removed, so reproduction creates fresh private test certificates. Do not execute historical role Docker probe logs or incident/restoration scripts from the original archive. The new disabled direct-Docker role probe is retained only as excluded diagnostic history.

The source clones under `sources/` are pinned research inputs. `evidence/binary-identities.json` identifies installed binaries; the installed host Jackin/Capsule is a different revision from the source baseline and is not current-pin runtime proof. The original 579-file archive passed content-integrity verification, which does not turn old primitive tests into product or new-platform evidence.

No authenticated coding-agent task, managed optional Docker solution, full verification worker, complete domain authority/session path, full required-target coverage, or critical combined replay passed. The future release suite is a plan for the unwritten product, not a claim of passing tests.

Artifact integrity/syntax results: `evidence/validation.json`. `RESEARCH_GATE.json` is the machine-readable negative assessment. `ARTIFACT_MANIFEST.json` hashes this new research bundle, excluding source clones, interpreter caches and the manifest itself; source commits remain pinned separately.
