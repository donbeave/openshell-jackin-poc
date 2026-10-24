# Workspace experiment reproduction

These are disposable synthetic Git fixtures for OpenShell v0.1.5 on local macOS ARM64 + OrbStack Linux ARM64. The selected role image is `jfr-20261024-architect-base:7b72b38` (`sha256:e7655072c6d511250b183e9511ca1f701e635766ec0d190a68bfe470745df63a`). Its shell/Git probes do not test agent authentication or a coding task.

## Prerequisites

- A separate OpenShell v0.1.5 gateway and client namespace; current evidence uses gateway B on port 28471.
- Resource admission enabled. Do not disable it to run raw host binds.
- Docker / OrbStack CLI and a disposable host checkout.
- OpenShell filesystem policy explicitly allows the chosen sandbox target.

## Reproduce

From repo root:

```sh
experiments/full-replacement-20261024/workspace/prepare-host-fixture.sh
experiments/full-replacement-20261024/workspace/probe-host-layouts.py
experiments/full-replacement-20261024/workspace/create-bind-volume-fixtures.sh
experiments/full-replacement-20261024/workspace/validate-volume-source.py jfr24ws-shared-rw "$(python3 -c 'import pathlib; print(pathlib.Path("results/full-replacement-20261024/workspace/jfr-20261024-ws/host-source").resolve())')" jfr-ws-20261024
```

Create the OpenShell workspace `jfr-ws-20261024`, then use `--driver-config-json` with a `type=volume` mount and the exact workspace label. `results/full-replacement-20261024/workspace/workspace-execution.md` includes the create command and all tested outcomes. Do not reuse its resource names against another live gateway. For the linked Git worktree, render the exact-path policy with `experiments/full-replacement-20261024/workspace/render-worktree-policy.py`, attach both absolute-path aliases, then use the rendered policy; a simple project mount fails because Git records an absolute common-dir path.

`try-host-bind-admission.sh` is a negative control; it keeps resource admission enabled. The raw bind rejection is expected and is not a pass for live checkout behavior. The bind-backed local volume is an **external fixture**: Jackin's trusted host layer must validate canonical source/options/labels and own creation/retention/cleanup. OpenShell label admission does not check that a volume points to the intended path.

The `probe-official-volume.py` and `probe-runtime-filewatch.py` scripts reproduce filesystem exchange and host-watch events using the earlier official base / current disposable fixture. Role-base Git, lifecycle, profile, read-only, and admission results are saved as separate raw files to avoid merging unlike paths. `results/full-replacement-20261024/workspace/workspace-execution.md` is the interpretation and scope ledger.
