#!/usr/bin/env python3
import datetime
import hashlib
import json
import pathlib
import subprocess

repo = pathlib.Path(__file__).resolve().parents[4]
client = repo / "research/full-refactor/experiments/control/client.sh"
name = "jrr24-worker-pass4"
command = [
    str(client), "sandbox", "exec", name, "--no-tty", "--no-login-shell", "--",
    "python3", "-c", "import sys; sys.stdout.write('x' * 100000)",
]
run = subprocess.run(command, capture_output=True, check=False)
get = subprocess.run([str(client), "sandbox", "get", name, "--output", "json"], capture_output=True, check=True)
identity = json.loads(get.stdout)
record = {
    "recorded_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "command": command,
    "sandbox_name": name,
    "immutable_sandbox_id": identity["id"],
    "runtime_generation": identity["annotations"]["internal.openshell.ai/runtime-generation"],
    "expected": "host client enforces 64 KiB stream cap or records truncation",
    "observed": {
        "exit_status": run.returncode,
        "stdout_bytes": len(run.stdout),
        "stderr_bytes": len(run.stderr),
        "stdout_sha256": hashlib.sha256(run.stdout).hexdigest(),
        "stdout_first_16": run.stdout[:16].decode(),
        "stdout_last_16": run.stdout[-16:].decode(),
        "stderr": run.stderr.decode(errors="replace"),
        "truncation_marker": b"truncated" in run.stdout.lower(),
    },
    "conclusion": "Released CLI streams uncapped output; Jackin-side host wrapper must cap it.",
}
out = repo / "research/full-refactor/evidence/control/output-bound.json"
out.write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps(record, indent=2))
