# Agent handoff: reviewing OpenShell for a Jackin rewrite

## Read first

1. **[JACKIN_REWRITE_READINESS.md](JACKIN_REWRITE_READINESS.md)** — latest product-level assessment. Start here rather than treating every original infrastructure experiment as a Jackin requirement.
2. **[Product contract](results/rewrite-readiness/product-contract.md)** — current Jackin user behavior traced into implementation, including roles, accounts, Capsule, Git modes, lifecycle and conditional DinD.
3. **[Gap relevance](results/rewrite-readiness/gap-relevance.md)** and **[evidence audit](results/rewrite-readiness/evidence-audit.md)** — which gaps matter to Jackin, what execution actually proved, and what remains untested.
4. **[Independent synthesis review](results/rewrite-readiness/final-review.md)** — review of the revised product assessment.
5. **[CAPABILITY_MATRIX.md](CAPABILITY_MATRIX.md)**, **[DECISION.md](DECISION.md)**, **[measurements](results/MEASUREMENTS.md)** and **[README.md](README.md)** — original runtime experiment, reproduction details and narrower platform results.

## Purpose and boundaries

The work asks whether OpenShell can provide the runtime capabilities Jackin needs. It does not implement a Jackin rewrite. No Jackin product code or OpenShell source patch was made. The experiments use small scripts, one Rust fixture project, real installed Claude CLI versions, disposable dedicated Docker engines, and a separate test gateway.

Original requirements asked for stronger infrastructure properties than Jackin necessarily promises. The later product analysis does not erase original failures; it distinguishes implementation responsibilities from actual rewrite blockers. Source research is not runtime validation.

## Pinned sources

- Jackin for the product follow-up: `41bad147b5ba9db09be99b07248531ce1bd867be`.
- Earlier Jackin snapshot used by the PoC: `7d4b8acea25d28fd5286c958e3890148fc2bf40e`.
- Architect: `7b72b38fe1d66e35c0931899c53bf3719592bbcc`.
- Tested OpenShell stable release: `v0.1.5`, commit `bdb956f2cd65a635f1294fccf1d138d263bf650f`.
- Machine: macOS ARM64, OrbStack Linux ARM64 Docker engine. This is not a Docker Desktop or native Linux-host result. The separate OpenShell VM profile proved only a limited agent/build/file-retention slice.

See [source pins](results/rewrite-readiness/source-pins.json), saved source snapshots and commit-pinned links throughout the reports. Some files under `results/sources/gaps/` are labeled source extracts/summaries rather than verbatim source copies; consult their cited pinned files for full code.

## Current conclusion

**Enough evidence to start a focused OpenShell-backed runtime prototype. Not enough to commit to full runtime replacement or claim user-feature parity.**

Demonstrated: prebuilt agent images, selected local image delivery, lifecycle and terminal primitives, approved project-volume sharing, dedicated-engine mTLS connectivity, Docker/Compose, first-run Rust Testcontainers data exchange, and externally owned cleanup.

Observed restrictions: a rebuilt native binary's later protected network connection can fail integrity verification; unrelated policy updates close active connections; forcibly killed tests leave Docker children; external engines outlive OpenShell sandbox deletion; Docker children do not inherit agent egress policy.

Do not treat every restriction as a Jackin blocker:

- Jackin can continue owning its optional dedicated engine; OpenShell does not have to own it.
- Instant cleanup of every killed test and live network-rule editing are not established current Jackin promises.
- Current Jackin already discloses a partial Docker-child egress boundary.
- Normal edited-code development, real accounts/authentication, Capsule sessions, real project/Git access, retained state and lifecycle semantics are central product requirements.

## Most important missing proofs

1. Actual Architect plus an authenticated coding agent and Capsule: prompt, edit/build/test, send/interrupt/resize, reconnect and documented state retention.
2. Real host checkout behavior, read-only mounts, Shared/Worktree/Clone Git modes and concurrent host edits. The successful live-bind experiment shared a Docker volume between agent and daemon; it did not prove live host-worktree parity.
3. Modified Rust Testcontainers tests rerun with normal Cargo/nextest commands under the intended security profile. The Docker-executed workaround only ran a loopback test and returned a copied result file; it is not a validated full substitute.
4. Security-profile/grant translation, conditional Docker access and intended resource limits without silently weakening checks.
5. Jackin's hardline/eject/exile/purge and interrupted-create ownership/retention semantics.
6. The intended Rust control plane and Capsule full-duplex transport. The tested mTLS client was Python/CLI; the pinned Rust SDK lacks client-certificate mTLS in its curated transport and its curated exec is buffered/non-TTY. Raw RPC or existing CLI paths are possibilities, not completed integration proof.

Authenticated model operation was **NOT TESTED**. API-key placeholders, agent version output, gateway mTLS and Docker mTLS do not establish agent OAuth/API-key authentication. No personal agent credential file was inspected for an authenticated model task.

## What is in this archive

- Original and follow-up reports, independent reviews and source pins.
- `experiments/`: prototype scripts, gateway configurations, image recipes including failed/intermediate versions, Rust source and lockfiles, Compose fixture, policy files and cleanup scripts.
- `results/`: saved commands, statuses, stdout/stderr, negative cases, resource identities, timings, source material, independent repeats/reviews, cleanup and collateral-restoration evidence.
- `ARCHIVE_MANIFEST.json`: per-file size and SHA-256 inventory. The manifest does not hash itself.

Generated private keys, live credentials, SDK virtualenv, Docker image binaries, VM disks and live runtime state are not included. They were removed during scoped cleanup. Published image identities and rebuild recipes are retained. Public source/base-image caches outside this project are not part of the archive.

## Reproduction and incident caution

This archive is safe to read, not a request to execute every script. Scripts contain the original machine's absolute paths, fixed resource names, gateway ports and test IDs. Read and adapt the reproduction instructions before running them in a separate disposable environment. Recreate fresh test credentials; do not reuse original keys.

The initial test gateway temporarily shared a Docker namespace with an existing gateway. Three pre-existing sandboxes were found stopped; the initial terminating actor is unproven. They were subsequently restored after explicit user authorization, retaining their sandbox IDs, and all three passed Ready/exec verification. The incident and limitations are preserved in `results/collateral/`; isolation by unique gateway namespace is an important operational finding.

**Do not run `experiments/collateral/restore-originals.py` as a reproduction step.** It targets those three original sandbox IDs and installed credential paths. It is incident evidence, not part of the generic OpenShell experiment. Cleanup scripts are similarly scoped to the original experiment's resources; inspect them before any reuse.

## Review discipline

Preserve the negative results. Do not infer another platform, authentication method or user journey from a passing primitive. Separate user-facing parity from backend implementation details. Judge readiness for design/prototype, full replacement and shipping separately. The original user requested research and experiments, not production development.
