#!/bin/sh
set -eu
BASE="/Users/example/openshell-jackin-poc/experiments/gateway-vm"
export XDG_CONFIG_HOME="$BASE/config"
export XDG_STATE_HOME="$BASE/state/xdg"
export OPENSHELL_LOCAL_TLS_DIR="$BASE/certs"
exec /opt/homebrew/opt/openshell/bin/openshell --gateway ojp-20261024-vm "$@"
