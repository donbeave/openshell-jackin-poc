#!/bin/sh
set -u
BASE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO=$(CDPATH= cd -- "$BASE/../../../../" && pwd)
OUT="$REPO/results/full-refactor-20261024/verification-worker/patch-tmpfs"
NAME=${1:?sandbox name required}
IMAGE=${2:-jfr-20261024-verify-worker:baseline-python}
mkdir -p "$OUT"
cd "$BASE/client"

target/debug/openshell-control-probe verification-worker \
  --endpoint https://localhost:28631 --gateway-id jfr-20261024-vpatch \
  --server-name localhost --ca "$BASE/gateway/private/certs/ca.crt" \
  --cert "$BASE/gateway/private/certs/client/tls.crt" \
  --key "$BASE/gateway/private/certs/client/tls.key" \
  --name "$NAME" --image "$IMAGE" \
  --retain-failed true > "$OUT/$NAME.stdout.json" 2> "$OUT/$NAME.stderr.txt" &
worker_pid=$!
printf '%s\n' "$worker_pid" > "$OUT/$NAME.worker-pid.txt"
container_id=
log_pid=
stats_pid=
oom_pid=
for _ in $(seq 1 300); do
  container_id=$(docker ps -aq --filter "name=$NAME" | head -n 1)
  if [ -n "$container_id" ]; then
    break
  fi
  kill -0 "$worker_pid" 2>/dev/null || break
  sleep 0.05
done
if [ -n "$container_id" ]; then
  printf '%s\n' "$container_id" > "$OUT/$NAME.container-id.txt"
  docker inspect "$container_id" | jq '.[0] | {
    Id,Name,Image,State,
    Config:{User:.Config.User,Entrypoint:.Config.Entrypoint,Cmd:.Config.Cmd},
    HostConfig:{Tmpfs:.HostConfig.Tmpfs,Mounts:.HostConfig.Mounts,Binds:.HostConfig.Binds,
      SecurityOpt:.HostConfig.SecurityOpt,CapDrop:.HostConfig.CapDrop,
      NetworkMode:.HostConfig.NetworkMode,ReadonlyRootfs:.HostConfig.ReadonlyRootfs,
      Memory:.HostConfig.Memory,NanoCpus:.HostConfig.NanoCpus,PidsLimit:.HostConfig.PidsLimit}
  }' > "$OUT/$NAME.container-config.json"
  docker logs --follow "$container_id" > "$OUT/$NAME.container.log.txt" 2>&1 &
  log_pid=$!
  docker stats --format '{{.MemUsage}} {{.CPUPerc}} {{.PIDs}}' "$container_id" > "$OUT/$NAME.docker-stats.txt" 2>&1 &
  stats_pid=$!
  docker events --filter "container=$container_id" --filter event=oom --format '{{json .}}' > "$OUT/$NAME.docker-oom-events.jsonl" 2> "$OUT/$NAME.docker-oom-events.stderr.txt" &
  oom_pid=$!
fi
wait "$worker_pid"
rc=$?
printf '%s\n' "$rc" > "$OUT/$NAME.exit-status"
if [ -n "$log_pid" ]; then
  wait "$log_pid" 2>/dev/null || true
fi
if [ -n "$stats_pid" ]; then
  kill "$stats_pid" 2>/dev/null || true
  wait "$stats_pid" 2>/dev/null || true
fi
if [ -n "$oom_pid" ]; then
  kill "$oom_pid" 2>/dev/null || true
  wait "$oom_pid" 2>/dev/null || true
fi
exit 0
