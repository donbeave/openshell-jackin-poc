#!/bin/sh
set -eu
REPO=$(CDPATH= cd -- "$(dirname -- "$0")/../../.." && pwd)
OUT="$REPO/results/full-refactor-20261024/verification-worker/cleanup"
mkdir -p "$OUT"
stop_one() {
  pid=$1
  port=$2
  config=$3
  label=$4
  command=$(ps -p "$pid" -o command= 2>/dev/null || true)
  if [ -z "$command" ]; then
    printf '%s\n' "$label absent_before_cleanup pid=$pid port=$port" >> "$OUT/gateway-stop-receipts.txt"
    return 0
  fi
  case "$command" in
    *"$config"*"--port"*"$port"*) ;;
    *) printf 'refusing unexpected process pid=%s port=%s command=%s\n' "$pid" "$port" "$command" >&2; return 1 ;;
  esac
  listener=$(lsof -nP -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)
  if [ "$listener" != "$pid" ]; then
    printf 'refusing listener mismatch pid=%s port=%s listener=%s\n' "$pid" "$port" "$listener" >&2
    return 1
  fi
  kill -TERM "$pid"
  for _ in $(seq 1 100); do
    if ! kill -0 "$pid" 2>/dev/null; then
      break
    fi
    sleep 0.1
  done
  if kill -0 "$pid" 2>/dev/null; then
    printf 'gateway did not stop pid=%s port=%s\n' "$pid" "$port" >&2
    return 1
  fi
  remaining=$(lsof -nP -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)
  if [ -n "$remaining" ]; then
    printf 'unexpected listener remains port=%s pid=%s\n' "$port" "$remaining" >&2
    return 1
  fi
  printf '%s\n' "$label stopped pid=$pid port=$port by SIGTERM; listener absent" >> "$OUT/gateway-stop-receipts.txt"
}
stop_one 53597 28630 "$REPO/experiments/full-refactor-20261024/verification-worker/gateway/gateway.toml" release-worker-gateway
stop_one 25374 28631 "$REPO/experiments/full-refactor-20261024/verification-worker/patch-tmpfs/gateway/gateway.toml" patched-worker-gateway
