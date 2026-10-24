#!/usr/bin/env python3
import datetime
import json
import pathlib
import subprocess

repo = pathlib.Path(__file__).resolve().parents[4]
client = repo / "research/full-refactor/experiments/control/client.sh"
name = "jrr24-wgrp01"
get = subprocess.run([str(client), "sandbox", "get", name, "--output", "json"], capture_output=True, check=True)
identity = json.loads(get.stdout)
code = """import os,subprocess
p=subprocess.Popen(["sleep","30"],start_new_session=True)
print("child_pid",p.pid,"pgid",os.getpgid(p.pid),"sid",os.getsid(p.pid))
try:
 os.killpg(p.pid,9)
 p.wait(timeout=2)
 print("process_group_signal","success")
except Exception as error:
 print("process_group_signal",type(error).__name__,str(error))
 p.kill()
 p.wait(timeout=2)
q=subprocess.Popen(["sleep","30"],start_new_session=True)
try:
 os.kill(q.pid,9)
 q.wait(timeout=2)
 print("single_pid_signal","success")
except Exception as error:
 print("single_pid_signal",type(error).__name__,str(error))
 q.kill()
 q.wait(timeout=2)
"""
command = [str(client), "sandbox", "exec", name, "--timeout", "10", "--no-tty", "--no-login-shell", "--", "python3", "-c", code]
run = subprocess.run(command, capture_output=True, check=False, timeout=15)
result = {
    "recorded_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "mechanism": "OpenShell v0.1.5 Docker sandbox with process UID/GID 1000 and Jackin verification policy",
    "target": {
        "gateway": "jrr24-worker", "workspace": "default", "sandbox_name": name,
        "sandbox_id": identity["id"],
        "runtime_generation": identity["annotations"]["internal.openshell.ai/runtime-generation"],
        "main_process_instance_id": identity["main_process_instance_id"],
    },
    "command": command,
    "result": {
        "exit_status": run.returncode,
        "stdout": run.stdout.decode(errors="replace"),
        "stderr": run.stderr.decode(errors="replace"),
    },
    "interpretation": "same-UID direct PID signal is a positive control; process-group SIGKILL is denied, so Jackin's worker timeout wrapper cannot terminate the child group.",
}
out = repo / "research/full-refactor/evidence/verification/pgid-fresh.json"
out.write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({"out":str(out),"target":result["target"],"result":result["result"]},indent=2))
