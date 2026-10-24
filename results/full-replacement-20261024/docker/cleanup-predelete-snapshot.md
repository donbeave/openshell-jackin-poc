# Before first OpenShell sandbox deletion

- Selected sandbox: `jfr24-native3`, ID `e146946e-666f-44b9-94f2-ebd1f3882b77`, owner `followup-docker-native3`; the successful Testcontainers run used external Engine B.
- Engine B outer container: ID `ec449dfdada098f2831f8d38ce9459d725e182e913e50476d4722f530ed6660c`; owner label `followup-docker-engine-b`; published only `127.0.0.1:28481` API and test service ports; data volume `jfr24-docker-b-data`; mTLS host fixture files under `experiments/full-replacement-20261024/docker/private-b/`.
- Before deletion, B's mTLS API reported engine ID `253d0666-9d55-4dc5-b165-733d2eb778e4`, empty child-container list, retained Redis 7.4 and nginx 1.29.3 images, no inner named volumes. Host Docker reported data volume label `ojp.owner=followup-docker-engine-b`.
- Engine A outer container: ID `ee75d2bf466f38e36be26f29c8d046d8f5ea41307639481a5b1278ef2bf4b3f9`; owner label `followup-docker-engine`; API published `127.0.0.1:28480`; inner engine ID `e6e98353-9c27-4c22-a966-1eb0b8821bc7`; exited child `jfr24-dk-child` ID `f05cde27924fd33aa4354a30b38f777188b269fa84f52fbe445d150c6b88ba33`; named volume `jfr24-dk-child-volume`; outer data volume `jfr-20261024-docker-data`.
- B mTLS cert source and A mTLS cert source were read-only mounts of the experiment's `private-b` and `private` dirs. `cleanup-private-inventory.txt` records paths, mode, and byte size without key values.

Raw inventories: `cleanup-sandbox-list-before.json`, `cleanup-sandboxes.tsv`, `cleanup-engine-{a,b}-owned-containers.txt`, `cleanup-engine-{a,b}-owned-volumes.txt`, `cleanup-engine-{a,b}-query.stdout`, `cleanup-engine-a-{children,images,volumes}.*`, and `cleanup-host-volumes.json`.
