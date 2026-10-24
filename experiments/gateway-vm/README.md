# Disposable VM profile

This profile uses the installed OpenShell v0.1.5 gateway and packaged VM driver. It writes only under this directory and binds `127.0.0.1:18771`. It does not use the registered `openshell-vm` gateway or alter the active global gateway.

Run `sh experiments/gateway-vm/setup.sh`, then `experiments/gateway-vm/run-gateway.sh` in a dedicated terminal. The script creates a profile-specific mTLS CA, server and client certificates, launch JWT key pair, SQLite/runtime state, and an isolated XDG client config. The VM driver's host tools need the installed e2fsprogs directory first in PATH; the script sets `/opt/homebrew/opt/e2fsprogs/sbin` explicitly.

In another terminal, `experiments/gateway-vm/client.sh gateway info` verifies the gateway. The `client.sh` XDG paths and gateway alias are local to this profile. To reproduce the VM experiment, run the recorded commands in `results/gateway-vm/README.md`.

The local v3 image import creates a large prepared ext4 disk. The experiment state is disposable and owned by this profile. `cleanup.sh` deletes this profile's sandbox, terminates only its `:18771` gateway, and removes this profile's runtime state and credentials. It does not touch `~/.local/state/openshell/preview-vm`, Docker images, or shared caches.

The VM sandbox has a VM boundary around the guest workload. This profile does not connect it to Docker-in-Docker and does not test container children.
