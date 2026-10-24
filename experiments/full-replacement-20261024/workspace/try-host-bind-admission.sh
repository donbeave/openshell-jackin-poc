#!/usr/bin/env bash
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
FIXTURE="$ROOT/results/full-replacement-20261024/workspace/jfr-20261024-ws/host-source"
sh "$ROOT/experiments/full-replacement-20261024/gateway-b/client.sh" sandbox create \
  --name jfrws24-bindneg \
  --from openshell-agent-preview:20261024 \
  --no-keep \
  --driver-config-json "{\"docker\":{\"mounts\":[{\"type\":\"bind\",\"source\":\"$FIXTURE\",\"target\":\"/workspace/jfr-20261024-ws\",\"read_only\":false}]}}" \
  -- /bin/sh -lc 'test -f /workspace/jfr-20261024-ws/README.md'
