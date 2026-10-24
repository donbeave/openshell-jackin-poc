#!/bin/sh
set -eu
BASE=/Users/example/openshell-jackin-poc/experiments/gateway
export XDG_STATE_HOME="$BASE/state"
export XDG_CONFIG_HOME="$BASE/config"
export OPENSHELL_LOCAL_TLS_DIR="$BASE/certs"
exec /opt/homebrew/opt/openshell/bin/openshell "$@"
