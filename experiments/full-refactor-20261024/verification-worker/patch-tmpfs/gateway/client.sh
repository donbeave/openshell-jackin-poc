#!/bin/sh
set -eu
BASE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
MODE=${1:?mode is required}
shift
exec "$BASE/../client/target/debug/openshell-control-probe" "$MODE" --endpoint https://localhost:28631 --server-name localhost --ca "$BASE/private/certs/ca.crt" --cert "$BASE/private/certs/client/tls.crt" --key "$BASE/private/certs/client/tls.key" "$@"
