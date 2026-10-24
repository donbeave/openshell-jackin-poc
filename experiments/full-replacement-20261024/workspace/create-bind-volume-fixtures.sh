#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
OUT="$ROOT/results/full-replacement-20261024/workspace/jfr-20261024-ws"
WS="jfr-ws-20261024"
OTHER="jfr-ws-other24"
source_for() { python3 -c 'import pathlib,sys; print(pathlib.Path(sys.argv[1]).resolve(strict=True))' "$1"; }
create_one() {
  local name="$1" source="$2" workspace="$3"
  if docker volume inspect "$name" >/dev/null 2>&1; then
    printf 'refusing to overwrite existing volume %s\n' "$name" >&2
    return 2
  fi
  docker volume create --driver local \
    --opt type=none --opt o=bind --opt "device=$source" \
    --label openshell.ai/sandbox-attachable=true \
    --label "openshell.ai/sandbox-attachable-workspace=$workspace" \
    --label "jackin.fixture=jfr-20261024-ws" "$name"
  docker volume inspect "$name" > "$OUT/volume-$name-inspect.json"
}
for path in "$OUT/host-source" "$OUT/worktree" "$OUT/clone"; do
  chmod 0777 "$path"
  [[ ! -L "$path" ]] || { printf 'source is symlink: %s\n' "$path" >&2; exit 3; }
done
chmod 0777 "$OUT/host-source/src" "$OUT/worktree/src" "$OUT/clone/src"
create_one jfr24ws-shared-rw "$(source_for "$OUT/host-source")" "$WS"
create_one jfr24ws-shared-ro "$(source_for "$OUT/host-source")" "$WS"
create_one jfr24ws-wrong-ws "$(source_for "$OUT/host-source")" "$OTHER"
create_one jfr24ws-worktree "$(source_for "$OUT/worktree")" "$WS"
create_one jfr24ws-clone "$(source_for "$OUT/clone")" "$WS"
create_one jfr24ws-common-git "$(source_for "$OUT/host-source/.git")" "$WS"
