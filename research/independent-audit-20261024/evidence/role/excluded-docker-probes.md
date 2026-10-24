# Excluded direct-Docker diagnostics

An earlier diagnostic ran the Architect preflight hook and Claude CLI inside `docker run` containers. The user required replacement runtime evidence through OpenShell and explicitly prohibited retaining a direct `docker run` agent-version probe. These runs are therefore excluded from replacement evidence and must not be counted as PASS results.

Raw logs remain for transparent research history:

- `hook-probe-2.1.310.log`: reduced hook fixture; manually installed only a subset of marketplaces/plugins, then ran preflight. This was direct Docker workload execution.
- `hook-mount-run.log`: direct Docker workload execution against a read-only Architect checkout mount; later tool version command hit unauthenticated GitHub rate limit.
- Build-time `RUN claude --version` is distinct: it ran as part of Docker image construction and supplied verified build output. The `2.1.309` build still reported `2.1.310`, so selected-version identity failed.

`experiments/role/run-hook-probe.sh` is disabled. Do not restore or replay direct Docker workload probes. Parent Capsule POC may use OpenShell with the isolated gateway for any required runtime check.
