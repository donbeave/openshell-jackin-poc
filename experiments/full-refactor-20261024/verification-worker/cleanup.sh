#!/bin/sh
set -eu

BASE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
EXPECTED_IMAGE='sha256:9644b32c48960dee46b1b7f47b7ba15a7f57f61e1b821fa6a4ea9c916dc6d77c'
FIXTURE_LABEL='jfr-20261024-verification-worker'
APPLY=0

if [ "${1:-}" = "--apply" ]; then APPLY=1; elif [ "$#" -ne 0 ]; then
  echo "usage: $0 [--apply]" >&2; exit 2
fi

for pair in \
  'jfr24verify-candidate|candidate' \
  'jfr24verify-bundle|trusted-bundle'; do
  volume=${pair%%|*}
  dir=${pair#*|}
  source="$BASE/fixture/$dir"
  if docker volume inspect "$volume" >/dev/null 2>&1; then
    inspect=$(docker volume inspect "$volume")
    printf '%s' "$inspect" | jq -e --arg label "$FIXTURE_LABEL" --arg source "$source" '
      length == 1 and .[0].Driver == "local" and
      .[0].Labels["jackin.fixture"] == $label and
      .[0].Labels["openshell.ai/sandbox-attachable"] == "true" and
      .[0].Labels["openshell.ai/sandbox-attachable-workspace"] == "default" and
      .[0].Options.device == $source and .[0].Options.o == "bind" and .[0].Options.type == "none"
    ' >/dev/null || { echo "refusing unexpected volume: $volume" >&2; exit 3; }
    users=$(docker ps -aq --filter "volume=$volume")
    [ -z "$users" ] || { echo "refusing in-use volume $volume: $users" >&2; exit 3; }
    echo "owned volume verified: $volume"
    if [ "$APPLY" -eq 1 ]; then docker volume rm "$volume"; fi
  else
    echo "owned volume already absent: $volume"
  fi
done

if docker image inspect jfr-20261024-verify-worker:baseline-python >/dev/null 2>&1; then
  image_id=$(docker image inspect jfr-20261024-verify-worker:baseline-python --format '{{.Id}}')
  [ "$image_id" = "$EXPECTED_IMAGE" ] || { echo "refusing unexpected image ID: $image_id" >&2; exit 3; }
  echo "owned image verified: $image_id"
  if [ "$APPLY" -eq 1 ]; then docker image rm jfr-20261024-verify-worker:baseline-python; fi
else
  echo "owned image already absent"
fi

config="$BASE/gateway/gateway.toml"
gateway_pids=$(ps -axo pid=,command= | awk -v cfg="$config" 'index($0, "openshell-gateway --config " cfg " ") { print $1 }')
if [ -n "$gateway_pids" ]; then
  [ "$(printf '%s\n' "$gateway_pids" | wc -l | tr -d ' ')" -eq 1 ] || {
    echo "refusing ambiguous gateway processes: $gateway_pids" >&2; exit 3;
  }
  pid=$gateway_pids
  echo "owned gateway verified: PID $pid ($config)"
  if [ "$APPLY" -eq 1 ]; then kill -TERM "$pid"; fi
else
  echo "owned gateway process already absent"
fi

if [ "$APPLY" -eq 0 ]; then
  echo "dry run only; pass --apply to remove the verified gateway, two volumes, and derived image"
fi
