# Scoped Docker experiment cleanup receipt

Date: 2026-10-24. Scope: this Docker experiment's labeled external engines, Gateway-D resources, and exact Docker sandboxes listed below. No global prune, historical cleanup script, unrelated gateway state, role-owned image, or shared cache cleanup ran.

## Sandbox deletion first, external ownership observed

First action deleted OpenShell sandbox `jfr24-native3`, immutable ID `e146946e-666f-44b9-94f2-ebd1f3882b77`; CLI exit 0 reported “deletion accepted; cleanup is pending.” Immediately afterward, the external Engine B remained reachable using its host-owned mTLS client certificate. It returned the same engine ID `253d0666-9d55-4dc5-b165-733d2eb778e4`, retained Redis and nginx images, and had no child containers or named volumes. Engine A also remained reachable with the same engine ID `e6e98353-9c27-4c22-a966-1eb0b8821bc7`; it retained exited child `jfr24-dk-child` ID `f05cde27924fd33aa4354a30b38f777188b269fa84f52fbe445d150c6b88ba33` and volume `jfr24-dk-child-volume`. Host-owned cert directories and engine data volumes remained. This confirms OpenShell sandbox deletion did not own or remove the external fixtures.

Then deleted the remaining five Gateway-D Docker sandboxes from the pre-cleanup inventory: `jfr24-rust-b`, `jfr24-native-tc`, `jfr24-native2`, `jfr24rootless2`, `jfr24rootless3`. Each deletion command exited 0 and reported cleanup accepted. Final Gateway-D list is empty. Raw exact IDs and commands/results: `cleanup-sandboxes.tsv`, `cleanup-delete-*.{stdout,stderr,exit}`, `cleanup-gateway-d-list-final.json`.

Gateway A pre-cleanup inventory identified ten Docker sandboxes by immutable ID. All ten were deleted after get-name/get-ID checks and CLI exit 0: `jfr24-dk-off`, `jfr24-dk-off2`, `jfr24-dk-cli`, `jfr24-dk-on`, `jfr24-dk-on2`, `jfr24-dk-on3`, `jfr24-dk-on4`, `jfr24-dk-noauth`, `jfr24-dk-b`, and `jfr24-dk-xa`. `jfr24-dk-off2`, ID `a4cac7a0-2784-42a6-be2f-17217d97477c`, was excluded from decisive evidence but deleted as an owned sandbox. Its unrelated preview image was retained. Gateway A remains running. Final Gateway-A inventory is empty, and no Docker container labels refer to any of its ten sandbox IDs. Inventory source: `../root-gateway-a-precleanup.json`; cleanup IDs/status: `cleanup-gateway-a-sandboxes.tsv`, `cleanup-gateway-a-delete-*.{stdout,stderr,exit}`, `cleanup-gateway-a-delete-off2.*`; final list `cleanup-gateway-a-inventory-final.tsv`.

## External resource cleanup

Before deletion, exact outer container IDs and ownership labels were verified:

- Engine A: `ee75d2bf466f38e36be26f29c8d046d8f5ea41307639481a5b1278ef2bf4b3f9`, `ojp.owner=followup-docker-engine`, Docker image `docker:29.8.2-dind@sha256:1e08cdb63405ca788aea94ef35b792d1e299607c667d33d7bcbcae1fd2611ced`, API `127.0.0.1:28480`.
- Engine B: `ec449dfdada098f2831f8d38ce9459d725e182e913e50476d4722f530ed6660c`, `ojp.owner=followup-docker-engine-b`, same pinned DinD image, API `127.0.0.1:28481`.

After all OpenShell sandboxes were deleted, removed Engine A's exited child and named volume through its mTLS API, then stopped and removed both outer containers by immutable ID after rechecking owner labels. Removed host volumes only after checking labels and no container attachments: `jfr-20261024-docker-data` (A), `jfr24-docker-b-data` (B), and approved host-bind fixture volume `jfr24-dk-host-project`. Removed exact outcomes and exit statuses are in `cleanup-engine-*-{remove-child,remove-child-volume,stop,rm}.*` and `cleanup-volume-*.rm.*`.

The host project fixture `results/full-replacement-20261024/docker/host-source/` remains as evidence. It is not engine data and is not deleted. No shared images were pruned.

## Gateway and generated secrets

Stopped only Gateway-D PID 39112 after verifying its command referenced this fixture's `gateway-d/gateway.toml` and port 28610; exit 0. `lsof` showed no listener afterward. Removed only generated Engine A/B mTLS directories `experiments/full-replacement-20261024/docker/private/` and `private-b/`, and this fixture's Gateway-D `config/`, `state/`, `certs/`, and `gateway.toml`. All removals exited 0. Kept `gateway-d/client.sh`, `run.sh`, `setup.sh`, and the experiment result logs; `setup.sh` can regenerate an isolated Gateway-D state.

Removed our unique no-agent Docker tools image by exact ID `sha256:db4bc2b50ccb48f25a8563ee4156953e6dfdbe4f3ad4c1bb138c6cefd0926239` after confirming no containers referenced it. Kept the role-owned Architect images, the official rootless image cache, and other shared Docker caches. Role agent was told its image was no longer used by my tests.

## Final resource inventory

- Gateway D: stopped; port 28610 has no listener; final sandbox list empty; generated private config/state/cert files removed.
- Gateway A: still running; no sandboxes remain in the final inventory.
- External engine A/B outer containers and owned data/workspace volumes: absent.
- Owned labels `followup-docker-engine` and `followup-docker-engine-b`: no containers or volumes remain.
- Ports 28480, 28481, 28610: no listener after cleanup.
- Owned supplemental image ID: absent. Shared/role images and caches: retained.
- Host-source project and evidence: retained.

Final inventories: `cleanup-gateway-{a,d}-inventory-final.tsv`, `cleanup-owned-engine-{a,b}-{containers,volumes}-final.txt`, `cleanup-test-ports-final.txt`, `cleanup-images-final.txt`, `cleanup-private-dirs-final.txt`, and `cleanup-gateway-d-dirs-final.txt`.
