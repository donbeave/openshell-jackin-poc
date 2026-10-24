# Proof-of-concept result index

Results below are scoped to the stated capability, version and configuration. Full workflow coverage is tracked separately in `BLOCKERS.md`, `TARGET_MATRIX.md` and `READINESS_REPORT.md`. Original failures and failed fixture attempts remain. A restricted operation being denied does not make the affected integration capability pass.

Selected sources: current Jackin6e, Architect7b, released OpenShellbdb/v0.1.5. The two experimental patches have separate source/binary pins in their run records. Reuse from the earlier41bad group is qualified in `results/full-refactor-20261024/compatibility.md`.

| Capability / requirement | Result | Mechanism | Observed evidence and remaining limit |
|---|---|---|---|
| Rust verified local mTLS and authenticated API | PASS | Released OpenShell feature | Public SDK `from_parts` + verified Tonic channel; CA/hostname/client-chain negatives. A distinct CA-issued identity is valid, not a bad certificate. `control/control-run.md`; independent `repeat-control/`. |
| Rust create/get/list/start/stop/delete primitives | PASS | Released OpenShell feature | Typed calls preserve inspected ID for ordinary lifecycle. This is not stale-target safety. |
| Literal argv, separate stdout/stderr/exit | PASS | Released OpenShell feature | Spaces/quotes/metacharacters remained literal, exit23 and separate byte streams. |
| Non-TTY duplex | PASS | Released OpenShell feature | Corrected1MiB shell fixture, split NUL input,500ms receiver pause, EOF and exact output hash. Original external-dd fixture failure retained. |
| PTY input/resize/interrupt | PASS | Released OpenShell feature |24x80→37x101 and Ctrl-C/exit130. New exec reconnect was correctly distinguished from same-process attachment. |
| Canonical main-process reconnect | PASS | Released OpenShell feature | Candidate B fixture reattached to same PID; separate A/B/shell processes; old stream failed after restart/generation change. Not full Capsule/operator-control/account proof. |
| Request-ID create/exec duplicate prevention | PASS | Released OpenShell feature | Same create request yielded one resource; create acknowledgement was discarded locally, not a dropped network packet. Exec stream loss + same request never relaunched marker command. Actual lost-create response remains untested. |
| Same-name stale Stop/Delete | FAIL | Released OpenShell feature | Exact old request bytes captured before deletion affected the replacement. Independently repeated Stop failure. |
| Immutable-ID Delete extension | PASS | Experimental OpenShell patch | Final commit `95a1e7fe2bfc731ec21096dea0758fa7fc90a8db`: stable-UUID receipt replay after delete/name reuse, changed-target fingerprint rejection, scope checks and old-server safe rejection. Independent code/log review closed; not independently rerun. No Stop/Start/Exec guard implied. |
| Two-gateway target attribution | PASS | Released OpenShell feature | Duplicate display names had distinct IDs; get/list/watch correctly attributed. Fresh state query superseded lagging event; dead target was unavailable, not deleted. Linux guest is not a remote-host qualification. |
| Current6e Capsule isolation under supported workload identity | FAIL | Configuration | Real Linux wrapper requires root; released policy rejects UID/GID0. Native macOS wrapper requires Linux Landlock. No checks removed. |
| Actual full Architect-derived OpenCode/Amp/Kimi/Grok images | PASS | Jackin-side adaptation | Real6e builder, selected installer, real preflight and version in OpenShell after explicit nonzero group/PATH/read-only runtime-path/default-home seed adaptation. Version/hook scope only; model task not covered. |
| Full Architect Claude build | FAIL | Jackin-side adaptation | Installer2.1.310 ran, then required marketplace source lacked marketplace.json. Existing role-input failure, not OpenShell regression. |
| Selected Codex build | FAIL | Jackin-side adaptation | Current fallback install URL returned404. Existing installer failure; no image/task pass. |
| Selected-agent cache fidelity | FAIL | Jackin-side adaptation | Fresh captured Amp request reused Grok image; exact-image positive Grok and absent Amp control. Manual removal of only owned mutable tag forced correct build; that is a workaround, not normal workflow. |
| Same-agent warm cache / changed role content | PASS | Jackin-side adaptation | Same image reused; declared preflight comment changed role/recipe/image identity. Not evidence that unknown agent versions are safely keyed. |
| Authenticated coding, account publication/refresh/resume | BLOCKED | Jackin-side adaptation | No approved disposable live account credentials. All distinct active authentication routes remain required. |
| Raw local host bind with admission preserved | FAIL | Configuration | Rejected by released driver; no admission disable. |
| Approved host-backed named-volume sharing and Git primitives | PASS | External service | Trusted canonical-path/label/options validation, live edits, atomic replace, RO/wrong-workspace negatives, selected Git operations and retained bytes; independent fresh repeat. Not complete product materialization/account/exit contract. |
| Linked Worktree alias route | PASS | Workaround | Narrow extra path aliases + exact Git safe.directory treatment enabled Git primitives. Bare project mount failed; complete worktree workflow remains untested. |
| Small CPU/memory enforcement | PASS | Configuration | Bounded throttle and OOM observations. Not every active profile/budget. |
| All effective profile outcomes and budgets | NOT TESTED | Configuration | PID/fd/reservation/identity/filesystem/privilege and aggregate boundaries lack complete mapping/enforcement proof. |
| External dedicated-engine mTLS/default-off | PASS | External service | Healthy endpoint positive; no-client-cert denial, distinct engine trust rejection. Earlier DNS-only denial is not used as TLS proof. Engines are outside OpenShell ownership. |
| External Docker online pull/build/CLI/Compose/live child bind | PASS | External service | Fresh absent pinned image, permitted RUN download, logs/exec/stream/volume/removal, actual returned service addresses and real project exchange. Required full concurrent managed workflow remains incomplete. |
| First native Testcontainers application exchange | PASS | External service | Real Redis data exchange and reported host/port under the admitted executable identity. |
| Two edited same-path native Testcontainers runs | FAIL | Configuration | Changed hashes, same executable path, explicit `transparent_tcp_identity_unavailable` denials. Ordinary mise command also exposed incomplete tool preparation; no complete normal-command alternative passed. |
| Fixed-port collision | PASS | External service | Clear bind conflict observed; partial Compose resources remained until explicit owned down. No automatic rollback guarantee claimed. |
| Managed optional Docker capability | NOT TESTED | Released OpenShell feature | No managed companion/inside-compute solution demonstrated. External forwarding cannot fill this row. Rootless startup failed before daemon readiness, with missing diagnostics; no global unsupported claim. |
| Workflow worker released tmpfs path | FAIL | Released OpenShell feature | Structured mount API rejected required flags. Create-only Docker control accepted equivalent HostConfig.Tmpfs; no verification work executed through Docker. |
| Workflow tmpfs serialization patch | PASS | Experimental OpenShell patch | Commit `68cfa648538a497acd4af2cf48424eda9834ba0f`, base released bdb; exported patch SHA256 `ff61fbd50e03e44d518dca339221cae9012f4eee4d8b24161ec320dfc4176a00`. Live option mapping, sizes/flags and admission/protected-target negatives; 150 driver tests passed, 2 ignored. Historical executed gateway binary hash was not captured before cache GC; a later rebuild hash is not substituted. Narrow translation only; full worker remains FAIL. |
| Worker read-only-root Landlock equivalence | FAIL | Configuration | P10 outside write succeeded; refined P14 denied contents but allowed chmod of an out-of-grant UID-owned inode. This disproves claimed metadata immutability equivalence. P14 stopped at first violation. |
| Worker CPU/PID/tmpfs/network/output/exit primitives | PASS | Experimental OpenShell patch | Individual bounded cases passed in the patched local fixture; result binding/full immutable worker contract not complete. |
| Worker memory cap | PASS | Experimental OpenShell patch | Exact-container OOM events observed.247 matches Python negative-signal exit wrapping; another run returned74 and lost readiness. Correct unknown/infrastructure outcome handling remains a separate gate. |
| Local Linux guest and packaged VM bootstrap slices | PASS | Configuration | Separate pinned platforms/control/storage slices with explicit limits; not full target journeys. |
| VM admission-preserving host sharing | FAIL | Configuration | Bind rejected; confinement, role layout, shutdown durability and children boundary unproved. |
| Docker Desktop/native Linux/remote hosts/Kubernetes | BLOCKED | Configuration | Required authorized environments unavailable; no cross-target inference. |
| Full combined journey and fresh independent replay | NOT TESTED | Jackin-side adaptation | Accounts/session authority/managed engine/worker/target gates prevent it. Primitive repeats are not counted as combined acceptance. |

## Evidence ownership and cleanup

Each group's commands, policies, image identities, resource IDs, expected/actual logs, statuses and cleanup receipts live beside its reproduction scripts. Gateways, private credentials, engine data and target storage are owned explicitly by the creating fixture unless OpenShell deletion was observed removing them. Fixture cleanup is never labeled OpenShell cleanup. Review and final cleanup indexes qualify any resources that remain, rejected cleanup actions, or concurrent unrelated inventory drift.

## Procedural limitations retained

- Several initial commands had invalid names, filesystem grants, mount paths or tool/bootstrap assumptions. Corrected tests have separate records; invalid attempts are not capability proof.
- One early Amp cache invocation's raw output was overwritten. It is retained only as a qualified observation; the later fresh captured Amp→Grok wrong-image reproduction is the decisive evidence.
- Early exploratory preview-image runs and an ancillary worker metadata `docker run` inspection are disclosed and excluded from candidate worker/agent execution proof. No direct Docker verification fallback is counted.
- Test harness exit/message assertion mistakes and patch review failures remain visible. JSON syntax checks are not semantic or readiness verification.
