# Linux target fixture (OrbStack-hosted)

This fixture is Linux ARM64 inside an isolated OrbStack machine. It is not a bare-metal Linux host. It does not qualify Docker Desktop, remote Linux, or the packaged OpenShell VM driver.

The machine name and immutable OrbStack ID are recorded in `results/full-replacement-20261024/targets/linux/manifest.json`. It has no host mounts and no forwarded SSH agent. The Linux guest has its own Docker Engine data root and a fresh OpenShell mTLS CA, XDG config, XDG state, and Docker driver namespace.

## Reproduce

1. Download OpenShell `v0.1.5` ARM64 Linux assets from the official GitHub release. Verify the gateway archive against `openshell-gateway-checksums-sha256.txt`; verify the CLI Debian asset against the release API digest recorded in the result manifest.
2. Create the fixture machine with `orbctl create --arch arm64 --cpus 2 --memory 4G --disk 32G --isolated --user jfr ubuntu:24.04 jfr-20261024-linux`. Stop if that exact machine name already exists.
3. Install `docker.io` in that guest and start only its `docker.service`. Install the downloaded OpenShell CLI and gateway binary. Do not attach the macOS Docker socket.
4. Run `sh experiments/full-replacement-20261024/targets/linux/bootstrap.sh`, then start its gateway with TLS and mTLS enabled. Register the private IP endpoint with `openshell gateway add https://<guest-ip>:18470 --local --name jfr-20261024-linux-ip`. The host is present in the gateway server certificate SAN and `grpc_endpoint` is set under the Docker driver configuration. Never bind `0.0.0.0` for this fixture.
5. Pull the pinned Ubuntu base image into the fresh guest engine, build the derived fixture image with `docker build`, then create the OpenShell sandbox from that local image. The build recipe is `probe-image/Dockerfile`.

`capture.py` records each command's arguments, exit status, elapsed time, stdout, and stderr in separate fields. It redacts the gateway token-reference ID from JSON output. The guest-generated private keys stay inside the isolated guest.

The separate `rebind-private-ip.sh` records the private-IP leaf certificate setup. `bootstrap.sh` retains the initial loopback configuration; reproducing the host-reachable endpoint also requires the exact `grpc_endpoint` entry shown in `results/full-replacement-20261024/targets/linux/commands/gateway-config.json`. The old loopback-only sandboxes were created before that change and failed reconnect after gateway rebinding. Preserve that failure as its own result.

## Scope

The positive results cover mTLS gateway health, the Docker driver, a pulled pinned base image, a small Docker-built arm64 derivative, image use by an OpenShell sandbox, basic `exec`, an approved named volume with admission enabled, and volume bytes across stop/start plus sandbox deletion/recreation.

This profile has no real Architect role, authenticated agent, Capsule session, host checkout, Git mode, Docker CLI in the sandbox, optional Docker engine grant, complete Jackin lifecycle, or model task. It does not prove the native Linux host profile.
