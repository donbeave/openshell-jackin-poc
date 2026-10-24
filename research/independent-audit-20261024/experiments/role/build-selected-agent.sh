#!/bin/sh
set -eu
if [ "$#" -ne 2 ]; then
    echo "usage: $0 CLAUDE_VERSION IMAGE_TAG" >&2
    exit 2
fi
version=$1
tag=$2
root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
manifest="$root/claude-$version-manifest.json"
mkdir -p "$root/$version"
curl -fsSL "https://downloads.claude.ai/claude-code-releases/$version/manifest.json" -o "$manifest"
expected=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["platforms"]["linux-arm64"]["checksum"])' "$manifest")
curl -fL "https://downloads.claude.ai/claude-code-releases/$version/linux-arm64/claude" -o "$root/$version/claude"
actual=$(shasum -a 256 "$root/$version/claude" | awk '{print $1}')
if [ "$actual" != "$expected" ]; then
    echo "Claude binary checksum mismatch for $version" >&2
    exit 1
fi
role_hash=$(python3 - "$root" <<'PY'
import hashlib, pathlib, sys
root = pathlib.Path(sys.argv[1])
source = root.parents[1] / "sources" / "architect"
paths = [source / "Dockerfile", source / "jackin.role.toml", source / "hooks/preflight.sh", source / "jackin-toolchain/mise.toml", root / "Dockerfile", root / "preflight.sh"]
h = hashlib.sha256()
for path in paths:
    h.update(str(path.relative_to(root.parents[1])).encode())
    h.update(b"\0")
    h.update(path.read_bytes())
    h.update(b"\0")
print(h.hexdigest())
PY
)
docker buildx build --builder orbstack --platform linux/arm64 --load \
    --tag "$tag" \
    --build-arg "CLAUDE_VERSION=$version" \
    --build-arg "ROLE_CONTENT_SHA=$role_hash" \
    "$root"
