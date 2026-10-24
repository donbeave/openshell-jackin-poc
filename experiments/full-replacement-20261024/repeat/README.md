# Fresh storage-path repeat

Purpose: independently repeat the selected bind-backed local named-volume path on OpenShell v0.1.5, with a new gateway, workspace, source tree, volume names, sandbox names and CA. This is a storage primitive repeat only. It is not the combined Jackin journey.

Gateway C: `https://localhost:28472`, OpenShell `0.1.5`, commit `bdb956f2cd65a635f1294fccf1d138d263bf650f`; Docker driver namespace `jfr-20261024-c`. `enable_bind_mounts=true` and resource admission `enabled=true`. Client and server certificates use a fresh experiment CA; no certificate values belong in the result record. Docker context: OrbStack, Linux ARM64 engine. Image digest: `nvcr.io/nvidia/base/ubuntu@sha256:7e0f726d635d440d28a7f18e6498d3bdb76c7038bd4c90a090c21eb7c9f40686` (`linux/arm64`, cached/warm).

Run from the repository root. First create gateway state and certificates using the checked-in setup assets, then run `gateway-c/run.sh` in a terminal. The live experiment commands are saved verbatim in `results/full-replacement-20261024/repeat/repeat-result.json`. Fixture details and exact OpenShell/Docker configuration are in the adjacent result files.

The positive path creates a fresh Docker local-driver volume:

```sh
docker volume create --driver local \
  --opt type=none --opt o=bind \
  --opt "device=$(python3 -c 'import pathlib; print(pathlib.Path("results/full-replacement-20261024/repeat/source").resolve(strict=True))')" \
  --label openshell.ai/sandbox-attachable=true \
  --label openshell.ai/sandbox-attachable-workspace=jfr-ws-repeat24 \
  --label jackin.fixture=jfr-20261024-repeat \
  jfr24repeat-host-rw
```

OpenShell attaches this *volume* at `/workspace/jfr-repeat24/project`, with `experiments/denied.yaml` explicitly allowing that disposable path. A separate raw `type=bind` request uses the same host source and is expected to fail while admission remains enabled. A volume with the wrong workspace label is expected to fail. The test then checks host/agent file exchange, atomic replacement, read-only attachment, and a sibling symlink canary.

Run exact owned-resource cleanup only after reviewing the manifest:

```sh
python3 experiments/full-replacement-20261024/repeat/cleanup-owned-fixture.py
```

The cleanup script checks sandbox UUIDs before name-based OpenShell deletion and rechecks volume driver/options/labels before removing exact Docker volume names. OpenShell v0.1.5 exposes sandbox delete by name in its CLI/curated API; the check and mutation are not atomic. Docker local volumes expose a name plus options/labels, not a separate immutable volume ID. Therefore this repeat does not prove the stronger stale-target protection Jackin needs.

## Results

- **PASS / EXTERNAL FIXTURE + CONFIGURATION:** trusted host fixture created bind-backed local volumes; OpenShell attached the approved volume with admission enabled. Host and sandbox observed each other's changes; atomic host replacement was visible in the running sandbox.
- **PASS / CONFIGURATION:** read-only volume mount rejected sandbox writes (`Read-only file system`).
- **PASS negative / CONFIGURATION:** wrong workspace volume label rejected before sandbox creation.
- **PASS negative / CONFIGURATION:** sibling canary behind `../` symlink was readable from host and returned `ENOENT` from sandbox.
- **FAIL / CONFIGURATION:** direct host bind rejected while admission is enabled (`no trusted label resolver`). This result remains visible; named-volume success does not change it.
- **PASS / cleanup:** sandbox absence confirmed before deleting its workspace; exact volume configuration checked, volumes removed; source bytes exported with SHA-256 manifest.

No Jackin product component created the volume; a trusted host Docker CLI fixture did. Before product use, Jackin must own authorization/canonicalization, volume creation and labels, workspace-to-volume mapping, exact resource bookkeeping, and teardown. Labels do not provide cryptographic identity. This result says nothing about remote gateways, VM, Docker Desktop, Linux hosts, or Kubernetes. It does not cover Capsule, agent accounts, Git mode behavior, image builds, optional Docker development, policy-profile parity, or a combined lifecycle journey.
