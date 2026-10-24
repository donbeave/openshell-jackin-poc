#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
NAME=ojp-20261024-sock
VOLUME=ojp-20261024-sock-dockersock
PROJECT=ojp-20261024-sock-project
IMAGE='docker:29.8.2-dind@sha256:1e08cdb63405ca788aea94ef35b792d1e299607c667d33d7bcbcae1fd2611ced'

if docker inspect "$NAME" >/dev/null 2>&1; then
    echo "fixture already exists: $NAME; inspect before reuse" >&2
    exit 1
fi

docker volume create \
    --label openshell.ai/sandbox-attachable=true \
    --label openshell.ai/sandbox-attachable-workspace=default \
    --label ojp.test-id=ojp-20261024 "$VOLUME" >/dev/null
docker volume create \
    --label openshell.ai/sandbox-attachable=true \
    --label openshell.ai/sandbox-attachable-workspace=default \
    --label ojp.test-id=ojp-20261024 "$PROJECT" >/dev/null

# Docker API uses one Unix socket; only child service port 18090 is published.
docker run --detach --name "$NAME" --privileged --cpus=2 --memory=4g \
    --label ojp.test-id=ojp-20261024 --label ojp.owner=experiments/engines/unix-socket.sh \
    --publish 18090:18090 \
    --sysctl "net.ipv4.ip_local_port_range=18090 18090" \
    --mount "type=volume,src=$VOLUME,dst=/var/run/ojp-docker-socket" \
    --mount "type=volume,src=$PROJECT,dst=/sandbox/ojp-project" \
    --env DOCKER_TLS_CERTDIR= \
    docker:29.8.2-dind@sha256:1e08cdb63405ca788aea94ef35b792d1e299607c667d33d7bcbcae1fd2611ced \
    dockerd --host=unix:///var/run/ojp-docker-socket/docker.sock

attempt=0
until docker exec "$NAME" docker --host unix:///var/run/ojp-docker-socket/docker.sock info >/dev/null 2>&1; do
    attempt=$((attempt + 1))
    [ "$attempt" -lt 60 ] || { echo "readiness timeout: $NAME" >&2; exit 1; }
    sleep 2
done

docker cp "$ROOT/../rust-project/." "$NAME:/sandbox/ojp-project/"
docker exec "$NAME" chown -R 1000:1000 /sandbox/ojp-project
docker exec "$NAME" sh -c 'chmod 0666 /var/run/ojp-docker-socket/docker.sock'
docker inspect "$NAME" --format '{{.Name}} {{.Id}} {{.Image}} ports={{json .HostConfig.PortBindings}} mounts={{json .Mounts}} resources={{.HostConfig.NanoCpus}} {{.HostConfig.Memory}}'
