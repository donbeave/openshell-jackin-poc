#!/bin/sh
set -eu
BASE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if lsof -nP -iTCP:28630 -sTCP:LISTEN >/dev/null 2>&1; then
    echo "port 28630 already has a listener; refusing to start" >&2
    exit 2
fi
nohup "$BASE/run.sh" > "$BASE/gateway.log" 2>&1 < /dev/null &
echo $! > "$BASE/gateway.pid"
for _ in $(seq 1 100); do
    if lsof -nP -iTCP:28630 -sTCP:LISTEN >/dev/null 2>&1; then
        exit 0
    fi
    sleep 0.1
done
cat "$BASE/gateway.log" >&2
exit 1
