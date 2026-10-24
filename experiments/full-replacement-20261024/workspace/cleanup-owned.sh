#!/bin/sh
set -eu
BASE=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
CLIENT="$BASE/gateway-b/client.sh"
OUT="$BASE/../../results/full-replacement-20261024/cleanup"
mkdir -p "$OUT/get"
cat > "$OUT/expected-sandboxes.tsv" <<'MANIFEST'
dfb460f3-edd1-41a0-ac19-c54d075056d0 jfrws24-official
303ea70d-e938-43bc-98f8-b1a925de1edf jfrws24-official2
f9d3d764-a34d-44bc-b3d3-942bc340b4fb jfrws24-officialro
6a1be9be-9e5f-423f-b47d-6ed730cca481 jfrws24-limits
a342d346-5bea-42eb-ac71-f829224ea436 jfrws24-recreat
52abba42-0002-4144-8645-0dc436fe873e jfrws24-rorole
202b7bca-03cd-42e7-8afc-9ba4adcb0abe jfrws24-wtplain
e4b4992c-b152-4cb5-8c44-d33f6601f733 jfrws24-cloner
c030e1a5-7a8a-4fd9-b114-d9ed3a04ef0e jfrws24-wtrecr
MANIFEST

# Verify every immutable ID through GetSandbox(name, workspace) before name-only
# delete. Abort if the gateway returns a different ID or resource labels.
while read -r expected_id name; do
  getfile="$OUT/get/$name.json"
  "$CLIENT" --workspace jfr-ws-20261024 sandbox get "$name" -o json > "$getfile"
  python3 - "$getfile" "$expected_id" "$name" <<'PY'
import json,sys
obj=json.load(open(sys.argv[1]))
assert obj.get('id') == sys.argv[2], (obj.get('id'),sys.argv[2])
assert obj.get('name') == sys.argv[3], (obj.get('name'),sys.argv[3])
assert obj.get('workspace') == 'jfr-ws-20261024', obj.get('workspace')
PY
  "$CLIENT" --workspace jfr-ws-20261024 sandbox delete "$name" > "$OUT/delete-$name.stdout" 2> "$OUT/delete-$name.stderr"
done < "$OUT/expected-sandboxes.tsv"
"$CLIENT" --workspace jfr-ws-20261024 sandbox list -o json > "$OUT/gateway-b-list-after-delete.json"
