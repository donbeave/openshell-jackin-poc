#!/bin/sh
set -u
BASE=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
OUT="$BASE/tmpfs-diagnostic"
NAME=jfr-20261024-tmpfs-validation-02
IMAGE=jfr-20261024-verify-worker:baseline-python
if docker ps -aq --filter "name=^/${NAME}$" | grep -q .; then
  echo "refusing pre-existing container $NAME" >&2; exit 3
fi
docker image inspect "$IMAGE" --format '{{.Id}} {{.Os}}/{{.Architecture}}' > "$OUT/image-before.txt"
docker create --name "$NAME" --entrypoint /bin/true \
  --tmpfs=/tmp:rw,noexec,nosuid,size=67108864 \
  --tmpfs=/build:rw,nosuid,size=268435456 "$IMAGE" \
  > "$OUT/create.stdout.txt" 2> "$OUT/create.stderr.txt"
rc=$?
printf '%s\n' "$rc" > "$OUT/create.exit-status"
if [ "$rc" -ne 0 ]; then exit "$rc"; fi
CID=$(tr -d '\r\n' < "$OUT/create.stdout.txt")
printf '%s\n' "$CID" > "$OUT/container-id.txt"
docker inspect "$CID" > "$OUT/inspect.json"
docker inspect "$CID" --format '{{json .HostConfig.Tmpfs}}' > "$OUT/hostconfig-tmpfs.json"
docker rm "$CID" > "$OUT/remove.stdout.txt" 2> "$OUT/remove.stderr.txt"
rc=$?
printf '%s\n' "$rc" > "$OUT/remove.exit-status"
if [ "$rc" -ne 0 ]; then exit "$rc"; fi
docker inspect "$CID" > "$OUT/inspect-after-remove.txt" 2>&1
rc=$?
printf '%s\n' "$rc" > "$OUT/inspect-after-remove.exit-status"
if [ "$rc" -eq 0 ]; then echo "container unexpectedly remains" >&2; exit 4; fi
echo "PASS: create-only validation accepted exact tmpfs options and removed CID $CID; no start command was issued"
