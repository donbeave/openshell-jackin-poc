#!/usr/bin/env python3
import datetime
import json
import pathlib
import subprocess
import time

repo = pathlib.Path(__file__).resolve().parents[4]
client = repo / "research/full-refactor/experiments/control/client.sh"
name = "jrr24-worker-pass4"
sandbox = [str(client), "sandbox", "exec", name, "--no-tty", "--no-login-shell", "--"]
remove = subprocess.run(sandbox + ["python3", "-c", "from pathlib import Path; Path('/tmp/jackin-worker-grandchild-marker').unlink(missing_ok=True)"], capture_output=True)
deadline = str(time.time() + 2.0)
command = sandbox + ["python3", "/jackin/checks/wrapper.py", deadline, "/usr/local/bin/python3.12", "/jackin/checks/timeout_child.py"]
start = time.monotonic()
timed = subprocess.run(command, capture_output=True, check=False)
elapsed = time.monotonic() - start
time.sleep(9)
check_cmd = sandbox + ["python3", "-c", "from pathlib import Path; print(Path('/tmp/jackin-worker-grandchild-marker').exists())"]
check = subprocess.run(check_cmd, capture_output=True, check=False)
result = {
    "recorded_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "mechanism": "OpenShell released sandbox exec stream plus Jackin's trusted process-group timeout wrapper semantics",
    "expected": "wrapper returns 124; grandchild marker absent after its 8-second delay",
    "sandbox_name": name,
    "immutable_sandbox_id": "f09bc76d-2120-455a-8544-a045bb9afd91",
    "runtime_generation": "2c9cd0a4-5702-4ede-a6f5-e334c23d4221",
    "timeout_seconds_from_request": 2.0,
    "elapsed_seconds": elapsed,
    "exec_command": command,
    "wrapper_result": {
        "exit_status": timed.returncode,
        "stdout": timed.stdout.decode(errors="replace"),
        "stderr": timed.stderr.decode(errors="replace"),
    },
    "marker_check_command": check_cmd,
    "marker_check": {
        "exit_status": check.returncode,
        "stdout": check.stdout.decode(errors="replace"),
        "stderr": check.stderr.decode(errors="replace"),
    },
    "initial_marker_cleanup_status": remove.returncode,
}
out = repo / "research/full-refactor/evidence/verification/timeout-process-group.json"
out.write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
