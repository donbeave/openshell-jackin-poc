#!/bin/sh
set -eu
BASE="/Users/example/openshell-jackin-public/experiments/full-replacement-20261024/targets/openshell-vm"
export XDG_CONFIG_HOME="$BASE/config"
export XDG_STATE_HOME="$BASE/state/xdg"
export OPENSHELL_LOCAL_TLS_DIR="$BASE/certs"
exec /opt/homebrew/opt/openshell/bin/openshell --gateway jfr-20261024-vm "$@"
