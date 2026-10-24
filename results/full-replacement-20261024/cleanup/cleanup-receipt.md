# Workspace/profile and gateway-B cleanup receipt

Cleanup owner: workspace/Git/profile probe (`jfr-20261024-ws`) and isolated gateway `jfr-20261024-b` only.

## OpenShell sandboxes

Gateway B was restarted only to use its own recorded client config for resource deletion. The CLI `GetSandbox(name, workspace)` response was saved per sandbox and checked against the expected immutable ID, name, and workspace before the release's name-only delete operation. All nine checks matched. The delete script aborts on any mismatch or command failure.

| Sandbox ID | Name | Result |
| --- | --- | --- |
| `dfb460f3-edd1-41a0-ac19-c54d075056d0` | `jfrws24-official` | Deleted |
| `303ea70d-e938-43bc-98f8-b1a925de1edf` | `jfrws24-official2` | Deleted |
| `f9d3d764-a34d-44bc-b3d3-942bc340b4fb` | `jfrws24-officialro` | Deleted |
| `6a1be9be-9e5f-423f-b47d-6ed730cca481` | `jfrws24-limits` | Deleted |
| `a342d346-5bea-42eb-ac71-f829224ea436` | `jfrws24-recreat` | Deleted |
| `52abba42-0002-4144-8645-0dc436fe873e` | `jfrws24-rorole` | Deleted |
| `202b7bca-03cd-42e7-8afc-9ba4adcb0abe` | `jfrws24-wtplain` | Deleted |
| `e4b4992c-b152-4cb5-8c44-d33f6601f733` | `jfrws24-cloner` | Deleted |
| `c030e1a5-7a8a-4fd9-b114-d9ed3a04ef0e` | `jfrws24-wtrecr` | Deleted |

Before evidence: `gateway-b-list-before-delete.json` and `get/*.json`. After evidence: `gateway-b-list-after-delete.json` has an empty sandbox list. Docker inspection after deletion found no containers with namespace `jfr-20261024-b`; see `gateway-b-docker-containers-after.txt`.

## Host workspace fixtures and external volumes

After sandbox deletion, Docker showed no remaining containers attached to the seven exact workspace volumes. Their saved inspections were checked for the expected local driver, `type=none`, `o=bind`, fixture labels, and source paths before removal. The volumes removed were:

`jfr24ws-clone`, `jfr24ws-common-git`, `jfr24ws-decoy-validlbl`, `jfr24ws-shared-ro`, `jfr24ws-shared-rw`, `jfr24ws-worktree`, and `jfr24ws-wrong-ws`.

The unrelated `jfr24verify-*` volumes were not touched. `workspace-volume-list-after.txt` is empty for the workspace fixture label; `workspace-volume-delete.stdout` records the seven Docker removals.

The disposable checkout and its three Git directories were removed from `results/full-replacement-20261024/workspace/jfr-20261024-ws` after producing `workspace-fixture-tree-hashes.json` (189 file, directory, and symlink entries). The byte export and before/after SHA-256 records remain in the workspace results. The tested retained file's pre-delete and post-recreation SHA-256 values match (`74662a530144fdda9cd0b979be93deb6e5b6fce6855a579e3266baf1744543db`); its 21-byte exported copy remains at `../workspace/retention-host-export.bin`.

## Gateway B process and private state

The gateway process used PID 65580. The recorded process command identified the executable, exact gateway-B config path, and port `28471` (`gateway-b-before-stop.txt`). It was sent SIGTERM after sandbox deletion; no process remained and no listener remained on port 28471 (`gateway-b-after-stop.txt`, `gateway-b-listener-after-stop.txt`). An initial extra command predicate expected the gateway ID in argv, although the gateway ID is configured in TOML; that predicate failed, but did not stop the subsequent SIGTERM command. The process identity was independently confirmed by the full saved command before termination.

Removed isolated gateway-B `certs/` (CA, server/client credentials, JWT signing key), `state/` (gateway runtime database/state), and `config/` (isolated client registration), plus generated active `gateway.toml`. A non-secret file-name/size inventory is `gateway-b-private-state-inventory.json`; the prior TOML configuration is preserved as `gateway-b-config-before-cleanup.toml`. Setup scripts remain and can generate fresh private credentials and gateway state. No global OpenShell client configuration was modified.

## Scope and remaining resources

The sandbox IDs above, their supervisor containers, the seven fixture volumes, the disposable Git checkout, and gateway-B private runtime state were removed. The worktree experiment scripts, policies, raw execution logs, source audits, image/build caches, and shared engine were kept. No shared cache or image was pruned. Historical preview resources were outside this cleanup and are recorded as already stopped/deleted in the original execution report.
