#!/bin/sh
set -u
BASE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO=$(CDPATH= cd -- "$BASE/../../../../" && pwd)
OUT="$REPO/results/full-refactor-20261024/verification-worker/landlock"
NAME=${1:-jfrv-20261024-p14}
IMAGE=jfr-20261024-verify-worker:patch-adversarial
mkdir -p "$OUT"
cd "$BASE/../patch-tmpfs/client"
target/debug/openshell-control-probe verification-adversarial \
  --endpoint https://localhost:28631 --gateway-id jfr-20261024-vpatch \
  --server-name localhost --ca "$BASE/../patch-tmpfs/gateway/private/certs/ca.crt" \
  --cert "$BASE/../patch-tmpfs/gateway/private/certs/client/tls.crt" \
  --key "$BASE/../patch-tmpfs/gateway/private/certs/client/tls.key" \
  --name "$NAME" --image "$IMAGE" > "$OUT/$NAME.stdout.json" 2> "$OUT/$NAME.stderr.txt" &
worker_pid=$!
printf '%s\n' "$worker_pid" > "$OUT/$NAME.worker-pid.txt"
container_id=
log_pid=
for _ in $(seq 1 400); do
  container_id=$(docker ps -aq --filter "name=/$NAME" | head -n 1)
  if [ -n "$container_id" ]; then break; fi
  kill -0 "$worker_pid" 2>/dev/null || break
  sleep 0.05
done
if [ -n "$container_id" ]; then
  printf '%s\n' "$container_id" > "$OUT/$NAME.container-id.txt"
  docker inspect "$container_id" | jq '.[0] | {Id,Name,Image,State,Config:{User:.Config.User,Entrypoint:.Config.Entrypoint,Cmd:.Config.Cmd},HostConfig:{Tmpfs:.HostConfig.Tmpfs,Mounts:.HostConfig.Mounts,Binds:.HostConfig.Binds,SecurityOpt:.HostConfig.SecurityOpt,CapDrop:.HostConfig.CapDrop,NetworkMode:.HostConfig.NetworkMode,ReadonlyRootfs:.HostConfig.ReadonlyRootfs,Memory:.HostConfig.Memory,NanoCpus:.HostConfig.NanoCpus,PidsLimit:.HostConfig.PidsLimit}}' > "$OUT/$NAME.container-config.json"
  docker logs --follow "$container_id" > "$OUT/$NAME.container.log.txt" 2>&1 &
  log_pid=$!
fi
wait "$worker_pid"
rc=$?
printf '%s\n' "$rc" > "$OUT/$NAME.exit-status"
if [ -n "$log_pid" ]; then wait "$log_pid" 2>/dev/null || true; fi
exit 0
