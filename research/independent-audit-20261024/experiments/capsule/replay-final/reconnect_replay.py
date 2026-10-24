#!/usr/bin/env python3
"""Prove same main shell process survives a CLI disconnect/reconnect."""
import json
import os
import pathlib
import pty
import select
import signal
import subprocess
import time
import uuid

BASE = pathlib.Path(__file__).resolve().parent
CLIENT = BASE / "client.sh"
EVIDENCE = BASE / "../../../evidence/capsule"
RUN_ID = uuid.uuid4().hex[:12]
NAME = f"jrr-{RUN_ID}"
OUT = EVIDENCE / f"reconnect-{RUN_ID}"
NAMESPACE = "jrr24-capsule-reconnect-poc"
IMAGE = "alpine@sha256:2e0b81d60597f449baa56dc25d355367869d2dca4cd57e866f1e2b52af3eb55f"
OUT.mkdir(parents=True, exist_ok=False)
RECEIPT = OUT / "ownership-receipt.json"
record = {
    "run_id": RUN_ID,
    "gateway": {"name": "jrr24-capsule-reconnect-poc", "endpoint": "https://127.0.0.1:18823", "version": "0.1.5", "workspace": "default"},
    "namespace": NAMESPACE,
    "image": IMAGE,
    "sandbox": {"name": NAME, "uuid": None, "runtime_generation": None, "main_process_instance_id": None},
    "cleanup": {"delete_exit": None, "polls": [], "status": "pending"},
    "limitations": ["One generic shell fixture only; no real account authorization or Jackin multiplexing claim.", "Delete is name-based and not atomic with the UUID observation; this run uses a high-entropy name and one owner with no concurrent creator."],
}

def save():
    RECEIPT.write_text(json.dumps(record, indent=2) + "\n")

def run(label, args, *, expected=0):
    p = subprocess.run([str(CLIENT), *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (OUT / f"{label}.stdout").write_bytes(p.stdout)
    (OUT / f"{label}.stderr").write_bytes(p.stderr)
    (OUT / f"{label}.exit").write_text(f"{p.returncode}\n")
    if p.returncode != expected:
        raise RuntimeError(f"{label} exit {p.returncode}, expected {expected}")
    return p

def sandbox_json(label, args):
    return json.loads(run(label, args).stdout)

def identity(label):
    obj = sandbox_json(label, ["sandbox", "get", NAME, "--workspace", "default", "-o", "json"])
    if record["sandbox"]["uuid"] and obj.get("id") != record["sandbox"]["uuid"]:
        raise RuntimeError("sandbox UUID changed")
    record["sandbox"].update({
        "uuid": obj.get("id"),
        "runtime_generation": obj.get("annotations", {}).get("internal.openshell.ai/runtime-generation"),
        "main_process_instance_id": obj.get("main_process_instance_id"),
        "phase": obj.get("phase"),
    })
    save()
    return obj

def pty_exchange(label, send_bytes, expect, timeout=10):
    master, slave = pty.openpty()
    proc = subprocess.Popen([str(CLIENT), "sandbox", "connect", NAME], stdin=slave, stdout=slave, stderr=slave, close_fds=True, start_new_session=True)
    os.close(slave)
    captured = bytearray()
    deadline = time.monotonic() + timeout
    sent = False
    started = time.monotonic()
    success = False
    while time.monotonic() < deadline:
        ready, _, _ = select.select([master], [], [], 0.2)
        if ready:
            try:
                part = os.read(master, 4096)
            except OSError:
                break
            if part:
                captured.extend(part)
        # Give connect time to negotiate its PTY before writing a deterministic command.
        if not sent and time.monotonic() - started >= 0.8:
            os.write(master, send_bytes)
            sent = True
        if sent and b"FRESH-RECONNECT-MARKER" in captured:
            success = True
            break
        if sent and not label.endswith("reconnect") and expect in captured:
            success = True
            break
        if proc.poll() is not None and not ready:
            break
    (OUT / f"{label}.transcript").write_bytes(bytes(captured))
    # Terminate only the local client to model a disconnected observer; then prove reconnect.
    if proc.poll() is None:
        os.killpg(proc.pid, signal.SIGTERM)
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=2)
    os.close(master)
    (OUT / f"{label}.client-exit").write_text(f"{proc.returncode}\n")
    if not sent or not success:
        raise RuntimeError(f"{label}: command response marker not observed")
    return bytes(captured)

def namespace_inventory(label):
    listed = sandbox_json(label + "-list", ["sandbox", "list", "--workspace", "default", "-o", "json"])
    p = subprocess.run(["docker", "ps", "-a", "--filter", f"label=openshell.ai/sandbox-namespace={NAMESPACE}", "--format", "{{.ID}} {{.Names}} {{.Labels}}"], capture_output=True)
    (OUT / f"{label}-namespace.stdout").write_bytes(p.stdout)
    (OUT / f"{label}-namespace.stderr").write_bytes(p.stderr)
    (OUT / f"{label}-namespace.exit").write_text(f"{p.returncode}\n")
    if p.returncode:
        raise RuntimeError(f"{label}: scoped Docker namespace inventory failed")
    return listed.get("sandboxes", []), p.stdout.decode(errors="replace").splitlines()

def cleanup():
    errs = []
    observed = None
    try:
        observed = identity("cleanup-get")
    except Exception as e:
        try:
            ss, cs = namespace_inventory("cleanup-pre-delete")
            matching_api = [x for x in ss if x.get("name") == NAME]
            matching_driver = [x for x in cs if NAME in x or (record["sandbox"]["uuid"] and record["sandbox"]["uuid"] in x)]
            if not matching_api and not matching_driver:
                record["sandbox"]["state"] = "absent-confirmed-by-authorized-list-and-scoped-driver-inventory"
                save()
                return []
            errs.append(f"Get failed but resource remains: {e}")
        except Exception as list_e:
            errs.append(f"Get failed and authorized inventory unavailable: {e}; {list_e}")
    if observed:
        expected_id = record["sandbox"]["uuid"]
        if not expected_id or observed.get("id") != expected_id:
            errs.append("identity mismatch; refusing deletion")
        else:
            record["sandbox"]["state"] = "delete-request-pending"
            save()
            p = subprocess.run([str(CLIENT), "sandbox", "delete", NAME, "--workspace", "default"], capture_output=True)
            (OUT / "delete.stdout").write_bytes(p.stdout)
            (OUT / "delete.stderr").write_bytes(p.stderr)
            (OUT / "delete.exit").write_text(f"{p.returncode}\n")
            record["cleanup"]["delete_exit"] = p.returncode
            save()
            if p.returncode:
                errs.append(f"delete failed with {p.returncode}")
            else:
                for i in range(1, 31):
                    try:
                        ss, cs = namespace_inventory(f"cleanup-poll-{i:02d}")
                    except Exception as e:
                        errs.append(f"poll {i}: authorized inventory unavailable: {e}")
                        break
                    owned_api = [x for x in ss if x.get("id") == expected_id or x.get("name") == NAME]
                    owned_driver = [x for x in cs if NAME in x or expected_id in x]
                    foreign = [x for x in cs if x not in owned_driver]
                    record["cleanup"]["polls"].append({"attempt": i, "matching_api": len(owned_api), "matching_driver": len(owned_driver), "foreign_namespace_resources": len(foreign), "api_scope": "gateway + default workspace", "driver_scope": NAMESPACE})
                    save()
                    if foreign:
                        errs.append("unowned namespace resources exist; preserved")
                        break
                    if not owned_api and not owned_driver:
                        record["sandbox"]["state"] = "deleted-and-confirmed"
                        save()
                        return []
                    time.sleep(1)
                else:
                    errs.append("resource still present after 30 authorized and scoped inventory polls")
    return errs

save()
failed = False
try:
    (OUT / "cli-version.txt").write_text(run("cli-version", ["--version"]).stdout.decode())
    run("gateway-info", ["gateway", "info"])
    run("create", ["sandbox", "create", "--workspace", "default", "--name", NAME, "--from", IMAGE, "--detach", "-o", "json", "--", "/bin/sh", "-i"])
    first = identity("identity-before")
    docker = subprocess.run(["docker", "ps", "-aq", "--filter", f"label=openshell.ai/sandbox-id={first.get('id')}"], capture_output=True)
    if docker.returncode == 0:
        ids = docker.stdout.decode().splitlines()
        rows = []
        for container_id in ids:
            inspected = subprocess.run(["docker", "inspect", "--format", "{{.Id}} {{.Config.Image}} {{.Image}} {{.Name}} {{json .Config.Labels}}", container_id], capture_output=True)
            if inspected.returncode:
                docker = inspected
                break
            rows.append(inspected.stdout)
        if docker.returncode == 0:
            docker.stdout = b"".join(rows)
    (OUT / "runtime-containers.stdout").write_bytes(docker.stdout)
    (OUT / "runtime-containers.stderr").write_bytes(docker.stderr)
    (OUT / "runtime-containers.exit").write_text(f"{docker.returncode}\n")
    if docker.returncode:
        raise RuntimeError("could not record runtime container image identities")
    marker = "persistent-" + RUN_ID
    cmd1 = b"echo FIRST-PID=$$; echo SESSION-MARKER=" + marker.encode() + b"; echo READY-BEFORE\r"
    transcript1 = pty_exchange("connect-before", cmd1, b"READY-BEFORE")
    import re
    pids = re.findall(rb"FIRST-PID=(\d+)", transcript1)
    if len(pids) != 1:
        raise RuntimeError(f"expected one shell PID marker, got {pids!r}")
    original_pid = pids[0]
    (OUT / "shell-pid-before.txt").write_bytes(original_pid + b"\n")
    time.sleep(1)
    second = identity("identity-after-disconnect")
    if first.get("id") != second.get("id") or first.get("main_process_instance_id") != second.get("main_process_instance_id"):
        raise RuntimeError("sandbox/main process identity changed across disconnect")
    cmd2 = b"echo FRESH-RECONNECT-MARKER:pid=$$:run=" + RUN_ID.encode() + b"\r"
    transcript2 = pty_exchange("connect-after-reconnect", cmd2, b"READY", timeout=10)
    (OUT / "shell-pid-after.txt").write_bytes(original_pid + b"\n")
    if (b"pid=" + original_pid + b":run=" + RUN_ID.encode()) not in transcript2:
        raise RuntimeError("fresh post-reconnect command did not run in the original shell process")
    (OUT / "interrupt-result.txt").write_text("NOT TESTED: no deterministic process-group signal control in this minimal replay; no signal result inferred.\n")
except Exception as e:
    failed = True
    (OUT / "replay-error.txt").write_text(f"{type(e).__name__}: {e}\n")
finally:
    errs = cleanup()
    record["cleanup"]["status"] = "confirmed-empty" if not errs else "failed; receipt and logs retained"
    if errs:
        (OUT / "cleanup-errors.txt").write_text("\n".join(errs) + "\n")
    save()
raise SystemExit(1 if failed or errs else 0)
