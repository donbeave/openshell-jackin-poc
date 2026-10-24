# Refactor plan and release gates

This is a future implementation sequence. No Jackin code has been refactored. The research gate is not passed, so production implementation must not begin from assumed compatibility. Fresh setup is allowed; no migration/import work or legacy internal-format preservation is planned. New-format recovery and normal user workflows remain required.

## Sequence and dependencies

| Stage | Crates/modules and change | Dependency | Exit gate |
|---|---|---|---|
| 0. Close research blockers | Current candidate POCs, source ledger/caller review, real accounts, target matrix, managed Docker and worker enforcement | Disposable test accounts and required hosts; any necessary upstream capability | One accepted architecture with live proof and independent review; no required assumption unresolved |
| 1. Introduce new identity/records | `jackin-instance/src/manifest/{resources,records}.rs`; `jackin-runtime-{identity,naming,coordination,universe,universe-claims}`; config/CLI target records | Accepted identity strategy and safe deletion tests | Round-trip new records, intent-before-effect recovery, stable request replay, forbidden canonical-name reuse, no legacy import |
| 2. Split builder from runtime | `jackin-runtime-image/src/image/{validated,build,version}.rs`; `jackin-image/src/derived_image.rs`; `jackin-runtime-launch-image-plan`, repo cache and prewarm | Exact actual-role image recipe and version fallback proved | Same role+agent built at launch, cache identity covers recipe, no direct execution probe, separate builder outage |
| 3. Authenticated OpenShell control | New narrow OpenShell adapter; generated pinned RPC types/channel; replace runtime backend selection | mTLS/remote authentication, streams, retries, protocol mismatch proved | Literal args/binary stdin/stdout/stderr/exit; complete inventory, runtime/application readiness, async delete; no unsafe TLS |
| 4. Project/private stores | `jackin-isolation`, `jackin-instance`, `jackin-instance-{credentials,agents}`; launch mounts/state preparation | Local container/VM layout and remote/Kubernetes storage proved | Shared/Worktree/Clone, RO/writable, watch/Git links, private-domain separation, recreation/flush failure safety |
| 5. Trusted authority and domain grouping | `jackin-runtime-launch-account-identity`, `launch-account-config`, `launch-supported-agents`, `launch-sibling-auth-prewarm`; host daemon/usage broker and reusable authorization functions | Accepted Candidate B authority fixture or revised accepted Candidate A | Two accounts + separate shell; revision/reconnect admission; usage/refresh/credential execution/MCP; no workload inventory/operator authority |
| 6. Session transport and host UX | Capsule reusable protocol/UI/session code; `jackin-runtime-{session-control,snapshot,host-attach,attach-transport,usage-relay,attach-sessions,attach-capsule-ready}` | Exact frame replay and process lifetime proved | Focus/send/take/release/resize/signal/detach/reconnect, exit ownership/no zombie accumulation, all host actions correct client |
| 7. Lifecycle/discovery/fleet | `jackin-runtime/src/runtime/{launch,attach,cleanup,finalize}`; launch-slot/restore/exit-diagnosis/running-gate/discovery/reactive-daemon | Identity, stores, sessions and ownership receipts | Fault every meaningful transition; stopped/deleting/unavailable/unauthorized/absent separate; retained work safe; targets independent |
| 8. Optional Docker capability | Replace `jackin-runtime-launch-dind`, cleanup-dind-gc/eject-resources engine portions with accepted capability interface | Tested released managed model or pinned upstream patch | Default denied; enabled Docker/Buildx/Compose/Testcontainers repeated/concurrent identical project, engine isolation, child boundaries/costs and complete explicit teardown |
| 9. Verification worker | `jackin-workflow/src/verify.rs` execution/cleanup; retain policy freeze, candidate/results and service call graph | Worker enforcement/transport/identity gates | Exact approved pinned image/checks, no credentials/network, RO root/source/checks, bounded scratch/resources/output/time, actual group kill/exit and cleanup |
| 10. Management/preflight/cache | `apps/jackin/src/{preflight,cli/status,cli/usage,cli/doctor,console/services/instances,console/workflows,app/context,app/restore,app/prune_cmd}.rs`; prune-images/cache/home/roles, keep-awake | Fleet state and explicit builder/runtime split | Target management without builder; image consumers include active+retained across targets; no foreign cleanup; JSON/human output contract |
| 11. Remove obsolete backends | Remove old Docker/Apple execution paths, selectors/state schemas and fallback tests; update CI/package/dependencies | All replacement release tests pass on all target rows | Runtime-dependency scan has only approved retained Docker actions; no `container`/Docker agent or verifier execution remains |
| 12. Release qualification | New product integration tests and user journey suite; docs/new command options | Stages 1–11 | Full fresh setup + combined run/replay on required target coverage; source and authority/storage/cleanup independent review |

Stages are intentionally gated. No “implement first and find out later” assumption is hidden in stage 3 or 8. A required OpenShell patch needs a pinned diff, build/component pins, live proof, compatibility analysis and ownership plan before depending on it. No production controller, broker, scheduler, multiplexer or backend was built in this research.

## Explicit removal list

Remove role execution via `runtime/launch/launch_runtime/docker.rs`, post-run Docker setup/exec in `launch_runtime/session.rs`, Docker attach proxy in host-attach/attach-transport, Docker session/status/snapshot/events/usage commands, Docker running/inspect/log-diagnosis/finalization and resource recovery assumptions. Replace their execution with accepted OpenShell interfaces. Remove `image/version.rs` direct `docker run --rm --entrypoint <agent> <image> --version`, including metadata-missing fallback. Remove independent `verify.rs` Docker worker run/inspect/rm and its Drop fallback after OpenShell worker cleanup is verified.

Remove `runtime/apple_container.rs`, Apple branch of `backend.rs`, `jackin-runtime-apple-container-{client,supervisor-env,check-dns,wait,stop,attach,probe-version,running,activate-entry,session-contract,attach-outcome}` and corresponding selectors/serialization after replacement behavior is qualified. Do not carry Phase 0 finalization failure into a supposed parity claim. Remove Docker/Apple backend defaulting from `jackin-runtime-backend-selection`; target identity is explicit. Remove old `BackendResources` shape, role-container handles and name-only assumptions from the new format. Do not retain backend fallback when OpenShell is unavailable.

Remove direct Docker-role consumer logic from `jackin-runtime-cleanup-prune-images`. Remove local-Docker-only discovery and keep-awake container count. Remove unconditional builder daemon prerequisite from management. Remove old `launch-dind` controller/GC implementation if the accepted scope requires a new managed model; do not quietly retain it as infrastructure. Remove host role exec firewall/sudo setup as runtime orchestration; retain grant calculations and fail unsupported requested behavior explicitly.

Do not delete useful utilities by crate name. `jackin-process`, coordinated child ownership/spooled output, telemetry, output redaction, shell argument helpers, image recipe rendering, Git materialization, state journals and error formatting need individual disposition. `ShellRunner` in a Docker-related crate may be generic reusable process tooling. `DockerApi`'s broad role/network/volume abstraction is not the new OpenShell API. In `jackin-docker/src/docker_client.rs`, `docker_http` is a telemetry wrapper around an awaited operation and may remain for retained builder calls. `consume_exec_start` merges stdout/stderr and decodes lossily to text; it must not be reused as the binary/separate-stream OpenShell session contract. Its caller actions are inventoried separately; the helpers are not independent resource mutations.

## Direct Docker retention ledger

These are the only allowed categories after refactor. Exact remaining production sites must be approved against the final source inventory before release.

| Current operation/site | Future disposition | Justification |
|---|---|---|
| `image/build.rs` Docker build/buildx build, image tag and inspect/list labels/digests | Retain under `ImageBuilder` | Required launch-time derived role image builder |
| Builder base/role image pull, build context/secret handling, cache query/rebuild | Retain scoped builder operations | Build inputs only, no agent execution |
| Image push/save/export and target import/pull where selected | Add narrowly under `ImageDelivery` | Image transfer with digest/platform/credential/complete-transfer proof; never workload execution |
| `cleanup-prune-images` builder `remove_image` after new global consumer decision | Retain builder-cache deletion only | Protect active and retained target references; runtime image caches separate |
| Builder health/version/Buildx availability in doctor/build preflight | Retain for builder capability only | Existing-target management does not depend on separate builder availability |
| Docker CLI/Buildx/Compose shipped in role image | Retain binary content; capability disabled by default | Explicit optional workload capability; presence is not an engine grant |
| Optional engine operations in accepted OpenShell-compatible capability owner | Unresolved, not preapproved old DinD retention | Need tested managed model and exact ownership/network/resource boundary; external fixture only establishes connectivity |
| OpenShell Docker driver container/network/volume/image operations | OpenShell infrastructure owner | OpenShell executes sandbox compute; Jackin does not directly create old role containers |
| CI/package image build and dedicated test environments | Retain with isolated labels/cleanup | Build/test infrastructure, not shipped old execution backend |
| Agent `docker run`, direct role exec/attach/snapshot/status/usage, verification worker | Remove | Neither builder nor explicit capability nor OpenShell infrastructure |
| Old per-instance DinD manager as permanent fallback | Remove or record required scope deviation for decision | Not silently allowed by “Docker may remain builder” |

## Proposed release acceptance suite

The following tests are requirements for the unwritten product. They have **not passed** merely because a POC primitive passed. Each test needs exact versions, image/platform digest, target/auth/policy, initial state, observed state/output, owned resources, cleanup and remaining limits. Use deterministic fixtures for errors/signals and an approved real coding task for usable agent behavior. Never replace actual denial with mock authorization success.

| ID | Required test and negative/control case |
|---|---|
| A01 | Fresh install/reset setup on four packaged desktops; missing host/tool prerequisites diagnosed; no unrelated deletion |
| A02 | Doctor splits builder/gateway/engine/host; existing target status/hardline/eject work with separate builder unavailable; new build fails builder-specific |
| A03 | Role discovery/trust/update/selection; exact Architect tools/hooks/config; reject untrusted/unsupported role-agent combination |
| A04 | Build selected agent into derived image; change agent version/content; cold/reuse/forced rebuild; complete recipe key; unknown metadata version through OpenShell/build metadata only |
| A05 | Same-engine delivery vs different-machine authenticated registry/import; correct architecture/digest; missing/unauthorized image and interrupted transfer; no partial adoption |
| A06 | Two admitted real account domains and separate shell; workspace/revision/reconnect admission, supported auth modes, separate GitHub auth/model config/custom URL/effort |
| A07 | Private homes/cache/history/plugins/config persist across documented boundaries; interrupted credential/config publication recovers atomically |
| A08 | Cross-domain private files/input/control/global inventory/usage/refresh/approved exec denied using actual authenticated channels; stale/replaced identity rejected |
| A09 | Harmless secret approval/denial/cancel/timeout/revocation/wrong domain; intended MCP response/transport; record exactly which consumer receives secret; no masking-based disclosure claim |
| A10 | Rust route local/remote mTLS positive and cert/token failure/renewal; verification enabled; version/protocol mismatch; no diagnostics in protocol stdout |
| A11 | Create/get/list pagination/start/stop/delete; runtime/application readiness separate; incomplete inventory visible; lost response/stable request replay/conflicting payload |
| A12 | Same-name replacement race; canonical non-reuse/server identity precondition actually enforced under stated authority; async deletion confirmed; outage/unauthorized/absent distinct |
| A13 | Exec literal argv, metacharacters, binary/NUL stdin, separate stdout/stderr/exit; interactive/noninteractive; output truncation/backpressure/slow receiver/cancel/lost connection |
| A14 | Two agent sessions + generic shell; add/switch supported agent; tabs/focus/input owner/observer/send/take/release; wrong client denied |
| A15 | Close client/reconnect same session; clean exit/supervisor failure/sandbox failure/grandchildren; accurate code/signal; one child owner, no zombies; Darwin only for macOS processes |
| A16 | Current host frames replay for clipboard images/image paths/URL/file export/resize/detach; interrupted export/wrong client; desktop terminal restored |
| A17 | Shared/Worktree/Clone actual host paths; host-agent edits both directions/watch; RO; workdir/Git links; UID/executable perms; spaces/symlinks; concurrent activity; private mounts separate |
| A18 | Retained project/private state across stop/start and normal recreation; writable layers disposable; orderly/interrupted VM shutdown and flush error visibility |
| A19 | Dirty/unpushed/clean/abnormal/failed-inspection preservation, active hold fixture; uncertainty never purges; normal hold creation vs foundation explicit; capture barrier if required |
| A20 | Profile/grant precedence and role requirements; allowed/denied network provider/GitHub/package/telemetry/local service/DNS/IPv4/IPv6/ports/redirects; no silent weakening |
| A21 | Allowed/denied filesystem writes/reads, privileges/capabilities, CPU/memory/PIDs/temp/nofile; aggregate vs per-domain budget explicit |
| A22 | Repeated ordinary Cargo/nextest edit-build-test at same executable path, network calls and Testcontainers when enabled; retain old integrity FAIL until resolved |
| A23 | Policy/provider update path used in active sessions: interruption/recovery explicit; no unneeded arbitrary-update continuity promise |
| A24 | No usable Docker endpoint/socket/engine credentials by default; positive network control distinguishes denial from broken path |
| A25 | Enabled managed Docker build/run/exec/logs/stream/Buildx/Compose/volumes; daemon paths/published ports/service discovery/callbacks; online pulls/dependencies |
| A26 | Two concurrent instances, same unmodified Testcontainers project, repeated source changes/data exchange; port isolation actually tested; cross-instance engine/cert denial |
| A27 | Daemon/children exact location, network policy and resource boundary/cost; stop/restart/teardown/interrupted setup/cleanup failures; killed-test explicit eventual cleanup |
| A28 | OpenShell worker exact approved argv and pinned image; candidate/check bundle RO and distinct; no account credentials/network; RO root and bounded scratch/resource/output/time enforcement |
| A29 | Worker success/failure/timeout/abnormal/unavailable/interrupted control; actual process-group termination/exit; candidate/check/policy result binding and complete owned cleanup |
| A30 | Inject launch failure after every external-effect boundary; receipt before effects, client interruption/gateway restart, partial create; preserve committed stores and foreign resources |
| A31 | Fleet discovery/status/events across required targets; stale/lost events/incomplete pages; stopped/deleting/unavailable/unauthorized/absent explicit; GitHub outage retains useful rows |
| A32 | Human/JSON session/Git branch/PR/CI/usage contracts; account unavailable and cancellation; builder and runtime health distinct |
| A33 | Runtime prune vs builder/target image prune; active/retained/foreign protected; required digest remains for reconnect/recreation |
| A34 | Prewarm binaries/roles/images and explicit optional engine; ordinary prewarm never enables capability; single prepared resource adoption; mount/account drift rejects |
| A35 | Concurrent first-entry/last-exit/keep-awake across targets and clients; host process owner and interrupted client recovery |
| A36 | Two gateways one engine: independent CA/inventory/state/namespace, no interference; compute-driver/VM-size targets separate; unsupported per-sandbox fields not used |
| A37 | VM actual role layout fits directory-only 3 x86_64/32 ARM64 mounts without unauthorized parents; host permissions/virtiofs limitations; service/callback path and size classes |
| A38 | Remote Linux/macOS different-machine image delivery and selected storage/sync/conflict/export model; no copied-file live-mount claim; host action to correct desktop |
| A39 | Kubernetes controller/CNI enforcement, PVC ownership, image credentials, authenticated reachability; target outage independent of other targets |
| A40 | Combined actual role + two accounts + shell + real authenticated coding/edit-build-test + persistent I/O/account operation/approved credential/disconnect/reconnect/retained recovery/failed-launch cleanup under one config |
| A41 | Combined enabled Docker and disabled denial plus independent worker; rerun critical combination from fresh owned resources, independently reviewed |
| A42 | Measurements with sample counts/cache conditions: build/transfer/start/application readiness/attach/reconnect/idle/domain/VM/engine/child/concurrent startup/stop/cleanup/disk/cache; same-hardware old Jackin comparison where practical; no unjustified percentiles |
| A43 | Final production source scan and caller audit: only retained builder/capability/OpenShell infrastructure Docker actions; zero old role/agent/version/verifier Docker or Apple execution paths |

Acceptance tests run through required target rows using representative combinations per distinct mechanism. New platform assumptions require live runs, not mock behavior. All supported agent/auth combinations need explicit qualification or a documented public support change before release. No environment is dropped to turn the verdict green.
