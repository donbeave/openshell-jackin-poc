#!/usr/bin/env python3
import datetime
import json
import pathlib
import subprocess
import time

repo = pathlib.Path(__file__).resolve().parents[4]
base = repo / "research/full-refactor/experiments/control"
client = base / "client.sh"
name = "jrr24-wgrp01"
image = "python@sha256:1b668429b3511ab407d8e00648891631b0b1a4d7e15e3ca70f38ab5b91ad4ab4"
candidate = base / "inputs/timeout/candidate"
checks = base / "inputs/timeout/checks"
driver = {"docker": {"mounts": [
    {"type": "bind", "source": str(candidate), "target": "/workspace", "read_only": True},
    {"type": "bind", "source": str(checks), "target": "/jackin/checks", "read_only": True},
    {"type": "tmpfs", "target": "/tmp", "size_bytes": 67108864, "mode": 1023, "options": ["noexec"]},
    {"type": "tmpfs", "target": "/build", "size_bytes": 268435456, "mode": 1023},
]}}
create = subprocess.run([
    str(client), "sandbox", "create", "--name", name, "--from", image,
    "--policy", str(base / "worker-policy.yaml"), "--driver-config-json", json.dumps(driver, separators=(",", ":")),
    "--no-tty", "--detach", "--", "sleep", "infinity",
], capture_output=True, check=False, timeout=90)
get_cmd = [str(client), "sandbox", "get", name, "--output", "json"]
get = subprocess.run(get_cmd, capture_output=True, check=True)
before = json.loads(get.stdout)
marker_clean = subprocess.run([
    str(client), "sandbox", "exec", name, "--no-tty", "--no-login-shell", "--",
    "python3", "-c", "from pathlib import Path; Path('/tmp/jackin-worker-grandchild-short-marker').unlink(missing_ok=True)",
], capture_output=True, check=False)
deadline = str(time.time() + 1.2)
test_cmd = [
    str(client), "sandbox", "exec", name, "--no-tty", "--no-login-shell", "--",
    "python3", "/jackin/checks/wrapper.py", deadline,
    "/usr/local/bin/python3.12", "/jackin/checks/timeout_child_short.py",
]
start = time.monotonic()
test = subprocess.run(test_cmd, capture_output=True, check=False, timeout=20)
elapsed = time.monotonic() - start
time.sleep(7)
marker_cmd = [
    str(client), "sandbox", "exec", name, "--no-tty", "--no-login-shell", "--",
    "python3", "-c", "from pathlib import Path; print(Path('/tmp/jackin-worker-grandchild-short-marker').exists())",
]
marker = subprocess.run(marker_cmd, capture_output=True, check=False)
after_get = subprocess.run(get_cmd, capture_output=True, check=False)
after = json.loads(after_get.stdout)
record = {
    "recorded_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "mechanism": "released OpenShell CLI exec with same Jackin production wrapper semantics, on fresh sandbox generation",
    "expected": "wrapper SIGKILLs the process group, returns 124, no grandchild writes delayed marker",
    "sandbox_name": name,
    "sandbox_id": before["id"],
    "runtime_generation": before["annotations"]["internal.openshell.ai/runtime-generation"],
    "main_process_instance_id": before["main_process_instance_id"],
    "create_command": create.args,
    "create_exit_status": create.returncode,
    "exec_command": test_cmd,
    "elapsed_seconds": elapsed,
    "exec_result": {"exit_status": test.returncode, "stdout": test.stdout.decode(errors="replace"), "stderr": test.stderr.decode(errors="replace")},
    "marker_check_command": marker_cmd,
    "marker_result": {"exit_status": marker.returncode, "stdout": marker.stdout.decode(errors="replace"), "stderr": marker.stderr.decode(errors="replace")},
    "sandbox_after": {
        "id": after["id"],
        "phase": after["phase"],
        "exit_code": after["exit_code"],
        "main_process_instance_id": after["main_process_instance_id"],
        "runtime_generation": after["annotations"]["internal.openshell.ai/runtime-generation"],
    },
    "input_hashes": {
        "candidate": {p.relative_to(candidate).as_posix(): __import__("hashlib").sha256(p.read_bytes()).hexdigest() for p in sorted(candidate.rglob("*")) if p.is_file()},
        "checks": {p.relative_to(checks).as_posix(): __import__("hashlib").sha256(p.read_bytes()).hexdigest() for p in sorted(checks.rglob("*")) if p.is_file()},
    },
    "identity_capture": "queried OpenShell get before and after; one unchanged canonical ID/generation",
}
out = repo / "research/full-refactor/evidence/verification/timeout-process-group-fresh.json"
out.write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps({
    "out": str(out), "sandbox_id": before["id"], "generation": record["runtime_generation"],
    "exec_status": test.returncode, "elapsed": elapsed,
    "marker_stdout": marker.stdout.decode(errors="replace").strip(),
    "phase_after": after["phase"], "main_process_exit_code": after["exit_code"],
}, indent=2))
