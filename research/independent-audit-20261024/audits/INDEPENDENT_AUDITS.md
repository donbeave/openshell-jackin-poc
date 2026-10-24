# Independent audit record

All source audits used Jackin `6e266406b49da2ab3c55355f3b7d33d1643ee6cd` and `rg` plus call-site inspection. Four separate initial scouts were assigned disjoint areas. They were read-only and returned findings to the parent; this record persists their findings. None ran Jackin, built a backend or equated tests/source with execution. The expanded per-site inventory is maintained separately and remains subject to coverage review.

## 1. Docker, image building, optional engines and cleanup

Reviewer: `audit_docker` (independent Rust scout). Production builder and runtime are intermixed, so `jackin-docker` cannot be deleted wholesale. `image/build.rs:69-218,221-455` performs build/buildx/tag/image inspect; `validated.rs:88,119,172` feeds launch/prewarm. `image/version.rs:37-95` performs a real agent `docker run` fallback and is called after build. It must be removed, not misclassified as build-only.

Runtime direct execution includes `runtime/launch/launch_runtime/docker.rs:31-321`, `session.rs:12-255`, `jackin-runtime-session-control/src/session_control.rs:28-416`, `jackin-runtime-snapshot/src/snapshot.rs:44-325`, and `jackin-runtime-host-attach/src/host_attach.rs:110-150`. Runtime inventory/inspect/log/stop/start/delete calls also occur in discovery, attach gates, diagnosis, launch slots and cleanup plus CLI/console. Replace each action by resource/transport semantics, not a generic crate rename.

Optional DinD owns network, sidecar, certificate volume, pulls, readiness, prewarm/restart and GC. Existing external-engine evidence does not establish the required managed capability. `cleanup-prune-images/src/prune_images.rs:9-71` derives consumers from Docker role-container labels, so it cannot remain unchanged across OpenShell target stores. Preflight currently gates management on Docker. Workflow verify is an independent execution backend. Generic shell/process/output utilities remain useful.

Exclusions: fake Docker and command expectation tests are tests, image Dockerfiles are build content, CI profile runners are infrastructure, schema/telemetry strings need semantic disposition but are not automatically executed operations. These exclusions do not excuse an operational script that really invokes Docker.

## 2. Apple, VM, storage and resource controls

Reviewer: `audit_storage` (independent Rust scout). Apple dispatch is active: orchestrate/runtime.rs:112-143, apple_container.rs:67-220, client.rs:163-269 and backend.rs:150-209. Actual `container run/start/stop/rm/list` commands exist. Hardline's foreground finalization explicitly fails Phase 0; mock tests assert this failure. It is incomplete, not demonstrated parity.

`jackin-isolation/src/materialize.rs:403-450` maps Shared to source, Worktree to per-instance host Git worktree, Clone to independent local clone; :480-540 writes auxiliary Git path bindings. Product materialization may remain, low-level runtime mounts cannot. Container state/manifest discriminator currently defaults missing legacy state to Docker; new format uses explicit target/sandbox identity and no import.

Preservation guards actively inspect holds at runtime/cleanup.rs:26-45 (eject/prune/purge callers). Normal checkpoint-to-hold creation was not found. Host daemon checkpoint stores `preservation_hold: None`; workflow history checkpoint is a separate concept. `capture_checkpoint()` lacks a production caller found.

Effective profiles: locked allowlist/no DinD/no sudo/4 GB/2 CPU/512 PIDs; hardened allowlist/no DinD/16 GB/4 CPU/2048; standard open/no DinD/16 GB/4 CPU/2048; compat open/privileged DinD/sudo/unbounded. Grant precedence matters. Launch setup starts root to provision/drop; sudoers presence does not imply interactive sudo requirement. Actual OpenShell limit enforcement is not proved by computed profile args.

## 3. Capsule, sessions, accounts, credentials and host integration

Reviewer: `audit_accounts` (independent Rust scout). Account choice travels load_cmd.rs:113-174 into launch, environment_prepare.rs:48-84,132-139 and active.rs:117-147. Account identity uses fingerprint/admission/revision and transactional staged publication. Hardline :61-87 checks current admission; it does not terminate existing sessions immediately on revocation.

Capsule main.rs:21-55 supports PID1 or forced-daemon mode and Darwin reaper setup. Linux isolation expects root and drops child identity; daemon boot installs one reaper. `session/spawn.rs` uses coordinated child ownership. Current-pin process/reaper changes cannot borrow older binary evidence. Attach handshake obtains SO_PEERCRED; host transport uses direct Unix socket or `docker exec -i <immutable ID> jackin-capsule attach-proxy`. New full-duplex bridge must replay current frame types including image/export/URL, not merely a terminal shell.

Usage relay authorization maps per-instance UID/GID/PID start identity to scoped accounts/surfaces. Candidate B same-UID helper is untrusted I/O and cannot own host approval/inventory/refresh. Credential_update_v2, checkpoint capture and grant inspect/readback are foundations without production caller found; classify separately. Host clipboard and URL opening stay at the desktop.

## 4. Workflow, CLI, discovery and distributed targets

Reviewer: `audit_workflow` (independent Rust scout). `verify.rs` stages private source clone/trusted checks, exact image/argv/policy hashes; service.rs:800-844 invokes and persists result. Baseline: no network, read-only root/candidate/checks, cap-drop/no-new-privileges, 512 MiB/1 CPU/64 PIDs, 64 MiB `/tmp` noexec/nosuid and 256 MiB `/build`, 64 KiB per stream and deadline. Root is implementation detail, not product requirement. Replace run/image/inspect/timeout/Drop cleanup operations independently.

`preflight.rs:76-134,189-220` unconditionally requires Docker for load/hardline/eject/exile/purge/prune. Separate builder health. `cli/status.rs`, `console/services/instances.rs`, `console/workflows.rs`, `cli/usage.rs` use local Docker inventory and snapshots. New fleet needs target-scoped immutable references and incomplete/unavailable/unauthorized states. Keep Git/usage useful when GitHub fails.

`jackin-host/src/caffeinate.rs:25-154` uses a Darwin PID file/lock and labeled local Docker container count; load/restore/finalization call it. Replace container count with logical-instance membership, preserving correct desktop ownership and concurrency. No existing target CRUD/distributed execution was established. Packaging supports four client triples; required new remote/Kubernetes behavior is not current working desktop evidence.

## Source-coverage independent review, pass 1

Reviewer: `review_source` (separate Rust reviewer, no edits/builds/tests). Verdict: coverage gate not passed. Concrete findings:

1. Generic path-based classification confused `launch_pipeline.rs:357` network removal with role execution and `reconnect_lease.rs:208` optional DinD with Capsule transport.
2. Multiline calls missed version.rs:52 agent execution, caffeinate.rs:145 list, reconnect_lease.rs:97 start; prune/restore/context/status inspect sites and Apple high-level calls.
3. Worker run/inspect/pull/timeout removal/exit observation/Drop cleanup needed distinct records.
4. Capture tests appeared in production ledger; capture/readback definitions lack production callers and need exact exclusions.
5. Root privilege drop, SO_PEERCRED and reaping assumptions need inventory even without Docker keywords.
6. Scanner could overwrite enriched records. Raw candidates must be separate and reconciliation validated.

Author expanded scan and operation records and requested re-review. Pass 1 is retained; it is not silently replaced with an inventory-complete claim. Final source coverage verdict must cite the subsequent reviewed ledger state.

## Authority/storage/cleanup independent review, pass 1

Reviewer: `review_authority` (separate Rust reviewer, no edits/builds/tests). Verdict: gate not passed. Findings:

1. Role hook probe directly used Docker run/Claude version. Exclude this historical builder diagnostic from OpenShell execution evidence; no further direct Docker probes.
2. Timeout fixture hard-coded sandbox UUID/generation inconsistent with another run. Recapture identities and rerun; old result cannot pass.
3. Worker mounted mutable host directories without candidate/check/policy result bindings. Need immutable snapshot and hash binding.
4. Read-only-root check accepted any OSError on already unwritable `/etc/hosts`; need a UID-owned otherwise writable path and positive control.
5. Worker bind fixture disabled resource admission, unlike proposed admitted-volume architecture. Record deviation explicitly.
6. Capsule replay swallowed asynchronous delete errors without confirmation. Add exact scoped receipts/polls.
7. Candidate B authority/session, Rust transport, managed Docker and approved credential consumer/MCP are unproved.
8. Normalize statuses to PASS/FAIL/BLOCKED/NOT TESTED; split passing primitives from untested product outcomes.

Authors were notified to correct records/rerun where possible. Docs correctly retained remote sharing limits, root-policy incompatibility, admission-only revocation, preservation under uncertainty and external-engine boundary. Reviewer found no production backend/broker/multiplexer/controller in the reviewed fixtures. Corrections and remaining blockers must be checked before final synthesis; independent review is not an approval of full replacement.

## Final static source signoff

Reviewer `review_source` reopened the final artifacts and passed the static coverage gate. The canonical ledger has 207 direct records, 10 cross-cutting records, 19 infrastructure records, and one separate active but incomplete Apple-finalization behavior. All 1,266 broad matches have dispositions; the 329 narrower candidates have no unresolved disposition. Documentation, tests, build-only dependencies and aliases are retained with reasons; these query counts overlap and must not be summed.

Later action reviewers inspected each original operation and traced exact source edges/routes or verified no-production-caller dispositions. Final corrections separated actual action from crate/backend labels: Docker client construction from reachability, optional-engine readiness from Capsule, Linux SIGCHLD reaping from Darwin lifecycle, Apple inspection via `container list` from a nonexistent `container inspect`, active Apple finalization from unused Docker helpers, and active fail-closed foreground-session inspection from uncalled checkpoint capture. Duplicate source descriptions at Apple purge and preflight became alias provenance, not extra operations. Final preflight constructor and ping remain separate, and the version request has one canonical execution row.

Source coverage is source-only. No replacement-execution flag is true. All changed runtime/transport/storage/identity/credential/platform assumptions still require their own execution evidence.

## Final authority/storage/cleanup disposition

The separate `review_authority` pass found the negative readiness decision justified but did not pass full integration authority/storage/cleanup. Corrections were applied: disabled/excluded Docker runtime probes; exact source-root rejection; explicit approved-consumer location and disclosure boundary; worker timeout/exit/storage restrictions retained; scoped cleanup receipts; permitted result statuses; and narrowed PTY claims. A fresh terminal replay remained inconclusive and is NOT TESTED for identical-process reconnect.

An alleged truncated generation in `exec-roundtrip.json` could not be reproduced by parent or author: the retained record has complete generation `2c9cd0a4-5702-4ede-a6f5-e334c23d4221`, matching the timeout evidence. No valid identity was replaced with a guess. The teardown's original inferred stop/curl claims were actually invalid and are retained as invalidated history; parent subsequently captured independent read-only listener/namespace observations. No stopping actor is inferred from later absence.

Remaining decision blockers include trusted domain/session/credential transport, bounded worker termination with observed exit, identity/retry enforcement, admitted durable storage, managed optional Docker, required platforms and full combined execution. No reviewer approved a full refactor start. No production backend, broker, multiplexer or controller was found in the research fixtures.
