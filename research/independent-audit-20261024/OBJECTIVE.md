# Establish readiness for the full OpenShell refactor of Jackin

## 1. Objective

Research the complete replacement of Jackin’s Docker and Apple Container execution backends with NVIDIA OpenShell.

Read Jackin source code. Audit all current runtime dependencies.

Make one complete integration design. Support each changed runtime assumption with execution evidence.

Make a detailed refactor plan.

Do not refactor Jackin during this task.

Use small proof-of-concept programs and scripts. Reuse existing binaries, functions, and protocol types when practical.

Do not build a production backend, terminal multiplexer, scheduler, credential broker, or runtime controller.

The required result is readiness to start the full refactor.

“Ready for a focused prototype” is not a successful result.

The result can be NOT READY when a required capability remains unproved.

### Product requirements

Keep these requirements:

- Build derived role images during launch.
- Use Docker or Buildx for these image builds.
- Install the selected coding agent and required tools in the image.
- Preserve current working role, account, workspace, session, and command workflows.
- Use OpenShell for role sandbox execution.
- Use OpenShell for workflow verification-worker execution.
- Provide optional Docker access inside selected sandboxes.
- Keep Docker access disabled by default.
- Support the required local, VM, remote, and Kubernetes targets.
- Give Jackin one view of its instances across these targets.

Docker can remain the image builder.

Docker access can remain an explicit workload capability.

Do not retain the old Docker or Apple execution backend as a fallback.

### Upgrade scope

Users can remove old Jackin containers, images, runtime state, and configuration before fresh setup.

Do not design legacy state import or configuration migration.

Do not preserve old internal formats merely for compatibility.

Preserve normal persistence and recovery for data created by the new design.

Preserve working user workflows after fresh setup.

Record any required change to public commands or options.

The reset allowance does not authorize deleting unrelated resources during this research.

## 2. Sources and versions

Start with these repositories:

- Jackin: https://github.com/jackin-project/jackin
- Architect role: https://github.com/jackin-project/jackin-the-architect
- OpenShell: https://github.com/NVIDIA/OpenShell
- Existing research: https://github.com/donbeave/openshell-jackin-poc
- Runtime documentation: https://docs.nvidia.com/openshell/latest/how-it-works/sandboxes/runtimes

Use these reviewed versions as the initial reference:

- Jackin: `6e266406b49da2ab3c55355f3b7d33d1643ee6cd`
- Architect: `7b72b38fe1d66e35c0931899c53bf3719592bbcc`
- Research repository: `2315e6a278231854b3139b1ca32402777ff3cd01`
- OpenShell: `v0.1.5`
- OpenShell commit: `bdb956f2cd65a635f1294fccf1d138d263bf650f`

Record current repository revisions and available releases.

Review relevant changes since these versions.

Pin every version used in an experiment.

Do not combine results from different versions without a recorded compatibility analysis.

Read the existing handoff, readiness report, capability matrix, measurements, and raw results.

Reuse valid evidence. Retain previous failures and limitations.

Do not convert a source-code statement into an execution result.

## 3. Make the complete source inventory

Use multiple subagents for independent source audits.

Separate the first audit into:

1. Docker, image building, optional engines, and cleanup.
2. Apple Container, VM targets, storage, and resource controls.
3. Capsule, sessions, accounts, credentials, and host integration.
4. Workflow execution, CLI behavior, discovery, and distributed targets.

Use later iterations to review decisions across these areas.

Use `rg` and call-site tracing.

Search beyond the main runtime adapters.

Include:

- `DockerApi`, Docker clients, Bollard, and container specifications.
- Direct Docker commands in Rust and shell scripts.
- Apple Container APIs and `container` commands.
- Docker sockets, Docker environment variables, and daemon connections.
- Runtime selectors and saved resource identities.
- Root setup, UID changes, PID assumptions, and peer authentication.
- Image building, version detection, prewarm, pruning, and image transfer.
- Capsule attach, exec, events, snapshots, and usage transport.
- Workflow verification workers.
- Discovery, doctor, preflight, status, finalization, and cleanup.
- Operational scripts, packaging, and CI runtime dependencies.

Classify each match by its executed action.

Do not classify an operation from its crate name alone.

For every production call site, record:

- File and symbol.
- Caller and user entry point.
- Current resource owner.
- Current behavior.
- Required user outcome.
- Proposed replacement owner.
- Exact OpenShell operation or alternative mechanism.
- Required code change.
- Evidence or proposed experiment.
- Future release acceptance test.

Classify source behavior separately:

- Active and demonstrated.
- Active but untested.
- Implemented without a production caller.
- Incomplete.
- Planned only.

Resolve every production runtime match.

Record excluded test, documentation, and build-only matches with a reason.

### Known paths that require explicit treatment

Include the agent-version probe in `jackin-runtime-image/src/image/version.rs`.

It can execute the agent with `docker run`.

Include `jackin-workflow/src/verify.rs`.

It creates an independent Docker verification sandbox.

Include direct runtime calls in status, snapshots, session control, usage, crash diagnosis, and finalization.

Include image pruning that identifies consumers through Docker role containers.

Include preflight rules that require Docker for management commands.

## 4. Define the user workflow contract

Trace current CLI and console actions into production code.

Run the unchanged Jackin version where practical.

Record expected behavior before testing replacements.

Cover:

- Fresh setup and prerequisite diagnosis.
- Role discovery, trust, selection, update, and launch.
- Agent selection, account selection, and sibling agent sessions.
- Runtime image construction, cache reuse, rebuild, and prewarm.
- Shared, Worktree, and Clone workspace modes.
- Terminal sessions, tabs, focus, input, interrupt, detach, and reconnect.
- Status, events, usage, quotas, and supported machine-readable output.
- Git branch, PR, and CI information.
- File export, clipboard images, URL opening, and terminal restoration.
- `hardline`, `eject`, `exile`, `purge`, and prune behavior.
- Retained work, dirty work, unpushed commits, and abnormal exits.
- Optional Docker workflows.
- Workflow verification and recorded results.
- Relevant host behavior, including keep-awake and first-entry or last-exit actions.

Separate current working behavior from new target requirements.

Do not infer successful agent support from an adapter enum.

Trace installation, role admission, launch command, and authentication separately.

Do not treat unfinished Apple finalization as demonstrated behavior.

Do not require interactive agent sudo merely because a profile can provision sudoers.

Trace checkpoint capture and grant readback callers before treating them as active features.

Record current revocation behavior.

Do not invent immediate session termination guarantees from admission checks.

## 5. Select one complete integration architecture

Use “target” to mean one gateway, compute driver, endpoint, workspace scope, and platform.

Use “domain” to mean sessions allowed to share private account data and authority.

Assign an owner to every resource and decision.

Separate:

- Docker builder.
- OpenShell gateway.
- OpenShell sandbox.
- Jackin logical instance.
- Session and account domain.
- Project storage.
- Private account storage.
- Optional Docker engine and its children.
- Image caches and transferred images.

Specify the proposed interfaces and records.

Include target identity, sandbox identity, session identity, image digest, resource ownership, and retained-state references.

Do not reproduce `DockerApi` as an OpenShell wrapper without reviewing its assumptions.

### Resolve the Capsule design first

Compare two candidates.

**Candidate A:** Use the current Capsule process structure under supported OpenShell settings.

**Candidate B:** Keep trusted Jackin control outside workloads. Use separate sandboxes for the required account and isolation domains.

Test both candidates against the same required outcomes.

For Candidate B, keep generic shell authority separate from agent account authority.

A logical Jackin instance can group multiple sandboxes.

Show how its sessions, limits, status, and lifecycle remain coherent.

Treat a helper sharing the agent UID as untrusted session I/O.

Do not give that helper authority over other accounts or operator actions.

Select one candidate after the decisive experiments.

Do not combine incompatible successes into one claimed design.

### Assign replacement work

For each subsystem, select one action:

- Retain product logic.
- Replace transport.
- Replace storage or identity mechanism.
- Replace execution through OpenShell.
- Remove obsolete backend code.
- Add a small Jackin mechanism.
- Require an OpenShell change.

Record the exact reason and dependency for each action.

## 6. Prove images, roles, and agent setup

Build the actual Architect role image with Docker.

Use its real tool configuration and hooks.

Install a selected supported agent during image construction.

Change the selected agent version and repeat the build.

Test cold preparation, valid cache reuse, forced rebuild, and changed role content.

Show that cache identity includes all relevant recipe inputs.

Test an installation path without prefetched version metadata.

Obtain its version through verified build metadata or OpenShell execution.

Do not retain a direct `docker run` agent probe.

Deliver the exact image to each required target type.

Separate same-engine image availability from remote image delivery.

Test registry authentication, architecture selection, missing images, and interrupted transfer.

Record the executed image digest and actual tool versions.

Show how role hooks run when OpenShell controls the entrypoint.

Test working directory, environment, shell tools, plugins, and agent configuration.

Separate binary installation from a usable authenticated coding session.

Map image ownership across the builder and OpenShell stores.

Prune an unused image safely.

Show that required images remain available for reconnect and normal recreation.

## 7. Prove the Rust control path

Select the actual Rust integration route.

Consider the pinned SDK, generated RPC clients, a custom authenticated channel, or a justified CLI adapter.

Test the route against a real gateway.

Test local mTLS and the selected remote authentication mode.

Keep certificate verification enabled.

Test certificate or token failure and renewal where applicable.

Do not assume SDK support from available type definitions.

Test:

- Create, get, list, start, stop, and delete.
- Application readiness after runtime readiness.
- Pagination and incomplete inventory.
- Execution with exact arguments.
- Separate stdout, stderr, and exit status.
- Binary input, NUL bytes, and metacharacters.
- Interactive and non-interactive streams.
- Slow receivers, output limits, cancellation, and connection loss.
- Lost responses and retries with stable request IDs.
- Version or protocol mismatch.

Keep transport diagnostics outside protocol stdout.

### Prove resource identity

Record target, workspace, immutable sandbox identity, and runtime generation where available.

Test same-name replacement between observation and action.

Do not assume a client-side identity read makes a later name-based action atomic.

Select and test a safe identity strategy.

Consider canonical names that are never reused or a server-side identity precondition.

State the authority and concurrency assumptions.

Test asynchronous deletion and confirmed completion.

Test missing resources separately from unavailable or unauthorized targets.

Do not treat a generic `NOT_FOUND` response as sufficient proof for deleting retained host data.

Confirm the expected authorized scope.

## 8. Prove sessions and process lifetime

Use the selected architecture.

Reuse current Capsule code where supported.

Otherwise, use a small fixture for the proposed session interface.

Limit that interface to the required operations:

- Start a process.
- Read and write terminal bytes.
- Resize the terminal.
- Send a signal.
- Report exit status.
- List sessions.
- Disconnect and reconnect.

Run a real supported coding agent.

Use deterministic processes for signal and child-lifetime tests.

Test two agent sessions and a generic shell.

Test changing or adding a supported agent within one logical role.

Test focus, input ownership, observation without ownership, send, take-control, and release-control.

Close the client while a session remains active.

Reconnect to that session.

Test clean exit, supervisor failure, sandbox failure, and grandchildren.

Record correct exit codes and signal results.

Show that child exits have one owner.

Test zombie accumulation and orphan cleanup.

Account for the current child-ownership and Darwin reaping code.

Test Darwin behavior only where a process actually runs on macOS.

Replay current host protocol frames over the proposed transport.

Cover clipboard images, image-path staging, URL opening, file export, resize, and detach.

Test interrupted export and wrong-client delivery.

Keep host actions on the user’s desktop.

Do not substitute a manual file copy for the export protocol test.

## 9. Prove accounts, credentials, and usage

Use two account domains and a separate shell domain.

Test selected account, workspace permission, account revision, and reconnect admission.

Test private homes, caches, history, plugins, and generated configuration.

Cover supported authentication modes.

Treat GitHub authentication separately from model-provider authentication.

Include custom provider URLs, model selection, and effort settings where supported.

Do not replace agent-specific configuration with one generic inference-provider assumption.

Test interrupted credential and configuration publication.

Show safe recovery without partial account assignment.

Test cross-domain denial for:

- Private files.
- Session input and control.
- Global inventory.
- Account usage.
- Credential refresh.
- Approved credential execution.
- Stale or replaced sandbox identities.

Reuse existing authorization functions where practical.

Use real authenticated channels.

Do not use a mocked authorization success as evidence.

Test the approved credential route with a harmless secret and consumer command.

Cover approval, denial, cancellation, timeout, revocation, and wrong-domain requests.

Record which process receives the secret.

Test the intended MCP response and transport.

Do not claim that output masking prevents an approved process from disclosing its input.

Trace unchanged usage logic into the proposed transport.

Test account-scoped usage operations, unavailable states, and cancellation.

## 10. Prove workspace and persistence behavior

Test actual host project access.

An uploaded archive does not prove live host sharing.

Cover Shared, Worktree, and Clone modes.

Test:

- Host edits visible to the agent.
- Agent edits visible to the host.
- File-watch behavior.
- Read-only mounts.
- Working-directory translation.
- Git links, branches, and worktree metadata.
- File ownership and executable permissions.
- Spaces and symbolic links in relevant paths.
- Concurrent host and agent activity.
- Multiple project and private-state mounts.

Show how approved project data can be shared without sharing account homes.

Test retained state across stop/start.

Test normal sandbox recreation using retained data.

Separate writable container layers from durable storage.

Test orderly VM shutdown and interrupted shutdown.

Record flush failures and their user-visible consequences.

Do not claim unconditional durability from a completed stop.

Test dirty work, unpushed commits, clean exit, abnormal exit, and failed session inspection.

Preserve work when the required state is uncertain.

Test active preservation guards with an explicitly identified fixture.

Trace whether normal hold creation is active or remains a foundation.

If consistent live capture is required, prove its write barrier.

Do not treat stop/start as process-preserving pause.

## 11. Prove policy and resource controls

Map current effective profile behavior to the candidate design.

Include profile precedence and role requirements.

Cover:

- Network-open and restricted network workflows.
- Provider, GitHub, package, telemetry, and local-service destinations.
- DNS, IPv4, IPv6, ports, and redirects.
- Read-only and writable filesystem areas.
- Process privileges and required capabilities.
- Memory, CPU, PID, temporary storage, and file-descriptor limits.
- Optional Docker permission.

Test effective enforcement.

Configuration output alone is insufficient.

Test allowed operations and denied operations.

Do not silently weaken a requested restriction.

Do not preserve an ineffective profile label as a claimed guarantee.

Test the normal Rust edit-build-test loop repeatedly.

Change a network-using executable at the same path.

Run ordinary Cargo and nextest commands under the intended policy.

Include Testcontainers where Docker is enabled.

Retain the previous executable-integrity failure until a tested design resolves it.

Test policy changes if the selected design uses them during active sessions.

Define connection recovery or interruption behavior.

Do not require uninterrupted arbitrary policy updates unless the product depends on them.

## 12. Prove optional Docker capability

Research released OpenShell support, relevant issues, pull requests, and small extension options.

Separate proposed support from released and executed support.

Compare these mechanisms:

1. A daemon inside OpenShell-managed compute.
2. An OpenShell-managed companion with explicit ownership.
3. A small OpenShell extension.
4. Explicit forwarding to a disposable external engine.

Use external forwarding to establish its own capability and limits.

Do not count an external fixture as proof of managed OpenShell-only Docker support.

Do not retain the old Jackin DinD runtime manager without identifying that deviation.

For the managed capability, select and test an OpenShell-compatible ownership model.

Keep the capability absent by default.

Show that a normal sandbox has no usable Docker endpoint, socket, or engine credentials.

Use a positive control to distinguish policy denial from broken networking.

For an enabled sandbox, test:

- Docker build, run, exec, logs, and streaming.
- Buildx where required.
- Compose services and volumes.
- Project paths resolved by the daemon.
- Published ports and service discovery.
- Real Rust Testcontainers data exchange.
- Repeated source changes and test runs.
- Two concurrent instances using the same unmodified test project.
- Cross-instance credential and engine denial.
- Online image pulls and dependency downloads.

Do not infer concurrent port isolation from different TLS certificates.

Do not infer Testcontainers compatibility from a loopback test in a Docker child.

Record the location of the daemon and every child container.

Record their network policy and resource boundary.

A VM agent connected to an external container daemon does not place those children inside the VM.

Test agent, daemon, and child resource costs separately.

Define ownership for engines, networks, volumes, certificates, and children.

Test stop, restart, teardown, interrupted setup, and failed cleanup.

Define cleanup after killed tests.

Do not invent an immediate child-cleanup guarantee that Jackin does not currently provide.

A required upstream patch must have a pinned diff and execution evidence.

If the required change is too large for a small POC, record the blocker.

## 13. Prove workflow verification workers

Replace the independent Docker execution mechanism used by workflow verification.

Use an OpenShell sandbox for the proposed test worker.

Keep workflow policy and result recording in trusted Jackin logic.

Preserve the required outcomes:

- Exact approved command.
- Pinned verification image.
- Read-only candidate source.
- Separate trusted check bundle.
- No agent account credentials.
- No network access.
- Read-only root with bounded writable scratch space.
- Bounded CPU, memory, PIDs, output, and execution time.
- Correct process-group termination.
- Actual exit-state observation.
- Result binding to the candidate and approved checks.
- Complete owned-resource cleanup.

Use the current limits as the baseline.

Record any necessary change and its reason.

Do not preserve root UID merely because the current worker uses it.

Test success, failure, timeout, abnormal exit, unavailable runtime, and interrupted control.

Do not fall back to host execution or direct Docker execution.

## 14. Prove lifecycle, management, and fleet behavior

Define the new lifecycle state machine.

Map current commands to explicit retain, stop, delete, recreate, and purge decisions.

Record ownership before effects that can leave resources behind.

Test failures at each meaningful launch transition.

Test client interruption, gateway restart, and partial resource creation.

Use small ownership receipts and scripts for these experiments.

Do not build a production recovery controller.

Test discovery and status across multiple targets.

Keep unavailable, unauthorized, stopped, deleting, and absent states distinct.

Test stale observations and lost events.

Cover session state, Git branch, PR, CI, usage, and human or JSON output contracts.

Keep useful instance state available when GitHub is unavailable.

Separate builder, gateway, optional-engine, and host health.

Test management with a reachable OpenShell target and an unavailable separate builder.

A new image build must report the builder failure accurately.

Test runtime pruning and image pruning separately.

Protect foreign resources and active instances.

Test prewarm for binaries, roles, images, and explicit optional engines.

Ordinary prewarm must not silently enable Docker capability.

Test single adoption of a prepared resource.

Cover mount-drift decisions, keep-awake behavior, and concurrent first-entry or last-exit actions.

## 15. Prove the required target matrix

Declare the required target matrix before final experiments.

Include current supported desktop environments.

Include required local container and VM targets.

Include remote Linux, remote macOS, and Kubernetes.

Keep new distributed requirements separate from current desktop behavior.

Keep Windows and general agent collaboration as future design requirements.

Do not claim they already work.

Do not require every possible role, architecture, engine, and account combination.

Use representative combinations that cover each distinct mechanism and supported launch path.

A missing required environment remains BLOCKED or NOT TESTED.

Do not remove it from scope to obtain a readiness verdict.

### Gateway and VM decisions

Use separate target configurations where compute drivers differ.

Prove independent credentials, inventories, state directories, and cleanup.

Test two gateways sharing an engine with distinct ownership namespaces.

The reviewed VM implementation uses gateway-level sizing.

Prove the chosen method for different requested VM sizes.

Do not pass unsupported per-sandbox CPU or memory fields.

Test the actual role mount layout.

Account for directory-only mounts and architecture-dependent mount limits.

The reviewed limits are three mounts on x86_64 and 32 on ARM64.

Do not expose unrelated private directories to reduce the mount count.

Test host permission boundaries and the documented virtiofs limitations.

Prove service access and callbacks through the VM network model.

### Remote and Kubernetes decisions

Prove image delivery to a different machine.

Select the remote project-storage model.

State synchronization, conflict, and export behavior.

Do not describe copied files as live host mounts.

For Kubernetes, test controller prerequisites, enforced network policy, storage, image credentials, and authenticated gateway reachability.

Test target outage while other targets remain usable.

Show that host actions return to the correct desktop client.

## 16. Run combined experiments and measure costs

Run the selected architecture as one combined fixture.

Include:

- The actual role-derived image.
- Two admitted agent/account domains.
- A generic shell domain.
- Shared project data and separate private data.
- One real authenticated coding task.
- An edit-build-test cycle.
- Persistent session I/O.
- An account-scoped operation.
- An approved credential operation.
- Disconnect and reconnect.
- Retained-state recovery.
- A failed launch followed by owned-resource cleanup.

Run the required Docker workflow with the capability enabled.

Run its denial test with the capability disabled.

Run the separate verification worker.

Show that the mechanisms work together under the same configuration.

Measure:

- Image build and image transfer.
- Cold and warm sandbox startup.
- Time to a usable agent session.
- Attach and reconnect latency.
- Idle gateway and supervisor costs.
- Per-sandbox CPU and memory.
- Additional account-domain costs.
- VM overhead.
- Docker engine and child-container costs.
- Concurrent instance startup.
- Stop and cleanup time.
- Disk growth and cache recovery.

Record sample counts and cache conditions.

Do not report tail percentiles from insufficient samples.

Compare with current Jackin on the same hardware where practical.

Explain material costs of the selected architecture.

## 17. Evidence and independent review

For each experiment, record:

- Requirement and source trace.
- Expected result.
- Exact versions and image digests.
- Host, architecture, kernel, engine, and gateway configuration.
- Policy and authentication mechanism.
- Commands or executable script.
- Observed result and relevant logs.
- Resource identities.
- Cleanup result.
- Remaining limitation.

Assign one result:

- PASS.
- FAIL.
- BLOCKED.
- NOT TESTED.

Assign the mechanism separately:

- Released OpenShell feature.
- Configuration.
- Jackin-side adaptation.
- External service.
- Workaround.
- Experimental OpenShell patch.

Do not use a successful workaround to erase a failed native behavior.

Show whether the workaround preserves the required user workflow.

Use disposable resources with unique ownership identifiers.

Compare unrelated workload inventory before and after experiments.

Use a separate reviewer for source coverage.

Use another reviewer for authority, storage, and cleanup.

Review the selected architecture across all feature areas.

Replay the critical combined experiment from fresh resources.

Resolve review findings or retain them as explicit blockers.

## 18. Deliverables and final decision

Produce these deliverables:

| Deliverable | Required content |
|---|---|
| Source inventory | Every production runtime call site, caller, classification, and replacement decision. |
| User workflow contract | Current working behavior, new requirements, incomplete features, and release acceptance cases. |
| Responsibility map | What OpenShell does, what Jackin retains, and what requires a different mechanism. |
| Architecture decisions | Selected process, identity, storage, transport, target, image, and Docker-capability designs. |
| POC results | Reproduction scripts, raw evidence, failures, workarounds, and target coverage. |
| Refactor plan | Crate and module changes, deletion list, new interfaces, dependencies, sequence, and test gates. |
| Readiness report | Final verdict, unresolved blockers, required patches, limits, and remaining implementation work. |

The refactor plan must identify each retained direct Docker operation.

Allow only justified builder, explicit capability, or OpenShell infrastructure operations.

Identify every old agent-execution path for removal.

Do not remove useful generic utilities merely because they reside in a Docker-related crate.

Give the future rewrite a complete release acceptance suite.

Do not claim that the unwritten product has passed that suite.

### Research acceptance

Use this verdict only when the research gate passes:

**READY TO START THE FULL OPENSHELL REFACTOR**

The research gate requires:

- A complete runtime source inventory.
- A replacement decision for every required workflow.
- One coherent architecture.
- Live evidence for every changed runtime, transport, storage, identity, and credential assumption.
- Successful critical combined experiments.
- Evidence for all required target types.
- A tested solution for optional Docker capability.
- No required capability left unresolved.
- A concrete implementation sequence and release test plan.
- Independent review of the decision.

Unchanged pure product logic can use source evidence and explicit release tests.

New platform assumptions require live experiments.

A proposed patch or unavailable test environment is not a pass.

Use this verdict when a required item remains unresolved:

**NOT READY TO START THE FULL OPENSHELL REFACTOR**

For each blocker, state:

1. The affected user workflow.
2. The missing capability or failed assumption.
3. The evidence.
4. The proposed solution.
5. The smallest remaining experiment or upstream change.

Keep the full replacement objective throughout the work.

Do not reduce the final result to readiness for a limited prototype.