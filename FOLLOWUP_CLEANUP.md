# Follow-up cleanup and retained artifacts

Cleanup is owned by each experiment fixture. OpenShell sandbox deletion is not credited with removing an external engine, its children, certificates or retained project storage. Read the receipts before reproducing cleanup; historical names and ports must not be reused against another run.

| Owner and resources | Evidence | Outcome |
|---|---|---|
| Root gateway A | `results/full-refactor-20261024/root-gateway-a-cleanup.json`; `experiments/full-refactor-20261024/cleanup-gateway-a.py` | Authenticated empty inventory preceded shutdown. The first cleanup was interrupted after stopping the gateway; write-ahead receipt-based resume removed only its remaining private state. A repeated resume reported already clean. |
| Workspace gateway B, nine sandbox IDs, seven volumes and disposable host Git fixture | `results/full-replacement-20261024/cleanup/cleanup-receipt.md` | Exact resources removed; host fixture hashes/export recorded first. No shared image or cache pruning. |
| Architect/agent and Candidate B session fixtures | `results/full-refactor-20261024/agents/owned-sandbox-cleanup/receipt.json`; `agents/owned-image-cleanup/receipt.json`; `agents/owned-image-cleanup/capsule-root-cleanup-receipt.json` | Recorded sandbox IDs removed. Eleven derived/test tags removed after dependency checks. A final root-Capsule fixture tag was separately identified by its unique label/provisioning log and removed after an exact-ID/zero-consumer check. The pinned Architect base and shared caches remain. |
| External dedicated engines and Docker probes | `results/full-replacement-20261024/docker/cleanup-receipt.md` and `cleanup-commands.md` | Engine survival after sandbox deletion was observed first. Fixture cleanup then removed engines, children, data volumes, certificates and gateway D. This is external-owner cleanup. |
| Linux guest, packaged VM and target probes | `results/full-replacement-20261024/targets/cleanup/` | Owned sandbox, VM/guest, volume, image and private-state cleanup recorded separately. Unrelated preview VMs and caches were preserved. |
| Independent storage/control repeats | `results/full-replacement-20261024/repeat-control/` and independent review receipts | Fresh repeat resources were cleaned by their owner. Primitive repetition does not establish the complete combined journey. |
| Experimental immutable-ID Delete gateway | `results/full-replacement-20261024/patch-delete/run-record.md` and `review.md` | Exact owned resources cleaned; second cleanup found no remaining listener/container. Generated keys and state removed. |
| Verification worker and tmpfs patch | `results/full-refactor-20261024/verification-worker/cleanup/` | Both authenticated gateway inventories were empty before shutdown. Exact processes, two labeled bind-backed volumes, eight derived image tags and private configuration/state were removed with recorded identity checks. The disk reviewer independently confirmed listener/container/volume absence. |

Generated source checkouts, compiled tools and rebuild caches may remain locally for inspection. They are excluded from publication. Source pins, patch diffs, checksums and reproduction procedures replace those large artifacts in the public handoff. The pinned Architect base image is a retained cache, not an orphaned runtime.

The dedicated disk reviewer performed read-only checkpoints and coordinated with active resource owners. Concurrent unrelated workload/cache inventory changed during the research; no causal attribution or cleanup of those resources is claimed. Global Docker pruning and shared-cache removal were not performed.

One abandoned build directory of approximately 14 MiB remains. Automatic approval review rejected the attempted removal: “rm -f style commands are not permitted. Use a safer approach”. No alternative deletion bypass was attempted, and this did not block the experiments.
