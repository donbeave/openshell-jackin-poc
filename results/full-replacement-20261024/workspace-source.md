# Workspace, Docker, profile, and isolation source map

**Jackin source:** `/Users/example/Projects/jackin-project/jackin`, commit `41bad147b5ba9db09be99b07248531ce1bd867be`, clean working tree; it matches requested pin. Public evidence checkout: `2315e6a278231854b3139b1ca32402777ff3cd01`. Static source map only; no new OpenShell runtime test.

## Workspace and Git contract

| Requirement | Source and behavior | Owner / runtime dependency | Required positive and negative evidence |
|---|---|---|---|
| Workspace authority, mounts, working directory | `crates/core/jackin-config/src/schema.rs:153-216,315-341`; `crates/core/jackin-config/src/resolve.rs:170-210`; `crates/apps/jackin/src/workspace/{planner,resolve,mounts}.rs`. Jackin resolves source paths, policy, read-only flags, working directory. | Jackin retains workspace selection, authorization and policy. OpenShell driver supplies host mount or explicit transfer semantics. | Host edit visible in agent and agent edit visible on host; read-only write denied; unauthorized source/protected target rejected; working directory correct. |
| Shared | `crates/core/jackin-core/src/isolation.rs:21-42`; `crates/services/jackin-isolation/src/materialize.rs:395-455,410-418`. Same source mounted. | Jackin chooses path; OpenShell driver owns runtime mount. | Two instances show promised shared edits; host watcher sees agent changes; read-only and permission behavior preserved. |
| Worktree | `crates/services/jackin-isolation/src/materialize.rs:44-52,96-134,395-455,458-...`. Allocates per-instance linked worktree in retained state and mounts `.git`/gitdir auxiliaries. | Jackin owns worktree, Git metadata and cleanup journal; runtime mounts project and auxiliaries. | Git status/diff/commit and linked paths both sides; two instances isolated; restore after recreation; source checkout intact. |
| Clone | `crates/services/jackin-isolation/src/materialize.rs:54-62,431-442`. Clone path per instance in state. | Jackin owns clone lifecycle and retention; runtime mounts retained clone. | Git operations work; two instances isolated; data survives runtime recreation; exact export. |
| Pull on entry | `crates/services/jackin-runtime/src/runtime/launch/launch_pipeline.rs:1222-1269`; only fresh launch when enabled. Existing test `.../launch/tests/case_07.rs::git_pull_on_entry_starts_all_repo_pulls_before_waiting`. | Jackin owns setting/Git behavior; runtime provides network and checkout. | Disposable remote pulled on fresh launch; disabled setting makes no pull; restore behavior distinct. |
| Durable state / recovery | `results/rewrite-readiness/product-contract.md`, section “Sessions, files, Git, and parallel work”; runtime restore/manifests under `crates/services/jackin-runtime/src/runtime/launch/restore/`. Host-backed workspace, worktree/clone, agent home and metadata are recovery sources; container writable-layer mutations are not. | Jackin owns state model and retain/purge decision; OpenShell persistent storage must retain bytes across runtime recreation. | Byte-exact state after runtime deletion/recreation; eject/exile retain, purge removes only after runtime absent; missing data errors visibly. |

Historical repeat-final evidence `results/repeat-final/README.md:27-29,47` proves same-path exchange through a Docker named volume shared by agent and external daemon. It does **not** prove host checkout bind, file watching, Shared/Worktree/Clone, read-only host mounts or linked Git semantics. Reuse only for child-container bind plumbing on that recorded OrbStack Linux ARM64 setup.

## Profiles and grants

Profile precedence is CLI, workspace, config, default (`crates/services/jackin-runtime-docker-profile/src/docker_profile/profile.rs:32-47`). Grants merge base, config, workspace (`profile.rs:65-80`). Network/DinD/sudo/writes broaden monotonically, resource values may raise/remove limits, capability additions accumulate (`effective.rs:98-149`). Profile names are not enforcement proof.

| Profile | Effective behavior in `effective.rs:26-87` | Required runtime proof |
|---|---|---|
| `locked` | Allowlist (empty base), no DinD, user `agent`, no sudo/system writes, NNP true; memory 4 GiB/reservation 3 GiB, CPU 2, PIDs 512, nofile 2048. Allowlist implicitly adds `NET_ADMIN`,`NET_RAW` (`profile.rs:82-91`). | Allowed host succeeds, other host and healthy Docker endpoint denied; identity/privilege restrictions; each limit enforced under bounded load. |
| `hardened` | Allowlist, no DinD, `agent`, no sudo/writes, NNP true; 16/12 GiB, CPU 4, PIDs 2048, nofile 8192. | Same positive/negative checks with distinct resource budgets. |
| `standard` (default) | Open network, no DinD, `agent`, no sudo, system writes, NNP true after resolution; 16/12 GiB, CPU 4, PIDs 2048, nofile 8192. | Network works; no Docker absent explicit grant; permitted system write; limits enforced. |
| `compat` | Open network, privileged DinD, `agent`, sudo/system writes, NNP false; no configured limits. | Granted sudo and Docker workflows work; ungranted cross-instance authority denied; do not claim limits. |

Further source: `docker_profile/grants.rs:6-61` validates root+sudo, capabilities, sizes, reservation<=memory, positive PID/CPU/nofile; `capabilities.rs:4-45`; `flags.rs`, `tmpfs.rs`, `drops.rs`, `probe.rs`, `workflow_grant.rs`. OpenShell must map user, sudo, system writes, network, capabilities, no-new-privileges, CPU/memory/reservation/process/fd limits and Docker access. Demonstrate one allowed and one prohibited operation per distinct grant. Measure agent, supervisor, engine, children separately; prove aggregate only if claimed.

## Optional Docker and resource owners

Docker is conditional. Standard base grants no engine; Compat defaults to privileged DinD. `crates/services/jackin-runtime-launch-dind/src/launch_dind.rs:88-106,143-205` creates role network, selects daemon image/privilege, mounts TLS cert volume, labels sidecar by owner and starts it. Runtime can adopt prewarmed sidecar; image/sidecar prewarming exists in the launch pipeline. Jackin currently owns optional engine, certificates, networks, children and cleanup. OpenShell owns the agent sandbox in the proposed design; keep engine access absent by default and dedicated per selected instance. Agent firewall does not automatically constrain Docker children; Jackin already describes child egress as partial.

The role image builder is a separate launch-time capability: build selected agent into derived image before sandbox creation. This must not accidentally grant sandbox Docker API credentials. Cache/prewarm retention or adoption needs two competing clients tested for unique ownership; no production pool manager.

## Historical evidence disposition

OpenShell v0.1.5 (`bdb956f2cd65a635f1294fccf1d138d263bf650f`) on macOS ARM64 + OrbStack Linux ARM64 may be reused narrowly for recorded CLI/SDK lifecycle, named-volume exchange, external mTLS Docker API, Compose first-run, and first Testcontainers data exchange. See original `CAPABILITY_MATRIX.md` and `results/repeat-final/README.md`.

Not proved: real host checkout, Shared/Worktree/Clone journey, full profile translation, all resource limits, Jackin-owned eject/exile/purge, prewarm adoption race, concurrent same-project workflows, or required target platforms. Earlier pinned OpenShell docs required `enable_bind_mounts=true` and disabled resource admission for host bind mounts (cited in `JACKIN_REWRITE_READINESS.md`). Record exact setting and negative path-boundary tests; do not silently disable admission. This is a significant security decision.

## Highest-risk small experiments

1. Real disposable host checkout: record admission settings; bidirectional edit, atomic replace, watcher, permission, symlink, RO denial, protected/unauthorized host path rejection and working directory. Stop if declared isolation boundary cannot be shown.
2. Run Shared, Worktree, Clone independently. Test Git status/diff/commit, linked metadata, two concurrent instances, host visibility, runtime recreation, retention, exact export; preserve original checkout.
3. Resolve all four profiles plus overrides. Prove permitted/prohibited network, user, sudo, writes, capabilities, Docker; measure CPU, memory, reservation, PIDs and fds under bounded workloads.
4. Default-off denial against a healthy reachable endpoint; selected dedicated engine online pull/build, Testcontainers edits twice, Compose/concurrency/ports/callback/collision and teardown. Record Jackin as owner of all engine-side resources.
5. Two clients contend for retained prewarm/cache resource; prove single-owner adoption or rejection.

Required scope stays fixed. Unavailable targets remain BLOCKED/NOT TESTED and preclude full-ready verdict.
