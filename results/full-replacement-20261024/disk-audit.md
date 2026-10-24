# Disk usage audit

Read-only audit at 2026-10-24 (UTC). No cleanup executed.

- `/System/Volumes/Data`: 3.6 TiB total, 1.6 TiB used, 2.0 TiB free (44%). User waived disk-policy gate; current free space is ample.
- Follow-up experiment files: 2.3 GiB. Of this, `experiments/full-replacement-20261024/role/jackin-target` is 2.0 GiB, exact pinned-source Rust build target. Other active experiment files include a 112 MiB disposable Linux VM profile, three isolated gateway state directories, generated private test PKI, and role-source checkout. Retain while agents execute and evidence is finalized.
- Docker daemon reports 20.68 GB images (10.22 GB marked reclaimable), 45.72 GB build cache (26.63 GB marked reclaimable), and 2.456 GB named volumes. These are shared-engine totals, not ownership proof. Do not prune: active agents use images/caches, and much of the inventory belongs to unrelated user workloads.
- Active follow-up resources include OpenShell sandbox/supervisor pairs named `jfr24-*`, `jfrws24-*`, exact Docker engine `jfr-20261024-docker-engine` (ID `ee75d2bf466f38e36be26f29c8d046d8f5ea41307639481a5b1278ef2bf4b3f9`), volume `jfr-20261024-docker-data`, three dedicated test gateways, and OrbStack VM `jfr-20261024-linux` (ID `01M5NQEC7J2BYG95SH85TRZHXW`). These remain active test fixtures. Only their assigned owners should clean them after recording immutable IDs and checking no active process uses them.
- `docker system df` lists 33 active containers. Besides current `jfr` resources, output includes unrelated `velnor-*` and `preview-*` workloads. No unrelated container, image, volume, shared cache, user session, or worktree is a cleanup candidate.

Cleanup recommendation: after all tests and independent repeat finish, each fixture owner should remove only exact immutable IDs/volumes/VM and private state listed in its manifest, then verify inventory and disk. No broad `docker system prune`, build-cache prune, `mbx gc`, or user-session pruning is justified by this audit.
