# Verification-worker resource cleanup

Cleanup was limited to resources owned by the verification-worker experiments.

- OpenShell inventories on dedicated gateways 28630 (`jfr-20261024-verify`) and 28631 (`jfr-20261024-vpatch`) were both empty over verified mTLS before shutdown.
- Gateways were stopped only after checking exact process PID, config path, and listener ownership. Both listeners are now absent. See `gateway-processes-before.txt`, `gateway-stop-receipts.txt`, and `final-cleanup-verification.txt`.
- Exactly two local volumes were removed after checking their names, unique fixture labels, driver, bind device, and `type=none,o=bind` options: `jfr24verify-candidate` and `jfr24verify-bundle`. Pre-cleanup full metadata and removal receipts are preserved.
- Eight exact derived tags under `jfr-20261024-verify-worker:*` were removed after comparing each image ID with the recorded pre-cleanup list. Shared base images and shared caches were left intact.
- Private certs, isolated gateway config state, and OpenShell gateway SQLite state for these two gateways were removed after listener shutdown. Their paths, byte counts, and absence receipts are in `private-state-cleanup.json`.
- No worker-labeled Docker containers were present at inventory time. No broader container or image prune was run.
