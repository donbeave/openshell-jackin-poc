# Scoped target-fixture cleanup

This is the 2026-10-24 cleanup after parent confirmed the cross-gateway Rust tests had finished. Commands and before/after evidence are under `commands/`; resource snapshots preserve exact IDs and ownership in `resource-snapshot-before.json` and `resource-snapshot-after.json`.

Sequence:

1. Read current sandbox inventories and exact resource labels/IDs. Delete the eight recorded Linux/VM sandbox names through their isolated OpenShell gateways. All delete commands exited 0. Re-list confirmed empty inventories.
2. Observe OpenShell-owned cleanup. Linux Docker child container list became empty; the five supervisor/channel volumes disappeared. Two Jackin named volumes remained with experiment labels. VM sandbox list was empty after deletion.
3. Stop only gateway PIDs whose command lines contained the exact fixture config and whose listeners matched 18470 guest IP, 28472 loopback, and 28473 loopback. Send SIGINT. Recheck showed no listeners. Packaged VM gateways had to be restarted with their isolated config to list/delete records after their earlier process exit; restart re-marked former VM records Error, then exact records were deleted.
4. Remove the two leftover Linux volumes and two host-built derived images by exact inspected names/IDs. Keep shared base images/caches.
5. Verify exact OrbStack machine ID `01M5NQEC7J2BYG95SH85TRZHXW`, then `orbctl delete --force` that ID. Post-delete lookup returned machine-not-found; OrbStack list empty.
6. Remove the two dedicated `/tmp/jfr-20261024-*` VM runtime trees and each profile's own `state`, `config`, and `certs` directories. Keep gateway templates, scripts, READMEs, manifests, and raw evidence.

OpenShell-owned sandbox cleanup did not remove the external named volumes or builder images. Fixture cleanup removed those afterward. This is ownership evidence, not a full Jackin retention/recovery pass.

Unowned workload hashes are in `unrelated-workloads.before.json`, `unrelated-workloads.after.json`, and `unrelated-workload-drift.json`. Shared host Docker container/image hashes changed during adjacent reads (90 to 88 then 78 unrelated container rows; 138 to 137 unrelated image rows). Those inventories were dynamic; no unrelated container IDs were inspected, stopped, or deleted, and no shared caches were pruned. Drift cannot support a byte-identical inventory claim.
