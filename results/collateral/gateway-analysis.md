# Collateral gateway diagnosis

**Scope:** read-only diagnosis of the original Homebrew OpenShell gateway and authentication path. No original gateway file, selected-gateway registry, service, or workload was changed or restarted. No workload was started. Temporary authenticated CLI profile was removed after the probe.

## Workload state and event evidence

`original-workload-states.json` records three pre-existing Docker containers as exited with code 137 and `OOMKilled=false`, with finish times clustered within 218 ms at 2026-10-23 22:14:39 UTC:

- `openshell-default--coding-agents-00000000-0000-4000-8000-000000000001`
- `openshell-default--preview-openrouter-00000000-0000-4000-8000-000000000003`
- `openshell-default--preview-docker-00000000-0000-4000-8000-000000000002`

The captured Homebrew gateway log sequence is: each sandbox supervisor stream ended around 22:14:28; Docker reported supervisor-container exit status 137 around 22:14:29; the gateway changed phase from Provisioning to Error (`Sandbox failed to become ready`); then around 22:14:39 it logged `Stopped Docker sandbox after control supervisor failure`. This establishes the gateway's stop action happened after the supervisor failure. It does **not** establish who first terminated the supervisor containers or prove the initiating cause. The Docker state says not OOM-killed. Attribution of the initial signal remains unresolved.

The earlier test-gateway configuration used the default `sandbox_label=default`, matching the installed gateway. The collateral time window overlaps the reported test activity, and a separate recorded namespace test later confirmed that two gateways sharing the default namespace can reconcile across one another. However, the retained :18770 startup log begins at 22:28:09Z, after these exits, and the initial gateway startup log was not retained. The exact test-gateway start time and causal link for these three exits remain unproven. Do not present namespace collision as established cause.

## Original gateway and certificate findings

- Original endpoint: `https://localhost:17670`, OpenShell 0.1.5, Docker driver.
- Original service command uses `/opt/homebrew/var/openshell/gateway.toml`; that config has only `[openshell] version = 2` and `[openshell.gateway]`.
- Installed service certificate material is under `/opt/homebrew/var/openshell/tls/`; the service launcher copies the CA and client cert/key into `~/.local/state/openshell/homebrew/tls/`.
- The installed server certificate and installed client certificate both verify with `/opt/homebrew/var/openshell/tls/ca.crt` (`openssl verify`: `OK`). The installed client identity is `CN=openshell-client, OU=openshell-user`, SHA-256 fingerprint `7D:7C:8F:8A:47:B3:0D:22:33:2E:11:68:0E:67:71:DC:C5:0D:5A:BD:96:39:C7:BB:A3:55:6A:1C:A6:8D:03:1B`.
- The registered user CLI profile at `~/.config/openshell/gateways/openshell/mtls/` contains a different CA and client certificate. Its client cert fingerprint is `B2:2F:00:73:DE:2E:00:3F:2C:46:A0:DB:CB:C3:47:10:7F:0A:D2:51:90:C9:2B:A4:93:AD:86:52:5C:F6:15:9B`; verification against the installed CA fails with `error 20 ... unable to get local issuer certificate`. The normal registered CLI request fails TLS peer verification with `BadSignature`. This is a certificate/profile mismatch before API authorization, not evidence of rejected sandbox permissions.

## Authenticated owner API probe

A temporary isolated `XDG_CONFIG_HOME` was populated with copies of the three installed client trust files (`ca.crt`, `client/tls.crt`, `client/tls.key`) under `openshell/gateways/openshell/mtls/`; key permissions were set to 0600. The command sequence was:

```sh
XDG_CONFIG_HOME="$probe/config" openshell gateway add --local --name openshell https://localhost:17670
XDG_CONFIG_HOME="$probe/config" openshell --gateway openshell gateway info
```

Observed: registration succeeded, then `gateway info` returned `Status: healthy`, `Version: 0.1.5`, and Docker driver version `0.1.5`. Exit status 0. TLS verification remained enabled; no insecure flag was used. A read-only `sandbox list -o json` also succeeded with exit status 0. It returned these three names and IDs, each in phase `Error` and with condition reason `ControlSupervisorExited` / message `Docker supervisor container exited with status 137`: `preview-docker` (`00000000-0000-4000-8000-000000000002`), `preview-openrouter` (`00000000-0000-4000-8000-000000000003`), and `coding-agents` (`00000000-0000-4000-8000-000000000001`). The temporary profile was removed. This gives the operator a safe authenticated API route: use an isolated temporary CLI profile populated from the installed gateway's own client CA/certificate/key. It does not alter the global CLI selection or stored credentials.

## Temporary owner-profile recipe

Only if an authorized operator needs the original gateway API, create a temporary directory and copy the installed owner identity into its local gateway profile. Never put the private key in evidence, logs, this repository, or a persistent CLI profile. Use mode 0600 for the key and remove the temporary directory when done:

```sh
profile=$(mktemp -d /tmp/ojp-owner.XXXXXX)
mkdir -p "$profile/config/openshell/gateways/openshell/mtls"
cp /opt/homebrew/var/openshell/tls/ca.crt "$profile/config/openshell/gateways/openshell/mtls/ca.crt"
cp /opt/homebrew/var/openshell/tls/client/tls.crt "$profile/config/openshell/gateways/openshell/mtls/tls.crt"
cp /opt/homebrew/var/openshell/tls/client/tls.key "$profile/config/openshell/gateways/openshell/mtls/tls.key"
chmod 600 "$profile/config/openshell/gateways/openshell/mtls/tls.key"
XDG_CONFIG_HOME="$profile/config" openshell gateway add --local --name openshell https://localhost:17670
XDG_CONFIG_HOME="$profile/config" openshell --gateway openshell sandbox list -o json
```

The probe used only list/info operations. Restoration/start is a separate state-changing operation and was not run here.

## Recovery boundary

The authenticated owner API path is available for inspecting and operating known sandbox IDs. Any restoration should be a deliberate action by the primary operator, with IDs checked against `original-workload-states.json`; this diagnostic did not invoke start, restart, Docker start, or gateway restart. The original workloads' saved state was exited, so their previous process state cannot be reconstructed by this report.

## v0.1.5 lifecycle source review and guarded plan

The exact v0.1.5 server lifecycle source confirms the safe order for these retained `Error` records. `StopSandbox` accepts phase `Error` and intentionally invokes the normal compute-driver stop and supervisor-session cleanup; the source comment says an `Error` state does not prove compute has stopped. `StartSandbox` permits `Stopped`, `Completed`, `Starting`, or a failed main-process result (plus a timed-out provisioning recovery); a `ControlSupervisorExited` error is not a failed main-process result, so a direct start is rejected with a failed-precondition message directing the caller to stop first. Thus the API sequence is `stop` → wait `Stopped` → re-read and verify the same ID → `start` → wait `Ready`.

Source references: [v0.1.5 compute lifecycle implementation](https://github.com/NVIDIA/OpenShell/blob/v0.1.5/crates/openshell-server/src/compute/mod.rs#L1833-L1843) and [v0.1.5 start phase guard](https://github.com/NVIDIA/OpenShell/blob/v0.1.5/crates/openshell-server/src/compute/mod.rs#L2033-L2065). The RPC handler authorizes `StartSandbox` against workspace and sandbox name before calling the compute lifecycle: [v0.1.5 gRPC handler](https://github.com/NVIDIA/OpenShell/blob/v0.1.5/crates/openshell-server/src/grpc/sandbox.rs#L1799-L1834).

SDK inspection used `uv run --with openshell==0.1.5`; no global SDK install was made. SDK `TlsConfig` accepts direct `Path` values for CA, client cert, and key; `SandboxClient` accepts the gRPC endpoint as `host:port` and TLS config. `SandboxClient.start`, `stop`, `get`, `wait_stopped`, and `wait_ready` are available. The SDK source is [v0.1.5 Python sandbox client](https://github.com/NVIDIA/OpenShell/blob/v0.1.5/python/openshell/sandbox.py).

A guarded, unexecuted plan is in [`experiments/collateral/restore-originals.py`](../../experiments/collateral/restore-originals.py). It uses the installed certificate paths directly, refuses to run without `--approved`, preflights all three exact IDs and `ControlSupervisorExited` states, rechecks identity/phase before each lifecycle change, uses only public OpenShell API stop/start operations, waits for `Stopped` and `Ready`, and writes state/action evidence without printing key bytes. No restore action has been run. The script passed an AST syntax parse and its SDK type/phase names were checked against the 0.1.5 package. Those checks do not prove restoration will succeed; readiness is only established if the authorized runtime execution succeeds.

## Authorized restoration completed

The user explicitly authorized corrective actions. The prepared guarded script was executed with `uv run --with openshell==0.1.5 python experiments/collateral/restore-originals.py --approved`. It used the existing installed gateway mTLS key paths directly, verified all target IDs/states before mutation, performed Stop then Start through the public SDK, and waited for Ready. No global registered certificate files were edited, private keys were not copied, and no TLS check was disabled. `restore-originals-execution.json` records all actions and PASS. `restoration-verification.json` records the same three sandbox IDs in Ready with harmless non-login-shell exec status 0 and expected stdout for each. The incident cause remains unproven; restoration does not retroactively establish the initiating actor.

Restoration verifies current Ready/exec state and unchanged sandbox IDs. Original in-memory sessions and in-flight commands were not recovered or verified; no claim is made about their continuity.
