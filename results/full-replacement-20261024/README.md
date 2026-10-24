# Full replacement follow-up evidence

The original evidence baseline is commit `2315e6a278231854b3139b1ca32402777ff3cd01`. Its files and results remain unchanged. Follow-up requirements were created in `FULL_REPLACEMENT_MATRIX.md` before new runtime execution. Source pins are frozen in `source-pins.json`; subsequent unrelated changes to the user's shared Jackin checkout are not selected revisions.

Start with the root `FULL_REPLACEMENT_MATRIX.md`, `TARGET_MATRIX.md`, `BLOCKERS.md`, `REPLACEMENT_ARCHITECTURE.md`, and `FOLLOWUP_DECISION.md` when the final decision is available. Source-only reports are `agents-source.md`, `workspace-source.md`, `control-source.md`, and `host-feature-map.md`. They do not constitute runtime PASS.

Execution groups have separate subdirectories: `control/`, `workspace/`, `docker/`, `role/`, `targets/`, `repeat/`, `repeat-control/`, and the separately labeled `patch-delete/` experiment. Exact commands, status and output live beside each group's reports. Some failed fixture attempts and interrupted commands are deliberately retained; a later successful test does not erase them.

Historical evidence is retained for comparison, not promoted to full-replacement coverage. In particular, old minimal images, Python SDK control, shell-only sessions, plain volume exchange and the loopback-only Docker workaround do not establish the new actual-role/account/session/workspace/development contract. No historical cleanup or collateral-restoration script is part of this follow-up procedure.

All agent sandboxes use OpenShell. Trusted host Docker operations create images and disposable infrastructure fixtures; those are distinct from an agent's optional Docker grant. Additional resources remain owned by the creating fixture, not by OpenShell unless execution demonstrates otherwise. Generated private keys, credential material, build outputs and runtime state are excluded from publication. Do not execute a fixture until its endpoint, namespace, source path, labels, and immutable resource manifest have been reviewed.

The result vocabulary is PASS, FAIL, BLOCKED and NOT TESTED. The mechanism vocabulary is RELEASED, CONFIGURATION, EXTERNAL FIXTURE, WORKAROUND, EXPERIMENTAL PATCH and RETAINED HOST LOGIC. “Conditional” in narrative describes dependencies; it is not a Result value. A source mapping of retained host logic is not a runtime PASS.
