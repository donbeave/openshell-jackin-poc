# Gateway namespace isolation diagnostic

Date: 2026-10-24 local (gateway log UTC: 2026-10-23)

## Released configuration

OpenShell v0.1.5 exposes Docker `sandbox_label` under `[openshell.drivers.docker]`. Its Docker driver uses that value as the `openshell.sandbox_namespace` container label and filters managed resources by that label. The default is `default`. There is no gateway-level `namespace` field in the v0.1.5 gateway TOML schema.

Source inspected: [v0.1.5 Docker driver](https://github.com/NVIDIA/OpenShell/blob/v0.1.5/crates/openshell-driver-docker/src/lib.rs), [`DockerComputeConfig`](https://github.com/NVIDIA/OpenShell/blob/v0.1.5/crates/openshell-driver-docker/src/lib.rs#L163-L186), and its default/filter code. This is source evidence, not the runtime result below.

## Runtime reproduction

Before this test, both the installed gateway on `127.0.0.1:17670` and the experiment gateway on `127.0.0.1:18770` used the default Docker namespace. The installed gateway log showed its `reconcile.sandboxes` pass calling stop on an experiment sandbox after the workload had already exited. This established cross-gateway resource interference, but did not explain the workload's first termination signal.

Changed only the experiment gateway's Docker label to a unique value:

```toml
[openshell.drivers.docker]
allow_driver_config = true
sandbox_label = "ojp-20261024"
```

Restarted only the isolated `:18770` gateway, retaining its mTLS and launch JWT configuration. It started with OpenShell v0.1.5 and connected to the existing OrbStack Docker engine. The Homebrew gateway and VM gateway were not restarted or modified.

Created a uniquely named, approved external volume and sandbox:

```sh
docker volume create \
  --label openshell.ai/sandbox-attachable=true \
  --label openshell.ai/sandbox-attachable-workspace=default \
  ojp-20261024-gwlabel-vol

bash experiments/os.sh sandbox create \
  --name ojp-20261024-gwl \
  --from ojp-20261024-agent:2.1.310 \
  --driver-config-json '{"docker":{"mounts":[{"type":"volume","source":"ojp-20261024-gwlabel-vol","target":"/workspace/ojp-project","read_only":false}]}}' \
  --cpu 1 --memory 2Gi --no-auto-providers --detach -- sleep infinity
```

The create command exited 0. At 47 seconds, sandbox phase was `Ready`; Docker reported the workload and supervisor running, workload health `healthy`, and `OOMKilled=false`. Docker labels showed `openshell.ai/sandbox-namespace=ojp-20261024`. Evidence is in [`gateway-unique-label-create.json`](../engine/gateway-unique-label-create.json) and [`gateway-unique-label-after-47s.json`](../engine/gateway-unique-label-after-47s.json).

## Interpretation and caveats

This confirms namespace collision avoidance for a mounted sandbox on the shared local engine: once the experiment gateway used a distinct `sandbox_label`, the workload remained running past the prior ~12-second failure window while the installed default gateway was still present. The unique label prevents default-namespace reconciliation from claiming the sandbox. It does not establish why the earlier workload first received termination, nor does it establish isolated daemon ownership or automatic cleanup of external resources.

The restarted test gateway reused its experiment SQLite state, which had records for old default-namespace test sandboxes. On startup, the new namespace correctly found no corresponding backend resources and removed those stale rows from this gateway's database. Its observed Docker resources were not removed by that reconciliation. Existing gateway state was not modified. The prior failure records remain preserved.

Result: **PASS** for avoiding this observed cross-gateway namespace collision; mechanism: **CONFIGURATION**. No OpenShell source patch or security relaxation was used.
