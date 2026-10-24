import os
import subprocess

child = subprocess.Popen(["sleep", "30"], start_new_session=True)
def uid_status(pid):
    status = open(f"/proc/{pid}/status", encoding="utf-8").read()
    return next(line for line in status.splitlines() if line.startswith("Uid:"))
print("parent_uid", uid_status("self"))
print("child_uid", uid_status(child.pid))
print("pid_pgid_sid", child.pid, os.getpgid(child.pid), os.getsid(child.pid))
try:
    os.killpg(child.pid, 9)
    child.wait(timeout=2)
    print("killpg_result", "success")
except Exception as error:
    print("killpg_result", type(error).__name__, str(error))
    child.kill()
    child.wait(timeout=2)
