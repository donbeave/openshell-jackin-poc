# Final acceptance audit against the 16-section request

This checks the requested experiment plan and deliverables against the current
README, capability matrix, decision, cleanup records, and experiment evidence.
It does not re-run gateways, sandboxes, Docker engines, or host workloads.

## Section-by-section coverage

| Section | Acceptance check | Disposition and evidence |
| --- | --- | --- |
| 1. Objective | All eight questions answered; terminology used consistently; Jackin product logic out of scope | **Covered.** `DECISION.md` answers build/image, no-grant, selected external engine, Docker/Compose/Testcontainers, edit/build/test, ownership, configuration/workaround, and platform questions. `CAPABILITY_MATRIX.md` distinguishes external daemon connectivity from native ownership. No Jackin files or production extension were added. |
| 2. Sources and requirements | Read Jackin for requirements and Architect as main runtime reference; short category matrix | **Covered.** Pinned source snapshots/commits and explanation are in `results/sources/`; matrix categories include tools/image, process/terminal, files, env/hooks/credentials, policy/limits, lifecycle, optional Docker. Source inspection is labeled separately from runtime results. |
| 3. Work limits | Dedicated experiment directory, small fixtures, one Rust project, real agent, no production subsystem; delegation and isolated repeat/review | **Covered.** `README.md`, `experiments/`, and `results/repeat-final/` identify the scope. The clean Engine B repeat uses its own sandbox and result directory. Independent review is recorded here. No controller, scheduler, worker protocol, dashboard, cluster, custom kernel, or large fork was built. |
| 4. Environment record | OS/CPU/memory/disk, Docker endpoints/versions, gateway identity/config, role/image/policy/resource identity | **Covered.** `results/environment.json`, `results/resource-identities.json`, `results/image-identity.json`, `experiments/gateway/gateway.toml`, `results/gateway/`, `results/architect.source`, and `results/jackin.source` contain these records. The environment is expressly identified as macOS ARM64 with an OrbStack Linux engine, not native Linux or Docker Desktop. |
| 5. A: build agent image | Prebuild before creation; real agent version; project compile; unchanged/cache and forced build; changed version; image delivery; auth status | **Covered with bounded NOT TESTED.** Image and sandbox records in `results/image/` prove an installed Claude Code version before OpenShell use, repeated cached and forced builds, and a second actual Claude version. The final v3 image digest is recorded. Local gateway shares the builder's OrbStack image store; remote registry delivery is not claimed. Authenticated model task is correctly **NOT TESTED** without approved credentials. v2 timings are not attributed to v3. |
| 6. B: basic sandbox operations | Lifecycle, output/status, interactive terminal, reconnect, env/hook, retained file, byte comparison, SDK probe, harmless credential methods | **Covered.** CLI and Python SDK records cover create/list/get/exec/status/stop/start/delete/wait, terminal input/resize/Ctrl-C and Ctrl-D disconnect/reconnect, env/hook, persistence, export/hash, and harmless API-key placeholder injection. Ctrl-P/Ctrl-Q remains a separately recorded failure. OAuth/OIDC and real provider authentication are separately **NOT TESTED**. |
| 7. C: Docker disabled | Docker client present, no socket/credential/engine grant, attempted API access denied | **Covered, with a precise denial limit.** `results/basic/host-mounts.json`, `results/denied/probe.json`, and `results/denied/no-engine.json` show no socket, Docker config, endpoint env, or engine grant and an attempted endpoint failure. Its host name failed DNS resolution in the restricted sandbox; this is endpoint unreachability, not a server-side Docker/TLS rejection. The matrix claims lack of a Docker grant, not a tested API authorization response. |
| 8. D: dedicated engine over mTLS | TCP/TLS passthrough; positive API and operations; invalid/cross-instance certs; resources labeled external | **Covered.** Engine A/B fixture and TLS records in `results/engines/`, `results/main/`, `results/engine/`, and `results/repeat-final/` cover API, build/run/log/exec/stream/cancel, volumes/removal, and cross-client TLS rejection. `README.md` labels it external daemon connectivity; native OpenShell companion support is not inferred. |
| 9. E: bind mounts, Compose, Testcontainers | Shared absolute path and bidirectional changes; Compose health/dependency/ports/source; Rust service data/cleanup; callback and UDP statement | **Covered, including the required negative outcome.** `results/main/`, `results/compose/`, `results/native/`, `results/callback/`, and `results/repeat-final/` contain the evidence. Fixed/allocated ports and `host.docker.internal` endpoint are recorded. Success and panic cleanup pass; actual SIGKILL/client termination leaves a child and is marked FAIL. TCP was tested; UDP remains **NOT TESTED**. |
| 10. F: edit/rebuild and active policy | Same-path source/hash cycles; explicit workaround; no-change control; changed policy and revocation | **Covered.** `results/native/native-identity-*` records normal rebuilds, hashes, network identity denial, and logs; `results/repeat-final/` independently repeats the failure/workaround. `results/policy-streams/` preserves 20-message no-change control, interruption on unrelated update, and separate revocation. Rebuild itself succeeds; the protected execution/network request is denied. |
| 11. G: alternative connections | Unix socket with files/database, disposable engine forwarding, rootless start, Docker-executed tests | **Covered with one FAIL.** `results/alternatives/` and `results/native/` show socket API/file/database, scoped disposable fixture forwarding, actual rootless attempt failing at kernel/network setup, and Docker-executed Rust result transfer. No personal shared daemon is claimed. The workaround is not called native compatibility. |
| 12. H: ownership/cleanup | Two instances, stop/start/delete observations, daemon interruption, child policy, resource limits | **Covered.** `results/ownership/`, `results/repeat-final/`, `results/engines/interrupted-provision.json`, `results/network/`, and `results/limits/` show separate A/B trust/files/ports, persistence, surviving daemon children after sandbox deletion, interrupted-fixture leftovers, network boundary, and distinct agent/daemon limits. OpenShell ownership and fixture cleanup are kept separate. |
| 13. Conditional platforms | Separate profiles; unavailable profiles labeled NOT TESTED; VM claims bounded | **Covered.** A packaged macOS ARM64 libkrun VM profile ran the limited version/build/file-retention slice in `results/gateway-vm/`. Docker Desktop, native Linux, remote gateway, Kubernetes, and a disposable daemon VM are explicitly **NOT TESTED** with missing prerequisites. No platform result is inferred from OrbStack. |
| 14. Small source patch | Reproduce before patch; patch only if one small safe behavior change exists; no large subsystem | **Not applicable and accurately reported.** Released failures were reproduced. Source analysis identifies policy stream revalidation, safe changed-binary authorization, and native daemon lifecycle ownership as broader/safety-sensitive capabilities. No source patch was applied; X1 is **NOT TESTED**, not reported as a pass. |
| 15. Evidence/measurements | PASS/FAIL/BLOCKED/NOT TESTED and one mechanism enum; command logs; redaction; cache/timing/resource measurements | **Covered.** The matrix uses the requested enums; exact commands/stdout/stderr/status are in JSON records. `results/MEASUREMENTS.md` now records image, readiness, first-test, cache and resource figures with limitations. TLS secrets are not in saved evidence. Some expected absent-resource inspections have nonzero statuses in cleanup logs, but their final absence checks are recorded. |
| 16. Deliverables and decision | README, experiments, results, matrix, decision, cleanup, independent repeat/review; per-profile conclusions | **Covered.** All six named artifact categories exist. Cleanup ran and is evidenced in `results/cleanup/execution.json`; the independent Engine B repeat is under `results/repeat-final/`; independent reviews are in `results/review/`. P1 full contract is **NOT READY**; constrained OrbStack slice is **CONDITIONAL**; full VM is **NOT READY** and its narrower tested slice is **CONDITIONAL**. Other tested/unavailable profiles are explicit. |

## Collateral correction completed after explicit approval

Three previously running Docker sandbox containers were found exited with
status 137 at a common timestamp. The initiating actor remains unproven;
subsequent namespace tests make the shared namespace a plausible cause only.
After explicit user approval, the existing original-gateway mTLS identity was
used with TLS verification enabled to stop and start the same three sandbox
IDs. Follow-up SDK checks found all three Ready and ran the same harmless
marker command successfully with exit 0. The raw records are
`results/collateral/restore-originals-execution.json` and
`results/collateral/restoration-verification.json`. No gateway configuration
or registered CLI credential was edited, no credential was copied, and no
TLS check was bypassed. Current workload state is corrected; cause attribution
is still unresolved. This corrective action is distinct from experiment
cleanup and does not change the runtime results.

## Acceptance conclusion

No required experiment group or named deliverable is missing. Several
capabilities correctly remain FAIL or NOT TESTED; they are results, not
unfinished work. The approved collateral restoration is complete and verified,
so it is no longer outstanding; the initial termination actor remains
unproven. The readiness question is answered: the full requested contract is
**NOT READY** on the tested OrbStack profile. A limited external engine
prototype is **CONDITIONAL**, with ownership, policy-change, executable
identity, forced-client cleanup, child network-policy, and authentication
limitations explicit. No production readiness is claimed.
