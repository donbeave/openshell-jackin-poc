# Final review: Jackin rewrite readiness synthesis

## Verdict

**Approved with one completeness note.** `JACKIN_REWRITE_READINESS.md` reaches the supported readiness split: bounded design/prototype **YES**; full replacement commitment **NO**; ship parity **NO**. It separates pinned Jackin source findings from PoC execution and avoids turning every infrastructure gap into a Jackin promise.

No material false claim found in the requested precision checks:

- Rust SDK limitation is scoped to the published Rust SDK; synthesis explicitly says OpenShell overall does not lack mTLS or interactive execution and that raw RPC/CLI routes remain to be proved.
- Jackin remains the current owner of conditional DinD. OpenShell-native daemon ownership is not required; manual external fixture evidence does not prove Jackin reconciliation.
- Named-volume agent↔DinD exchange is not described as a host repository bind. The synthesis calls out missing Shared/Worktree/Clone and host bind proof, plus OpenShell's documented mount/admission configuration.
- Docker-executed Rust proof is correctly identified as loopback-only and distinct-target with returned files, not a proven changed Testcontainers cycle.
- Architect's six choices are distinguished from Jackin's twelve source-enumerated adapters, filtered by role. The enum is not called twelve validated runtime integrations.
- OpenShell's packaged VM experiment is not equated with Jackin's partial Apple Container backend.
- Current standard profile/network-open behavior is not used to infer that same-path denial vanishes: synthesis says that profile was not tested.
- Live-policy update is correctly treated as conditional. It notes account/provider updates might still trigger effective-policy reloads and require testing.
- No requirement for immediate cleanup after every killed test is introduced. Explicit eject/exile runtime teardown and state retention are distinguished from destructive purge.

All six PoC gap categories receive current-product relevance and practical semantics. Current Jackin source supports the key distinctions: scoped-egress rebuild risk; no live rule editor found, with reload caveat; no promise of per-test SIGKILL cleanup; Jackin-owned DinD lifecycle; documented partial child egress boundary; authenticated agent task as required user-ready proof.

## Completeness note

The synthesis has a small but meaningful product-parity omission: Jackin's effective profile grants include more than network and DinD. Source defines `sudo`, `system_writes`, `user`, memory/CPU/PID/file limits, capabilities, and `no_new_privileges` in `crates/services/jackin-runtime-docker-profile/src/docker_profile/effective.rs:10-23`; profile defaults materially differ (`:26-87`). Root capability provisions sudo (`.../docker_profile/exec.rs:32-34`). The OpenShell PoC tested a narrow memory limit and separate external-engine limits, but did not execute Jackin effective-profile mapping, sudo provisioning, system-write behavior, added capabilities, or equivalent no-new-privileges/resource policy.

Recommend adding this to the “Important rewrite questions” and one acceptance gate: **Profile and privilege mapping** — for each intended Jackin profile/grant, prove the translated OpenShell user, sudo/system-write behavior, capabilities, resource limits, and network/DinD grants; preserve any explicit unsupported-grant UX. Treat this as an untested parity surface, not a claim that OpenShell cannot provide it.

This omission does not change the readiness verdict. The main synthesis remains a sound basis to start a bounded prototype, not a full replacement decision. No runtime/build/credential action was performed for this review.

## Final delta review

Root synthesis now includes the recommended security/profile translation gate for network/user/sudo/system-write/capability/no-new-privileges/Docker/resource-limit semantics. It also states that OpenShell's equivalent network-open profile was not tested, so the changed-native-binary issue cannot be assumed absent there. Product source links distinguish existing Shared/Worktree/Clone semantics and conditional Jackin-owned DinD from OpenShell ownership requirements. The earlier completeness finding is resolved.

**Final disposition: approved.** No further source, PoC, or runtime claim requires correction for this review. Design/prototype **YES**; full replacement **NO**; ship parity **NO**. This was read-only review; no new runtime, build, credential, or gateway action.
