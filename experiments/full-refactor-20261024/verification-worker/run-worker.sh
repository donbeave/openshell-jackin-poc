#!/bin/sh
set -eu
BASE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
RESULTS="$BASE/results"
CLIENT="$BASE/client/target/debug/openshell-control-probe"
NAME=jfrv-20261024-w03
IMAGE=jfr-20261024-verify-worker:baseline-python
mkdir -p "$RESULTS"
cd "$BASE/client"
set +e
"$CLIENT" verification-worker \
  --endpoint https://localhost:28630 \
  --server-name localhost \
  --ca "$BASE/gateway/private/certs/ca.crt" \
  --cert "$BASE/gateway/private/certs/client/tls.crt" \
  --key "$BASE/gateway/private/certs/client/tls.key" \
  --name "$NAME" \
  --image "$IMAGE" \
  > "$RESULTS/worker.stdout.json" 2> "$RESULTS/worker.stderr.txt"
status=$?
set -e
printf '%s\n' "$status" > "$RESULTS/worker.exit-status"
python3 - "$RESULTS/worker.command.json" "$CLIENT" verification-worker \
  --endpoint https://localhost:28630 --server-name localhost \
  --ca "$BASE/gateway/private/certs/ca.crt" \
  --cert "$BASE/gateway/private/certs/client/tls.crt" \
  --key "$BASE/gateway/private/certs/client/tls.key" \
  --name "$NAME" --image "$IMAGE" <<'PY'
import json,sys
with open(sys.argv[1],'w') as f:
 json.dump(sys.argv[2:],f,indent=2); f.write('\n')
PY
exit "$status"
