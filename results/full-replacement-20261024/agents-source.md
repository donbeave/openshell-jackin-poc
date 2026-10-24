# Agent, account, and Capsule source inventory

## Source freeze

This inventory traces Jackin source commit `41bad147b5ba9db09be99b07248531ce1bd867be` in `/Users/example/Projects/jackin-project/jackin`. `git rev-parse HEAD` matched that pin at inspection. This is source evidence only; no runtime test was run. Root froze current revisions after one remote resolution: Jackin unchanged at `41bad147b5ba9db09be99b07248531ce1bd867be`; Architect unchanged at `7b72b38fe1d66e35c0931899c53bf3719592bbcc`; selected OpenShell stable is `v0.1.5` at `bdb956f2cd65a635f1294fccf1d138d263bf650f`. `main` `f571c8e99c185804c39e837a2b70692e957de327` is recorded separately and is not selected for the stable group.

Architect role evidence comes from the pinned-role source extract and `results/rewrite-readiness/product-contract.md`; role commit `7b72b38fe1d66e35c0931899c53bf3719592bbcc` supports Claude, Codex, Amp, Kimi, OpenCode, and Grok. Do not infer support for other agents from Jackin's enum.

## Adapter inventory

At this source pin, `crates/core/jackin-core/src/agent.rs:14-27,29-59` declares and enumerates twelve agents. `crates/core/jackin-core/src/agent/adapters.rs:35-49` registers twelve runtime adapters. This is distinct from actual image launch: `docker/runtime/entrypoint.sh:59-108` handles only six (`claude`, `codex`, `amp`, `kimi`, `opencode`, `grok`); other values fail with `unknown JACKIN_AGENT` and exit 2. Role manifest selection also filters agents: `crates/core/jackin-core/src/manifest.rs:64-82` reads `agents` (default Claude) and only has role-specific configuration for the first six. Architect declares those six.

| Agent | Jackin adapter and image installer | Active launch path at this pin | Architect role | Rewrite test scope |
|---|---|---|---|---|
| Claude | `agent/adapters/claude.rs`; release/install in `jackin-image/src/agent_binary.rs:440-460,522-542` | Yes; entrypoint lines 59-68 | Supported | Build/install, selected model/effort, API key and OAuth-token paths separately, profile-sync path, hooks/plugins/state, authenticated task. |
| Codex | `agent/adapters/codex.rs`; resolver lines 440-460,591-615 | Yes; lines 69-74 | Supported | Include sibling code-mode binary and selected model/account state; test API key separately from profile sync. |
| Amp | `agent/adapters/amp.rs`; resolver lines 440-460,544-566 | Yes; lines 75-79 | Supported | API key/profile sync, `.local/share/amp` and `.config/amp` state, actual startup and task. |
| Kimi | `agent/adapters/kimi.rs`; resolver lines 440-460,568-589 | Yes; lines 80-85 | Supported | API key/profile sync, `.kimi-code` account state, actual startup and task. |
| OpenCode | `agent/adapters/opencode.rs`; resolver lines 440-460 | Yes; lines 86-92 | Supported | Provider API key/profile sync; config, state and plugin/MCP setup. |
| Grok | `agent/adapters/grok.rs`; resolver lines 440-460 | Yes; lines 93-103 | Supported | xAI API key/profile sync, model argument and authenticated task. |
| Antigravity | `agent/adapters/antigravity.rs`; resolver lines 448-449 | No; falls through to entrypoint rejection | Not in Architect | Enum/adapter presence does not establish a usable end-to-end Jackin launch. Explicit unsupported/negative result required; do not count as an Architect path. |
| Gemini | `agent/adapters/gemini.rs`; npm resolver lines 449-450 | No; falls through to rejection | Not in Architect | Same; installer mapping exists, actual standard entrypoint missing. |
| Cursor | `agent/adapters/cursor.rs`; resolver deliberately returns no relocatable binary (lines 450-453) | No | Not in Architect | Installer reason makes image-prefetch path unavailable; no full workflow established. |
| Muse | `agent/adapters/muse.rs`; no verified standalone installer (fallback errors) | No | Not in Architect | Requires host binary prefetch per fallback text; no standard entrypoint. |
| omp | `agent/adapters/omp.rs`; npm resolver lines 455-456 | No | Not in Architect | Installer mapping exists; no standard entrypoint. |
| Hermes | `agent/adapters/hermes.rs`; resolver says official Python/uv install is not relocatable (lines 456-459) | No | Not in Architect | Installer reason makes relocatable image-prefetch path unavailable; no standard entrypoint. |

The six non-entrypoint agents are existing Jackin completeness gaps at this pin, not OpenShell regressions. The enum, registry, and installer resolvers must not be presented as twelve active supported launch workflows. Scope for the full replacement includes all six actually implemented/role-supported paths plus explicit preservation of current rejection behavior for the six unsupported launch paths unless Jackin's separately frozen current revision changes that contract.

## Identity, account, credential, and agent state

Static contract anchors: `crates/core/jackin-core/src/agent.rs:91-139` maps API-key environment names and modes. Claude supports `Sync`, `ApiKey`, `OAuthToken`, `Ignore`; all other adapters expose `Sync`, `ApiKey`, `Ignore`. Its OAuth-token path is unique. `results/rewrite-readiness/product-contract.md:91` traces launch selection to `jackin-runtime-launch-capsule-setup`, per-instance credential staging/swap, agent-specific helpers, account revision fingerprints, and reconnect admission. These source mappings do not prove OpenShell runtime behavior.

Required rewrite behavior per actual supported path:

- Resolve named account for agent/workspace/role; reject missing or unauthorized binding and wrong-agent binding.
- Preserve the distinct auth methods: API key injection, profile synchronization of agent files/state, and Claude OAuth token. Do not infer one method from another.
- Stage credentials into per-instance private paths; prevent ordinary agent or sibling instance from reading another account's material. Test harmless fixture identities, negative cross-account reads and wrong revision.
- Keep credential values out of logs and artifacts. Use approved live test credentials for model authentication; current evidence says none were approved/available, so authenticated coding tasks remain BLOCKED until provisioned.
- Preserve each adapter's credential/config directories, agent state, selected model, effort, session metadata, plugins and cache where its adapter defines them. Exact `AgentStatePaths` live in `crates/core/jackin-core/src/agent/adapters/*.rs`; profile/credential staging also has provider-specific implementations in `crates/services/jackin-instance-agents/src/`.

Required evidence for full readiness: for each of the six role-supported adapters, installed binary version and launch, one approved authenticated coding task that edits a file and runs the role's build/test, plus account-selection positive and wrong-account negative cases. Shared evidence is acceptable only where the exact installed launcher, auth route, config path, and session route are identical; source currently defines agent-specific launch args, state roots, and credential handling, so blanket six-agent extrapolation is not valid. In absence of credentials, each live authentication row is BLOCKED, not PASS or NOT TESTED.

## Role build, tools, plugins, and hooks

Jackin's `crates/adapters/jackin-image/src/derived_image.rs` builds the role-specific image: role Dockerfile plus supported agent binaries, runtime entrypoint, Capsule, agent status support, hooks, and selected configuration. `image_recipe.rs` derives selected agent set and recipe invalidation. Architect role's pinned manifest/README and preflight hook are the requirements source; the earlier published PoC used a reduced image/hook and cannot be reused for complete role coverage.

For each supported agent, require exact Architect role source, tool/plugin/skill inputs and image identity; unchanged cached build, forced rebuild, agent switch, and local role-source change; installed-agent execution; online dependency fetch; selected model and effort; cache-warm behavior. Reuse of old evidence is not justified for the full role because old image omitted its full manifest/tool/plugin/skill/hook content and was not an authenticated task.

The actual start path explicitly executes `/jackin/runtime/jackin-capsule runtime-setup`, then `setup-once.sh`, `source.sh`, `preflight.sh`, then `exec` of selected CLI (`docker/runtime/entrypoint.sh:23-33,110-159`). Setup-once marker is under `${JACKIN_SESSION_STATE_DIR:-/jackin/state}/hooks/setup-once.done` and therefore requires proof across the promised recreation/state-retention boundary. Hook nonzero status prevents agent launch. Source hook is sourced in the existing working directory and PWD restored. Preflight runs with `$HOME` as working directory. OpenShell does not run image ENTRYPOINT as a contract; proposed integration must invoke this path explicitly or provide an equivalent tested owner.

## Capsule session and control contract

Capsule is a separate Jackin runtime process/protocol, not equivalent to a shell PTY. `crates/apps/jackin-capsule/src/main.rs:21-51` chooses isolated-exec, Git commit hook, `jackin-exec`, daemon mode (PID 1 or scoped `JACKIN_CAPSULE_FORCE_DAEMON`), or client mode. `argv.rs:16-45,85-101` shows forced-daemon guard, exec dispatch, and initial agent resolution. Must scope `JACKIN_CAPSULE_FORCE_DAEMON` to daemon; `attach-proxy`, `take-control`, `release-control` remain client operations.

Protocol/session source is under `crates/apps/jackin-capsule/src/attach_protocol/`, `client/`, `daemon/`, and `crates/core/jackin-protocol/`. Contract requiring runtime proof: binary protocol negotiation; create/focus/send/snapshot/status/events; one exclusive operator control lease; input/output full duplex; stream interruption and session-local cancellation; file export, clipboard, URL-open, reveal-path, activity and usage messages; origin authorization for host actions. Capsule process isolation (`process_isolation/`) is root-dependent before it changes user identity; test actual wrapper as root with two accounts and capture UID/GID/groups/capabilities/filesystem boundaries. A nonroot workload/PTY result does not cover it.

Positive/negative evidence must distinguish: client disconnect vs agent/session exit; sandbox restart vs conversation resume; interrupt one session while another stays alive; unauthorized control claimant; malformed/wrong protocol major; missing capability; denial of host action from untrusted origin. Deterministic event and usage fixtures prove transport only, not billing correctness. Full byte-stream test must include NUL, fragmented frames, EOF, backpressure and diagnostics separation. No mock shell alone establishes this contract.

OpenShell proof currently only establishes ordinary exec/TTY primitives; it did not run Capsule daemon/protocol, account isolation or full lifecycle. Reuse none of those primitive results as Capsule PASS.

## jackin-exec and MCP

`main.rs:24-33` dispatches `__isolated-exec` and `jackin-exec` invocations before daemon/client modes. Entrypoint injects a prompt naming available secure bindings when `JACKIN_EXEC_BINDINGS` is nonempty (`docker/runtime/entrypoint.sh:45-57`). Test real `jackin-exec` contract with a disposable secret: allowed matching binding, operator approval, refusal, missing session capability, wrong identity, unauthorized binding, unavailable resolver, output redaction, and prove ordinary agent cannot obtain the secret from environment/files. Keep model auth distinct from command credential access.

MCP server is a Capsule client command (`argv.rs:25-27,51-54`) and implementation under `crates/apps/jackin-capsule/src/mcp_server/`; probe local tools plus required remote MCP connection. Preserve authentication, session capability and authorization. Historical research reports baseline Linux PID1 requirement for authenticated relay and non-Linux unsupported path; rerun on the frozen source/config. Broader host-account/credential-transcript modules are inactive foundations unless active selected launch path proves otherwise; don't count names/tests as launch support.

## Evidence status and minimal next experiments

All rows above are requirements/source mapping, not runtime PASS. Before any model-login experiment, check only approved test credential availability; never inspect personal credential files. No live agent credential is currently documented as approved in the baseline evidence. Authenticated agent task: BLOCKED pending approved credential. Other independent runtime experiments can proceed after the complete replacement matrix freezes.

Smallest decisive sequence: (1) full Architect image for each supported agent and hook order, no authentication required; (2) Capsule root daemon through actual OpenShell image startup, two account boundaries and framed binary protocol; (3) approved live auth per supported agent, file edit plus role command; (4) account revision/reconnect and persistent-state boundary with harmless distinct fixture accounts. Keep each OpenShell release/patch/target result separate.
