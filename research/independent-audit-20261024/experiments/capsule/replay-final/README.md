# Same process reconnect replay

This replay attempted to prove that a fresh command runs in the same canonical shell process after the local OpenShell terminal client disconnects.

## Pinned setup

- OpenShell CLI and gateway: 0.1.5; source commit bdb956f2cd65a635f1294fccf1d138d263bf650f.
- Gateway: jrr24-capsule-reconnect-poc, HTTPS 127.0.0.1:18823, local mTLS with CA verification.
- Docker sandbox namespace: jrr24-capsule-reconnect-poc.
- Image: Alpine ARM64, sha256:2e0b81d60597f449baa56dc25d355367869d2dca4cd57e866f1e2b52af3eb55f.
- No builder, Rust build, or user credentials.

Run GATEWAY_NAME=jrr24-capsule-reconnect-poc GATEWAY_PORT=18823 SANDBOX_LABEL=jrr24-capsule-reconnect-poc ./setup.sh, copy the generated client certificate, key, and CA into the isolated OpenShell XDG gateway mtls/ directory, register with ./client.sh gateway add https://127.0.0.1:18823 --local --name jrr24-capsule-reconnect-poc, then run ./run-gateway.sh and python3 reconnect_replay.py from separate terminals. The scripts do not skip certificate validation.

## Result

**NOT TESTED** for same-process reconnect. The client showed the shell startup notice, prompt, and locally echoed submitted input. It did not show the shell command response or PID marker before timeout. This does not prove that the command reached the canonical process. The run did capture UUID, runtime generation, main-process instance ID, and live supervisor/sandbox image IDs. It made no process signal claim.

Each attempt writes an ownership intent receipt before create, records immutable sandbox identity before delete, deletes only the matching resource, and polls authorized workspace and namespace-scoped Docker inventories. All recorded attempt receipts reached confirmed-empty. The replay does not save a global Docker inventory before create, so it cannot support a causal statement about concurrent foreign-resource changes.

Raw logs, transcripts, identity records, cleanup polls, and errors are in research/full-refactor/evidence/capsule/reconnect-<run-id>/. Generated client keys, gateway registration, and runtime state were removed after the gateway stopped.
