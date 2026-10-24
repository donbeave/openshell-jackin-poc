# Architect image POC

Purpose: test the pinned role build and selected Claude installation version. No Jackin product code changed.

`build-selected-agent.sh VERSION TAG` retrieves Claude's version manifest, verifies Linux ARM64 binary SHA-256, then invokes Docker Buildx with the pinned Architect base recipe. The script currently models Jackin's native `claude install` block. The observed 2.1.309 input installed 2.1.310, so the script is an intentionally failing reproduction of current Jackin behavior. The shell script only builds an image; it does not run a workload.

`Dockerfile` and reduced-hook image are a diagnostic workaround fixture. They omit the two Tailrocks marketplace/plugin entries because the current Claude marketplace command rejects those repositories. Never call this reduced fixture the actual Architect image.

The failed full recipe is retained as `Dockerfile.full-role-failing`; its SHA-256 matches the `ROLE_CONTENT_SHA` recorded in the failing Buildx command. `build-selected-agent.sh` retrieves manifest and binary URLs recorded in the evidence, verifies the binary checksum, then builds. Downloaded binary payloads were removed after hashes were retained. The last repeat attempt is recorded as failed because the payload had been cleaned before `COPY`; do not claim derived cache reuse from it.

`run-hook-probe.sh` is disabled. Its earlier contents ran a role hook and agent version inside Docker. Its captured output is historical diagnostic only and excluded from replacement evidence. Use the parent isolated OpenShell fixture for runtime verification.

See `../../evidence/role/` for source refs, exact failure, output digests, versions, and limits.
