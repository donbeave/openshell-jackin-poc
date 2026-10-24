# Architect role image proof

## Result

**FAIL for the actual Architect role image and selected-version installation.** Docker can assemble the pinned Architect tool image and Jackin derived image layers, but the full role plugin recipe fails at a declared marketplace. A verified Claude 2.1.309 native installer artifact then installs Claude Code 2.1.310. A reduced workaround image was built for diagnostic purposes; it is not a full-role PASS.

No Jackin product source changed. OpenShell runtime execution is not established by this image work. Parent's Capsule POC owns the separate OpenShell runtime test.

## Pins and environment

- Jackin: `6e266406b49da2ab3c55355f3b7d33d1643ee6cd`.
- Architect: `7b72b38fe1d66e35c0931899c53bf3719592bbcc`.
- OpenShell parent fixture baseline: `v0.1.5`, `bdb956f2cd65a635f1294fccf1d138d263bf650f`.
- Platform: macOS ARM64, OrbStack Linux ARM64 Docker Engine. Client `29.9.2`; engine `29.8.2`; kernel `7.2.9-orbstack-00391-g2b298d05fbd4`.
- Builder: Docker Buildx, builder `orbstack`, BuildKit `v0.33.1`, `--platform linux/arm64`.
- Base: Architect `Dockerfile` pins Construct `projectjackin/construct:0.37-trixie@sha256:67fc093e1dd9a021e2af66beebbeddbb4d676839dcd0a5371ce8a5d7b2cdcab4`.
- Build cache: Architect steps reported `CACHED`; this proves a warm cache path, not a cold-host build. A prior derived-repeat observation was not retained as raw output and is not counted. A logged repeat on 2026-10-24 failed before cache lookup because coordinated cleanup removed the downloaded Claude `COPY` input; see `warm-repeat-build.log`. Cache reuse for the derived recipe is therefore NOT TESTED on retained evidence. Forced rebuild, role-content change matrix, remote registry delivery and other target types remain NOT TESTED.

Full inputs, image IDs/digests, platform, source manifest and detailed limitations: `source-resolution.txt`. Build logs: `build-2.1.309.log`; full plugin failure: `full-recipe-marketplace-failure.log`.

## Full role plugin failure

Jackin's pinned `render_claude_plugin_section` in `crates/adapters/jackin-image/src/derived_image.rs:219-254` emits a `claude plugin marketplace add <source>` command for each role marketplace, then `claude plugin install` for each configured plugin. With Claude Code `2.1.310`, the actual Architect recipe failed at `tailrocks/tailrocks-rust-skills`:

`Marketplace file not found at /home/agent/.claude/plugins/marketplaces/tailrocks-tailrocks-rust-skills/.claude-plugin/marketplace.json`

The role also declares `tailrocks/tailrocks-roadmap-skills`; it has the same incompatible shape. Resolved public repository HEADs were `18467d1531760a017d425509ce461569a306895e` and `51d058af8e800a7f39a850a51728461525f3c9d2`. Both contain `.claude-plugin/plugin.json`, not the required marketplace file. No plugin list was fully installed. This is a required actual-role launch blocker. Fix the role entries or publish valid marketplace manifests, pin their revisions, then rebuild the full role and execute its preflight in OpenShell.

The full failed recipe is preserved at `experiments/role/Dockerfile.full-role-failing` (SHA-256 `d34b1d106ba3dae26357af52a6f5c107b223ba4249b8fbabe06b47acaeb6ca49`). The reduced `experiments/role/Dockerfile` has SHA-256 `655f8f6da67eaa68efb2776548cfd7787825e429afc03d1049e4ebda0acc3173` and omits those two marketplace sources and their plugins. Images using it are workaround fixtures and cannot support a full Architect readiness pass.

## Agent version mismatch

The pinned Jackin Claude native `AgentRuntime::install_block` (`crates/core/jackin-core/src/agent/adapters/claude.rs`) copies a verified host-prefetched binary and runs `/jackin/agent-binaries/claude install`, then `claude --version`. `build-selected-agent.sh` reproduced this using the official version-specific binary manifest and checksum:

- Claude `2.1.310` Linux ARM64 binary SHA-256: `9c64d9a7442436b65fcd7cc02c1aa0051bb5a7041e7788576ed3b5f29c447d54`.
- Claude `2.1.309` Linux ARM64 binary SHA-256: `9796dd26899337f687739a0b39a7353b639f062a3436a7b941fcf19a1b757a9b`.

The derived build for input `2.1.310` reported `2.1.310`. Changed input `2.1.309` passed manifest checksum verification, rebuilt the derived image on cached Architect base layers and reported `2.1.310` inside the Dockerfile build. Selected agent version is therefore not controlled by the copied artifact on this path. This is build-time verified output, not a direct runtime `docker run` probe.

Proposed solution: use a package/version installation mechanism that honors the selected version, or revise the native installer invocation to install that exact release. Smallest experiment: in a clean full Architect derived build, install exact Claude package version `2.1.309` without prefetched version metadata, assert `RUN claude --version` reports `2.1.309`, and verify the resulting digest/version label in an OpenShell sandbox. Then rebuild `2.1.310` and repeat.

## Tool and hook observations

The pinned Architect base image included its role Dockerfile's actual mise tool recipe. Source recipe and resolved versions are recorded in build logs and source pin notes: Rust/Cargo `1.98.1`, cargo-nextest `0.9.140`, uv `0.12.15`, Node `24.21.0`, headroom `0.37.0`, RTK `0.49.0`; Claude `2.1.310`. These are actual observed versions, not claims about the newer root-level role source `mise.toml` pins.

The real Architect preflight is included at `/jackin/runtime/hooks/preflight.sh`. A historical direct-Docker diagnostic initially failed because the reduced image lacked the Caveman plugin; manually installing a subset made the hook proceed, but tool path and mise behavior were not fully validated. Those direct-Docker logs are explicitly excluded under `excluded-docker-probes.md`. Only an OpenShell execution can establish role-hook behavior under OpenShell's entrypoint control.

The full role's unauthenticated plugin and hook installation is distinct from a usable authenticated coding session. No personal credential was read. No live model request ran. Agent authentication remains NOT TESTED.

## Cache identity and ownership

Docker owns the builder image and BuildKit cache. OpenShell gateway imports/pulls a digest into its own target store; the role experiment only established same-engine image presence through Docker builds. No remote target transfer was tested. Jackin's production source computes recipe labels in `jackin-image/src/image_recipe.rs`; the native agent installer in `jackin-runtime-image/src/image/build.rs` adds image labels from prefetched agent metadata. This POC label includes role revision, recipe-content hash, agent slug and requested version; actual image digest remains the immutable execution identity.

One reduced workaround image tag (`jrr24-architect-claude:2.1.310-hookproof`) was removed after an empty Docker container-consumer check and parent confirmation that no Capsule sandbox referenced Architect tags. Receipt: `image-ownership-receipt.json`. Its sibling workaround image, other experiment images, shared Architect base, and BuildKit cache remain. Claude binary payloads were removed after manifest URLs and checksums were retained in `external-source-pins.json`; the build script downloads and verifies them when replayed. No shared or foreign resource was pruned.

## Evidence classification

| Requirement | Result | Mechanism | Evidence limit |
|---|---|---|---|
| Build pinned Architect tool image with Docker/Buildx | PASS | Docker builder, cached pinned base + pinned role Dockerfile | Warm BuildKit layers; not complete derived role |
| Build actual full Architect Claude role | FAIL | Jackin derived Dockerfile renderer + Claude 2.1.310 | Tailrocks marketplace command fails, so full plugin installation stops |
| Reuse valid image cache | NOT TESTED | Docker BuildKit | Prior repeat output was not retained; logged repeat failed before cache lookup after binary cleanup |
| Force rebuild | NOT TESTED | Docker Buildx | No `--no-cache` run |
| Change role content and validate identity | NOT TESTED | Docker Buildx | No controlled source mutation + digest acceptance |
| Change Claude from 2.1.310 to 2.1.309 | FAIL | Jackin native installer block | Exact 2.1.309 source checksum verified; final build output remains 2.1.310 |
| Install exact version without prefetched metadata | NOT TESTED as complete role | Candidate pinned npm package route | Earlier ephemeral direct-Docker diagnostic is excluded; no full recipe build or OpenShell assertion |
| Run role hook under OpenShell entrypoint | NOT TESTED here | OpenShell sandbox command needed | Parent Capsule POC must report separately; Docker-only logs excluded |
| Authenticated coding session | NOT TESTED | Real selected account required | No credentials used |
| Remote image delivery/authentication/architecture failure/retry | NOT TESTED | Target registry/OpenShell image pull needed | Same-engine local image only |
