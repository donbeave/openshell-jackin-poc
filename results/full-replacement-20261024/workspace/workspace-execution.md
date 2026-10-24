# Workspace, Git, and profile execution evidence

## Scope and version

- OpenShell release: `v0.1.5`, commit `bdb956f2cd65a635f1294fccf1d138d263bf650f`.
- Platform: macOS 27.0.1, arm64 host; OrbStack Docker Engine running Linux/arm64 containers.
- Gateway: isolated `jfr-20261024-b`, `https://localhost:28471`, PID 71130, separate client/XDG/TLS state; resource admission stayed enabled. Config: `experiments/full-replacement-20261024/gateway-b/gateway.toml`.
- Role image used for repeated runtime operations: `jfr-20261024-architect-base:7b72b38`, image ID `sha256:e7655072c6d511250b183e9511ca1f701e635766ec0d190a68bfe470745df63a`, linux/arm64. This is the real Architect role base with Git; it is not the final selected-agent derived image.
- Earlier filesystem probes used pinned official Ubuntu image `nvcr.io/nvidia/base/ubuntu@sha256:7e0f726d635d440d28a7f18e6498d3bdb76c7038bd4c90a090c21eb7c9f40686`. Their evidence remains separate; selected-agent authentication was not involved.
- Synthetic host checkout and sibling canary are under `results/full-replacement-20261024/workspace/jfr-20261024-ws/`. No personal source checkout or credentials were mounted.
- Four earlier shell-only `openshell-agent-preview:20261024` sandboxes are historical exploratory runs only, not decisive role evidence. They used shell/sleep and synthetic fixture only, had no providers or credentials, were stopped/deleted, and are excluded from PASS claims. Raw bind was separately repeated with Architect BASE and rejected before workload start.

## Host mount boundary

### Released raw host bind

The v0.1.5 pinned runtime guide documents raw bind mounts only with `enable_bind_mounts=true` and resource admission disabled; it warns that binds can bypass workspace isolation and filesystem policy. We did not disable admission.

With gateway B configured `enable_bind_mounts=true` and `[openshell.drivers.docker.resource_admission] enabled=true`, an actual Architect BASE request for `type=bind` failed before sandbox creation, exit 1:

```text
host bind or image mount cannot be attached while resource admission is enabled: no trusted label resolver
```

Evidence: `architect-rawbind.json`, `architect-rawbind.stderr`; request image was the actual Architect BASE and did not start. This is **FAIL / RELEASED** for raw host binds under the required admission boundary. Do not describe bind-backed named-volume tests as raw-bind support.

### Reviewed bind-backed named-volume fixture

A small external host fixture creates Docker local-driver named volumes with `type=none`, `o=bind`, `device=<canonical fixture path>`, and exact labels:

- `openshell.ai/sandbox-attachable=true`
- `openshell.ai/sandbox-attachable-workspace=jfr-ws-20261024`

OpenShell receives a normal `type=volume` mount through `--driver-config-json`; resource admission remained enabled. Sandbox workspace `jfr-ws-20261024` was created separately. `experiments/full-replacement-20261024/workspace/create-bind-volume-fixtures.sh` creates the volume fixtures; `validate-volume-source.py` checks the source and labels before attachment. Inspects are saved in `results/full-replacement-20261024/workspace/jfr-20261024-ws/volume-*-inspect.json`.

The source validator accepted the exact canonical host checkout and rejected a harmless sibling-directory decoy with the same valid attach/workspace labels (`volume-source-positive.json`, `volume-source-decoy.json`). The decoy was not attached. This means OpenShell's labels authorize an external volume for a workspace; they do not prove that its `device` is the authorized checkout. The retained Jackin host controller must canonicalize the selected checkout, inspect exact volume options and labels, fail closed on any mismatch, and keep Docker volume-control authority away from the agent.

Runtime result: **PASS / EXTERNAL FIXTURE + CONFIGURATION**, only for this local OrbStack host. `jfr24ws-shared-rw` mounted at `/workspace/jfr-20261024-ws/host-source` using this request shape:

```sh
openshell sandbox create --workspace jfr-ws-20261024 \
  --from jfr-20261024-architect-base:7b72b38 \
  --policy experiments/full-replacement-20261024/workspace/architect-workspace-policy.yaml \
  --driver-config-json '{"docker":{"mounts":[{"type":"volume","source":"jfr24ws-shared-rw","target":"/workspace/jfr-20261024-ws/host-source","read_only":false}]}}' \
  --no-tty --detach -- sh -lc 'sleep 600'
```

The custom policy explicitly admits `/workspace` read-write and sets UID/GID 1000. With the default filesystem policy, the `/workspace` mount target was denied with `Permission denied`; the volume is not a policy bypass. Policy used: `experiments/full-replacement-20261024/workspace/architect-workspace-policy.yaml`. The OpenShell identity was `uid=1000(agent) gid=1000 groups=1000`.

- Host file change and atomic `os.replace` were observed immediately by the sandbox; old/new SHA-256 differ.
- Sandbox file creation was observed on the host; a concurrent second sandbox saw that write.
- macOS `kqueue` directory watch received `WRITE` for a file created from the sandbox.
- A host `0444` file remained unchanged after the RW mount write attempt (exit 2, `Permission denied`). A distinct `read_only=true` volume denied file creation (exit 2, `Read-only file system`), and the host path remained absent.
- A symlink to a sibling protected canary resolved on the host, but the sandbox could not read it because only the checkout subtree was mounted.
- Explicit working directory resolved to `/workspace/jfr-20261024-ws/host-source`.
- A volume labeled for `jfr-ws-other24` was rejected for `jfr-ws-20261024` before sandbox creation: `external resource not admitted by required labels`.
- OpenShell stop/start preserved the project bytes. Deleting the sandbox and recreating it with the same external named volume preserved byte-exact bytes (SHA-256 before/after identical; exported bytes compare exit 0).

Detailed evidence: `official-volume-probes.json`, `runtime-filewatch.json`, `architect-readonly-*`, `architect-shared-*`, `retention-*`, `volume-source-*`, `architect-wrong-volume.*`. Some initial raw-bind attempts using the exploratory preview image were rejected before execution; the actual Architect BASE rejection is recorded separately and governs the conclusion.

### Shared, Clone, and Worktree Git

All three paths used a disposable real Git repository and the Architect BASE with Git installed. No workspace contents were uploaded/copied into a sandbox. The host checkout and named volumes are the same live paths.

- **Shared:** Actual Architect BASE ran `git status`, observed host edits, wrote `src/architect-role-write.txt`, and the host read the bytes. After sandbox stop/start the file remained. After deleting and recreating the sandbox with the same labeled volume, it remained and matched the pre-delete exported bytes exactly. Main checkout was unchanged except for fixture edits. Evidence: `architect-shared-git.*`, `architect-shared-lifecycle-status.json`, `retention-*`.
- **Clone:** `jfr24ws-clone` is a separate host clone mounted under the same project-style path. Architect BASE ran status/diff/commit. Commit `38ae5af14bcbd673347a2ff4581e72473a135e0f` appeared in the host clone; main checkout stayed at fixture baseline `30ac5218d0b44565616ab9417905a61bf02ca276`. Deleting/recreating the sandbox with the same volume retained commit and content. Evidence: `architect-clone-*`, `clone-recreate-*`, `retained-git-status.json`.
- **Worktree:** A single project volume at `/workspace/.../worktree` is insufficient because the host `.git` file contains an absolute path to the common `.git/worktrees` metadata. The baseline request failed `git status` with exit 128: `fatal: not a git repository: /Users/.../host-source/.git/worktrees/worktree`. An external fixture workaround added two narrow mounts: the worktree itself at its recorded absolute host path and common `.git` at its original absolute path. Filesystem policy admitted only those exact paths in addition to `/workspace`. Git status, diff, commit and `git rev-parse --git-dir` then worked; commit `202827e99b11e506ec1ec59cccc08a46649474c6` appeared on the host worktree; main checkout remained at its baseline. Runtime deletion/recreation with the same external volumes retained content, HEAD, and worktree metadata. Running `git worktree list` against the host common checkout initially failed Git's dubious-ownership check (host-owned metadata vs sandbox UID 1000); exact one-command `git -c safe.directory=<fixture repo>` succeeded. This exact-path, per-command safe-directory setting is a **WORKAROUND**, not a disabled/global Git safety check. Evidence: `architect-worktree-plain-*`, `architect-worktree-git.*`, `worktree-recreate-*`, `worktree-recreate-list.*`.

The named-volume pattern is not OpenShell-owned storage. The trusted Jackin host layer must own path authorization, volume creation, labels, retention/export, worktree alias layout, and cleanup. Volumes survive sandbox deletion until the host owner removes them. This evidence does not yet demonstrate the current Jackin materializer against OpenShell paths or a complete real workspace account/session journey.

## Identity and resource controls

Probe ran in the actual Architect BASE sandbox as UID/GID 1000:

- Supplementary groups: only 1000.
- `CapInh`, `CapPrm`, `CapEff`, `CapBnd`, `CapAmb`: all zero.
- `NoNewPrivs: 1`.
- `sudo -n id`: fails with sudo's message that NNP prevents running as root.
- `/usr/local/share` write failed due DAC permission denied; `/tmp` write succeeded. This does **not** test Jackin `system_writes`, because that grant removes Docker read-only-rootfs and Capsule session Landlock rules differ. Do not classify system_writes as pass/fail from this path test.
- `--cpu 250m --memory 256Mi` yielded cgroup `cpu.max=25000 100000`, `memory.max=268435456`. A bounded 3-second CPU loop increased throttled periods by 31 and throttled time by about 2.36 seconds. A bounded 512 MiB touched allocation exited 137; cgroup memory events recorded `oom=2`, `oom_kill=1`; sandbox remained Ready. This demonstrates Docker-driver enforcement for these requested CPU/memory settings, not exact Jackin profile budgets or aggregate agent+engine+child budgets.
- cgroup `pids.max=2048` and `/proc/self/limits` open-file soft/hard `20480/1048576` on the default sandbox. Jackin `locked` requires PIDs 512 and nofile 2048; hardened/standard require nofile 8192. These measured defaults do not match `locked`. The docs expose gateway-wide `sandbox_pids_limit`; there is no per-sandbox CLI flag for PIDs or nofile in `sandbox create --help`. Per-profile PIDs/no-file parity is unresolved. Jackin also configures memory reservation, which was not tested as a per-sandbox OpenShell option.

Raw outputs and exit statuses: `profile-identity.*`, `resource-limits-*`, `resource-memory-*`, `resource-cpu-bounded.*`. CPU/memory outcomes are runtime measurements. Requested flags alone were not counted as proof.

## Scope limits

These experiments are not a full profile matrix. They do not prove Jackin's Capsule session wrapper, its Landlock contract, compat/standard system-write semantics, capability grants, network allowlists, sudo provisioning, aggregate resource ceilings, daemon child limits, pull-on-entry, or remote/VM/Kubernetes workspace behavior. Docker child mounts, parallel Jackin worktrees, conflict handling, pull-on-entry and account/session state must be tested separately. Local OrbStack evidence does not imply Docker Desktop or Linux/macOS remote results.
