#!/bin/sh
set -eu
BASE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
WS=default
CANDIDATE="$BASE/fixture/candidate"
BUNDLE="$BASE/fixture/trusted-bundle"
for volume in jfr24verify-candidate jfr24verify-bundle; do
    if docker volume inspect "$volume" >/dev/null 2>&1; then
        echo "refusing to reuse existing volume $volume" >&2
        exit 2
    fi
done
for path in "$CANDIDATE" "$BUNDLE"; do
    test -d "$path"
    test ! -L "$path"
done
candidate=$(python3 -c 'import pathlib,sys; print(pathlib.Path(sys.argv[1]).resolve(strict=True))' "$CANDIDATE")
bundle=$(python3 -c 'import pathlib,sys; print(pathlib.Path(sys.argv[1]).resolve(strict=True))' "$BUNDLE")
docker volume create --driver local --opt type=none --opt o=bind --opt "device=$candidate" \
  --label openshell.ai/sandbox-attachable=true \
  --label "openshell.ai/sandbox-attachable-workspace=$WS" \
  --label jackin.fixture=jfr-20261024-verification-worker jfr24verify-candidate > "$BASE/results/candidate-volume-create.txt"
docker volume create --driver local --opt type=none --opt o=bind --opt "device=$bundle" \
  --label openshell.ai/sandbox-attachable=true \
  --label "openshell.ai/sandbox-attachable-workspace=$WS" \
  --label jackin.fixture=jfr-20261024-verification-worker jfr24verify-bundle > "$BASE/results/bundle-volume-create.txt"
docker volume inspect jfr24verify-candidate > "$BASE/results/candidate-volume-inspect.json"
docker volume inspect jfr24verify-bundle > "$BASE/results/bundle-volume-inspect.json"
python3 "$BASE/validate-volume-source.py" jfr24verify-candidate "$candidate" "$WS" > "$BASE/results/candidate-volume-validation.json"
python3 "$BASE/validate-volume-source.py" jfr24verify-bundle "$bundle" "$WS" > "$BASE/results/bundle-volume-validation.json"
cat "$BASE/results/candidate-volume-validation.json" "$BASE/results/bundle-volume-validation.json"
