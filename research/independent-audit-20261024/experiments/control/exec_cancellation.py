#!/usr/bin/env python3
import datetime
import json
import pathlib
import subprocess
import time

repo = pathlib.Path(__file__).resolve().parents[4]
client = repo / "research/full-refactor/experiments/control/client.sh"
name = "jrr24-worker-pass4"
prefix = [str(client), "sandbox", "exec", name, "--no-tty", "--no-login-shell"]
clean_cmd = prefix + ["--", "python3", "-c", "from pathlib import Path; Path('/tmp/jackin-worker-grandchild-marker').unlink(missing_ok=True)"]
clean = subprocess.run(clean_cmd, capture_output=True, check=False)
command = prefix + ["--timeout", "2", "--", "python3", "/jackin/checks/timeout_child.py"]
start = time.monotonic()
run = subprocess.run(command, capture_output=True, check=False)
elapsed = time.monotonic() - start
time.sleep(9)
check_cmd = prefix + ["--", "python3", "-c", "from pathlib import Path; print(Path('/tmp/jackin-worker-grandchild-marker').exists())"]
check = subprocess.run(check_cmd, capture_output=True, check=False)
get = subprocess.run([str(client), "sandbox", "get", name, "--output", "json"], capture_output=True, check=False)
sandbox = json.loads(get.stdout)
record = {
    "recorded_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "mechanism": "released OpenShell CLI remote exec timeout; sandbox exec on live canonical sleep process",
    "expected": "CLI timeout kills remote child group; marker remains absent after 8-second delayed write",
    "sandbox_name": name,
    "immutable_sandbox_id": sandbox["id"],
    "runtime_generation": sandbox["annotations"]["internal.openshell.ai/runtime-generation"],
    "timeout_command": command,
    "elapsed_seconds": elapsed,
    "timeout_result": {"exit_status": run.returncode, "stdout": run.stdout.decode(errors="replace"), "stderr": run.stderr.decode(errors="replace")},
    "marker_check_command": check_cmd,
    "marker_check": {"exit_status": check.returncode, "stdout": check.stdout.decode(errors="replace"), "stderr": check.stderr.decode(errors="replace")},
    "initial_marker_cleanup_status": clean.returncode,
}
out = repo / "research/full-refactor/evidence/control/exec-cancellation.json"
out.write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps(record, indent=2))
