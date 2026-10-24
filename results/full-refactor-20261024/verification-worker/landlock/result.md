# P14: adversarial Landlock equivalence probe

## Result

**FAIL — CONFIGURATION** for the required read-only-root equivalence. The P11 policy denied ordinary creation, directory creation, data writes, truncation, and rename in the first DAC-writable directory tested, but allowed `chmod` on a file owned by UID 1000 in that same directory. The probe stopped immediately after this first successful out-of-grant operation as instructed. The root confinement requirement is not met by this policy.

This run does not change the P10/P11 records, and it does not make the verification worker pass. The separate P12/P13 OOM lifecycle result remains unresolved/FAIL in the parent report.

## Reproduction

Run `experiments/full-refactor-20261024/verification-worker/landlock/build-image.sh`, then `experiments/full-refactor-20261024/verification-worker/landlock/run-adversarial.sh jfrv-20261024-p14` from the repository root. The run script invokes the existing Rust control client through OpenShell mTLS at `https://localhost:28631` (gateway ID `jfr-20261024-vpatch`). It creates one sandbox, reads the effective policy via GetSandbox, runs `/sandbox/checks/adversarial-worker.py`, and confirms deletion. No worker was run directly by Docker.

- Control operation: `verification-adversarial`; create request ID `94cca77d-9223-49fb-bf53-114ed97a62c3`.
- Sandbox name/ID: `jfrv-20261024-p14` / `81c25a40-9eb0-49e1-b52d-ce93a291c1d2`.
- Expected: all changes outside `/tmp` and `/build` denied, while both writable tmpfs paths remain writable.
- Observed: `/home/jackin-test/landlock-probe` allowed chmod of `chmod-canary` (owner UID/GID1000, mode 0666). The call returned success (`errno: null`). Earlier attempts to create, mkdir, write, truncate, and rename returned EACCES (13). No later tests ran.
- Exec exit: 10 (probe's deliberate stop-after-first-boundary-success code). Separate client process exit: 1 (the result is recorded as FAIL). Stderr was empty.
- Cleanup: DeleteSandbox accepted and wait_deleted confirmed absence; gateway log records successful deletion.

## Effective policy and process facts

GetSandbox reported policy version 1, admission state `Accepted`; the gateway separately logged policy status `loaded`, hash `a79c53775fb007bbf636e880aa4b3b90d77e85289a343620097a5504248e4ca8`, `include_workdir=false`, read-only paths `/bin,/usr,/lib,/proc,/dev/urandom,/etc,/var/log,/sandbox`, read-write paths `/tmp,/dev/null,/build`, zero network policies, and workload image `jfr-20261024-verify-worker:patch-adversarial`. The P14 image derives from the exact P11 image and retains linux/arm64 and UID/GID1000.

The worker process reported UID/GID/groups1000, effective and bounding capabilities all zero, NoNewPrivs=1, seccomp mode 2 with six filters, and Landlock kernel ABI 10. The FD audit found no writable regular descriptors above FD2 outside `/tmp` or `/build`. These controls do not prevent the observed chmod on an agent-owned file.

The successful metadata change is sufficient to reject the proposed equivalence for this policy. `/proc/self/root`, symlink aliases, traversal, child-fork, `/dev/shm`, setuid helper, and positive tmpfs tests were deliberately not attempted after the first violation.

## Image and patch context

- P11 base image: `sha256:e461f6a0b7c788b8f33cac5de39341033afdc10cceef5618174f6710148b58db`, linux/arm64, UID/GID1000.
- P14 derived image: `sha256:6c005dccad5abf6cd7c2ce997505b7acc9764cc1824ce41ff5cf1dc68084ac50`, linux/arm64, UID/GID1000.
- The setuid probe helper was compiled statically with Zig 0.17.0 for `aarch64-linux-musl`; source SHA256 `84c300b1d33e19e1c48966f0ddf97ae6ab7beeff8241fbd9d2de357fc8893ffc`, binary SHA256 `ac2221038b6d35b411689b057f623121615befd4dc7e78009db8cda5215c61b4`. The helper was staged but not executed because the first boundary violation stopped the test.
- The test gateway is the bounded OpenShell experimental tmpfs patch based on v0.1.5 `bdb956f2cd65a635f1294fccf1d138d263bf650f`. This patch only fixes Docker tmpfs option serialization; it does not change Landlock enforcement. Therefore this chmod FAIL is not evidence that the tmpfs patch introduced the permission gap.

## Evidence files

- Full Rust client result with policy, process identity, attempted operations, exit code, request ID, and cleanup: `jfrv-20261024-p14.stdout.json`.
- Client stderr and exit status: `jfrv-20261024-p14.stderr.txt`, `jfrv-20261024-p14.exit-status`.
- Relevant gateway policy-load, ExecSandbox, and delete records: `gateway-relevant.log.txt`.
- Image identity, layers, recipe, compiler helper hashes: `image-identity.txt`, `image-provenance.json`, `image-build.log`, `setuid-helper-build.log`, `setuid-helper-hashes.txt`.
- Harness source: `experiments/full-refactor-20261024/verification-worker/fixture/trusted-bundle/adversarial-worker.py`, `experiments/full-refactor-20261024/verification-worker/landlock/Dockerfile-adversarial`, and `experiments/full-refactor-20261024/verification-worker/landlock/run-adversarial.sh`.

## Procedural note

Before this OpenShell run, an ancillary `docker run --rm` was inadvertently used to inspect staged image fixture ownership/modes and setuid-helper metadata. It did not invoke the adversarial worker and exited after printing those metadata; the OpenShell worker run itself used the control API. This direct container inspection was outside the intended Docker-only-for-build/infrastructure rule, is not used as runtime evidence, and will not be repeated.
