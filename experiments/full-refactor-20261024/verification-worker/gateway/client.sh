#!/bin/sh
set -eu
BASE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec "$BASE/target/debug/openshell-control-probe" --endpoint https://localhost:28630 --server-name localhost --ca "$BASE/private/certs/ca.crt" --cert "$BASE/private/certs/client/tls.crt" --key "$BASE/private/certs/client/tls.key" "$@"
