#!/bin/sh
set -eu
export DOCKER_HOST=tcp://127.0.0.1:28481
export DOCKER_TLS_VERIFY=1
export DOCKER_CERT_PATH="$(cd "$(dirname "$0")" && pwd)/private-b/client"
docker info --format 'id={{.ID}} name={{.Name}} root={{.DockerRootDir}}'
docker ps -a --no-trunc
docker image ls --digests --no-trunc
docker volume ls --format '{{.Name}}'
