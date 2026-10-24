# Disk audit: full replacement follow-up

Snapshot: 2026-10-24. User waived disk thresholds. No cache cleanup performed.

- Data volume: 3,902,614,160 KiB total; 2,146,072,192 KiB available (about 2.0 TiB).
- Active follow-up tree: approximately 2.3 GiB. The role Rust target is approximately 2.5 GiB. Capsule build target is approximately 14 MiB; owner reports abandoned output, and pinned recovery was proven with `git cat-file` plus `git archive` for commit `41bad147b5ba9db09be99b07248531ce1bd867be`. No product executable exists in the target; it contains only incomplete Cargo fingerprints/metadata. `lsof +D` found no open files. Exact target is not a symlink or MBX-managed cache. Cleanup attempt via the required Rust guard was rejected (`unsupported Cargo command 'clean'`); raw deletion was rejected by command review, so retained.
- Docker daemon totals: 62 active containers, 9.3 GB active container storage, 2.6 GB volume storage, 56.3 GB build cache (37 GB reported reclaimable). Tests and unrelated user workloads are active. These totals do not establish ownership; no Docker pruning.
- Dedicated test Linux VM remains running. No VM or gateway cleanup while owners execute.
- `patch-delete/openshell/target/check` had an active Cargo process at audit time; protected. Shared Rust caches, worktrees, sessions, images and active targets are protected.

Potential cleanup candidate: `experiments/full-replacement-20261024/role/capsule-build/target` (14 MiB). Owning agent confirmed it came from an earlier failed build and has no active process/open files. It is retained because the mutable checkout HEAD is `6e266406b49da2ab3c55355f3b7d33d1643ee6cd`, but its Git object database contains frozen commit `41bad147b5ba9db09be99b07248531ce1bd867be`; `git archive` recovered the Capsule manifest from that exact commit. The owner confirmed this exact target is abandoned. It remains because the mandated Rust guard rejects `cargo clean`, and command review rejected raw deletion. No alternate deletion route was attempted.

## Bounded monitor

Six samples taken 30–43 seconds apart from `01:42:08Z` to `01:45:28Z`; raw counters are in `disk-samples.jsonl`.

- Free space ranged from 2,198,664,314,880 to 2,206,053,212,160 bytes (about 2.0 TiB); no threshold concern under the user's waiver.
- Follow-up experiment files grew from 3,677,861,475 to 3,678,198,927 bytes, then stayed level for the final two samples.
- Failed Capsule target stayed exactly 14,242,055 bytes throughout.
- Latest Docker inventory: 68 active containers; images 32.37 GB with 6.414 GB reported reclaimable; build cache 57.84 GB with 37.75 GB reported reclaimable. Active test work increased shared inventory. No prune is safe.

## Second bounded monitor

Six additional samples taken from `01:47:00Z` through `01:50:26Z` (30–53 seconds apart). Docker inventory queries slowed while the number of active test containers increased; the last two samples recorded only local disk and owned-tree counters. All raw samples append to `disk-samples.jsonl`.

- Free disk ranged from 2,187,268,259,840 to 2,195,718,787,072 bytes (about 2.0 TiB).
- Follow-up experiment tree grew about 185 KiB during the interval.
- Candidate failed target remained 14,242,055 bytes.
- Earlier live Docker sample showed 80 active containers and 59.09 GB build cache, 37.46 GB marked reclaimable. That growth belongs to active concurrent builds; do not prune.
- Owners report no further cleanup candidates. Role, control and Docker outputs remain in active use or preserve experiment evidence.

## Cleanup verification checkpoint

Read-only checkpoint while owners were removing owned resources. No delete or prune command was run.

- Data volume currently reports 2,111,363,728 KiB available. This is a concurrent before/after snapshot; other workers and host activity affect it.
- Docker shows 14 active containers, 141 images (7 active), 71 named volumes, and 981 build-cache records. Cache is 118.8 GB, with 83.61 GB listed reclaimable. Do not prune shared caches.
- The 14 running Docker containers are pre-existing OpenShell and unrelated project workloads; none matched follow-up experiment names. Preserve them.
- OrbStack machine inventory is empty; the follow-up Linux VM is gone.
- Two volumes remain, labeled as owned by the verification worker. Preserve until that worker confirms final cleanup.
- Gateway A remains on port 28470 for root cleanup. Patch worker gateway remains on 28631 with its process active; preserve until its report finishes. Other follow-up gateway ports checked were absent.
- Docker image inventory still contains experiment role and patch-worker images. Preserve the pinned Architect base and worker images until owner manifests/report completion. No image deletion performed.
- The 14 MiB abandoned Capsule Cargo target remains. Prior safe-clean route was rejected; do not retry or bypass review.

## Owner-manifest reconciliation

Compared the read-only inventory with experiment manifests after the first cleanup pass:

- Root gateway A remains on port 28470. Patch verification worker has an active gateway on port 28631. A separate verification-worker manifest records its release gateway on port 28630 as retained for review; check it before closure.
- The Linux and packaged-VM target manifests enumerate former sandboxes; no experiment-named containers remained in current Docker listing, and `orb list` returned empty.
- Two Docker volumes still carry the verification-worker fixture label. Its manifest supplies exact device paths and a scoped cleanup script, but owner has not released cleanup.
- Role-image cleanup manifest lists derived images released by the Docker experiment owner, while preserving the Architect base. Images remain present. No image removal or shared prune was run.
- The 14 remaining containers were identified by inventory as pre-existing workloads. Their names and IDs are omitted here.

This is an in-progress checkpoint. Active worker gateways, volumes and patch binaries remain untouched pending owner release and the root agent's final verification.

## Post-owner cleanup checkpoint

Read-only inspection after Gateway A and the scoped sandbox/image cleanups:

- Gateway A receipt reports its listener stopped and its isolated CA/client credentials/database removed. Live check confirms PID 65583 and port 28470 are absent.
- Owner receipts confirm the 15 role/Capsule sandboxes and nine workspace sandboxes deleted; the Docker experiment receipt confirms engines A/B and engine data/workspace volumes removed. The 11 released derived image tags are absent; the Architect base remains.
- Linux VM inventory is empty. No Docker container name matched the experiment namespace.
- Two gateways remain for verification work: release gateway on 28630 (PID 53597) and patch gateway on 28631 (PID 25374). Their owner is still working; leave both running.
- Two Docker volumes retain the verification-worker label. Its manifest lists the exact paths, but the expected cleanup script is absent. Await owner confirmation and an auditable safe path; leave both volumes.
- Docker reports 14 active pre-existing containers, 141 images (7 active), 71 named volumes, and 981 shared cache records (118.8 GB). No prune.
- Available disk: 2,126,177,380 KiB. Concurrent changes make this a snapshot; no cleanup was performed by the disk auditor.

## Final verification-worker cleanup

Read-only check after the worker's scoped cleanup receipts appeared:

- Receipts confirm both worker gateway lists empty, zero worker containers/tags/volumes, stopped PIDs on ports 28630/28631, and removed only worker private certificates/state. Independent `lsof`, Docker volume and container checks agree. All other experiment gateway ports checked are absent.
- Available disk is 2,119,850,904 KiB; shared Docker images, containers, volumes, and caches remain as recorded. No pruning.
- One 11.9 GB image remains: `jfr-20261024-capsule-root-6e:fixture`, ID `sha256:c8f1f20f48889d8ced6af633778663bdde90a1b659c8ab4ff08d624e0b6f2d88`. No container references it. Its image labels identify it as a Jackin construct base, but the role experimenter's cleanup manifest does not list it and the agent says it is outside their cleanup authority. Retained pending owner mapping; do not remove based on name or labels alone.

## Capsule image cleanup and final inventory check

The owner receipt confirms exact image ID `sha256:c8f1f20f48889d8ced6af633778663bdde90a1b659c8ab4ff08d624e0b6f2d88` was removed without force after verifying no container references. A read-only rescan confirms no experiment-named containers or volumes, no OrbStack guests, and none of the assigned gateway listeners. Available disk: 2,123,989,112 KiB.

Docker inventory now has 132 images (7 active), 14 pre-existing containers, 71 named volumes, and 981 cache records (118.8 GB). No prune. Four role-base tags remain: the designated pinned Architect base plus three `jk_jfr24_architect__base` / `jrr24-architect-role-base` tags. Their ownership/provenance is under review; they were retained. No shared cache or remaining image was deleted by the disk auditor.

## Base-image alias reconciliation

The only remaining `jfr`-family image references are four Jackin/Architect base tags. Their Docker image IDs and labels differ, but all four have exactly identical 37 RootFS layer digests to the pinned `jfr-20261024-architect-base:7b72b38` (ID `sha256:e7655072c6d511250b183e9511ca1f701e635766ec0d190a68bfe470745df63a`). No container references them. They are retained as metadata/cache aliases, not separate runtime outputs. No image mutation was run.
