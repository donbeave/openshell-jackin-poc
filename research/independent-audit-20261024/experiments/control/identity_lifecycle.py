#!/usr/bin/env python3
import datetime
import json
import pathlib
import subprocess
import time

repo = pathlib.Path(__file__).resolve().parents[4]
client = repo / "research/full-refactor/experiments/control/client.sh"
name = "jrr24-idprobe"
image = "python@sha256:1b668429b3511ab407d8e00648891631b0b1a4d7e15e3ca70f38ab5b91ad4ab4"
calls = []

def call(key, args, timeout=30):
    result = subprocess.run([str(client), *args], capture_output=True, timeout=timeout, check=False)
    record = {
        "key": key,
        "argv": [str(client), *args],
        "exit_status": result.returncode,
        "stdout": result.stdout.decode(errors="replace"),
        "stderr": result.stderr.decode(errors="replace"),
    }
    try:
        parsed = json.loads(result.stdout)
        if isinstance(parsed, dict) and "annotations" in parsed:
            safe = {key: parsed.get(key) for key in (
                "id", "name", "phase", "exit_code", "main_process_instance_id",
                "conditions", "workspace", "revision", "resource_version",
            )}
            safe["runtime_generation"] = parsed.get("annotations", {}).get(
                "internal.openshell.ai/runtime-generation"
            )
            record["json"] = safe
            record["stdout"] = json.dumps(safe, indent=2) + "\n"
        else:
            record["json"] = parsed
    except json.JSONDecodeError:
        record["json"] = None
    calls.append(record)
    return record

def get(key):
    return call(key, ["sandbox", "get", name, "--output", "json"])

def wait_absent(key):
    observations = []
    for _ in range(30):
        item = get(key)
        observations.append({
            "exit_status": item["exit_status"],
            "phase": None if item["json"] is None else item["json"].get("phase"),
            "id": None if item["json"] is None else item["json"].get("id"),
            "error": item["stderr"],
        })
        if item["exit_status"] != 0:
            break
        time.sleep(0.5)
    return observations

# A prior failed local recorder attempt may have left this exact owned fixture.
preexisting = get("preexisting_owned_fixture_cleanup_check")
if preexisting["exit_status"] == 0 and preexisting["json"] is not None:
    call("cleanup_preexisting_owned_fixture", ["sandbox", "delete", name])
    wait_absent("wait_preexisting_owned_fixture_cleanup")
missing_before = call("missing_resource_before", ["sandbox", "get", "jrr24-no-such", "--output", "json"])
create1 = call("create_first_generation", [
    "sandbox", "create", "--name", name, "--from", image, "--no-tty", "--detach", "--", "sleep", "infinity",
], timeout=90)
first = get("observe_first_generation")
old_id = first["json"]["id"]
old_gen = first["json"]["runtime_generation"]
delete1 = call("delete_first_generation", ["sandbox", "delete", name])
absent1 = wait_absent("wait_first_generation_deleted")
create2 = call("create_same_name_second_generation", [
    "sandbox", "create", "--name", name, "--from", image, "--no-tty", "--detach", "--", "sleep", "infinity",
], timeout=90)
second = get("observe_second_generation")
new_id = second["json"]["id"]
new_gen = second["json"]["runtime_generation"]
stop_by_name = call("stale_name_stop_after_replacement", ["sandbox", "stop", name])
after_stop = get("observe_state_after_stale_name_stop")
start_again = call("start_second_generation", ["sandbox", "start", name])
after_start = get("observe_second_generation_started")
delete2 = call("delete_second_generation", ["sandbox", "delete", name])
absent2 = wait_absent("wait_second_generation_deleted")
unavailable = call("unavailable_target", [
    "sandbox", "get", "jrr24-no-such", "--output", "json",
    "--gateway-endpoint", "https://127.0.0.1:18819",
], timeout=10)
result = {
    "recorded_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "tool": "OpenShell Rust CLI 0.1.5 with verified TLS and experiment-owned local client certificate",
    "target_scope": {"gateway": "jrr24-worker", "endpoint": "https://127.0.0.1:18818", "workspace": "default"},
    "identity_test": {
        "sandbox_name": name,
        "first": {"id": old_id, "runtime_generation": old_gen},
        "second": {"id": new_id, "runtime_generation": new_gen},
        "replacement_changed_id": old_id != new_id,
        "replacement_changed_generation": old_gen != new_gen,
        "stale_name_stop_targeted_second_generation": after_stop["json"]["phase"] == "Stopped",
        "authority": "gateway-wide mTLS client certificate owner; same isolated POC gateway/workspace",
        "limitation": "Name-based stop has no expected-sandbox-id or expected-generation precondition. Read-then-act is not atomic.",
    },
    "async_delete": {
        "first_delete": delete1,
        "first_get_not_found_observations": absent1,
        "second_delete": delete2,
        "second_get_not_found_observations": absent2,
        "get_reports_not_found": bool(absent1 and absent1[-1]["exit_status"] != 0 and absent2 and absent2[-1]["exit_status"] != 0),
        "resource_cleanup_completion": "NOT TESTED by this script; see UUID-scoped Docker inventory receipt before inferring no compute resources remain",
        "missing_resource_control": missing_before,
    },
    "unavailable_target_control": unavailable,
    "calls": calls,
}
out = repo / "research/full-refactor/evidence/control/identity-lifecycle.json"
out.write_text(json.dumps(result, indent=2) + "\n")
print(out)
print(json.dumps({
    "identity_test": result["identity_test"],
    "get_reports_not_found": result["async_delete"]["get_reports_not_found"],
    "missing_status": missing_before["exit_status"],
    "unavailable_status": unavailable["exit_status"],
}, indent=2))
