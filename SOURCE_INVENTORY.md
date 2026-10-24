# Runtime source inventory

Selected Jackin: `6e266406b49da2ab3c55355f3b7d33d1643ee6cd`; tree `11c7af3812dd9ba0be27f6ae33fc078fa40ff85c`. Architect: `7b72b38fe1d66e35c0931899c53bf3719592bbcc`. Released OpenShell: v0.1.5 / `bdb956f2cd65a635f1294fccf1d138d263bf650f`. Source provenance and compatibility analysis are under `results/full-refactor-20261024/`.

The source snapshot is a `git archive`, not a Git checkout. Running `git rev-parse` inside it reports the containing research repository and is not source provenance. The snapshot hash checks and pinned archive command establish its identity.

## Independent audits

| Area | Source inventory | Detailed records |
|---|---|---|
| Docker, image building, optional engines, cleanup | [Docker audit](results/full-refactor-20261024/audit-docker.md) | [Call-level inventory](results/full-refactor-20261024/exhaustive-docker-calls.json) |
| Apple Container, VM, storage, resources | [Apple/VM audit](results/full-refactor-20261024/audit-apple-vm.md) | [JSON](results/full-refactor-20261024/audit-apple-vm.json) |
| Capsule, sessions, accounts, credentials, host integration | [Capsule/account audit](results/full-refactor-20261024/audit-capsule-accounts.md) | [JSON](results/full-refactor-20261024/audit-capsule-accounts.json) |
| Workflow workers, CLI, discovery, distributed targets | [Workflow/fleet audit](results/full-refactor-20261024/audit-workflow-fleet.md) | [JSON](results/full-refactor-20261024/audit-workflow-fleet.json) |

The broad search index is `results/full-refactor-20261024/runtime-search-all.txt`. It includes imports, documentation, tests, manifests and executable code; a keyword match alone does not establish an operation. Detailed rows resolve actual actions and distinguish agent sandbox control, builder operations, optional-engine infrastructure, host logic, uncalled foundations, and test/build-only matches. The independent coverage review is [source-coverage-review.md](results/full-refactor-20261024/source-coverage-review.md). Its latest disposition controls the inventory gate; counting rows or validating JSON does not close semantic findings.

## Required decisions

- Replace all agent execution, including the independent workflow verification worker, with OpenShell execution. There is no Docker/Apple agent fallback.
- Retain direct Docker only for justified image construction, an explicitly granted capability, or identified OpenShell infrastructure. Split the old DockerApi consumers by actual behavior rather than wrapping ContainerSpec as a new backend.
- Keep generic command, process ownership, parsing, hashing and host UX utilities where still needed. Move or rename utilities by responsibility; do not delete them solely because their crate has “Docker” in its name.
- Replace the agent-version `docker run` probe with verified installer/build metadata or an OpenShell execution probe.
- Replace Docker-container image-consumer detection with references from authorized OpenShell targets and retained logical instances before pruning images.
- Separate management prerequisites from builder health. A reachable target must remain manageable when the separate image builder is unavailable.
- Treat initial and sibling agent launch separately from enum entries and setup branches. Both currently route through the six-case runtime entrypoint; twelve adapters/setup handlers do not establish twelve working launches.
- Treat uncalled grant readback, live checkpoint capture and normal preservation-hold producers as foundations unless the audited production call graph proves otherwise. Metadata checkpoint recording is different from live byte capture.

All classifications based only on source are marked active but untested, implemented without a production caller, incomplete, or planned. A retained pure product function may use source evidence plus a future release test; changed runtime assumptions require live evidence. No source-only mapping is a runtime PASS.
