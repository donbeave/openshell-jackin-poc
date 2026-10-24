# Source record

These files are source-inspection evidence, not runtime tests.

- OpenShell selected stable release: v0.1.5, published 2026-10-20, commit bdb956f2cd65a635f1294fccf1d138d263bf650f. The installed CLI and gateway report 0.1.5. `results/release.source` and `results/tag.source` preserve release API responses.
- Architect: 7b72b38fe1d66e35c0931899c53bf3719592bbcc; Jackin: 7d4b8acea25d28fd5286c958e3890148fc2bf40e. Their README snapshots are in `results/architect.source` and `results/jackin.source`.
- OpenShell source snapshots here come from https://github.com/NVIDIA/OpenShell/tree/bdb956f2cd65a635f1294fccf1d138d263bf650f .
- Requested runtime docs: https://docs.nvidia.com/openshell/latest/how-it-works/sandboxes/runtimes ; network rules: https://docs.nvidia.com/openshell/latest/how-it-works/policies/network-rules . Version-specific `.md` fetch returned 404; the pinned repository `.mdx` snapshots were fetched instead. Browser reads of the requested pages also succeeded.
- Docker: https://docs.docker.com/ ; daemon mutual TLS: https://docs.docker.com/engine/security/protect-access/ ; bind mounts: https://docs.docker.com/engine/storage/bind-mounts/ .
- Rust Testcontainers: https://github.com/testcontainers/testcontainers-rs ; runtime configuration: https://rust.testcontainers.org/features/configuration/ .

Architect is the main requirements reference. Its full tool inventory and product plugin logic are outside this small experiment. Jackin product logic, scheduling, account selection UI, worker protocols, and orchestration are outside scope.
