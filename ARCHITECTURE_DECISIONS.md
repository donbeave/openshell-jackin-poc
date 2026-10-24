# Full OpenShell integration architecture decisions

Status: one candidate architecture is selected for further proof; required capabilities remain unresolved. This is not full-refactor readiness. Selected revisions and compatibility are recorded under `results/full-refactor-20261024/`.

## AD01 — Target and logical instance are different identities

A **target** is one gateway, compute driver, endpoint, workspace scope and platform. Jackin assigns a stable TargetId bound to the configured trust authority; display names are not authority. A logical instance is anchored to one TargetRef and groups its domain/session sandbox receipts on that target. Fleet views combine logical instances across targets; cross-target session migration/collaboration is not added to the current contract. A domain identifies sessions allowed to share private account data and authority. Generic shell authority is separate.

Proposed records:

- `TargetRef`: TargetId, gateway identity/trust reference, driver, endpoint, workspace, platform, driver profile and authentication mode.
- `SandboxRef`: TargetRef, canonical name, immutable sandbox ID, observed runtime generation, main-process identity, requested/actual image descriptors and state observation time.
- `DomainRef`: domain ID, account/revision, role/agent admission, private persistent-state references and allowed operations.
- `SessionRef`: logical instance/domain, SandboxRef, canonical-process receipt, selected agent/model/effort, operator-control lease and exit/event state.
- `ImageRecipeRef`: role/source/content hash, base image/platform, resolved selected-agent artifact/version, tool/plugin/skill/hook inputs, Capsule or bootstrap artifact, recipe version and digest.
- `ResourceReceipt`: owner, authority, resource kind/identity, target/scope, retained-data reference, stable operation request ID, created/retained/deleting state and cleanup outcome.
- `VerificationBinding`: workflow/run/round, candidate commit/tree, approved argv/policy/bundle/image digests, worker SandboxRef and trusted observed result.

These are proposed interfaces, not a new controller implementation. Fresh setup can use new formats. Normal persistence/recovery remains mandatory.

## AD02 — Select Candidate B; current Capsule process structure fails

**Candidate A** is rejected for released v0.1.5: current 6e Capsule's real Linux isolation wrapper fails `capsule isolation wrapper must start as root`; OpenShell policy rejects UID/GID zero. Native macOS Capsule fails `isolated agent sessions require a Linux Landlock boundary`. Removing those restrictions would not preserve the required boundary.

**Candidate B** keeps trusted control outside workloads and uses OpenShell sandboxes for agent/account and shell domains. Each independently addressable canonical session process has a sandbox receipt; sessions sharing authorized private state may reference the same domain storage, but never a different account's storage. Shared project mounts do not imply shared private homes. Existing host product/authorization logic remains authoritative.

Released canonical-main-process PTY tests demonstrate reconnect to the same PID, replayed output, independent deterministic sessions, and generation change on restart. This is stronger than a fresh `ExecSandboxInteractive` connection, which creates a new process. It does not establish the complete Capsule protocol, exclusive operator control, credential relay, agent conversation resume or host-action authorization.

Any helper running as the agent UID is untrusted I/O only. It gets no gateway operator key, another account's data, approval authority or desktop authority. Trusted host control validates origin and binds requests to its own SandboxRef/domain, never an account ID asserted by workload text. Full Candidate B account/credential/host-protocol proof remains a blocker; no replacement production Capsule/multiplexer/broker is implemented.

## AD03 — Rust control uses public SDK types and a verified custom channel

Use release-matched generated RPC types and `OpenShellClient::from_parts` with a Tonic channel configured for private CA, hostname and client identity verification. This is a released public transport route, despite missing convenience mTLS fields in the curated SDK configuration. Non-TTY binary duplex and typed lifecycle/streams have execution evidence; CLI table parsing is not used as an API.

Canonical PTY attachment may use securely invoked, release-matched OpenShell CLI transport where its byte/identity contract is proved. Diagnostics remain outside protocol stdout. No plaintext/insecure TLS fallback is selected. Select mTLS for local and remote Linux/macOS/Kubernetes gateway control, with per-target trust and renewal policy; the Linux guest private-IP probe covers only that configuration. Actual remote/cluster bootstrap and certificate renewal remain unproved. OIDC/bearer modes are not claimed or required as a substitute for this selected route.

## AD04 — Immutable resource mutation is required upstream

Released Get/List read by canonical name; compare returned `metadata.id` with the stored receipt. This is a read identity check, not an atomic mutation guard. Released Stop/Delete old requests demonstrably affect same-name replacements. Exec and generation-bound input require their own guarantees.

The selected design requires identity/generation-bound mutation/execution. The Delete-only experimental patch95a1e7fe is built, runtime-tested and independently reviewed; it does not fix Stop/Start/Exec. Earlier failed revisions and review findings remain visible. ID mode requires a caller-persisted nonnil stable UUID, authorizes the workspace before replay, rejects allow_missing, and replays the saved original receipt after deletion/name reuse. Unknown and foreign IDs both return NotFound; that response is not an absence receipt for purge. Never assume an unknown protobuf field is enforced by an old server. The experiment's ID request uses an empty legacy name so old servers fail closed. A never-reused-name allocator is not claimed as a tested substitute.

Purge requires authorized expected-scope confirmation and trusted owned-resource receipts. Generic NOT_FOUND, incomplete inventory, unauthorized scope or unavailable target does not authorize deleting retained data.

## AD05 — Build images before creating sandboxes

Docker/Buildx constructs the actual role-derived image and installs the selected agent/tools. Separate builder health/endpoint from gateway health and optional Docker permission. Resolve agent/platform/artifact identity before cache reuse; verified build metadata or OpenShell execution handles missing version metadata. Do not retain `docker run` version probing.

Pin the effective platform image, not merely a mutable tag. Distinguish local image config ID, OCI manifest/index digest, role/recipe hash and target-delivery identity. Remote delivery must be tested with an image absent at the destination. Keep builder and target-store ownership separate. Pruning protects active and retained references across targets.

Actual role experiments preserve existing role/installer failures. Changing the role's mutable published-base reference to the locally built, digest-recorded source image and changing GID0 to a nonzero group are explicit experiment deltas. They do not justify dropping required plugins or replacing the full role with a compiler-only image.

## AD06 — Storage is target-specific and explicitly authorized

For the tested local Docker profile, select administrator-prepared bind-backed named volumes, with bind support enabled and resource admission still enabled. The host validates canonical source, volume driver/options, exact workspace labels, intended mode and mount target before use. OpenShell admits the volume; it does not supply Jackin's underlying path authorization. This is a Jackin-side/storage-service adaptation with TOCTOU/concurrency requirements, not native raw-bind support.

Selected layout to qualify in the combined journey: reserve `/sandbox` for OpenShell's canonical workspace/bootstrap, preserve the role's project view at `/workspace`, and use a dedicated private persistent directory below the domain home rather than mounting over a protected OpenShell root. The derived image/bootstrap must set an admitted OCI working directory and then explicitly enter the authorized project with exact argv/path translation. Seed only public image defaults into the domain's private state, run setup-once/source/preflight in their declared order, and publish setup receipts outside untrusted I/O authority. Explicitly preserve role PATH/model/environment settings instead of assuming image ENTRYPOINT or ENV survives unchanged. These combined path/home/hook assumptions are not yet proved; successful version/preflight slices do not close them.

Count every external project, linked-Git alias, private-state and engine-credential mount per sandbox. ARM64's reviewed32-mount limit is distinct from x86_64's three. Group only data already within the same authorized domain; do not mount a broad host/private parent to fit. Any required layout exceeding the qualified limit needs a tested storage/driver capability or remains unsupported for that profile.

Shared, Worktree and Clone remain separate materialization policies. Linked worktrees need narrowly scoped path aliases or a tested metadata conversion; broad home-directory exposure is not acceptable. Private domain state uses separate persistent mounts, independent of image writable layers.

For remote targets, the selected source authority is the remote target's durable checkout. Shared means that authorized remote checkout, not automatic live sharing with the desktop. Desktop synchronization is explicit Git synchronization/export with conflicts surfaced; no last-writer-wins claim. Remote worktree/clone and transfer still require live proof.

For Kubernetes, use approved persistent storage plus enforced NetworkPolicy and image credentials. For the packaged VM profile, select explicitly sized gateway targets (initial small2vCPU/2048MiB and proposed standard4vCPU/8192MiB), not unsupported per-sandbox sizing flags. Only the small size was observed. Admission-preserving host sharing and documented virtiofs host-confinement limits remain unresolved. Uploaded copies are not a substitute for required live local Shared semantics. No custom kernel or cluster is built.

## AD07 — Optional Docker must have a managed owner

Select an OpenShell-managed companion per granted authority domain, implemented by the appropriate compute driver/extension and attached through an explicit managed resource interface. This required component is not available as a demonstrated released capability. Engines, certificates, data, networks, ports and children need interruption-safe ownership and cleanup. Do not share engine administration across private account domains merely because they share a logical instance or project. Any intentional authority sharing must be explicit in the domain admission. Strong profiles must place daemon/children inside the declared isolation boundary. Do not retain the old Jackin DinD runtime manager as an unidentified second backend.

External mTLS fixtures demonstrate connectivity, online pulls/builds, Compose, live project binds and initial Testcontainers exchange only. Rootless startup did not establish a managed solution. No released companion lifecycle was demonstrated. Rootless-inside-workload and external forwarding were evaluated as alternatives, but neither is selected as the managed owner. A privileged companion/lifecycle interface is therefore an unresolved upstream requirement; implementing a production manager would exceed this task.

Required upstream interface, not implemented here: provision a companion with target/domain identity, stable request ID, boundary/resource profile and authorized project references; return immutable engine identity, provisional ownership receipt, scoped client-credential reference and API/service routes. Inspect/start/stop/delete must bind expected identity/generation and report completion. Record ownership before partial provisioning can leave a daemon behind. Optional engine prewarm needs an explicit prepared-resource claim with single-owner CAS adoption, not an untracked pool. Eject removes engine compute/certificates/networks/children and ephemeral engine data; project/private account state is retained according to Jackin policy. Ordinary stop/reconnect must preserve the declared engine continuity. No account-private home is mounted into the daemon merely to support project binds.

Service routes must be per companion or explicitly allocated ports; Docker API permission does not grant service/callback access. Preserve end-to-end Docker TLS verification through TCP passthrough. Exposing every port on a shared developer host is not selected. An API proposal, issue or custom-driver sketch is not executed support. Implementing durable companion reconciliation would exceed a small connectivity fixture and remains an upstream dependency.

Docker children have their own policy/resource boundary. They do not inherit agent egress. A container daemon outside an agent VM does not place children inside that VM. Keep the existing partial-boundary disclosure and prove any stronger profile separately.

## AD08 — Verification workers also execute through OpenShell

Retain Jackin's trusted candidate/check preparation, policy approval and result binding. A single-use OpenShell worker receives only read-only candidate source and the separate trusted check bundle, no agent credentials and no network. Preserve bounded scratch/CPU/memory/PIDs/output/time, process-group termination and actual exit observation. No host or direct-Docker execution fallback exists.

The released tmpfs mount path failed. A separate one-behavior Docker-driver patch, commit `68cfa648538a497acd4af2cf48424eda9834ba0f`, passed narrow option-translation execution and focused driver tests while preserving noexec/nosuid/sizes, the supervisor CA tmpfs, protected paths and external-resource admission. The historical executed binary hash was not captured before cache GC; later rebuilt binaries are not substituted as that identity. This is experimental support only. Full worker isolation still fails: the refined P14 policy permitted chmod of an out-of-grant UID-owned file. All complete worker outcome, lifetime, result-binding and security cases remain required.

## AD09 — Retain host lifecycle and fleet meaning

Jackin owns role/account decisions, dirty/unpushed-work preservation, hardline/eject/exile/purge semantics, host first/last entry actions, keep-awake, PR/CI/usage interpretation and desktop behavior. OpenShell supplies runtime facts/execution. Target queries are bounded, paginated and marked incomplete/unavailable when appropriate; status does not infer deletion from outage.

Live policy changes are required only where the selected credential/provider design uses them. Previous stream-loss evidence remains. Define interruption/recovery rather than assuming automatic retries preserve revocation or reexecute uncertain prompts. New-format receipts and explicit request IDs preserve uncertainty and ownership without a production recovery service in this research.
