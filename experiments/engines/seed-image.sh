#!/bin/sh
set -eu

IMAGE=nginx:1.29.3-alpine
if ! docker image inspect "$IMAGE" --format '{{.Id}} {{json .RepoDigests}}' >/dev/null 2>&1; then
    docker pull "$IMAGE"
fi
for name in ojp-20261024-engine-a ojp-20261024-engine-b; do
    docker save "$IMAGE" | docker exec -i "$name" sh -c 'cat > /tmp/nginx.image.tar'
    docker exec "$name" docker load --input /tmp/nginx.image.tar
    docker exec "$name" rm /tmp/nginx.image.tar
done
