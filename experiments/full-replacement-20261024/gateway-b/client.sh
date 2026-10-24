#!/bin/sh
set -eu
BASE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
export XDG_CONFIG_HOME="$BASE/config" XDG_STATE_HOME="$BASE/state" OPENSHELL_LOCAL_TLS_DIR="$BASE/certs"
exec /opt/homebrew/opt/openshell/bin/openshell --gateway jfr-20261024-b "$@"
