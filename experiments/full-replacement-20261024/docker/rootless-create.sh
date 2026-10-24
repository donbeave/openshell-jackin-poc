#!/bin/sh
set -eu
BASE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec "$BASE/gateway-d/client.sh" sandbox create \
  --name jfr24rootless3 \
  --from docker:29.8.2-dind-rootless@sha256:c652fa9cebdaa3d655c33c6389c3c409f9a0fea6449c7d7c56c486fe71af0591 \
  --policy "$BASE/rootless-ordinary.yaml" \
  --restart-policy never --detach \
  --label ojp.test-id=jfr-20261024-docker-rootless \
  --label ojp.owner=followup-docker-rootless-corrected \
  -- /usr/local/bin/dockerd-entrypoint.sh
