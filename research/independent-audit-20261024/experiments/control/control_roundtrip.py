#!/usr/bin/env python3
import datetime
import json
import pathlib
import subprocess
import sys

root = pathlib.Path(__file__).resolve().parents[4]
client = root / "research/full-refactor/experiments/control/client.sh"
sandbox = "jrr24-worker-pass4"
tests = {}
identity = subprocess.run([str(client), "sandbox", "get", sandbox, "--output", "json"], capture_output=True, check=True)
identity_json = json.loads(identity.stdout)

def run(key, args, stdin=None):
    command = [str(client), *args]
    result = subprocess.run(command, input=stdin, capture_output=True, check=False)
    tests[key] = {
        "argv": command,
        "exit_status": result.returncode,
        "stdout_utf8": result.stdout.decode("utf-8", errors="replace"),
        "stdout_hex": result.stdout.hex(),
        "stderr_utf8": result.stderr.decode("utf-8", errors="replace"),
        "stderr_hex": result.stderr.hex(),
        "stdin_hex": None if stdin is None else stdin.hex(),
    }

run("separate_stdout_stderr_exit", [
    "sandbox", "exec", sandbox, "--no-tty", "--no-login-shell", "--",
    "python3", "-c",
    "import sys; print('OUT:ready'); print('ERR:diagnostic', file=sys.stderr); raise SystemExit(23)",
])
run("exact_arguments", [
    "sandbox", "exec", sandbox, "--no-tty", "--no-login-shell", "--",
    "python3", "-c",
    "import json,sys; print(json.dumps(sys.argv[1:]))",
    "space value", "semi;colon", "$(printf hacked)", "quote'\"mix", "wild*card",
])
binary = b"prefix\x00middle;$(not-shell)\xffsuffix"
run("binary_stdin", [
    "sandbox", "exec", sandbox, "--no-tty", "--no-login-shell", "--",
    "python3", "-c",
    "import sys; sys.stdout.write(sys.stdin.buffer.read().hex())",
], binary)

result = {
    "recorded_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "tool": "OpenShell Rust CLI 0.1.5",
    "target": {
        "gateway": "jrr24-worker",
        "endpoint": "https://127.0.0.1:18818",
        "sandbox_name": sandbox,
        "immutable_sandbox_id": identity_json["id"],
        "runtime_generation": identity_json["annotations"]["internal.openshell.ai/runtime-generation"],
        "image": "python@sha256:1b668429b3511ab407d8e00648891631b0b1a4d7e15e3ca70f38ab5b91ad4ab4",
    },
    "tests": tests,
}
out = root / "research/full-refactor/evidence/control/exec-roundtrip.json"
out.write_text(json.dumps(result, indent=2) + "\n")
print(out)
