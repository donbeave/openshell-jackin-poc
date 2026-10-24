#!/bin/sh
set -eu
BASE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO=$(CDPATH= cd -- "$BASE/../../../../" && pwd)
OUT="$REPO/results/full-refactor-20261024/verification-worker/landlock"
IMAGE=jfr-20261024-verify-worker:patch-adversarial
mkdir -p "$OUT"
"$HOME/.local/share/mise/installs/zig/0.17.0/zig" cc -target aarch64-linux-musl -static -O2 -Wall -Wextra -o "$BASE/jfr-setuid-probe" "$BASE/setuid-probe.c" > "$OUT/setuid-helper-build.log" 2>&1
shasum -a 256 "$BASE/setuid-probe.c" "$BASE/jfr-setuid-probe" > "$OUT/setuid-helper-hashes.txt"
docker build --pull=false --progress=plain -t "$IMAGE" -f "$BASE/Dockerfile-adversarial" "$BASE" > "$OUT/image-build.log" 2>&1
rc=$?
printf '%s\n' "$rc" > "$OUT/image-build.exit-status"
docker image inspect "$IMAGE" --format 'id={{.Id}} os={{.Os}} arch={{.Architecture}} user={{.Config.User}} workdir={{.Config.WorkingDir}}' > "$OUT/image-identity.txt"
docker image inspect "$IMAGE" --format '{{json .RootFS.Layers}}' > "$OUT/image-layers.json"
