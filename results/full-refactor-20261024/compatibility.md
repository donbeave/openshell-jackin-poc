# Compatibility and scope analysis

Selected Jackin revision changed from `41bad147b5ba9db09be99b07248531ce1bd867be` to `6e266406b49da2ab3c55355f3b7d33d1643ee6cd` at the user’s updated reference. Architect7b and released OpenShellbdb remain unchanged. Full name-status diff: `jackin-revision-diff.txt`. There are34 changed Jackin files in total;12 are in Capsule. These are different counts, not contradictory provenance.

| Evidence | Decision | Applicability and limit |
|---|---|---|
| Rust gateway transport, mTLS, raw RPC lifecycle/duplex/PTy/idempotency | REUSE narrow primitives | No Jackin binary is executed; exact same OpenShell release, local gateway configurations and official image/control client. Does not cover Capsule or authorization. |
| Two-gateway inventory and unavailable-target handling | REUSE narrow primitives | Independent Rust control fixture uses OpenShell types only. Linux guest is a separate profile, not remote or native host evidence. |
| Approved host-backed named-volume Git/storage primitives | REUSE narrow primitives | Actual Architect base7b and OpenShellbdb unchanged; Jackin materializer/account/hook code was not invoked. Complete workspace journey remains unproved. |
| Native Rust Testcontainers and changed-binary denial | REUSE narrow primitives | Standalone Rust fixture/role-tools image/OpenShell release pinned independently of Jackin. Profile translation and ordinary command workflow limitations remain visible. |
| Role base Docker build | REUSE only role-tool image | Architect source7b unchanged; full selected-agent derived recipe/hook/account path requires its own current-source execution. |
| Old41bad CLI prewarm/Capsule prerequisite | KEEP separate; no current-CLI PASS | Image code unchanged but process library and child handling changed; new6e CLI experiment required. Old failure retained. |
| Any41bad Capsule process/session/child lifetime | DO NOT REUSE | 34 changed files across Jackin include12 Capsule files and generic process/reaping libraries. Current6e process path must execute. |
| Current6e actual Capsule root-wrapper/Linux and nativeMac restriction | USE current-pin results only | New6e binary identity and toolchain recorded by role experiment. Does not prove session/authentication parity. |
| Historical policy-update stream loss/rootless/VM | COMPARISON only unless exact relevant configuration documented | Do not infer full profile behavior, managed daemon ownership or changed credential-update route from old experiments. |
| Experimental immutable-ID Delete patch | SEPARATE EXPERIMENTAL OpenShell patch | Different source/binary from releasedbdb. Only guardedDelete behavior qualifies after built positive and negative tests; stop/exec safety unchanged. |

## Explicit scope change

The updated user request allows fresh setup after user-owned legacy removal. Legacy state/configuration migration and import are excluded. No unrelated deletion is authorized. New-design private data, workspaces, retention, recovery and recreation remain required. Old top-level matrices describe the earlier full-replacement request; the new full-refactor contract supersedes only the explicitly changed migration requirement and adds explicit verification-worker and complete-source-inventory coverage. No old failure is removed.

The mechanism terms in earlier evidence are preserved verbatim. For the new report: RELEASED means Released OpenShell feature; CONFIGURATION means Configuration; EXTERNAL FIXTURE means External service; WORKAROUND means Workaround; EXPERIMENTAL PATCH means Experimental OpenShell patch; RETAINED HOST LOGIC maps to retained Jackin product logic, while a new Jackin fixture adaptation is labeled Jackin-side adaptation. This translation does not promote an old result.
