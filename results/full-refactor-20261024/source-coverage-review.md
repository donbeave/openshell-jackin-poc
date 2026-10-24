# Independent source coverage review

Reviewed Jackin commit `6e266406b49da2ab3c55355f3b7d33d1643ee6cd`, source archive tree `11c7af3812dd9ba0be27f6ae33fc078fa40ff85c`. This review inspects source and research artifacts only. No runtime test or product change was performed. The archive has no `.git`; the containing research repository revision is not source provenance.

## Disposition

Final source-coverage disposition: all actionable findings identified by this review are closed in the revised artifacts. The reviewed inventory now distinguishes called production behavior, uncalled foundations, builder operations, optional-engine resources, and required OpenShell API changes. This is a source-coverage review only: it gives no runtime-readiness or full-refactor approval. Historical findings and their correction checkpoints are retained below.

## Findings

1. **High — the claimed exhaustive inventory initially left every executed action unresolved.** At first review, all 111 `method_calls[].action` values in `exhaustive-docker-calls.json` were exactly `unresolved operation`; rows lacked callers/user entries, exact replacement operations and code changes. The owner is expanding the schema. In the updated DM-001 sample, `replacement_operation` still says only “Replace only Docker agent-runtime transport with OpenShell sandbox API”; `required_code_change` says only “Migrate this exact method caller”. Those are not an exact replacement operation or an unresolved API requirement. The row's release-test text still refers to “unresolved operation”. Complete each row with its actual resource and operation, including name/ID precondition and failure semantics. Do not mark the inventory complete merely because 111 search lines exist.

2. **High — resource ownership was classified from a cleanup crate rather than the operation.** `crates/services/jackin-runtime-cleanup-eject-resources/src/eject_resources.rs:35` removes `role_handle`, the agent runtime container. DM-023 classified that call `ACTIVE_OPTIONAL_DOCKER` and routed it to the dedicated-engine owner. In the same function, line 40 removes `dind_handle`, and lines 44/46 remove certificates/network. The role removal must map to OpenShell sandbox deletion; the engine and its infrastructure require the explicitly selected engine owner. Review mixed-resource functions similarly: `jackin-runtime-launch-load-cleanup/src/load_cleanup.rs:151` removes the role, while `:169` removes DinD. The new inventory must distinguish those operands and retained resources, rather than assigning a whole source directory one replacement.

3. **High — active/foundation classification conflicts with production callers.** The Apple audit says Docker grant readback is active (`audit-apple-vm.md` profile/readback rows; JSON `profiles-grant-readback-sizing`). At the selected pin, `DockerApi::inspect_full_container_by_id` exists at `crates/core/jackin-core/src/docker.rs:253` and its adapter implementation at `crates/adapters/jackin-docker/src/docker_client.rs:974`; no production invocation was found. `compare_grant_vs_actual` is defined at `jackin-runtime-docker-profile/src/docker_profile/workflow_grant.rs:212`, invoked only by its tests, and re-exported. The launch caller explicitly passes `workflow_grant: None` at `jackin-runtime/src/runtime/launch/launch_pipeline/launch_core/orchestrate/initialize.rs:68`. Keep active ordinary profile flag application distinct from this uncalled readback foundation. Likewise, `jackin-isolation/src/capture.rs:450` defines `capture_checkpoint`, but only `capture/tests.rs` invokes it. DM-028–031 must not call its pause/resume path active production behavior. Current `workflow record checkpoint` records metadata through the service; it does not invoke this paused-worker capture procedure.

4. **Medium — the 59-line direct-command index omitted multiline and helper-mediated execution.** Missing call-level rows included `jackin-runtime-image/src/image/version.rs:53–54` (`docker run --rm --entrypoint ... --version`), `jackin-runtime/src/runtime/launch/launch_runtime/profile.rs:48–49` (`docker info`), `crates/apps/jackin/src/console/services/instances.rs:111` and `:285` (list/inspect), `crates/apps/jackin/src/console/workflows.rs:155` and `:185` (inspect/status), `crates/apps/jackin/src/app/workflow_cmd.rs:1383` (image digest query), and `jackin-runtime-usage-relay/src/usage_relay.rs:381` (Docker program passed into `start_tunnel_with_command`, spawned at `:404–419`). Several appear in grouped domain prose, but were missing from the purported per-call inventory. Include each executed action, caller and owner; a diagnostic string containing “docker inspect” is not the corresponding execution call. Use multiline searches and trace program arguments through generic subprocess helpers.

## Checks and supported observations

- The selected entrypoint has six initial agent cases. Capsule sibling spawn ultimately invokes that same entrypoint; twelve setup branches do not establish twelve launches. The corrected Capsule audit now makes this distinction. The entrypoint and agent-setup source are unchanged between `41bad147...` and `6e266406...`; child ownership/reaping paths changed and require separate compatibility analysis.
- `crates/apps/jackin-capsule/src/main.rs:38–47` places Darwin reaper preparation/activation behind `cfg(target_os = "macos")`. Linux workloads on a macOS host do not execute that path. Keep the Apple audit wording qualified by the actual process platform.
- The workflow verification path is correctly identified as independent Docker execution, rather than optional agent Docker access: `jackin-workflow/src/verify.rs:431` and `docker_sandbox_command` at `:776` are active through workflow record-test callers.
- Agent-version probing, management preflight, status, snapshot, usage and crash diagnosis are recognized in the domain reports. Recognition is useful, but exact action/owner/replacement rows remain necessary.
- Tests, documentation, telemetry labels and dependency declarations must stay separate from production invocations. CI/build commands may remain justified infrastructure dependencies, but must have named exclusions rather than being silently dropped.

## Reproduction of the coverage checks

From the research repository, inspect the immutable source archive with `rg`:

```sh
rg -n '"docker"' experiments/full-refactor-20261024/source/jackin/crates --glob '*.rs' --glob '!**/tests/**' --glob '!**/tests.rs'
rg -n 'inspect_full_container_by_id|compare_grant_vs_actual|capture_checkpoint' experiments/full-refactor-20261024/source/jackin/crates --glob '*.rs'
rg -n -uu 'docker|container' experiments/full-refactor-20261024/source/jackin/.github
```

Then follow each production caller, including variable `program` arguments and generic runner wrappers. Search counts alone do not establish a call graph or completeness.

## Re-review of the expanded inventory

The author expanded the inventory to 137 rows (111 method hits plus 26 individual direct Docker operations). The concrete missing version/profile/console/workflow/usage calls were added, along with image-store diagnostics, Docker version preflight, and Docker context discovery. Role sandbox removal is now distinct from DinD sidecar removal; mixed rollback and engine-network/certificate operations were corrected. Builder image listing/removal remains separate from OpenShell sandbox inventory and prepared-image stores. The duplicate `class`/`classification` fields now agree.

The Apple audit corrected grant readback and paused checkpoint capture to no-production-caller foundations, and qualified Darwin reaping by the actual process target. Those concrete classification findings are resolved.

Two accuracy issues remain pending the final mapping revision:

- Released OpenShell `GetSandboxRequest` (`proto/openshell.proto:1392`) has `name` and `workspace_scope`, not an immutable ID. `grpc/sandbox.rs:933` resolves it through `resolve_and_authorize_sandbox_name` and the user branch at `:225` performs `get_message_by_name`. An exact replacement must therefore say name-based read plus returned-ID verification, or explicitly require a new ID-aware operation. It must not describe `GetSandbox by immutable ID` as a released feature. The same distinction applies to name-based exec/mutations; the experimental Delete patch does not supply an ID-aware Get/Exec/Stop interface. Root confirmed the intended design: canonical-name reads with metadata-ID comparison; identity-guarded mutations remain required upstream changes except as demonstrated by the separately labeled Delete experiment and its own execution results. This is a valid replacement decision with an unresolved capability, not grounds to claim runtime support.
- Some direct command rows still use an internal helper name as `user_entry` (for example DM-132 `finish_test_execution`, DM-133 `test_worker_command`, DM-134 `RemoveContainerOnDrop::drop`) rather than the actual public workflow entry and caller chain. Source inventory should link those helpers to `workflow record test` and its service path; equivalent image helper rows should name load/prewarm/build callers. This is a content requirement, not a JSON-presence check.

Additional outside-index checks: searched `native/**/*.swift`, host operational scripts, and hidden `.github` paths. The Swift matches observed were UI `NSView` containers, UI text and tests/prototypes, not Docker/Apple execution APIs. CI/xtask Docker preflight and profile probes are build/test dependencies and need explicit retained-builder/updated-conformance classifications; they are not proof that the production backend already uses OpenShell.

### Final mapping correction checkpoint

The 137-row Docker inventory now distinguishes released name-addressed reads from proposed ID-bound mutations. Method rows for Capsule readiness/status and CLI status explicitly require an ID/generation-bound exec interface, rather than claiming the released name-addressed Exec RPC already supplies it. Worker rows now trace the actual `workflow record test` → host-daemon `WorkflowRecordTest` → `WorkflowService::record_test` → `run_test_command` path. The earlier helper-only user-entry and API-parameter findings are resolved as source-inventory corrections; the required API capability remains a readiness blocker until executed.

Independent archive verification compared all 5,045 tracked Git blob entries in tree `11c7af3812dd9ba0be27f6ae33fc078fa40ff85c` against the archive files (including symlink contents). There were no missing or mismatched tracked files and no non-blob/submodule entries. This verifies source provenance, not runtime behavior.

One additional Apple classification needs closure: `runtime/apple_container.rs:333–346` defines `remove`/`remove_with` and calls `AppleContainerApi::remove_container`, but no production caller was found for those functions. `AppleContainerBackend::eject` at `runtime/backend.rs:154–155` only invokes `stop_with`; the purge guard lists/checks existence. The Apple audit must not label CLI `rm` as an active product workflow merely because the adapter implements it. Its owner has been asked to trace a caller or mark the path implemented without a production caller.

### Current disposition after the 137-row corrections

The revised Docker inventory closes the concrete Docker findings above. No remaining Docker omission was identified in this review's indexed method/command checks and the additional multiline/helper-mediated checks. This is source coverage only; ID/generation-bound exec and deletion are explicitly required capabilities rather than released support claims. The separately labeled patch must be assessed from its own build and execution evidence.

**One source-classification finding remains open:** the Apple audit still groups CLI `rm` with active production operations even though `apple_container::remove`/`remove_with` has no production caller found. Correct that classification (or cite an actual production caller) before treating the merged source inventory gate as closed. The replacement must not infer that current Apple eject removes the runtime object: its backend calls `stop_with` only, and purge refuses while the object exists. This is a current incomplete Apple workflow, not an OpenShell regression.

No execution-readiness or full-refactor approval is given by this source review.

## Final closure

The Apple audit now explicitly marks `remove`/`remove_with`/CLI `rm` as implemented without a production caller; active eject stops and purge checks exact inventory. This closes the last source-classification finding. No further actionable source-coverage omission was identified in the reviewed 137-row Docker inventory, four domain audits, known required paths, and outside-index checks described above. Required ID/generation-bound operations remain explicit unresolved platform capabilities; their source mapping is a decision, not a claim that released OpenShell executes them.

Reviewed artifact SHA-256 values at 2026-10-24T02:12:02.970003+00:00:

- `exhaustive-docker-calls.json`: `a4ece866ee110db0cb224635ec916e4d2ccc26b9f32a01a686c31da3f0b44140`
- `audit-docker.json`: `22a12dd3a4a9b2cf449b963d1082197d007895f35d75cdc9655bddd005c94138`
- `audit-apple-vm.json`: `6da50171fa23db31010fb64d3f73c88488dc76d956b59b183e9d5cd43b5b0536`
- `audit-capsule-accounts.json`: `6ce85fd620ca66f3e7ac499e4259b71e5ba494c84a8358b90f2b80f9c8c67fcf`
- `audit-workflow-fleet.json`: `ede8fe611dd29792e2f6a0f18f728e30bf99e1c3d93b0c0a0ae44fa28e12b9a3`
