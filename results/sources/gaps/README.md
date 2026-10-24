# Jackin source extracts for rewrite-readiness review

Source fetched read-only via connected GitHub fetch tools. Jackin repository: `jackin-project/jackin`. Revision: `41bad147b5ba9db09be99b07248531ce1bd867be` (commit reports source tree `a9581e5b9435294fe5e64083760154bbba9ac63a`). Excerpts below are saved with repository paths in their headings. Full source remains available at the pinned commit.

- `jackin-runtime-instance-model.mdx`: user-facing instance identity and lifecycle semantics.
- `jackin-network-egress-policy.mdx`: explicit scope of firewall and DinD child residual risk.
- `jackin-docker-runtime-hardening-contract.mdx`: current profile and enforcement claims.
- `jackin-idle-runtime-cleanup-design.mdx`: cleanup is research/incomplete, not a shipped crash-cleanup promise.
- `jackin-launch-dind.rs`: actual Jackin-managed sidecar/role ownership boundary.
- `jackin-docker-profile-readme.md`: profile resolution and Docker flag emission ownership.
- `jackin-command-*.mdx`: public eject/exile/hardline/purge semantics.
- `jackin-eject-resources.rs`, `jackin-purge.rs`, `jackin-dind-gc.rs`: active teardown and garbage collection behavior.
- `jackin-firewall.rs`, `jackin-profile-effective.rs`: active network policy mechanism and actual profile defaults.
- `jackin-profile-exec.rs`, `jackin-launch-session-policy.rs`: active allowlist command construction and pre-agent launch invocation.
- `architect-readme.md`, `architect-toolchain-mise.toml`: Rust development role and pinned Cargo/nextest environment.

Architect pin `7b72b38fe1d66e35c0931899c53bf3719592bbcc` is captured in `results/architect.source`; its README names the-architect as Jackin's Rust-development role and gives `jackin load the-architect`.
