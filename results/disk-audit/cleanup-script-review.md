# Cleanup script ownership review

Read-only review, 2026-10-24. No resources changed.

## Urgent issue

`cleanup.sh` sends SIGTERM to the experiment gateway PID whose command contains `experiments/gateway/gateway.toml`, then sleeps one second and removes `experiments/gateway/certs`, `state`, and `config`. It does not verify the listener/process exited before deleting files it may still use. A slow shutdown can leave a live listener with its credentials/state removed.

Recommended gate: after SIGTERM, poll `lsof -tiTCP:18770 -sTCP:LISTEN` and verify each returned PID's command still matches this experiment gateway path. Wait with a bounded timeout. Abort before removing certs/state/config if the owned listener remains.

## Other inspected scopes

- Top-level Docker container selection uses exact experiment prefix `ojp-20261024-` or the corresponding `openshell-default--ojp-20261024-` prefix.
- Volume deletion checks remaining Docker container references and uses recorded mounts plus the unique prefix.
- Agent image cleanup is restricted to repository tags beginning `ojp-20261024-agent:`.
- Engine cleanup names exact fixtures `engine-a`, `engine-b`, `sock`, `interrupted`, their explicit volumes, and the named network endpoint. It removes only experiment `private` credentials and the bundled fixture tar.
- VM cleanup verifies its exact experiment path; it waits for sandbox, VM, driver, and listener termination before deleting VM state and certificates. Its config and logs remain in results.

Top-level `cleanup.sh` has not yet been executed at this review.

## Pre-cleanup external workload baseline

Observed before top-level cleanup:

- OpenShell gateway listeners `127.0.0.1:17670` (PID 19896) and `127.0.0.1:17671` (PID 31366) both listened.
- `openshell --gateway openshell-vm sandbox list --output json` returned unrelated sandbox `preview-vm`, phase `Ready`; its guest/driver/supervisor processes were running. No process command-line arguments were printed.
- Existing Docker sandboxes `openshell-default--preview-openrouter-*`, `openshell-default--preview-docker-*`, and `openshell-default--coding-agents-*` were already exited with status 137. Their state predates the cleanup check; they were preserved.
