#!/bin/sh
set -eu
BASE="/Users/example/openshell-jackin-poc/research/full-refactor/experiments/capsule/replay-final"
export XDG_CONFIG_HOME="$BASE/config"
export XDG_STATE_HOME="$BASE/state/xdg"
export OPENSHELL_GATEWAY_CONFIG="$BASE/gateway.toml"
exec /opt/homebrew/opt/openshell/bin/openshell-gateway --config "$BASE/gateway.toml" --bind-address 127.0.0.1 --port 18823 --tls-cert "$BASE/certs/server/tls.crt" --tls-key "$BASE/certs/server/tls.key" --tls-client-ca "$BASE/certs/ca.crt" --enable-mtls-auth true --compute-driver docker
