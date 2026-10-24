#!/bin/sh
set -eu
BASE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO=$(CDPATH= cd -- "$BASE/../../../../" && pwd)
OUT="$REPO/results/full-refactor-20261024/verification-worker/patch-tmpfs"
CLIENT="$BASE/client/target/debug/openshell-control-probe"
NAME=jfrv-20261024-p01
IMAGE=jfr-20261024-verify-worker:baseline-python
mkdir -p "$OUT"
cd "$BASE/client"
set +e
"$CLIENT" verification-worker \
  --endpoint https://localhost:28631 \
  --gateway-id jfr-20261024-vpatch \
  --server-name localhost \
  --ca "$BASE/gateway/private/certs/ca.crt" \
  --cert "$BASE/gateway/private/certs/client/tls.crt" \
  --key "$BASE/gateway/private/certs/client/tls.key" \
  --name "$NAME" \
  --image "$IMAGE" \
  > "$OUT/worker.stdout.json" 2> "$OUT/worker.stderr.txt"
rc=$?
set -e
printf '%s\n' "$rc" > "$OUT/worker.exit-status"
python3 - "$OUT/worker.command.json" "$CLIENT" verification-worker \
  --endpoint https://localhost:28631 --gateway-id jfr-20261024-vpatch \
  --server-name localhost --ca "$BASE/gateway/private/certs/ca.crt" \
  --cert "$BASE/gateway/private/certs/client/tls.crt" \
  --key "$BASE/gateway/private/certs/client/tls.key" \
  --name "$NAME" --image "$IMAGE" <<'PY'
import json,sys
with open(sys.argv[1], 'w') as f:
    json.dump(sys.argv[2:], f, indent=2)
    f.write('\n')
PY
exit "$rc"
