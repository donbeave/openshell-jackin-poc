#!/bin/sh
set -eu
BASE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
OUT="$BASE/results"
mkdir -p "$OUT"
IMAGE=jfr-20261024-verify-worker:baseline-python
set +e
docker build --pull=false --progress=plain -t "$IMAGE" -f "$BASE/Dockerfile" "$BASE" >"$OUT/image-build.stdout.txt" 2>"$OUT/image-build.stderr.txt"
status=$?
set -e
printf '%s\n' "$status" > "$OUT/image-build.exit-status"
if [ "$status" -ne 0 ]; then cat "$OUT/image-build.stderr.txt" >&2; exit "$status"; fi
docker image inspect "$IMAGE" --format '{{json .}}' > "$OUT/image-inspect.json"
docker image inspect "$IMAGE" --format 'id={{.Id}} os={{.Os}} arch={{.Architecture}} user={{.Config.User}} repo_digests={{json .RepoDigests}}' > "$OUT/image-identity.txt"
docker version --format 'client={{.Client.Version}} server={{.Server.Version}}' > "$OUT/docker-version.txt"
docker context show > "$OUT/docker-context.txt"
docker context inspect "$(cat "$OUT/docker-context.txt")" --format '{{.Endpoints.docker.Host}}' > "$OUT/docker-endpoint.txt"
cat "$OUT/image-identity.txt"
