#!/usr/bin/env python3
"""Stop the isolated POC gateway if its exact command is present; remove only its owned files."""
import datetime
import json
import pathlib
import shutil
import subprocess

base = pathlib.Path(__file__).resolve().parent
pid = 4083  # historical PID; process identity is rechecked before any signal
ps_before = subprocess.run(["ps", "-p", str(pid), "-o", "command="], capture_output=True, text=True)
command_before = ps_before.stdout.strip()
matched = bool(command_before and str(base / "gateway.toml") in command_before)
if command_before and not matched:
    raise SystemExit(f"refusing PID {pid}: command does not match owned gateway: {command_before}")
kill_result = None
if matched:
    kill_result = subprocess.run(["kill", "-TERM", str(pid)], capture_output=True, text=True)
    if kill_result.returncode != 0:
        raise SystemExit(f"TERM failed for matched owned gateway PID {pid}: {kill_result.stderr}")
    subprocess.run(["/bin/sleep", "1"], check=True)
ps_after = subprocess.run(["ps", "-p", str(pid), "-o", "command="], capture_output=True, text=True)
command_after = ps_after.stdout.strip()
if command_after and str(base / "gateway.toml") in command_after:
    raise SystemExit(f"owned gateway PID {pid} still present; not removing state")
if command_after:
    raise SystemExit(f"PID {pid} changed to an unrelated command; not removing state: {command_after}")

port_cmd = ["lsof", "-nP", "-iTCP:18818", "-sTCP:LISTEN"]
port_result = subprocess.run(port_cmd, capture_output=True, text=True)

owned = [base / "state", base / "config", base / "certs"]
inventory = []
for path in owned:
    if path.exists():
        inventory.append({"path": str(path), "files": sum(1 for x in path.rglob("*") if x.is_file()),
                          "bytes": sum(x.stat().st_size for x in path.rglob("*") if x.is_file())})
for path in owned:
    if path.exists():
        shutil.rmtree(path)

record = {
    "recorded_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "scope": {"gateway": "jrr24-worker", "endpoint": "127.0.0.1:18818", "namespace": "jrr24-worker-poc"},
    "gateway_process": {
        "pid": pid,
        "ps_before_command": command_before,
        "ps_before_exit_status": ps_before.returncode,
        "command_matched_owned_config": matched,
        "term_requested_by_this_run": bool(kill_result),
        "term_exit_status": kill_result.returncode if kill_result else None,
        "ps_after_command": command_after,
        "ps_after_exit_status": ps_after.returncode,
        "state": "stopped_by_this_run" if matched and not command_after else "already_absent" if not command_before and not command_after else "not_stopped",
    },
    "port_observation": {"command": port_cmd, "exit_status": port_result.returncode,
                          "stdout": port_result.stdout, "stderr": port_result.stderr,
                          "interpretation": "listener present when exit status is 0; no listener when exit status is 1 and stdout is empty"},
    "removed_owned_paths": inventory,
    "remaining_owned_paths": [str(path) for path in owned if path.exists()],
    "foreign_resources": "not inspected or modified by this teardown",
}
out = base.parents[1] / "evidence" / "control" / "gateway-teardown.json"
out.write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps(record, indent=2))
