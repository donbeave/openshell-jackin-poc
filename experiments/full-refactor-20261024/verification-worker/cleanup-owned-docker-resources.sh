#!/bin/sh
set -eu
REPO=$(CDPATH= cd -- "$(dirname -- "$0")/../../.." && pwd)
OUT="$REPO/results/full-refactor-20261024/verification-worker/cleanup"
mkdir -p "$OUT"
if [ -s "$OUT/owned-containers-before.txt" ]; then
  echo "refusing cleanup: worker-labelled Docker containers existed in the recorded pre-cleanup inventory" >&2
  exit 1
fi
for spec in \
  'jfr24verify-candidate|/Users/example/openshell-jackin-public/experiments/full-refactor-20261024/verification-worker/fixture/candidate|candidate-volume-before.json' \
  'jfr24verify-bundle|/Users/example/openshell-jackin-public/experiments/full-refactor-20261024/verification-worker/fixture/trusted-bundle|bundle-volume-before.json'; do
  name=${spec%%|*}
  rest=${spec#*|}
  device=${rest%%|*}
  record=${rest#*|}
  file="$OUT/$record"
  jq -e --arg name "$name" --arg device "$device" \
    'length == 1 and .[0].Name == $name and .[0].Driver == "local" and
     .[0].Labels["jackin.fixture"] == "jfr-20261024-verification-worker" and
     .[0].Labels["openshell.ai/sandbox-attachable"] == "true" and
     .[0].Options == {"device":$device,"o":"bind","type":"none"}' "$file" >/dev/null
  docker volume rm "$name" >> "$OUT/docker-resource-cleanup-receipts.txt"
done
while IFS=' ' read -r reference expected_id; do
  [ -n "$reference" ] || continue
  actual_id=$(docker image inspect --format '{{.Id}}' "$reference")
  [ "$actual_id" = "$expected_id" ] || { echo "image identity mismatch: $reference" >&2; exit 1; }
  docker image rm "$reference" >> "$OUT/docker-resource-cleanup-receipts.txt"
done < "$OUT/derived-image-tags-before.txt"
for name in jfr24verify-candidate jfr24verify-bundle; do
  if docker volume inspect "$name" >/dev/null 2>&1; then echo "volume remains: $name" >&2; exit 1; fi
done
if docker image ls --format '{{.Repository}}:{{.Tag}}' --filter 'reference=jfr-20261024-verify-worker:*' | grep -q .; then
  echo "derived worker image tag remains" >&2
  exit 1
fi
printf '%s\n' 'confirmed absent: exact two owned volumes and all eight recorded derived image tags; shared base images/caches untouched' >> "$OUT/docker-resource-cleanup-receipts.txt"
