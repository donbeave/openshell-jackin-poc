#!/bin/sh
set -eu
BASE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
export XDG_CONFIG_HOME="$BASE/config"
export XDG_STATE_HOME="$BASE/state/xdg"
export OPENSHELL_LOCAL_TLS_DIR="$BASE/certs"
exec /opt/homebrew/opt/openshell/bin/openshell --gateway jrr24-worker "$@"
