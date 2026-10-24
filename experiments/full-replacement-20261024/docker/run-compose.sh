#!/bin/sh
set -eu
export DOCKER_CERT_PATH=/home/agent/.docker/client/client
cd /workspace/rust-project
P=jfr24compose2
docker compose -p "$P" up -d --wait
docker compose -p "$P" ps
docker port "${P}-app-1" 80/tcp
AUTO_PORT=$(docker port "${P}-app-1" 80/tcp | awk -F: '$NF != 30080 {print $NF; exit}')
printf 'Docker reported dynamic host port=%s\n' "$AUTO_PORT"
printf 'automatic service response: '
curl -fsS "http://host.docker.internal:${AUTO_PORT}/"
printf 'fixed service response: '
curl -fsS http://host.docker.internal:30080/
printf 'database health: '
docker inspect --format '{{.State.Health.Status}}' "${P}-database-1"
docker compose -p "$P" logs --no-color
docker compose -p "$P" down --volumes --remove-orphans
docker ps -a --filter "name=${P}" --format '{{.ID}} {{.Names}} {{.Status}}'
