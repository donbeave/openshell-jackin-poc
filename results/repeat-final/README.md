# Independent Engine B repeat

Date: 2026-10-24 local (UTC timestamps are in each JSON record). OpenShell
gateway: release 0.1.5, isolated gateway `ojp-20261024-gw`; Docker-in-Docker
fixture: `ojp-20261024-engine-b`, endpoint `host.docker.internal:18777`, engine
29.8.2. Test sandbox `ojp-20261024-rpt2` used image
`ojp-20261024-agent:2.1.310-poc-v3`, image digest
`sha256:88b9118075feb284f28b34bb8baa4568aff8ab75c22022441e52a37079049ba4`,
1 CPU / 4 GiB, with only Engine B API and ports 15433, 18085-18089 allowed.
Engine B is an external fixture, not an OpenShell-owned dedicated-engine
companion.

The sandbox had no Docker socket, Docker `config.json`, or registry credentials.
It received Engine B's per-instance TLS client certificate and key. Docker CLI
29.9.2 and Compose 5.6.1 used TLS mutual authentication to Engine B. The
attempt with Engine A's certificate failed (`engine-a-rejected-by-b.json`);
the root run's cross-client test independently established TLS client
certificate rejection by B.
The actual installed agent version command returned Claude Code 2.1.310; no
authenticated agent task was run in this repeat.

## Results

| Requirement | Result | Mechanism | Evidence |
| --- | --- | --- | --- |
| Engine B API and client certificate isolation | PASS | EXTERNAL FIXTURE | `engine-b-api.json`, `engine-a-rejected-by-b.json` |
| Same-path runtime bind mount, both directions | PASS | EXTERNAL FIXTURE | `engine-same-path.json`, `agent-bind-child-read.json`, `child-bind-readback.json`, `child-bind-second-readback.json` |
| Docker build and child execution | PASS | EXTERNAL FIXTURE | `docker-build.json`, `docker-build-ctx.json`, `docker-run.json` |
| Compose build, health dependency, fixed and allocated ports, live source mount | PASS | EXTERNAL FIXTURE | `compose-unique-up.json`, `compose-unique-ps.json`, `compose-logs.json`, `compose-agent-edit.json`, `compose-agent-read-child-write.json`, `compose-fixed-v2.json`, `compose-auto-v2.json` |
| Native Rust `nextest` and Testcontainers application data exchange | PASS | EXTERNAL FIXTURE | `nextest-final-retry.json`; Docker reported `host.docker.internal:18085` |
| Testcontainers cleanup after test panic | PASS | EXTERNAL FIXTURE | `testcontainers-deliberate-failure.json`, `testcontainers-after-failure-resources.json` |
| Testcontainers cleanup after client termination | FAIL | EXTERNAL FIXTURE | `testcontainers-client-termination.json`, `testcontainers-after-termination-resources.json`; exit 124 left Redis container `ca5129897a008d98af96b7a4c1b7c00c2047513d3948916f89de3d8ff619338c` and volume `34da10aa4200094ca6419e461ebbcc9c1b681d0fdcc3dc1a939706f885a4e113` running/present |
| Rebuild native test to same executable path after source change | FAIL | RELEASED | `native-hash-v1.json`, `native-hash-v2.json`, `native-same-path-v2.json`, `native-identity-denial-logs.json`; the hash changed and OpenShell denied execution for binary integrity violation |
| Native Rust external TCP egress after source change | PASS | WORKAROUND | `native-workaround-distinct-path-v2.json`; changed `CARGO_TARGET_DIR` produced a distinct executable path |
| Sandbox stop/start retains project and Docker access | PASS | RELEASED | `stop-rpt2`, `start-rpt2`, `post-start-check.json`; using the configured persistent volume and cert upload, project `Cargo.toml` remained readable and Docker server version remained 29.8.2 |
| OpenShell removes external-daemon children at sandbox delete | FAIL | RELEASED | `engine-b-before-sandbox-delete.txt`, `engine-b-after-sandbox-delete.txt`; Compose app/database/network and terminated-test Redis child remained after sandbox deletion |

The external TCP test exercised an HTTP request to the fixed Engine B service
port 15433. `native-egress-v1-pass.json` records successful native access;
`native-same-path-v2.json` records the changed-binary denial; the separate
target-directory run is explicitly a workaround, not same-path compatibility.
TCP only was tested; UDP remains untested.

Compose auto allocation returned port 18088, within the allowed range. The
Compose database used fixed port 18086. Compose application used fixed ports
15433 and 18087. Compose logs confirmed dependency startup after the database
health check. The source bind mount propagated agent edits into the child and
child writes back to the project.

## Cleanup and ownership

Before deleting the OpenShell sandbox, its own workload container was
`07e57ed7db80c5e3fbde9adbbb662f81111d7279f02603e430a6cd0c9e8fd653` and its
sandbox ID was `89d7ea10-0acc-4b86-b24b-53097a3accd9`. OpenShell deletion
removed that workload (the asynchronous delete was absent from subsequent
`sandbox list`). It did not remove Engine B children: the two Compose services
and the Testcontainers Redis child remained running. `host-after-stop.txt`
also shows the Engine B service still answered on 15433 while the sandbox
workload was stopped. This confirms daemon/resource ownership is external in
this arrangement.

After preserving the before/after ledgers, fixture cleanup used Compose
against only project `ojp-rpt2`, then removed only the captured Testcontainers
container and anonymous volume IDs. `docker ps -a` on Engine B was empty
afterward. Engine B itself and the shared project volume were left intact.

Commands use the repository wrapper, for example:

```sh
sh experiments/os.sh sandbox create --help
sh experiments/os.sh sandbox exec ojp-20261024-rpt2 -- docker version
```

The JSON evidence files preserve the exact command, stdout, stderr, exit
status, and duration where commands were run through `record.py`. Text ledgers
record raw Docker API listings. Private key/certificate values are not
included.

## Scope limits

This repeat does not test authenticated agent task execution, UDP, a native
OpenShell daemon companion, Docker Desktop/Linux/remote/VM/Kubernetes profiles,
or every environment-variable and credential-injection method. The external
fixture path shows Docker, Compose, Rust and Testcontainers connectivity; it
does not provide OpenShell ownership or cleanup of daemon-created resources.
