#!/bin/sh
set -eu

# Rebuild selected-agent Architect image from frozen public sources.
# Performs image construction only: no OpenShell sandbox or agent process.

if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
    echo "usage: rebuild-role-image.sh NEW_OUTPUT_DIR [agent]" >&2
    exit 2
fi
out=$1
agent=${2:-opencode}
case "$agent" in
    claude|codex|amp|opencode|kimi|grok) ;;
    *) echo "unsupported Architect agent: $agent" >&2; exit 2 ;;
esac
if [ -e "$out" ]; then
    echo "output path already exists; choose a fresh directory" >&2
    exit 2
fi
if [ -z "${JACKIN_CAPSULE_BIN:-}" ] || [ ! -x "$JACKIN_CAPSULE_BIN" ]; then
    echo "JACKIN_CAPSULE_BIN must name the executable Linux ARM64 Capsule artifact" >&2
    exit 2
fi

jackin_commit=6e266406b49da2ab3c55355f3b7d33d1643ee6cd
architect_commit=7b72b38fe1d66e35c0931899c53bf3719592bbcc
base_tag=jfr-20261024-architect-base:7b72b38
docker_context=${DOCKER_CONTEXT:-default}
mkdir -p "$out"
out=$(cd "$out" && pwd)
src="$out/src"
jackin="$src/jackin"
architect="$src/architect-pinned"
role="$src/architect-derived"
base_context="$src/architect-base-context"
mkdir -p "$src"

date -u '+%Y-%m-%dT%H:%M:%SZ' > "$out/started-utc.txt"
clone_pinned() {
    url=$1
    dest=$2
    rev=$3
    label=$4
    git clone --filter=blob:none --no-checkout "$url" "$dest" > "$out/$label-clone.stdout.txt" 2> "$out/$label-clone.stderr.txt"
    git -C "$dest" sparse-checkout init --no-cone
    git -C "$dest" sparse-checkout set --no-cone '/*' '!/.velnor/**' '!/config/fleet/velnor-host.env'
    git -C "$dest" checkout --detach "$rev" > "$out/$label-checkout.stdout.txt" 2> "$out/$label-checkout.stderr.txt"
    test "$(git -C "$dest" rev-parse HEAD)" = "$rev"
    test ! -e "$dest/config/fleet/velnor-host.env"
}
clone_pinned https://github.com/jackin-project/jackin.git "$jackin" "$jackin_commit" jackin
clone_pinned https://github.com/jackin-project/jackin-the-architect.git "$architect" "$architect_commit" architect
clone_pinned https://github.com/jackin-project/jackin-the-architect.git "$role" "$architect_commit" role

# Create a curated base build context from exact role files required by the
# Dockerfile. The omitted .velnor directory and host fleet environment path are
# excluded before copy and never read or staged.
mkdir -p "$base_context/AGENTS.md.d" "$base_context/jackin-toolchain"
cp "$architect/Dockerfile" "$architect/caveman-config.json" "$architect/jackin.role.toml" "$base_context/"
cp "$architect/hooks/preflight.sh" "$base_context/hooks-preflight.sh"
cp "$architect/AGENTS.md.d/"*.md "$base_context/AGENTS.md.d/"
cp "$architect/jackin-toolchain/mise.toml" "$architect/jackin-toolchain/rust-toolchain.toml" "$base_context/jackin-toolchain/"
docker --context "$docker_context" buildx build --load --progress=plain --platform linux/arm64 \
    --label org.jackin.poc.id=jfr-20261024-role-rebuild \
    --tag "$base_tag" "$architect" > "$out/base-build.stdout.txt" 2> "$out/base-build.stderr.txt"
docker --context "$docker_context" image inspect "$base_tag" --format '{{.Id}} {{.Os}}/{{.Architecture}} {{.Size}}' > "$out/base-image.txt"

python3 - "$role/jackin.role.toml" "$role/hooks/preflight.sh" "$base_tag" <<'PY'
from pathlib import Path
import sys

manifest = Path(sys.argv[1])
hook = Path(sys.argv[2])
base = sys.argv[3]
original = 'published_image = "docker.io/projectjackin/jackin-the-architect:latest"'
replacement = f'published_image = "{base}"'
text = manifest.read_text()
if text.count(original) != 1:
    raise SystemExit("expected one pinned published_image line")
manifest.write_text(text.replace(original, replacement))
hook.write_text(hook.read_text() + "\n# POC role-source cache-key change: 2026-10-24, behavior unchanged.\n")
PY
changed=$(git -C "$role" diff --name-only)
test "$changed" = "hooks/preflight.sh
jackin.role.toml"
git -C "$role" add -- hooks/preflight.sh jackin.role.toml
GIT_AUTHOR_NAME='Jackin OpenShell POC' GIT_AUTHOR_EMAIL='poc@example.invalid' \
GIT_COMMITTER_NAME='Jackin OpenShell POC' GIT_COMMITTER_EMAIL='poc@example.invalid' \
    git -C "$role" commit -m 'Apply local OpenShell role image test inputs' > "$out/role-commit.stdout.txt" 2> "$out/role-commit.stderr.txt"
git -C "$role" rev-parse HEAD > "$out/role-commit.txt"

mkdir -p "$out/jackin-home" "$out/jackin-config"
printf '\n' > "$out/jackin-config/config.toml"
mise exec -- cargo build --locked --release --target-dir "$out/jackin-target" -p jackin \
    --manifest-path "$jackin/Cargo.toml" > "$out/jackin-build.stdout.txt" 2> "$out/jackin-build.stderr.txt"
jackin_bin="$out/jackin-target/release/jackin"
"$jackin_bin" --version > "$out/jackin-version.txt" 2>&1

export JACKIN_HOME_DIR="$out/jackin-home"
export JACKIN_CONFIG_DIR="$out/jackin-config"
export JACKIN_CAPSULE_BIN
export DOCKER_CONTEXT="$docker_context"
export NO_COLOR=1
"$jackin_bin" prewarm --agent "$agent" --image --role jfr24/architect --role-git "$role" \
    > "$out/prewarm.stdout.txt" 2> "$out/prewarm.stderr.txt"
docker --context "$docker_context" image inspect "jk_jfr24_architect:$(git -C "$role" rev-parse --short HEAD)" \
    --format '{{.Id}} {{.Os}}/{{.Architecture}} {{.Size}} {{.Config.User}}' > "$out/derived-image.txt"
shasum -a 256 "$JACKIN_CAPSULE_BIN" "$out/derived-image.txt" > "$out/artifact-hashes.txt"
echo "role-image build completed; logs and image identities are in $out"
