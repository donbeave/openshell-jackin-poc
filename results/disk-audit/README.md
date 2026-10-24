# Read-only disk audit

Date: 2026-10-24. User authorized an independent cleanup search; no deletion authorized. No files, caches, worktrees, or containers changed.

## Storage

- `/System/Volumes/Data`: 3,996,276,899,840 bytes total; 2,007,957,237,760 bytes free at audit start.
- `~/.cache`: 2.6 GB.
- `~/Library/Caches`: 391 GB by `du -sh` (directory walk took about 40 seconds; individual directory report rounded to 393 GB).
- Largest entries: `~/Library/Caches/mbx` 323 GB; `~/Library/Caches/unrelated-project-build-targets` 30 GB; `~/Library/Caches/CloudKit` 26 GB; `~/Library/Caches/unrelated-project-verify-2805ac7` 11 GB; `~/.cache/codex-runtimes` 1.6 GB; Google caches 1.9 GB.

## Cleanup disposition

No safe removal candidate established. `mbx` and managed build targets are shared, active build caches, explicitly protected by local policy. `unrelated-project-*` directories are recent task-scoped caches, but ownership does not establish that their task is finished or recoverable. `codex-runtimes` is recent and may support active sessions. CloudKit and Google are application-managed caches; deletion can trigger long re-downloads or affect app state. Recommend owner-specific cache tools after confirming each task/session is finished. No blanket cache deletion is safe from this evidence.

## Docker engine

`docker system df`: images 14.76 GB (5.005 GB reclaimable), containers 14 / 666.1 MB, volumes 51 / 2.426 GB, build cache 18.37 GB (9.673 GB reclaimable). `docker ps -a` showed all 14 containers running, including six OpenShell gateway/sandbox containers and eight `unrelated-project-*` proof containers. No Docker image, volume, build cache, or container is safe to remove based on this audit. Reclaimable means unreferenced to Docker, not approved for deletion.

## Commands

- `df -h /System/Volumes/Data`
- `du -sh ~/.cache ~/Library/Caches`
- `du -d 1 -h ~/Library/Caches ~/.cache | sort -h`
- `docker system df`
- `docker ps -a`
- `stat -f '%N | modified=%Sm | owner=%Su | type=%HT' ...`

Directory sizes and modified dates are observations, not proof of disposal safety. No cleanup performed.

## Temporary-directory follow-up

Read-only scan covered `$TMPDIR` (`/var/folders/EXAMPLE/SESSION/T`, 1.3 GB) and `/private/var/tmp` (2.8 GB).

- Largest paths include `/private/var/tmp/unrelated-project-journal-recovery-target` (2.4 GB, modified Oct 22), `/private/var/tmp/unrelated-project-new` (172 MB, modified Oct 8), `/private/var/tmp/unrelated-project-pr368-fixture-fix-20261023` (130 MB, modified Oct 23), `/private/var/tmp/unrelated-project-parent-candidate` (46 MB), and `/private/var/tmp/unrelated-project-stage1.GDAm5n` (29 MB). These names and contents indicate task/recovery fixtures. No active process name matched the selected paths, but inactivity alone does not prove recoverability or disposal safety. Preserved.
- `$TMPDIR` contains Jackin and unrelated-project build/test artifacts, including many `unrelated-project-goldens-bin-test.*` executables (8–10 MB each), a 58 MB Node compile cache, and recent task-specific probes. Preserved because they are not owned by this experiment and may be recoverable work.
- No stale `.download`, `.partial`, `.part`, `.crdownload`, old `pip-*`, `go-build*`, or `rustc-*` temporary file candidates were found at the searched ages.
- Four arbitrary temp directories dated Sep 5 total about 256 KB. Contents include a 27-byte executable shell script and three 84 KB Mach-O `true` test binaries. No process had them open, but their role is unidentified. Preserved.

No files removed. Before/after free space unchanged within normal reporting precision. All candidate paths remain available for owners to identify.
- Follow-up scan found no files older than 60 days and larger than 10 MB in either temporary root. No new candidate identified.

## Current experiment Docker inventory (read-only)

Audit time: 2026-10-24 05:30 +07. Docker endpoint: existing OrbStack context. No cleanup performed.

### Containers

All named `ojp-20261024-*` containers belong to this experiment. Active external fixtures: `ojp-20261024-engine-a` (ID `61afbb648399712924b635278f193883a419afff4c0d7b111037dabcf44a12ac`), `ojp-20261024-engine-b` (`3c2c95d7c2140ff06f9941018250a8798e3bfa79ce9fc04bdc79c41ec4bbac46`), `ojp-20261024-sock` (`4820db703c070eb8504697e8b7c9a51da95f70558281fec694a5789d4dec9f6b`), and `ojp-20261024-network-endpoint` (`ec28dce7c0abcda8ae5a7017ca8a499aebaea7f1dbb5d4dea2cfb977195f8325`). Preserve: live fixtures and test service.

OpenShell resources include 3 running sandbox main containers (`rust`, `main`, `gwl`) plus their 3 supervisors, and 12 exited sandbox containers. Exited IDs/names/statuses: `7eba7e0616df` alt (exit 1); `5beba59ce8d2` gwe (137); `d16f82ff7dfc` v2 (1); `c1ff8bdc9771` gwi (1); `187b8f89c6e3` as (137); `7401f86f5b35` gwp (1); `a3b81d87c1cf` gws (137); `4d4c5c732d46` ah (137); `448c496d66b6` gwn (1); `a2ad300c01d8` gwm (137); `3dea180fbcea` gwd (137); `625659b88624` basic (1). All retained as execution evidence; some failed sandboxes remain addressable by gateway.

### Unreferenced experiment image tags

Docker container inspection found no container references to these image IDs at audit time:

| Image ID | Tag | Docker-reported size |
| --- | --- | ---: |
| `5887b574540db1f1eb82bae9a827cf4baa685144f2f2bf5d55d790f67de3404e` | `ojp-20261024-agent:2.1.310-poc-forced` | 3.8 GB |
| `157daf4a9831f4a56a4105c154f5282bc91e3a49137e5946bc23988e079d546b` | `ojp-20261024-agent:2.1.310-poc-warm` | 3.8 GB |
| `6c642b9c2847baf49a4b420f8cb5378facb9ddf2bb90c095f8b92bc2c2bf98c6` | `ojp-20261024-agent:2.1.310-poc-final` | 3.71 GB |
| `791d44dbe1d6e99b02f6b4b8aa9016ca4e82ec9a94dc7cf360a87779419b2e66` | `ojp-20261024-agent:2.1.309-final-tools` | 2.88 GB |
| `7dfcb7b929575803916ec9790be94b4e020e6699e9295170bd0ec5c92148683d` | `ojp-20261024-agent:2.1.310-final-forced` | 2.88 GB |
| `24f91a2565b4a638c228ad2edddb5623a58d4e4c2bd4ed171a86b72444202d01` | `ojp-20261024-agent:2.1.310-final-warm` | 2.88 GB |
| `80e997102a8c32701ea92c04a665e91daf73db139251dd4de59b77e780390486` | `ojp-20261024-agent:2.1.310-final-tools` | 2.88 GB |
| `4ab1ec92e08aacc0bb331c93f21ecb7be6f2a102f73fac137a21077680b2081e` | `ojp-20261024-agent:2.1.309-tools` | 3.09 GB |
| `60f4469769db713f35b2a529cf305a26383d62fd65764bbbc9829f32c8a42554` | `ojp-20261024-agent:2.1.310-tools` | 3.09 GB |

These are candidates for later cleanup only. Retain until final image/build cache measurements and reproduction results are backed up. Docker size is per image report, not guaranteed reclaimable space because layers may be shared.

### Volumes and local files

Five experiment volumes, all currently attached to running or stopped test containers: `ojp-20261024-engine-a-project` (seven containers), `ojp-20261024-engine-b-project` (engine B), `ojp-20261024-gwlabel-vol` (gateway label test sandbox), `ojp-20261024-gwvol` (external mount test sandbox), and `ojp-20261024-sock-dockersock` (socket test daemon). Preserve: each remains part of experiment evidence/state.

`experiments/` totals 73 MB, including `sdk-venv/` at 47 MB and fixture archive `experiments/engines/host-images/nginx-1.29.3-alpine.tar` at 24,037,376 bytes. Both support reproducibility; preserve. No wheel, ZIP, compressed source archive, disk installer, or package installer found in experiment-owned paths. No experiment-owned tool-download archive found.

## Authorized old-namespace cleanup (script-owned)

The experiment gateway uses `sandbox_label = "ojp-20261024"`. Read-only query of its current SQLite database (`openshell.db`, opened with `mode=ro`) returned the active sandbox names `gwl`, `lim`, `main`, `root`, `root2`, `rpt2`, `rust`, and `soc`; none of the 12 prior default-namespace orphan names appeared. The gateway CLI itself returned `invalid peer certificate: BadSignature`, so database verification used SQLite directly. Docker label is `openshell.ai/sandbox-namespace=default` (the runtime form of OpenShell's `sandbox_namespace` label).

Before removal, saved complete selected container IDs, names, states, exit codes, image IDs/tags, sandbox IDs/names, non-secret labels, and mounts in `orphan-pre-removal.json`. Selection required name substring `ojp-20261024`, exact namespace label `default`, exited state, and absence of each sandbox name from the current database. Immediate recheck found the same 12 IDs and all exited. Ran `docker rm` with those exact IDs only, without `-v`; exit 0; post-check found zero matching containers. Action was **script-owned cleanup**, not OpenShell cleanup. All mounted volumes remain. Record and stdout: `orphan-removal.json`.

Host free bytes: `2,017,741,168,640` before; `2,017,736,994,816` after (4,173,824-byte decrease while other experiment work continued; no free-space gain demonstrated).

### Authorized unused image-tag cleanup (script-owned)

Immediately before removal, inspected every container, including exited containers. Removed only exact `ojp-20261024-agent` tags with no container references and outside the protected list. Preserved `2.1.310`, `2.1.310-poc-final-v2`, `2.1.310-poc-v3`, and `2.1.309-poc-final`. All 10 removed tag records, image IDs/digests, byte sizes, image commands/entrypoints, and `NOT APPLICABLE` container exit status (no container references) are in `image-tag-pre-removal.json`. Docker `image rm` returned 0; verified all 10 tags absent and all 4 protected tags present. stdout and free-byte measurements are in `image-tag-removal.json`. This was **script-owned cleanup**, not OpenShell cleanup.

Host free bytes: `2,017,232,650,240` before; `2,017,228,230,656` after (4,419,584-byte decrease while active experiments continued). Docker reported each image as deleted; host free-space increase was not demonstrated. Layer deduplication and active writes affect apparent image sizes.

Post-cleanup follow-up: exact old-namespace Docker filter returns no containers. Experiment image repository now contains only the four protected tags; no new Rust v4 tag existed at this check. Active namespace still has running sandboxes including `soc2`; preserved. Latest observed host free bytes: `2,022,748,594,176` (later than cleanup measurements; concurrent runtime writes make attribution unsafe).
