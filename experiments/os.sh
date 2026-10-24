#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
export XDG_CONFIG_HOME="$ROOT/experiments/gateway/config"
export XDG_STATE_HOME="$ROOT/experiments/gateway/state"
export OPENSHELL_LOCAL_TLS_DIR="$ROOT/experiments/gateway/certs"
exec openshell --gateway ojp-20261024-gw "$@"
