#!/bin/sh
set -eu
BASE="/Users/example/openshell-jackin-public/experiments/full-replacement-20261024/targets/openshell-vm-bind"
export XDG_CONFIG_HOME="$BASE/config"
export XDG_STATE_HOME="$BASE/state/xdg"
export OPENSHELL_GATEWAY_CONFIG="$BASE/gateway.toml"
export PATH="/opt/homebrew/opt/e2fsprogs/sbin:$PATH"
exec /opt/homebrew/opt/openshell/bin/openshell-gateway --config "$BASE/gateway.toml" --bind-address 127.0.0.1 --port 28473 --tls-cert "$BASE/certs/server/tls.crt" --tls-key "$BASE/certs/server/tls.key" --tls-client-ca "$BASE/certs/ca.crt" --enable-mtls-auth true --compute-driver vm
