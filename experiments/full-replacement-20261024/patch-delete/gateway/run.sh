#!/bin/sh
set -eu
BASE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
export XDG_CONFIG_HOME="$BASE/config" XDG_STATE_HOME="$BASE/state" OPENSHELL_GATEWAY_CONFIG="$BASE/gateway.toml"
REPO_ROOT=$(CDPATH= cd -- "$BASE/../../../.." && pwd)
GATEWAY="$REPO_ROOT/experiments/full-replacement-20261024/patch-delete/openshell/target/debug/openshell-gateway"
test -x "$GATEWAY" || { echo "build the patched openshell-gateway first: $GATEWAY" >&2; exit 1; }
exec "$GATEWAY" --config "$BASE/gateway.toml" --bind-address 127.0.0.1 --port 28620 --tls-cert "$BASE/certs/server/tls.crt" --tls-key "$BASE/certs/server/tls.key" --tls-client-ca "$BASE/certs/ca.crt" --enable-mtls-auth true --compute-driver docker
