# Independent final review

Reviewed `README.md`, `CAPABILITY_MATRIX.md`, `DECISION.md`, linked command
records, raw policy-stream events, the VM profile, and the clean Engine B
repeat. This is a read-only review of the main deliverables. No engine or
sandbox operations were run for this review.

## Conclusion

The central decision is supported: the complete P1 runtime contract is **NOT
READY**, while the smaller OrbStack external-engine slice is **CONDITIONAL**.
The VM profile supports only its stated agent/version, copied project, offline
Rust compile, and retained-file slice; the full VM contract remains **NOT
READY**. The docs correctly keep authenticated agent operation, UDP, and the
other platform profiles untested. They distinguish external daemon
connectivity from native OpenShell ownership and do not claim production
readiness.

Evidence inspected supports the primary conclusions:

- `native-identity-baseline.json` plus cycles 3 and 4 records a real resolved
  mbx executable path, changed SHA-256 values, normal build commands, denial,
  and policy logs. The alternate target-directory run is clearly labeled a
  workaround.
- Policy stream records show the no-change control complete 20 messages per
  stream, while the unrelated update interrupts both streams (Docker output
  stops at 10 of 30; database gets EOF at iteration 10). The independent
  control is not described as passing the changed-policy case.
- The actual Testcontainers harness was SIGKILLed after data exchange; the
  recorded daemon inspection shows its Redis child remained. Normal success
  and panic cleanup are separate, and do not overstate termination cleanup.
- Engine A/B TLS controls include a valid connection, absent client cert, and
  A's certificate/key against B. The latter is rejected by TLS as “certificate
  required.” The Engine B repeat separately rejects A credentials and keeps
  its own Engine B resources outside OpenShell cleanup.
- The clean repeat confirms the v3 image and bounded Docker/Compose/live-bind/
  Testcontainers slice. Its distinct-path native pass is described as a
  workaround, and forced-client termination left a fixture child, consistent
  with the main result.
- The VM raw report states the effective 2 vCPU / 2048 MiB driver allocation,
  the explicit environment workaround for offline Rust compilation, copied
  file transfer, retained files, and the absence of Docker/Compose/
  Testcontainers tests. The limited profile conclusion matches that scope.
- The rootless Docker status relies on an actual entrypoint attempt whose
  output ends in `iptables: Failed to initialize nft: Operation not
  permitted`; earlier setup errors are retained.

## Finalization status

1. `results/MEASUREMENTS.md` is now present and covers image builds, sandbox
   readiness, authenticated daemon readiness, first successful development
   test, cache state, and available idle/peak usage. It explicitly bounds
   single-run timings and cold/warm conditions. Its figure sources are
   present; the readiness record includes an initial expected EOF poll before
   the successful mutual-TLS response.
2. Final cleanup has run; `results/cleanup/execution.json` records the
   operations. All experiment sandbox deletions were accepted and the next
   scoped sandbox listing was empty. Owned fixture containers and volumes,
   disposable agent tags, temporary gateway listeners and certificate state
   were removed. Final host inventory showed no `ojp-20261024` containers,
   both tested ports had no listeners, and the preserved `unrelated-project-cache-*`
   volumes remained. Some attempted inspect commands returned status 1 because
   a resource was already absent; the socket-engine diagnostic also failed to
   reach an inner Docker socket, but cleanup still removed that disposable
   fixture container and named volumes. Given the final inventories, H6 can
   be marked **PASS / EXTERNAL FIXTURE** for script-owned cleanup only. This
   does not change H4 or establish OpenShell-owned external resource cleanup.
3. The collateral incident is documented consistently across the README,
   matrix and decision. The evidence verifies three previously running
   containers exited with code 137 at the same time, later gateway log lines
   show shutdown following supervisor failure, and an isolated authenticated
   owner profile successfully lists their `Error` state. After explicit user
   approval, the original gateway's existing valid mTLS identity performed
   guarded stop/start on the same three IDs; follow-up get/exec checks report
   all Ready and return the harmless marker with status 0. TLS verification
   stayed enabled; no original config or registered CLI profile changed and
   no key was copied. The initial actor remains unproven and namespace overlap
   remains plausible only. Restoration is now complete, not outstanding.

No other result/mechanism enum mismatch or broken Markdown local link was
found in the reviewed matrix and top-level docs. The matrix's details keep
workarounds separate from released behavior and bound the platform claims.

## Final disposition

No blocking overclaim was found in the revised deliverables. The main decision
remains **NOT READY** for the full runtime requirements. The constrained
external-engine prototype remains **CONDITIONAL**. VM is **NOT READY** for the
full contract and **CONDITIONAL** only for the tested limited slice. Other
platform profiles and authentication modes remain explicitly untested. The
separately approved collateral restoration is complete and verified; it does
not change the cause attribution or any runtime capability result.
