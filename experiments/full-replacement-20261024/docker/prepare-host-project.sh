#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../../.." && pwd)
SRC="$ROOT/results/full-replacement-20261024/docker/host-source"
VOL=jfr24-dk-host-project
[ ! -e "$SRC" ] || { echo "refusing existing source: $SRC" >&2; exit 2; }
mkdir -p "$SRC"
cp -R "$ROOT/experiments/rust-project/." "$SRC/"
printf 'host-created-before-sandbox\n' > "$SRC/host-marker.txt"
chmod -R ugo+rwX "$SRC"
git -C "$SRC" init -q
git -C "$SRC" config user.name 'Jackin Replacement PoC'
git -C "$SRC" config user.email 'poc@example.invalid'
git -C "$SRC" add .
git -C "$SRC" commit -qm 'Create disposable Rust Testcontainers checkout'
[ ! -e "$(docker volume inspect "$VOL" 2>/dev/null || true)" ] || { echo "refusing existing volume: $VOL" >&2; exit 3; }
docker volume create --driver local \
  --opt type=none --opt o=bind --opt "device=$SRC" \
  --label openshell.ai/sandbox-attachable=true \
  --label openshell.ai/sandbox-attachable-workspace=default \
  --label jackin.fixture=jfr-20261024-docker \
  --label ojp.owner=followup-docker-engine \
  "$VOL"
docker volume inspect "$VOL" > "$ROOT/results/full-replacement-20261024/docker/host-volume-inspect.json"
