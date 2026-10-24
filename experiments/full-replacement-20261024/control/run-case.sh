#!/bin/sh
set -eu
BASE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
OUT="$BASE/../../../results/full-replacement-20261024/control"
case_name=$1
shift
mkdir -p "$OUT"
umask 077
set +e
"$BASE/target/debug/openshell-control-probe" "$@" >"$OUT/$case_name.stdout.json" 2>"$OUT/$case_name.stderr.txt"
status=$?
set -e
printf '%s\n' "$status" >"$OUT/$case_name.exit-status"
python3 - "$OUT/$case_name.command.json" "$BASE/target/debug/openshell-control-probe" "$@" <<'PY'
import json, sys
with open(sys.argv[1], "w") as f:
    json.dump(sys.argv[2:], f, indent=2)
    f.write("\n")
PY
exit "$status"
