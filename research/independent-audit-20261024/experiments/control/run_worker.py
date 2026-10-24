#!/usr/bin/env python3
"""Run one pinned verification-worker trial through the OpenShell CLI."""
import datetime
import hashlib
import json
import pathlib
import subprocess
import sys
import time

repo = pathlib.Path(__file__).resolve().parents[4]
base = repo / "research/full-refactor/experiments/control"
client = base / "client.sh"
image = "python@sha256:1b668429b3511ab407d8e00648891631b0b1a4d7e15e3ca70f38ab5b91ad4ab4"
name, candidate_dir, task, timeout = sys.argv[1], pathlib.Path(sys.argv[2]).resolve(), sys.argv[3], int(sys.argv[4])
checks_dir = candidate_dir.parent / "checks"

def hash_tree(root):
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*")) if path.is_file()
    }

driver = {
    "docker": {
        "mounts": [
            {"type": "bind", "source": str(candidate_dir), "target": "/workspace", "read_only": True},
            {"type": "bind", "source": str(checks_dir), "target": "/jackin/checks", "read_only": True},
            {"type": "tmpfs", "target": "/tmp", "size_bytes": 67108864, "mode": 1023, "options": ["noexec"]},
            {"type": "tmpfs", "target": "/build", "size_bytes": 268435456, "mode": 1023},
        ]
    }
}
deadline = str(time.time() + timeout)
approved = ["/usr/local/bin/python3.12", "/jackin/checks/test_check.py"] if task == "check" else [
    "/usr/local/bin/python3.12", "/jackin/checks/timeout_child.py"
]
policy_path = base / "worker-policy.yaml"
before_hashes = {
    "candidate": hash_tree(candidate_dir),
    "trusted_check_bundle": hash_tree(checks_dir),
    "policy_sha256": hashlib.sha256(policy_path.read_bytes()).hexdigest(),
    "driver_config_sha256": hashlib.sha256(json.dumps(driver, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
}
command = [
    str(client), "sandbox", "create", "--name", name, "--from", image,
    "--cpu", "1", "--memory", "512Mi", "--policy", str(policy_path),
    "--driver-config-json", json.dumps(driver, separators=(",", ":")), "--no-tty", "--",
    "python3", "/jackin/checks/wrapper.py", deadline, *approved,
]
before = subprocess.run(command, capture_output=True, check=False)
get_command = [str(client), "sandbox", "get", name, "--output", "json"]
get = subprocess.run(get_command, capture_output=True, check=False)
try:
    observation = json.loads(get.stdout)
except json.JSONDecodeError:
    observation = None
docker = subprocess.run([
    "docker", "ps", "--all", "--filter", f"label=openshell.ai/sandbox-name={name}",
    "--format", "{{.ID}} {{.Names}} {{.State}}",
], capture_output=True, check=False)
after_hashes = {
    "candidate": hash_tree(candidate_dir),
    "trusted_check_bundle": hash_tree(checks_dir),
    "policy_sha256": hashlib.sha256(policy_path.read_bytes()).hexdigest(),
    "driver_config_sha256": hashlib.sha256(json.dumps(driver, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
}
record = {
    "recorded_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "mechanism": "released OpenShell v0.1.5 Docker sandbox; Jackin CLI wrapper process policy",
    "expected": {
        "approved_argv": approved,
        "result": "exit 0 and worker-policy-pass" if task == "check" and "fail" not in name else "nonzero check result" if task == "check" else "exit 124 from trusted deadline wrapper",
        "policy": {
            "image": image, "cpu": "1", "memory": "512Mi", "pids": 64,
            "network": "no network rules", "candidate_mount": "/workspace:ro",
            "trusted_check_mount": "/jackin/checks:ro", "scratch": {"/tmp": 67108864, "/build": 268435456},
            "identity": "UID:GID 1000:1000",
        },
    },
    "inputs_before": before_hashes,
    "command": command,
    "create_result": {
        "exit_status": before.returncode,
        "stdout": before.stdout.decode(errors="replace"),
        "stderr": before.stderr.decode(errors="replace"),
        "stdout_hex": before.stdout.hex(),
        "stderr_hex": before.stderr.hex(),
    },
    "get_result": {
        "exit_status": get.returncode,
        "stderr": get.stderr.decode(errors="replace"),
        "phase": None if observation is None else observation.get("phase"),
        "exit_code": None if observation is None else observation.get("exit_code"),
        "sandbox_id": None if observation is None else observation.get("id"),
        "runtime_generation": None if observation is None else observation.get("annotations", {}).get("internal.openshell.ai/runtime-generation"),
        "main_process_instance_id": None if observation is None else observation.get("main_process_instance_id"),
        "conditions": None if observation is None else observation.get("conditions"),
    },
    "inputs_after": after_hashes,
    "inputs_unchanged_during_trial": before_hashes == after_hashes,
    "docker_inventory_for_owned_name": docker.stdout.decode(errors="replace").splitlines(),
}
out = repo / f"research/full-refactor/evidence/verification/{name}.json"
out.write_text(json.dumps(record, indent=2) + "\n")
print(out)
print(json.dumps(record["get_result"]))
print(record["create_result"]["stdout"])
print(record["create_result"]["stderr"])
raise SystemExit(0 if before.returncode == 0 else before.returncode)
