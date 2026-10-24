# Post-cleanup verification

Date: 2026-10-24. Read-only checks except the explicitly authorized exact-volume removal recorded in `supervisor-volume-cleanup.json`.

## Experiment resource audit

- No Docker containers or image tags named `ojp-20261024-*` remain.
- No Docker named volumes named `ojp-20261024-*` remain.
- No listener remains on ports 18770 or 18771.
- Experiment gateway certs, `certs-b`, SQLite state/encryption key, VM certs, and engine private fixture cert directory are absent.
- Scanned all remaining 11 Docker containers, 59 volumes, 122 images, and 4 networks. No labels contain an old sandbox UUID or sandbox name from `orphan-pre-removal.json`.
- Scanned all 122 image labels for the old sandbox UUIDs; no match.
- All 12 old sandbox `openshell-channel-*` volumes are absent and have zero Docker container references.
- Found 12 paired `openshell-supervisor-*` volumes. Each carried labels `openshell.ai/sandbox-id=<old UUID>`, `openshell.ai/sandbox-namespace=default`, `openshell.ai/managed-by=openshell`, and `openshell.ai/isolation-backend=openshell-sandbox`; no current container referenced any. They were removed one by one after immediate label and reference rechecks. Exact names, old container IDs/names, labels, commands, exit statuses, and free-byte readings are in `supervisor-volume-cleanup.json`. This was **script-owned cleanup**, not OpenShell-owned cleanup. No volume data was read.
- Removed supervisor volumes had 4.167 kB Docker-reported size each (about 50 kB total); host free space moved from 2,049,317,593,088 bytes to 2,049,319,514,112 bytes during cleanup.

No OpenShell-created image or snapshot artifacts with old sandbox UUID/name labels remain. No old UUID/name labels remain on any inspected Docker resource. Unrelated/shared images, volumes, networks, caches, and gateway resources were preserved.

## Preserved workloads and collateral

- OpenShell `preview-vm` remains `Ready`; readiness condition `True`. Existing OpenShell gateways on ports 17670 and 17671 and VM driver/supervisor processes remain alive. Process arguments were not printed.
- Three pre-existing Docker workloads remain exited with status 137 and `OOMKilled=false`: `openshell-default--coding-agents-00000000-0000-4000-8000-000000000001` finished `2026-10-23T22:14:39.212323112Z`; `openshell-default--preview-openrouter-00000000-0000-4000-8000-000000000003` finished `2026-10-23T22:14:39.430047836Z`; `openshell-default--preview-docker-00000000-0000-4000-8000-000000000002` finished `2026-10-23T22:14:39.305476094Z`. These stop times predate top-level cleanup. No restart or mutation performed; restoration awaits approval.

## Disk space

Top-level cleanup script recorded 2,037,538,013,184 bytes before and 2,045,334,794,240 bytes after. Its execution record warns that concurrent activity prevents sole attribution. Latest observed free space after exact supervisor-volume cleanup: 2,049,295,106,048 bytes. Concurrent experiment, VM, and system activity prevents attributing the full change to cleanup.

## Continued cleanup scan

Follow-up after final cleanup found no experiment-prefixed containers, image tags, named volumes, listeners on 18770/18771/18779, or temp certificate/key files in the temporary roots. The collateral diagnostic report says its temporary authenticated CLI profile was removed. A 24-hour filename scan for `.key`, private `.pem`, `.p12`, `.pfx`, client `.pem`, and credential JSON in `/private/var/tmp` and `$TMPDIR` found zero files. No `ojp`, OpenShell, or collateral diagnostic temp directory remained. Other `jackin-*`/application temp paths and user/task artifacts remain unidentified or outside this experiment; preserved. No new safe removal candidate found. Latest free space: 2,103,098,765,312 bytes at the final query; this is an observation, not cleanup attribution.

## 2026-10-24 06:16 +07 preservation update

Approved restoration now complete. Read-only Docker label checks matched each original sandbox UUID in `results/collateral/restoration-verification.json` to exactly two running containers: one sandbox and one supervisor. API verification records all three original sandboxes Ready, and the safe exec marker exited 0. Exact IDs remain `coding-agents` `00000000-0000-4000-8000-000000000001`, `preview-docker` `00000000-0000-4000-8000-000000000002`, and `preview-openrouter` `00000000-0000-4000-8000-000000000003`. The prior stopped observations above remain historical; they predate approved restoration.

`preview-vm` remains Ready with readiness condition True. Gateways on 17670 and 17671 and VM driver/supervisor processes remain present. No listener on 18770, 18771, or 18779. No `ojp-20261024` Docker container, image tag, named volume, private-key file, or experiment private-key directory remains. No safe new cleanup candidate found. Latest free space: 2,093,886,783,488 bytes; concurrent activity prevents attribution.
