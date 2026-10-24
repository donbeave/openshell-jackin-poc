# Architect image reproduction

This procedure reproduces the selected-agent image construction experiment from the frozen public sources. It only builds images. It does not create an OpenShell sandbox or start the coding agent.

## Inputs

- Jackin source commit: `6e266406b49da2ab3c55355f3b7d33d1643ee6cd`.
- Architect role commit: `7b72b38fe1d66e35c0931899c53bf3719592bbcc`.
- OpenShell release tested separately: v0.1.5, commit `bdb956f2cd65a635f1294fccf1d138d263bf650f`.
- Target image platform: `linux/arm64`.
- Docker context: set `DOCKER_CONTEXT` for the local builder (the original test used `orbstack`).
- A Linux ARM64 `jackin-capsule` built from the pinned Jackin source. The original artifact SHA-256 is `60f50d7441a4caa64e92205444cc97868166a0714bac4c8b0a1fc334020de22d`; the binary is intentionally not included in public staging.
- `git`, Docker Buildx, mise, Rust, and network access to public GitHub and agent installer endpoints.

The original role build used the public Architect Dockerfile and pinned sources. The only role-specific changes were:

1. `jackin.role.toml`: point `published_image` at the local pinned base tag `jfr-20261024-architect-base:7b72b38`.
2. Append a behavior-neutral comment to `hooks/preflight.sh` so the role-source cache key changes.

The exact focused diff is `architect-role-inputs.patch`; its SHA-256 is recorded in `source-hashes.txt`. The reproduction script uses a filtered sparse checkout that excludes `.velnor` and `config/fleet/velnor-host.env` before worktree extraction, then copies only the Dockerfile's required inputs into the image-build context. During earlier evidence review, a one-off comparison transiently read tracked file bytes to identify path mismatches; it did not print or save that file's contents or a per-file hash. The historical handling is recorded in `source-hashes.json` and must not be described as “never read.” No host environment file is included in the exported patch or reproduction context.

## Run

Choose a new output directory for every run. The script checks out exact commits, builds the base image and Jackin CLI, applies only the two listed role changes, then invokes Jackin image prewarm for the selected agent. It records stdout, stderr, statuses, versions, and image IDs under that output directory.

```sh
export DOCKER_CONTEXT=orbstack
export JACKIN_CAPSULE_BIN=/path/to/pinned/linux-arm64/jackin-capsule
sh experiments/full-refactor-20261024/agents/role-reproduction/rebuild-role-image.sh \
  /tmp/jackin-openshell-role-rebuild-opencode opencode
```

Substitute a different agent listed in the script to reproduce that installer path. A version check is not an authenticated coding task. The original experiment had no approved model credentials, so authenticated coding remains **BLOCKED**.

The original `prewarm` implementation may reuse a mutable selected-agent image tag. The cache-switch reproduction and its actual OpenShell version checks are documented separately in `results/full-refactor-20261024/agents/role-findings.md` and the adjacent raw result directories.
