# macOS ARM64 VM profile result

## Environment and versions

The exact host release record is [`host-os.json`](host-os.json); the gateway TOML and captured startup log are preserved in [`gateway-config.toml`](gateway-config.toml) and [`gateway-startup.log`](gateway-startup.log). The libkrun process arguments confirming effective vCPU/memory values are in [`vm-launcher-before-delete.txt`](vm-launcher-before-delete.txt).

- Host: macOS 27.0.1, build `26A434`, arm64 (Apple Silicon); raw `sw_vers` output is in [`host-os.json`](host-os.json). Docker endpoint is the existing OrbStack engine. No host Docker runtime was used for VM children.
- OpenShell CLI, gateway, and VM driver: 0.1.5; source release commit `bdb956f2cd65a635f1294fccf1d138d263bf650f`.
- VM backend: packaged `openshell-driver-vm` 0.1.5 with packaged libkrun/Hypervisor.framework path. The host already had a cached guest bootstrap rootfs and overlay template under the separate existing `preview-vm` profile; the new experiment used a dedicated runtime state/cache and prepared its own bootstrap and image disks.
- Host image: `ojp-20261024-agent:2.1.310-poc-v3`, ID/digest `sha256:88b9118075feb284f28b34bb8baa4568aff8ab75c22022441e52a37079049ba4`, Linux arm64.
- Guest sandbox name/ID: `ojp-20261024-vm1` / `c87a19b1-d941-4e22-a9cc-68d00be18b0f`. It ran under VM driver state `experiments/gateway-vm/state/runtime`, not Docker.
- Gateway endpoint/name: `https://localhost:18771` / `ojp-20261024-vm`; mTLS and launch-scoped JWT enabled with credentials unique to this profile.
- Resource request and effective configuration: create passed `--cpu 1 --memory 2Gi`, but the [v0.1.5 runtime documentation](https://docs.nvidia.com/openshell/v0.1.5/how-it-works/sandboxes/runtimes) says MicroVM ignores those CLI CPU/memory requests. The gateway config set `vcpus = 2`, `mem_mib = 2048`, and `overlay_disk_mib = 4096`; the libkrun launcher process confirmed `--vm-vcpus 2 --vm-mem-mib 2048`. Thus actual configured allocation was 2 vCPUs, 2048 MiB guest memory, and 4 GiB writable overlay. Combined host+guest utilization was not sampled. This profile does not provide per-sandbox CPU/memory limits through the generic CLI; use VM gateway-wide config, which applies its fixed values to each sandbox.

## Setup result

`openshell-gateway config preflight --path experiments/gateway-vm/gateway.toml` initially failed with `inspect /usr/local/bin/mke2fs: Permission denied`. The user shell has a protected `/usr/local/bin`; the installed Homebrew e2fsprogs binaries are accessible at `/opt/homebrew/opt/e2fsprogs/sbin`. Prepending that directory made preflight pass and identified mke2fs, debugfs, and e2fsck as version 1.47.4. The profile's run script carries this PATH setting. No checks were disabled. See [`preflight-with-host-path.json`](preflight-with-host-path.json) and [`preflight-with-e2fsprogs.json`](preflight-with-e2fsprogs.json).

The isolated gateway started, accepted mTLS, reported healthy, and advertised VM driver 0.1.5. The independent client alias was added in the profile XDG config, so global gateway selection remained unchanged. See [`info.json`](info.json), [`register.json`](register.json), and [`version.json`](version.json).

## Runtime experiment

The experiment used these commands:

```sh
experiments/gateway-vm/client.sh sandbox create \
  --name ojp-20261024-vm1 \
  --from ojp-20261024-agent:2.1.310-poc-v3 \
  --policy experiments/denied.yaml \
  --cpu 1 --memory 2Gi --no-auto-providers --detach \
  -- bash --noprofile --norc -i

experiments/gateway-vm/client.sh sandbox upload \
  ojp-20261024-vm1 experiments/rust-project /sandbox/ojp-project

experiments/gateway-vm/client.sh sandbox exec ojp-20261024-vm1 \
  --workdir /sandbox/ojp-project/rust-project --no-login-shell -- claude --version
```

The `--upload` create flag cannot be combined with an explicit command in v0.1.5, so the project was transferred in a separate upload request. It is a copy: the guest source path has no live bind mount.

The VM driver resolved both the bootstrap image `nvcr.io/nvidia/base/ubuntu:24.04` and the derived local agent image from the host's local container engine. It prepared a guest root disk, then reported the sandbox Ready with resolved workload UID:GID 1000:1000. Create began at 22:42:06.975 UTC; the first Ready observation was 22:43:18.974 UTC (~72 seconds cold). First successful compile completed at 22:44:08.894 UTC (~122 seconds from create). The prepared agent image ext4 file has 13 GiB logical size. This was a cold profile cache; local Docker image cache was warm, while the VM profile's bootstrap/prepared disk caches were cold. Gateway driver logs identify the local image digest and successful preparation; exact CLI results are [`create-vm1.json`](create-vm1.json), [`get-vm1-after-prep.json`](get-vm1-after-prep.json), and the later commands below.

Claude's actual installed agent version ran successfully: `claude --version` returned `2.1.310 (Claude Code)`. Authenticated Claude operation was not tested; no provider credentials were attached. A `codex --version` probe failed because this image installs Claude Code, not Codex; see [`codex-version.json`](codex-version.json).

The project had to be uploaded, then built using a per-command environment override:

```sh
experiments/gateway-vm/client.sh sandbox exec ojp-20261024-vm1 \
  --workdir /sandbox/ojp-project/rust-project --no-login-shell -- \
  env HOME=/home/agent \
      MISE_DATA_DIR=/home/agent/.local/share/mise \
      CARGO_HOME=/home/agent/.cargo \
      RUSTUP_HOME=/usr/local/rustup \
      MISE_TRUSTED_CONFIG_PATHS=/home/agent/ojp-toolchain:/workspace:/sandbox/ojp-project/rust-project \
      PATH=/usr/local/cargo/bin:/usr/local/bin:/home/agent/.local/share/mise/shims:/home/agent/.local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
      mise exec -- cargo build --locked --offline
```

The build exited 0 and compiled `runtime-probe`; output artifacts were under `/home/agent/.cache/mbx/targets/.../debug/libruntime_probe.rlib`. The build used the image's preinstalled Rust 1.99.1 and no network. Bare `cargo` and `mise exec -- cargo` failed first: the VM guest process environment exposed `HOME=/sandbox`, no `CARGO_HOME`, `RUSTUP_HOME`, or `MISE_DATA_DIR`, and a default PATH without Cargo. `mise exec` without explicit home/data settings attempted network downloads and failed under the default-deny policy. Supplying the known, non-secret image paths for one command restored the preinstalled toolchain. This profile therefore demonstrates agent/build capability with a **WORKAROUND**; the normal image environment is not automatically applied to the guest process in this run.

Stop/start retained project files. The marker SHA-256 before and after was `3c181b2f9f8333addf46a991333a2e474fff87d8a32ae74943ce73160544e008`; both commands exited 0. See [`write-retained-file.json`](write-retained-file.json), [`stop-vm1.json`](stop-vm1.json), [`start-vm1.json`](start-vm1.json), and [`read-retained-file.json`](read-retained-file.json).

## Interpretation

**CONDITIONAL** for a Jackin integration prototype limited to a native VM agent plus explicit project upload and configured tool environment. The local ARM64 host, published v0.1.5 runtime, and packaged libkrun guest were sufficient to start a VM from the same v3 coding-agent image, run the agent's actual version, compile the Rust fixture, and retain files through stop/start. VM sandbox compute belongs to the VM driver, which owns the per-instance overlay. The driver retains prepared image disks as a separate profile cache until fixture cleanup. The project upload is a gateway-mediated copy, not a live mount. Generic `--cpu/--memory` requests are ignored by this driver; actual vCPU and memory values come from gateway-wide configuration.

Docker API, Compose, Testcontainers, service ports, and VM-to-Docker child isolation were not tested in this profile. Do not infer Docker-child VM isolation from this successful VM agent test. Authenticated agent operation was not tested. Linux KVM, Docker Desktop, remote gateways, and Kubernetes remain untested here.

The exact reproduction and each initial failure remain in this directory's individual JSON records. The disposable VM sandbox was deleted through OpenShell. The delete command exited 0; the next `get` returned “sandbox not found.” OpenShell removed its per-instance directory and 4 GiB overlay, and its VM helper and host supervisor processes exited. Its prepared image and bootstrap caches remained under the experiment state directory, totaling 6.2 GiB allocated (the prepared ext4 image's logical size was 13.6 GB). The scoped fixture cleanup then stopped only the `:18771` gateway and removed that experiment-owned cache, XDG client state, and ephemeral certificates. It preserved the gateway TOML and startup log as evidence. The existing `preview-vm` driver and VM processes remained live, with their runtime paths unchanged. See [`cleanup-inventory.json`](cleanup-inventory.json), [`sandbox-delete-vm1.json`](sandbox-delete-vm1.json), [`sandbox-get-after-delete.json`](sandbox-get-after-delete.json), [`profile-cleanup.json`](profile-cleanup.json), [`cleanup-inventory-after.json`](cleanup-inventory-after.json), [`vm-gateway-port-after-cleanup.json`](vm-gateway-port-after-cleanup.json), and [`preview-vm-still-active.json`](preview-vm-still-active.json). Before cleanup, the experiment state occupied 6.3 GiB; afterward the profile working directory was 40 KiB. The complete evidence directory occupies 132 KiB.
