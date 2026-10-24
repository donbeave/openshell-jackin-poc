# Is the OpenShell research enough to rewrite Jackin?

## Decision

**Enough to start a focused runtime rewrite prototype. Not enough to commit to replacing Jackin's current runtime or claim user-feature parity.**

The earlier report measured an infrastructure contract. This follow-up asks a different question: which properties preserve what Jackin gives its users? Several earlier gaps are not independent blockers for Jackin. Conversely, the PoC did not exercise several of Jackin's most important product behaviors.

Recommended direction: rewrite the execution backend around OpenShell while retaining explicit ownership of Jackin's roles, workspaces, account authorization, session UX, durable state, and optional Docker engines. Use the existing runtime boundaries as the implementation seam. This is not a recommendation to keep a permanent legacy shim or to replace product behavior with OpenShell CLI commands.

No Jackin code was modified, built, or run for this follow-up. This is pinned source research plus an audit of the earlier execution evidence, not new runtime validation.

## Source baseline and evidence limits

- Jackin current main checked for this research: **41bad147b5ba9db09be99b07248531ce1bd867be**. The earlier PoC read **7d4b8acea25d28fd5286c958e3890148fc2bf40e**. The current local checkout matches the new pin and was read without modification.
- Architect: **7b72b38fe1d66e35c0931899c53bf3719592bbcc**, unchanged from the PoC. Its manifest declares six agent choices; the Jackin core source enumerates twelve adapters, subject to per-role support filtering. An adapter enum is not a runtime-tested compatibility result.
- OpenShell latest published stable remains **v0.1.5**, tested commit **bdb956f2cd65a635f1294fccf1d138d263bf650f**. No newer runtime behavior is inferred.
- Source pins: [source-pins.json](results/rewrite-readiness/source-pins.json). Independent research: [product contract](results/rewrite-readiness/product-contract.md), [six-gap relevance](results/rewrite-readiness/gap-relevance.md), [evidence audit](results/rewrite-readiness/evidence-audit.md).
- Existing runtime proof remains OrbStack Linux ARM64 on macOS, plus a limited packaged OpenShell VM profile. The latter is not Jackin's Apple Container backend.

The newly merged host-account authority and credential transcript foundations are not production launch/reconnect dependencies at this pin. They must not be counted as already shipped account-refresh behavior. Existing named coding-agent accounts, per-workspace authorization, credential staging and admission checks are active and must be considered.

## What Jackin actually gives users

| User outcome | Product behavior that a rewrite must account for | What OpenShell could replace |
| --- | --- | --- |
| Start the right agent in the right project | Console/load flow; role selection/trust/manifest; supported agent and account; launch progress and failure messages | Sandbox create/exec and runtime process supervision |
| Work on the intended files | Workspace authorization, read-only/writable mounts, working directory, Shared/Worktree/Clone Git modes, Git links and configured pull-on-entry | Low-level storage and mount mechanism, if semantics are proved |
| Use the correct credentials and keep personal state | Named account discovery/selection, workspace grants, per-instance credential/home/cache staging, revision/admission rules, history/plugins/runtime config | Credential transport or isolation primitives, not Jackin account decisions |
| Supervise and resume multiple agents | Capsule sessions/tabs, input/send/interrupt/resize, events/status, reconnect and new-session behavior | Underlying transport and sandbox lifecycle |
| Build and test ordinary projects, optionally using Docker | Role tools/hooks, normal Cargo/nextest commands, selected Docker grants, Docker/Compose/Testcontainers access | Workload execution and network/engine connectivity |
| Stop, recover or remove an instance predictably | `hardline`, `eject`, `exile`, `purge`, immutable resource identity checks, retained state versus destroyed runtime resources | Runtime stop/start/delete primitives, not the product retention decision |

These contracts are traced into implementation in the [product report](results/rewrite-readiness/product-contract.md#implementation-trace-at-41bad147-static-source-evidence). Important corrections to README-only research:

- Docker is the default/full path; Apple Container has real dispatch and launch/reconnect code but still an explicit Phase 0 finalize failure. It is neither nonexistent nor a complete parity baseline. See [backend.rs](https://github.com/jackin-project/jackin/blob/41bad147b5ba9db09be99b07248531ce1bd867be/crates/services/jackin-runtime/src/runtime/backend.rs).
- DinD is conditional on effective grants. The base `standard` Docker profile is network-open with DinD disabled; `compat` enables privileged DinD. Role/workspace/CLI resolution matters. Do not assume every Jackin instance needs an engine. See [effective.rs](https://github.com/jackin-project/jackin/blob/41bad147b5ba9db09be99b07248531ce1bd867be/crates/services/jackin-runtime-docker-profile/src/docker_profile/effective.rs#L26-L90).
- Plain eject/exile tears down runtime plumbing while retaining persisted instance state. Purge is a separate destructive operation. Hardline reconnects/reconstructs retained instances. A rewrite must not silently replace these with one indiscriminate delete operation.
- Architect declares Claude, Codex, Amp, OpenCode, Kimi and Grok, plus a real preflight script that configures agent-specific hooks/MCP/state. The small PoC image and one marker hook are not the complete role. See [role manifest](https://github.com/jackin-project/jackin-the-architect/blob/7b72b38fe1d66e35c0931899c53bf3719592bbcc/jackin.role.toml) and [preflight](https://github.com/jackin-project/jackin-the-architect/blob/7b72b38fe1d66e35c0931899c53bf3719592bbcc/hooks/preflight.sh).

## Do the six reported gaps matter to Jackin?

| Gap | Needed for Jackin? | Product assessment and existing proof |
| --- | --- | --- |
| Changed-binary network denial | **A real parity risk for normal compiled-code network tests** | Users need to edit and rerun tests with normal commands. The precise output filename is an internal detail; breaking network access after rebuild is user-visible. The PoC proves a native Rust HTTP baseline works, then two same-path changed-hash cycles fail. The real Rust Testcontainers first run works. It does **not** prove a modified Testcontainers cycle works through a transparent workaround. An equivalent mapping of Jackin's current network-open profile was not tested either; do not infer that the risk disappears there. |
| Policy updates drop active connections | **Only if the chosen design updates effective policy during work** | No existing live network-rule editor was found. Creation-time policies can avoid requiring hot-update continuity. However, a rewrite using automatic provider/account updates may also trigger effective-policy changes; absence of a UI does not prove absence of reloads. Test the chosen credential/policy path. The observed stream loss remains real. |
| Killed test process leaves a child container | **Immediate per-test cleanup is not a demonstrated Jackin promise** | Current Jackin owns the whole instance stack and supplies explicit teardown and orphan-sidecar GC. That is different from cleaning every Testcontainers child immediately after SIGKILL. Preserve recovery and explicit eject/exile cleanup; do not automatically destroy the instance merely because one test/tab died. Stronger per-test cleanup would be an additional guarantee. |
| OpenShell does not own the external daemon | **Native OpenShell ownership is not required** | Jackin already provisions, labels, tracks and tears down its DinD resources. It can continue owning a dedicated external engine while OpenShell owns the agent sandbox. The required outcome is correct Jackin lifecycle and cleanup, not a particular owner implementation. The manual fixture proves connectivity, not the rewritten product's reconciliation. |
| Docker children do not inherit agent policy | **Not a newly introduced parity gap by itself** | Current Jackin has a documented and code-visible partial boundary: the role-container firewall does not enforce inner Docker egress. Preserve that disclosure or implement/prove a stronger boundary. Never advertise agent-level rules as containment of all child workloads. |
| Real agent authentication untested | **Essential missing proof before user-ready replacement** | Jackin's purpose is to run actual coding agents with selected accounts. `--version`, harmless provider placeholders and gateway/daemon mTLS do not prove API-key/OAuth login, refresh, account selection or conversation continuation. This is an evidence gap, not proof OpenShell cannot authenticate an agent. |

Detailed sources, current teardown semantics and evidence caveats are in [gap-relevance.md](results/rewrite-readiness/gap-relevance.md). Its interpretation of current Jackin profiles describes Jackin source; it is not an executed OpenShell network-open compatibility test.

## Important rewrite questions the original six-gap list missed

### 1. A live host project is not the named-volume experiment

The PoC uploaded test source into an approved Docker volume, attached that volume to agent and dedicated daemon, and proved live changes between those two consumers. That is useful. It does not prove that a user's real host checkout, read-only mounts, linked Git worktrees, clone isolation and concurrent host editor retain their behavior.

OpenShell's pinned Docker runtime documentation says host bind mounts require `enable_bind_mounts = true` and driver resource admission disabled. The PoC did not disable admission or test that path. Mount targets also cannot replace the workspace root or protected OpenShell paths. Therefore host-workspace integration and working-directory translation need an explicit security/semantics design and execution proof. Do not silently disable checks to call the existing mount proof complete. See [runtime mount contract](https://github.com/NVIDIA/OpenShell/blob/bdb956f2cd65a635f1294fccf1d138d263bf650f/docs/how-it-works/sandboxes/runtimes.mdx#L150-L190).

### 2. A shell PTY is not a Capsule session

Jackin's user interface relies on Capsule's session/control protocol. Current host attach chooses a direct Unix socket or `docker exec -i ... jackin-capsule attach-proxy`. OpenShell's tested shell input, resize and Ctrl-D reconnect do not prove that protocol, tab state, events, send/interrupt and conversation resume.

OpenShell replaces the image entrypoint and owns PID1. Capsule supports a forced daemon mode, so PID1 is not sufficient evidence of incompatibility. But its startup mode, environment, control socket, protocol negotiation, signal/lifetime behavior and binary-safe full-duplex bridge remain untested. See [Capsule main](https://github.com/jackin-project/jackin/blob/41bad147b5ba9db09be99b07248531ce1bd867be/crates/apps/jackin-capsule/src/main.rs), [argv](https://github.com/jackin-project/jackin/blob/41bad147b5ba9db09be99b07248531ce1bd867be/crates/apps/jackin-capsule/src/argv.rs), and [attach transport](https://github.com/jackin-project/jackin/blob/41bad147b5ba9db09be99b07248531ce1bd867be/crates/services/jackin-runtime-attach-transport/src/transport.rs).

### 3. The tested Python/CLI control plane is not a Rust integration proof

The PoC used CLI and Python SDK mTLS. Jackin is Rust. The pinned `openshell-sdk` Rust client explicitly lacks client-certificate mTLS support; the CLI has a separate legacy mTLS path. Its curated exec buffers output, accepts initial stdin bytes, and hardcodes `tty: false`; raw RPCs expose additional server functionality.

This does **not** mean OpenShell lacks mTLS or interactive execution. It means a Rust-native caller cannot simply be assumed equivalent to the tested Python path. A raw authenticated gRPC route, existing CLI path or other secure transport must be selected and proved, including Capsule streaming and cancellation. No TLS check should be disabled to bridge the mismatch. Sources: [ClientConfig](https://github.com/NVIDIA/OpenShell/blob/bdb956f2cd65a635f1294fccf1d138d263bf650f/crates/openshell-sdk/src/config.rs#L63-L98), [TLS transport](https://github.com/NVIDIA/OpenShell/blob/bdb956f2cd65a635f1294fccf1d138d263bf650f/crates/openshell-sdk/src/transport.rs#L129-L143), [curated exec](https://github.com/NVIDIA/OpenShell/blob/bdb956f2cd65a635f1294fccf1d138d263bf650f/crates/openshell-sdk/src/client.rs#L604-L665).

### 4. Stored bytes are not agent/account-state parity

The PoC retained files across stop/start. Jackin selects accounts, authorizes them for workspaces, stages runtime-specific credential/home/cache directories, and checks account revisions on reconnect. History, plugins, OAuth refresh and agent-specific files need their own user-journey proof. Its twelve source-enumerated adapters and six Architect choices were not validated by changing one Claude version to another.

### 5. Docker-executed Rust is only a partial workaround proof

The child-container experiment compiled and ran a loopback Rust test, used a distinct target directory, and returned a result file by copy. It did not run a changed Rust Testcontainers test inside that child against the dedicated engine, nor prove a transparent way for ordinary agent-issued Cargo commands to take that route. That solution remains a candidate, not completed parity evidence.

## Smallest evidence gates before a full runtime replacement decision

| Gate | User-visible acceptance condition | Why existing proof is insufficient |
| --- | --- | --- |
| Real role + account + Capsule journey | Launch actual Architect with one approved account; prompt performs an edit/build/test; attach/send/interrupt/resize/reconnect work; expected session/history survives the documented restart boundary | Version commands, marker hook and plain shell PTY are not this journey |
| Real host workspace and Git modes | Host edit appears in agent, agent edit appears on host, read-only mount is enforced, Shared/Worktree/Clone behave as declared, Git links/status work and cleanup preserves the original checkout | Agent-to-daemon volume exchange and upload copies do not prove host-worktree behavior |
| Repeatable networked development | Edit a Rust Testcontainers test twice; normal Cargo/nextest workflow rebuilds and exchanges data with its service each time under the intended security profile; any internal workaround is explicit and tested | Native HTTP replacement fails; first Testcontainers and Docker loopback tests pass separately |
| Security/profile translation | Selected Jackin network, user, sudo/system-write, capabilities, no-new-privileges, Docker grant and resource-limit semantics map explicitly to the supported OpenShell profile; unsupported grants are visible rather than silently weakened | One restricted sandbox and a few memory/CPU checks do not validate Jackin's profile matrix |
| Lifecycle and ownership | Interrupted create, restart/hardline, eject/exile and purge have correct ownership and distinct retention; engine/children disappear on explicit runtime teardown; unrelated instances survive | Manual fixture cleanup and sandbox deletion are not the Jackin product state machine |
| Rust control-plane transport | Secure gateway authentication, raw/full-duplex Capsule path, status/errors, process cancellation and deletion confirmation work from the intended Rust caller | Python/CLI mTLS success does not cover Rust SDK limitations or the Capsule protocol |

Before shipping broader parity, extend the account/agent matrix to the supported role combinations and the platform matrix to the intended supported hosts. A Docker-first prototype does not validate Docker Desktop/native Linux, and the OpenShell VM experiment does not validate Jackin's partial Apple Container backend. Explicitly decide any scope changes rather than silently dropping existing behavior.

Security/profile translation is part of these gates: network-open versus allowlist behavior, optional DinD, system-write/sudo grants, hooks and resource limits cannot be inferred from one default restricted sandbox. The PoC did not verify all existing Jackin security profiles. The assessment assumes implemented user behavior remains in scope unless a deliberate product change is declared; it does not require reproducing every old internal implementation.

These are proposed next acceptance experiments. They were **not run** in this source-research follow-up. No controller, daemon manager, production OpenShell extension or Jackin integration was built.

## Final answer

**Start a bounded OpenShell-backed runtime prototype: yes. Commit to the full rewrite or call it a verified replacement: no.**

We do not need OpenShell itself to own DinD, support live policy editing that Jackin does not expose, or guarantee instant cleanup of every killed test. We do need a usable authenticated agent, Capsule/session behavior, correct real-project access and retained state, working normal development loops, and Jackin-owned lifecycle semantics. The original PoC established valuable building blocks but did not verify that product contract.

The original [DECISION.md](DECISION.md) and [CAPABILITY_MATRIX.md](CAPABILITY_MATRIX.md) are retained as answers to the original infrastructure experiment. This product-level assessment changes the relevance of some gaps; it does not turn untested features into passes or erase negative execution results.
