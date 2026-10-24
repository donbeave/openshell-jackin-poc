# Independent clean-state basic sandbox rerun

Profile: local macOS arm64 host, OrbStack Docker runtime, OpenShell `v0.1.5`, gateway `ojp-20261024-gw` at `https://127.0.0.1:18770` with gateway mTLS and sandbox launch JWT enabled. Gateway and API checks used only `sh experiments/os.sh`, which pins isolated XDG state and gateway selection. Workspace `default`.

Image: `ojp-20261024-agent:2.1.310`, Linux/arm64, `sha256:e6da050ff5fec47de2c997ec10ea8f52b9a80af20594e5078d5131ec51f611d8`. OpenShell CLI and gateway `0.1.5`; Python SDK `openshell==0.1.5`; Claude Code `2.1.310`; Rust `1.99.1`; Docker client `29.9.2`. The Rust probe needed `RUSTUP_HOME=/usr/local/rustup CARGO_HOME=/usr/local/cargo` because the image's rustup defaults point to root's home. The first image's default Rust invocation failed; retained in `repeat-version-env.json` and the later exec output. The Architect-derived corrected image was not used in this repeat.

## Results

| Capability | Result | Evidence |
|---|---|---|
| Create/list/inspect | PASS | `repeat-create-initial.json`, `repeat-list.json`, `repeat-inspect.json` |
| Real agent version | PASS | `repeat-version-env.json`: `claude --version` reports `2.1.310 (Claude Code)` |
| Rust test compile/run | PASS | `repeat-project-test-correct-path.json`: 1 test passed; same-path second compile hash unchanged in `repeat-native-build-second.json` |
| Exec stdout/stderr and exit status | PASS | `repeat-exit-code.json`: exit 9, separate expected stdout/stderr |
| Required environment and simple startup hook | PASS | `repeat-version-env.json`, `repeat-hook.json` |
| No Docker grant | PASS for attempted endpoint denial | `repeat-denied.json`: Docker CLI exists; no `/var/run/docker.sock`, Docker config, or `DOCKER_HOST`; explicit endpoint fails before API access because `host.docker.internal` cannot resolve under empty network policy |
| SDK create/ready/exec/get/delete/wait-delete | PASS | `sdk-lifecycle.json`, including sandbox ID |
| Stop/start and project file retention | PASS | `repeat-stop-start.json`, `repeat-retained.json` |
| Exported bytes | PASS | SHA-256 `2d0186aa298403c0138bfcb0c009efe43a8255d6d2c610a2a65a2dc61d96222b` for both sandbox and exported `retained.txt` |
| CLI delete and absence check | PASS | `repeat-cli-delete.json`, `repeat-delete-verify.json` |
| `sandbox connect` disconnect escape and reconnect | NOT PASS | Two attempts ran shell commands but did not detach with Ctrl-P/Ctrl-Q; PTY clients were terminated at 20 seconds. See `repeat-connect*.json`. Interactive `sandbox exec --tty` input/resize/interruption passed in the main run, not repeated here. |
| Authenticated coding-agent task | NOT TESTED | No approved agent credentials used; version command does not test authentication. |

This rerun covers basic released sandbox operations only. It does not verify Docker access, Compose, Testcontainers, gateway ownership of external daemon resources, or other platforms.

## Reproduction

The isolated gateway must already be running, and the local image must exist.

```sh
sh experiments/os.sh sandbox create --name ojp-20261024-repeat --from ojp-20261024-agent:2.1.310 --policy experiments/denied.yaml --env OJP_VALUE=harmless-value --cpu 1 --memory 1Gi --no-auto-providers --detach --tty -- sh -c 'printf role-hook-ran > /workspace/ojp-hook.txt; exec bash --noprofile --norc -i'
sh experiments/os.sh sandbox upload ojp-20261024-repeat experiments/rust-project /workspace/ojp-project
sh experiments/os.sh sandbox exec ojp-20261024-repeat --no-login-shell --env RUSTUP_HOME=/usr/local/rustup --env CARGO_HOME=/usr/local/cargo -- sh -ec 'rustc --edition 2024 --test /workspace/ojp-project/rust-project/tests/native_tcp.rs -o /workspace/native_tcp_test; sha256sum /workspace/native_tcp_test; /workspace/native_tcp_test'
sh experiments/os.sh sandbox stop ojp-20261024-repeat
sh experiments/os.sh sandbox start ojp-20261024-repeat
sh experiments/os.sh sandbox download ojp-20261024-repeat /workspace/retained.txt results/repeat/retained.txt
sh experiments/os.sh sandbox delete ojp-20261024-repeat
```

For the SDK probe, run `experiments/sdk-venv/bin/python experiments/repeat/sdk-lifecycle.py`. It creates and deletes separate sandbox `ojp-20261024-sdk`.
