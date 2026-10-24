#!/bin/sh
set -eu

# Remove only the two named disposable fixtures created by setup.sh.
for name in ojp-20261024-engine-a ojp-20261024-engine-b; do
    if docker inspect "$name" >/dev/null 2>&1; then docker rm -fv "$name"; fi
done
for name in ojp-20261024-sock ojp-20261024-interrupted; do
    if docker inspect "$name" >/dev/null 2>&1; then docker rm -fv "$name"; fi
done
for name in ojp-20261024-engine-a-project ojp-20261024-engine-b-project; do
    if docker volume inspect "$name" >/dev/null 2>&1; then docker volume rm "$name"; fi
done
for name in ojp-20261024-sock-dockersock ojp-20261024-sock-project ojp-20261024-interrupted-run; do
    if docker volume inspect "$name" >/dev/null 2>&1; then docker volume rm "$name"; fi
done
if docker inspect ojp-20261024-network-endpoint >/dev/null 2>&1; then docker rm -f ojp-20261024-network-endpoint; fi
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
rm -rf "$ROOT/private"
rm -f "$ROOT/host-images/nginx-1.29.3-alpine.tar"
