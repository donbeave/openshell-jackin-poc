#!/bin/sh
set -eu
BASE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
export XDG_CONFIG_HOME="$BASE/config" XDG_STATE_HOME="$BASE/state" OPENSHELL_GATEWAY_CONFIG="$BASE/gateway.toml"
exec /opt/homebrew/opt/openshell/bin/openshell-gateway --config "$BASE/gateway.toml" --bind-address 127.0.0.1 --port 28471 --tls-cert "$BASE/certs/server/tls.crt" --tls-key "$BASE/certs/server/tls.key" --tls-client-ca "$BASE/certs/ca.crt" --enable-mtls-auth true --compute-driver docker
