# Supplemental role-tools image delta

Base: Architect role-tools image `jfr-20261024-architect-base:7b72b38`, immutable ID `sha256:e7655072c6d511250b183e9511ca1f701e635766ec0d190a68bfe470745df63a`, linux/arm64.

The pinned base image sets `agent` primary GID 0. OpenShell v0.1.5 rejects it with `IdentityResolutionFailed: workload identity must not contain UID or GID zero`. Derived experiment image creates group `sandbox` GID 1000 and sets `agent` primary group to it. This removes GID 0 from the workload identity; it does not broaden privilege.

The base also carried mise 2026.7.12 and Rust 1.98.1. Architect's pinned toolchain asks for mise 2026.10.18, Rust 1.99.1 and mbx 1.27.0. Derived image replaces mise from its checksum-pinned official binary and adds checksum-pinned mbx 1.27.0. This image has no installed coding agent and no Jackin Capsule. Results from it are supplemental toolchain/runtime evidence, not actual Architect agent or Capsule evidence.
