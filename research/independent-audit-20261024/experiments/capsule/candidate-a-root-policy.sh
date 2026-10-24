#!/bin/sh
set -eu
BASE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
CLIENT="$BASE/client.sh"
ROOT=$(CDPATH= cd -- "$BASE/../.." && pwd)
OUT="$ROOT/evidence/capsule"
set +e
"$CLIENT" sandbox create \
  --name jrr24-root-a \
  --from alpine@sha256:2e0b81d60597f449baa56dc25d355367869d2dca4cd57e866f1e2b52af3eb55f \
  --policy "$BASE/policy-root.yaml" \
  --no-keep \
  -- /bin/sh -c id \
  > "$OUT/a-root-policy-rejection.stdout" \
  2> "$OUT/a-root-policy-rejection.stderr"
EXIT_CODE=$?
set -e
printf '%s\n' "$EXIT_CODE" > "$OUT/a-root-policy-rejection.exit"
if [ "$EXIT_CODE" -eq 0 ]; then
  printf 'Unexpected success: inspect and delete only jrr24-root-a.\n' >&2
  exit 1
fi
if ! grep -q 'run_as_user must be' "$OUT/a-root-policy-rejection.stderr"; then
  printf 'Unexpected failure mode; inspect captured stderr.\n' >&2
  exit 1
fi
