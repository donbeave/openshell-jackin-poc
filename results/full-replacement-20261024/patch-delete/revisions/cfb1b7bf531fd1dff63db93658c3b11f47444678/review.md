# Independent immutable-ID deletion patch review

## Scope and disposition

Reviewed the patch based on released OpenShell `bdb956f2cd65a635f1294fccf1d138d263bf650f`, exported final source commit `cfb1b7bf531fd1dff63db93658c3b11f47444678`. This is a bounded Rust/API/concurrency review, not a full OpenShell or Jackin security review. No product source was edited and no new runtime experiment was run by this reviewer.

**Current disposition: revised strict-ID source passes this bounded code review; new-revision runtime evidence is still pending.** The original `cfb1b7bf` findings and narrow execution scope are preserved below. The strict-ID revision closes those code findings by requiring a stable request UUID, rejecting `allow_missing` in ID mode, binding ledger admission to the requested immutable ID without requiring a live row, preserving workspace authorization, and restricting test cleanup to recorded resources.

## Actionable findings

### 1. Durable request-ID retries fail after successful deletion

`crates/openshell-server/src/grpc/mutation_replay/ordinary.rs:582–588` looks up the requested sandbox ID during `DeleteSandboxRequest::authorize` and returns `NotFound` when the object no longer exists. `mutation_replay.rs:164,170` invokes authorization before the saved-admission lookup/replay path at `:265–318`. Therefore an ordinary successful delete that completes cleanup makes the same nonempty `request_id` retry fail before its persisted success can be replayed. A new missing-ID deletion with `allow_missing=true` also differs between empty and nonempty request IDs. This contradicts the documented 24-hour successful-result replay contract and matters precisely when the original response is lost.

The integration test exercises SDK helpers that set `request_id` to the empty string. The fingerprint unit test proves that a different ID changes the fingerprint; it does not prove admission/replay after the object has disappeared.

Preserve workspace authorization and the immutable target binding independently of a currently existing object row, so a valid prior receipt can be recovered after deletion without resolving a reused name. Add an actual nonempty-UUID request test: first delete, wait until original ID is gone, create a same-name replacement, then retry identical bytes/request ID; return the original receipt without affecting the replacement. Also test a genuinely missing ID with `allow_missing=true` and changed-ID reuse of the same request ID.

### 2. `allow_missing` reports absence for an existing ID in another workspace

`crates/openshell-server/src/grpc/sandbox.rs:1732–1738` combines an absent object and an existing object rejected by the workspace filter into the same branch. With `request_id` empty and `allow_missing=true`, a request selecting an authorized but different workspace returns `AlreadyAbsent` with the foreign object's immutable ID, even though that object still exists. This is not a demonstrated unauthorized deletion, but the result cannot serve as a global-ID absence receipt for retained-data purge and contradicts the new SDK documentation saying wrong selected workspace is rejected.

Keep actual missing-ID handling separate from existing-ID scope mismatch, retaining non-disclosure/error conventions. Test a real second authorized workspace with `allow_missing=true` for both empty and nonempty request IDs; the wrong-scope request must not delete or affirm absence of the existing foreign target. The existing live wrong-workspace test uses default `allow_missing=false`, so it does not cover this branch.

### 3. Integration pre-cleanup trusts short prefixes rather than experiment ownership

`crates/openshell-sdk/tests/delete_by_id_integration.rs` defines `cleanup_prefix` and invokes it with `po`/`pn` before each experiment. It deletes every matching sandbox in the default workspace without a saved creation receipt or ownership label. Immutable-ID deletion prevents name-retarget races, but does not prove that the enumerated resource belongs to this test. No unrelated deletion was demonstrated on the isolated test gateways; reproduction against a reused endpoint remains unsafe.

Use a fresh uniquely owned workspace/namespace or remove the broad pre-cleanup scan and clean only IDs created and recorded by the current run. Keep explicit retained receipts for interrupted-run cleanup rather than broadening name matching.

## Positive review observations

- The new client sends `sandbox_id` with an empty legacy `name`, so an unpatched server rejects instead of silently ignoring an optional identity guard and performing name deletion. The saved released-gateway test demonstrates safe rejection.
- The selector check requires exactly one of name or ID. ID deletion requires a workspace selection, and the handler authorizes the workspace before fetching the object.
- On an existing authorized ID, the handler calls the existing compute `delete_sandbox_by_id`; `compute/mod.rs:2812–2890` locks by target ID and re-reads that ID before mutation. It does not re-resolve the old name to a new object. The saved same-name replacement experiment covers the intended narrow behavior.
- The new field is included in the request fingerprint. Legacy name delete remains available; adding the ID path does not make legacy Stop/Start/Exec or name-based Delete safe from stale first-admission requests.
- No security check was removed to permit root workload execution or alter network/file confinement.

## Evidence and provenance limits

The saved runtime tests and focused tests were reviewed as execution evidence, not rerun. `server-unit-tests.log` contains two new handler tests plus one existing persistence test. `replay-fingerprint-test.log` contains one new fingerprint test. `patched-gateway-runtime.log` records successful deletion and same-name replacement preservation, a valid other workspace creation and denial, dual-selector rejection, and final cleanup. It does not exercise durable ID-delete replay.

The parent identified runtime proof as source commit `1cf7ec3b` before the final `cfb1b7bf` cleanup. Inspection of `git diff 1cf7ec3b cfb1b7bf` shows only collapsing the authorization signature and changing `super::Scope` to the already imported same `Scope` type; no behavior change was found. This is a recorded source compatibility analysis, not proof that an exact `cfb1b7bf` binary was executed. `cargo-check-final.log` is a compile check, not a replacement runtime result.

The run record specifies mutable image tag `ubuntu:22.04`, not an executed immutable image digest. The ID-control result is narrow; final evidence should record the actual image identity if recoverable, or explicitly retain this provenance limitation. Gateway binary identity and the build-overlay inputs also need to remain separate from the published source-patch hash.

No conclusion follows for released support, other drivers/targets, stale Stop/Start/Exec, generation fencing, full session authority, or full Jackin refactor readiness.

Reviewed patch SHA-256: `6b9a7bf23af3676322e55f45e92a4eb65ccc9e5639fbd86bd379638e620632e5`. Review time: 2026-10-24T02:14:06.728699+00:00.

## Strict-ID revision re-review

Reviewed the current uncommitted strict-ID worktree after the original findings. All three code-level findings are closed for the revised interface:

- ID deletion requires a stable nonzero request UUID; the SDK accepts it from the caller and reuses it unchanged in its retry closure.
- Workspace authorization precedes ID resolution. Replay scope binds the literal requested immutable ID without requiring the removed object to exist, while the handler still requires an existing object in the authorized workspace for a first deletion.
- ID mode rejects `allow_missing`, so it cannot issue an absence acknowledgement for an unknown or foreign-workspace target. Unknown and foreign IDs remain indistinguishable errors.
- Dual selectors and missing workspace selection are rejected before mutation admission; normal legacy name semantics remain separate.
- The broad prefix pre-cleanup scan is removed. Current-run sandbox IDs are recorded before readiness waits and carry ownership labels. The unpatched comparison server uses explicitly separate name-based teardown only for those recorded resources, with ID checks and deletion confirmation.

The legacy comparison teardown is **not atomic**. It is acceptable only as a disposable, sole-authority fixture with no concurrent name replacement; document that precondition and do not count it as the new identity guarantee. Tests still need external receipt-based recovery if their process is forcibly interrupted or a panic prevents the normal cleanup path.

The revised tests exercise receipt replay after original deletion and same-name replacement, changed-target request-ID conflict, workspace membership recheck, wrong-scope/unknown-ID errors, unsupported `allow_missing`, and old-server rejection. Source inspection supports the test intent; successful compilation or unit tests alone are not live gateway evidence. Freeze the new commit, retain the original patch/logs separately, and run the revised old/new gateway tests before reporting runtime PASS. No new full-readiness claim follows.

Strict-ID worktree diff SHA-256 relative to `cfb1b7bf` (code/test/dependency files only, tooling overlay excluded): `5a416323fb4a15f7d703944affb46da18efc5abfe7ef5144994d29f650c66b07`. Reviewed 2026-10-24T02:29:35.027691+00:00.
