# Independent design and security review

Scope: read-only challenge of the proposed full replacement architecture and the first follow-up requirement matrix. Source pins are recorded in `source-pins.json`. This review does not count source inspection as runtime proof.

## Findings

### 1. Rust mTLS client route is plausible, still requires validation

The pinned OpenShell SDK exposes public `OpenShellClient::from_parts(Channel, EdgeAuthInterceptor)` and `raw_grpc()` (`results/rewrite-readiness/sources/openshell-rust-sdk-client.rs:71-83`). The public `ClientConfig` explicitly lacks client-certificate support (`openshell-rust-sdk-config.rs:55-65`). Therefore a caller-built Tonic TLS `Channel` with a private CA and client identity is a reasonable released-SDK composition; it avoids the insecure verification flag and avoids CLI human-output parsing.

This route still needs execution proof for server CA validation, hostname validation, client-certificate identity, rejection cases, and the exact v0.1.5 Tonic/rustls versions. `from_parts` does not itself establish TLS correctness, OIDC refresh, reliable retries, or a stable streaming session API. Keep the Rust SDK and raw generated gRPC calls behind a small experiment client until those contracts pass. Don't build a larger control service around this yet.

### 2. Root Capsule launch retains security controls, but is a high-risk boundary

The proposed unchanged Capsule daemon launched as root, with `JACKIN_CAPSULE_FORCE_DAEMON=1` scoped only to the daemon, matches the source's root-required identity transition better than the prior nonroot shell experiment. This is a good first test, not an approved architecture yet. Test the real Capsule binary and its root wrapper under the unmodified OpenShell restrictions. Record actual UID/GID, supplementary groups, capabilities, Landlock rules, NNP, filesystem visibility and two-account home separation. Then prove client commands (`attach-proxy`, `take-control`, `release-control`) do not daemonize.

If OpenShell cannot retain root and the required capabilities, fail at the exact point. Do not grant broad privilege or remove account identity fields. An alternative supervisor would be substantial product work unless Jackin already contains a supported equivalent process model; a mock shell cannot replace this proof.

### 3. Host bind mount boundary is a release-level blocker under the stated security rule

The pinned runtime docs require both `enable_bind_mounts=true` and `resource_admission.enabled=false` for Docker-driver host binds (`results/sources/docs__how-it-works__sandboxes__runtimes.mdx:171-182`). The same text warns that binds can bypass workspace isolation and filesystem policy. There is no reviewed source evidence here for a path allowlist that safely compensates for globally disabled admission.

Retaining admission and demonstrating the bind rejection is safe evidence, but it does not satisfy Shared/worktree/clone live host behavior. Disabling admission without a replacement authorization boundary is not acceptable. Required next smallest experiment: on an isolated, disposable gateway, test an ordinary approved volume and the denied host bind under unchanged admission; inspect the full released admission API/config for a narrow per-path authorization primitive. If none exists, record an upstream scoped-bind/admission interface as a blocker rather than broadening the gateway.

### 4. External dedicated Docker engine can fit ownership, but its authority remains broad

Jackin already owns its optional engine, certs, network, children and teardown in the pinned source map (`workspace-source.md`, `control-source.md`). So an external dedicated engine is architecturally compatible if Jackin retains a resource ledger and the default sandbox gets no endpoint, socket or credential. OpenShell sandbox deletion alone will not clean this external engine. The Jackin-owned eject/exile/purge path must explicitly clean it and preserve retained state rules.

An mTLS Docker client certificate generally grants engine-admin API authority. Keep one engine, key, data directory, network and allowed service-port range per instance; test cross-instance denial at both API and application ports. Do not claim the OpenShell agent's egress policy contains engine children. The historical fixture only demonstrates external daemon connectivity and a narrow first-run development workflow; it does not prove this ownership composition or full rewritten Jackin behavior.

### 5. Identity-safe cleanup and retry semantics are not optional

Jackin's current destructive path validates immutable container IDs and refuses mismatches (`control-source.md`, `crates/services/jackin-runtime/src/runtime/cleanup/eject.rs:53-76`). A replacement must anchor mutations and cleanup to immutable gateway/sandbox identity plus an instance generation/owner record. A list/get by reusable display name followed by stop/delete by name leaves a stale-target race. Test delete, same-name recreation, then delayed stop/delete/exec against the old identity; prove the replacement survives.

The pinned v0.1.5 SDK populates mutation `request_id` with an empty string. No current evidence proves caller-supplied idempotency keys or exactly-once behavior after a lost response. The required same-request-ID retry marker experiment may expose an API limitation rather than a client bug. Never automatically replay agent prompts. Unknown create/exec results must remain unknown until reconciled by immutable IDs/events/state queries.

These may require narrow upstream API additions (caller request IDs, generation/conditional mutations) if the gateway service lacks them. If existing RPC request fields already support caller IDs, using raw generated calls may be a small integration change; prove server deduplication before treating that as sufficient.

### 6. The current top-level matrix needs more traceability before it is a decision artifact

`FULL_REPLACEMENT_MATRIX.md` currently has 33 broad rows with generic source areas and a repeated generic positive/negative statement. It does not yet record exact pinned source paths for every behavior, target/profile per row, component/resource owner per additional resource, distinct auth paths, installer/hook paths, or evidence-specific reuse decisions. The three companion source reports improve traceability but do not make every requirement row auditable. Keep this matrix marked **draft/source map**, and reconcile it to `agents-requirements.json`, `workspace-requirements.json`, and `control-requirements.json` before final verdict. Do not mark aggregate rows PASS when only one primitive or one platform passed.

## Target and scope conclusion

The currently available platform is macOS ARM64 with OrbStack's Linux ARM64 Docker engine. Historical OpenShell v0.1.5 tests apply only to the specific primitives and configuration recorded; the limited packaged VM slice does not establish Docker Desktop, native Linux, complete VM parity, remote macOS/Linux, or Kubernetes. Each required profile needs its own full journey. Missing machines, clusters, credentials, or transport remain BLOCKED/NOT TESTED and prevent a full-readiness verdict.

The six additional Jackin enum adapters without active entrypoint launch paths are existing Jackin behavior defects, not OpenShell regressions. Preserve their current rejection semantics at this pinned source unless separately authorized scope changes. The six actual Architect agents still each need install/start/auth evidence; shared evidence only applies where launcher and credential/state paths truly match. Live authenticated tasks remain blocked until approved test credentials are available.

## Addendum: Jackin-authorized bind-backed named volumes

The proposed local-driver volume is a coherent **candidate architecture** for preserving Jackin's host-workspace boundary. Jackin's trusted host controller can canonicalize and authorize a checkout, create a Docker local-driver volume with `type=none,o=bind,device=<authorized-path>`, label it for OpenShell's workspace admission, then attach that named volume with resource admission still enabled. The agent sees the live host files through the mount; Jackin retains path authorization and engine ownership. This is a Jackin-owned host mount component using Docker driver infrastructure. It is not evidence that OpenShell itself authorizes arbitrary host paths safely.

The workspace agent was asked to test the exact release behavior. It must not change admission configuration. The pinned v0.1.5 guide documents direct host `bind` mounts as requiring `enable_bind_mounts=true` plus disabled resource admission (`runtimes.mdx:171-182`), but it does not expressly say whether a named local volume whose driver options bind a host path is classified as a `bind` by that gate. Current `main` documentation's additional `enable_bind_mounts` mention does not establish v0.1.5 behavior. Only an execution on the clean v0.1.5 gateway can settle whether this volume route is released with admission enabled. If it requires disabling admission, do not disable it for a positive result; record the denial and use a narrow Jackin-side mount broker/admission interface as the blocker.

Security conditions for any positive result:

- Only the trusted Jackin host component can access the Docker control socket and create/relabel volumes. Agent processes and ordinary sandbox commands cannot call Docker volume APIs.
- Resolve source and required Git metadata paths against an explicit workspace authorization record; reject traversal, unauthorized siblings, unexpected symlinks, and protected targets. Record the exact canonical paths.
- Inspect volume driver/options/device and owner/workspace labels before attach; reject mismatches. Treat labels as authorization metadata checked by the trusted control path, not as cryptographic proof.
- Test read-only enforcement, writable behavior only when granted, relative and absolute symlinks, a sibling canary, host/agent edits, atomic replacement, file-watch behavior, and two instances using Shared/Worktree/Clone semantics.
- Test recreation/reuse of a volume name and source path. Do not assume a Docker volume name is immutable identity. If the daemon has no immutable volume ID, keep Jackin's owner manifest and fail closed on any inspected option/label/path mismatch immediately before attach; document the remaining daemon-administrator trust assumption.

Thus the reviewed pattern does not inherently weaken Jackin's intended boundary, but remains **NOT TESTED** until released v0.1.5 accepts it with admission enabled and the negative path tests pass. Even a pass would be limited to the tested driver/platform; it would not establish VM, remote or Kubernetes host-share behavior.

## Review decision

Design direction has a plausible control transport and ownership split, but no coherent full replacement candidate has execution evidence yet. The host-bind isolation requirement is unresolved under released v0.1.5 configuration; Capsule identity/session boundaries, immutable recovery, profile grants, authenticated agents, full workspace/Git, optional Docker development, lifecycle cleanup and required target journeys remain open. Full-replacement readiness cannot be claimed from the existing limited PoCs or from the proposed architecture.
