# Dedicated Docker engines: host-side fixture evidence

Two disposable Docker-in-Docker engines ran outside OpenShell. They use image
`docker:29.8.2-dind@sha256:1e08cdb63405ca788aea94ef35b792d1e299607c667d33d7bcbcae1fd2611ced`
and Docker Engine `29.8.2` (commit `8af9fe3`). Outer engine: OrbStack Docker
`29.8.2` on macOS 27.0 arm64. Each outer container has a 2 CPU and 4 GiB
limit. No host Docker socket enters either container.

Engine A uses `host.docker.internal:18776`, fixed service port `15432`, and
auto-allocated service port `18080` from range `18080-18084`. Engine B uses
`host.docker.internal:18777`, fixed service port `15433`, and auto-allocated
service port `18088` from range `18085-18089`. The fixture sets each DinD
container's `net.ipv4.ip_local_port_range` and publishes only its assigned
small port range. Docker API is protected by mTLS. Each engine has a distinct
CA and client certificate. No client private key is included in result files.

OpenShell-approved named volumes `ojp-20261024-engine-a-project` and
`ojp-20261024-engine-b-project` have labels
`openshell.ai/sandbox-attachable=true` and
`openshell.ai/sandbox-attachable-workspace=default`. The outer daemon mounts
each at `/sandbox/ojp-project` inside its DinD container. The same absolute
path is used for child-container bind mounts. Engine A and B use separate
volumes. The Rust fixture was copied into both volumes. A child-container
write was visible from the outer DinD container.

## Results

| Probe | Result | Mechanism | Evidence and boundary |
| --- | --- | --- | --- |
| Valid mTLS API connection to A and B | PASS | EXTERNAL FIXTURE | `tls-probes.json`; host client only. |
| Missing client certificate denied | PASS (expected denial) | EXTERNAL FIXTURE | TLS handshake says `tls: certificate required`. |
| A client certificate rejected by B | PASS (expected denial) | EXTERNAL FIXTURE | B reports TLS certificate required; independent CA boundaries. |
| Project-context image build on both engines | PASS | EXTERNAL FIXTURE | `api-probes.json`; actual Rust project supplied as context; small `Child.Dockerfile` copies it. Build times 1.78 s and 1.35 s. Nginx base image was pre-pulled; BuildKit did not report `CACHED` steps. This is not a Rust compile. |
| Redis image for Compose/Testcontainers | PASS | WORKAROUND | `redis-image-seed.json`; `redis:7.4-alpine`, digest `sha256:57e4255cc971b1c8d8f6a8ca283ac01bc3ecdd914273ef6bfaede87aaecd6541` loaded into A, B, and Unix-socket engine by `docker save`/`docker load`. |
| Container run, logs, exec, HTTP fixed port | PASS | EXTERNAL FIXTURE | `api-probes.json`; A `15432`, B `15433`. |
| Docker automatic host port allocation | PASS | EXTERNAL FIXTURE | A `18080`, B `18088`; both within the forwarded ranges and HTTP-tested from host. |
| Child bind mount and named volume operations | PASS | EXTERNAL FIXTURE | Child read `Cargo.toml` hash `ea3f8b22f608e82fb73f6f6c40e29dbec7f01bb03fef1517fb3ac8d011f617c6`; child write visible in source volume. Named volume create/write/inspect pass. |
| Container removal | PASS | EXTERNAL FIXTURE | Temporary control containers removed after probes. |
| Dedicated Unix socket API | PASS | EXTERNAL FIXTURE | `unix-socket-project.json`; Docker API listens on Unix socket only. Approved volume path `/sandbox/docker/docker.sock`; no Docker API port is published. Child-service port `18090` is the only outer TCP mapping. |
| Unix socket access as UID 1000 | PASS after configuration | CONFIGURATION | Socket mode `0660` denied API access; `chmod 0666` allowed UID 1000. Any process with this volume mount receives full Docker-daemon authority. |
| Shared project path on socket daemon | PASS | CONFIGURATION | `unix-socket-project.json`; approved project volume attached at `/sandbox/ojp-project` in DinD and intended same path in the OpenShell sandbox. Directory UID:GID `1000:1000`; UID 1000 wrote a file successfully. |
| Interrupted provisioning cleanup | PASS | EXTERNAL FIXTURE | `interrupted-provision.json`; SIGKILL produced exit 137 and left container plus named and anonymous volumes. Fixture script removed only those resources and verified absence. |
| Child-container local endpoint network | PASS | EXTERNAL FIXTURE | `child-network.json`; both nested engines' children reached experiment-owned Nginx endpoint on host port 15434 without OpenShell policy. This does not prove that Docker children inherit sandbox policy; it demonstrates an independent path requiring separate controls. |
| Resource limits | PASS | EXTERNAL FIXTURE | `resource-limits.json`; outer DinD container caps aggregate daemon and children at 2 CPUs/4 GiB; child-specific 0.5 CPU/128 MiB limit appears in child cgroup. No OpenShell agent container was available for a live comparison. |

The release also terminated an OpenShell sandbox when the project volume was
mounted at `/workspace/ojp-project` (exit status 137). Parent evidence retains
this failure. Moving both project mounts to `/sandbox/ojp-project` is a
**Workaround**. It does not prove that the default workspace mount works.

These results establish external daemon connectivity and API operation only.
They do not establish that a Docker CLI or Testcontainers client inside an
OpenShell sandbox can reach these engines, that OpenShell allows service
connections on these ports, or that sandbox deletion removes daemon resources.
The DinD containers, project volumes, images, and in-daemon resources belong
to the experiment fixture. OpenShell has not removed them. The pre-Testcontainers
inner-resource snapshot is in `inner-resource-ledger.json`: each TCP engine has
its project-context image and named inner volume `ojp-20261024-engine-*-inner-volume`;
Engine A also has the parent-owned `ojp-native-http` endpoint on port `15432`.
Engine B and the Unix engine had no running inner containers at snapshot time.
Inner images, containers,
and volumes live in DinD's anonymous `/var/lib/docker` volume. The fixture
cleanup script removes that data root with its owner DinD container, then
removes only the explicitly named external project and socket volumes.

An early Alpine HTTP control failed because that image lacked `httpd`; the
failure is retained in `api-probes-initial-defect.json`. The corrected probes
use pinned `nginx:1.29.3-alpine`.

## Reproduction

Run from `/Users/example/openshell-jackin-poc`:

```sh
experiments/engines/setup.sh
experiments/engines/seed-image.sh
python3 experiments/engines/seed-redis.py
python3 experiments/engines/probe.py
python3 experiments/engines/api-probes.py
```

`setup.sh` creates two privileged disposable DinD containers, which is needed
for nested container execution. It fails if either named fixture container
already exists. It creates experiment-only private keys under
`experiments/engines/private`; those files stay out of the saved evidence.
`seed-image.sh` transfers pinned Nginx image `nginx:1.29.3-alpine` from the
host image store into each dedicated engine. It avoids the nested registry
error `cannot assign requested address` observed during retest. This image
transfer is a **Workaround** and does not prove registry access from a sandbox.
`unix-socket.sh` creates an extra isolated DinD engine with an approved socket
volume and project volume. It publishes child port `18090` only and narrows
automatic host-port allocation to that single port for the database probe.
The Docker API remains Unix-socket-only.
`cleanup.sh` removes only the named experiment containers and project volumes,
their anonymous DinD data volumes, and generated fixture keys. Run cleanup
only after OpenShell sandbox experiments have ended and exported results.
