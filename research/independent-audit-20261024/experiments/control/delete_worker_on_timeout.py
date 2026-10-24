#!/usr/bin/env python3
import datetime
import hashlib
import json
import pathlib
import subprocess
import time

repo = pathlib.Path(__file__).resolve().parents[4]
base = repo / "research/full-refactor/experiments/control"
client = base / "client.sh"
name = "jrr24-wtime01"
image = "python@sha256:1b668429b3511ab407d8e00648891631b0b1a4d7e15e3ca70f38ab5b91ad4ab4"
candidate = base / "inputs/timeout/candidate"
checks = base / "inputs/timeout/checks"
policy = base / "worker-policy.yaml"
driver = {"docker": {"mounts": [
    {"type": "bind", "source": str(candidate), "target": "/workspace", "read_only": True},
    {"type": "bind", "source": str(checks), "target": "/jackin/checks", "read_only": True},
    {"type": "tmpfs", "target": "/tmp", "size_bytes": 67108864, "mode": 1023, "options": ["noexec"]},
    {"type": "tmpfs", "target": "/build", "size_bytes": 268435456, "mode": 1023},
]}}
command = [
    str(client), "sandbox", "create", "--name", name, "--from", image, "--cpu", "1", "--memory", "512Mi",
    "--policy", str(policy), "--driver-config-json", json.dumps(driver, separators=(",", ":")),
    "--no-tty", "--", "python3", "/jackin/checks/timeout_child.py",
]
create = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
get_command = [str(client), "sandbox", "get", name, "--output", "json"]
observations = []
deadline = time.monotonic() + 45
live = None
while time.monotonic() < deadline:
    probe = subprocess.run(get_command, capture_output=True, check=False)
    try:
        current = json.loads(probe.stdout)
    except json.JSONDecodeError:
        observations.append({"exit_status": probe.returncode, "stderr": probe.stderr.decode(errors="replace")})
        time.sleep(0.4)
        continue
    observations.append({"phase": current.get("phase"), "id": current.get("id"), "exit_code": current.get("exit_code")})
    if current.get("phase") == "Ready":
        live = current
        break
    if current.get("phase") in ("Error", "Completed", "Stopped"):
        live = current
        break
    time.sleep(0.4)
if live is None or live.get("phase") != "Ready":
    raise SystemExit("worker never reached Ready; inspect partial resource and clean it by exact name")
time.sleep(2)
before_delete = subprocess.run(get_command, capture_output=True, check=True)
before_json = json.loads(before_delete.stdout)
docker_before = subprocess.run([
    "docker", "ps", "--all", "--filter", f"label=openshell.ai/sandbox-id={before_json['id']}",
    "--format", "{{.ID}} {{.Names}} {{.State}}",
], capture_output=True, check=True)
delete = subprocess.run([str(client), "sandbox", "delete", name], capture_output=True, check=False)
post_delete = []
for _ in range(60):
    probe = subprocess.run(get_command, capture_output=True, check=False)
    try:
        value = json.loads(probe.stdout)
        post_delete.append({"phase": value.get("phase"), "id": value.get("id"), "exit_code": value.get("exit_code")})
    except json.JSONDecodeError:
        post_delete.append({"exit_status": probe.returncode, "stderr": probe.stderr.decode(errors="replace")})
        if probe.returncode != 0 and "sandbox not found" in probe.stderr.decode(errors="replace").lower():
            break
    time.sleep(0.5)
docker_after = subprocess.run([
    "docker", "ps", "--all", "--filter", f"label=openshell.ai/sandbox-id={before_json['id']}",
    "--format", "{{.ID}} {{.Names}} {{.State}}",
], capture_output=True, check=True)
try:
    stdout, stderr = create.communicate(timeout=5)
except subprocess.TimeoutExpired:
    create.kill()
    stdout, stderr = create.communicate()
record = {
    "recorded_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "mechanism": "released OpenShell sandbox Delete requested by trusted host after observing live canonical main process; not agent-requested exec cancellation",
    "expected": "live workload/descendants disappear after complete Delete; no worker process remains under sandbox UUID",
    "sandbox_name": name,
    "sandbox_id": before_json["id"],
    "runtime_generation": before_json["annotations"]["internal.openshell.ai/runtime-generation"],
    "main_process_instance_id": before_json["main_process_instance_id"],
    "live_phase_before_delete": before_json["phase"],
    "exit_code_before_delete": before_json["exit_code"],
    "create_command": command,
    "observations_before_timeout_delete": observations,
    "docker_owned_inventory_before": docker_before.stdout.decode(errors="replace"),
    "delete_result": {"exit_status": delete.returncode, "stdout": delete.stdout.decode(errors="replace"), "stderr": delete.stderr.decode(errors="replace")},
    "confirmed_absence_observations": post_delete,
    "docker_owned_inventory_after": docker_after.stdout.decode(errors="replace"),
    "create_attach_result_after_delete": {"exit_status": create.returncode, "stdout": stdout.decode(errors="replace"), "stderr": stderr.decode(errors="replace")},
    "candidate_hashes": {p.relative_to(candidate).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(candidate.rglob("*")) if p.is_file()},
    "check_hashes": {p.relative_to(checks).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(checks.rglob("*")) if p.is_file()},
    "policy_sha256": hashlib.sha256(policy.read_bytes()).hexdigest(),
    "limitations": [
        "OpenShell Delete removed the process boundary, but no process-level exit code was observed for the interrupted task.",
        "A later sandbox get reports not found; do not interpret it as an execution result or as sufficient authority to purge retained host data.",
        "Runtime client timeout and killpg continue to fail independently in exec-cancellation.json and timeout-process-group.json.",
    ],
}
out = repo / "research/full-refactor/evidence/verification/timeout-delete-worker.json"
out.write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps({
    "out": str(out),
    "id": record["sandbox_id"],
    "generation": record["runtime_generation"],
    "phase_before_delete": record["live_phase_before_delete"],
    "exit_code_before_delete": record["exit_code_before_delete"],
    "delete_status": delete.returncode,
    "confirmed_absent": bool(post_delete and "not found" in post_delete[-1].get("stderr", "").lower()),
    "docker_containers_before": docker_before.stdout.decode().splitlines(),
    "docker_containers_after": docker_after.stdout.decode().splitlines(),
    "create_attach_exit_after_delete": create.returncode,
}, indent=2))
