#!/usr/bin/env python3
import datetime
import json
import pathlib
import subprocess

repo = pathlib.Path(__file__).resolve().parents[4]
client = repo / "research/full-refactor/experiments/control/client.sh"
ids = []
identity_doc = json.loads((repo / "research/full-refactor/evidence/control/identity-lifecycle.json").read_text())
ids.extend(identity_doc["identity_test"][key]["id"] for key in ("first", "second"))
for path in sorted((repo / "research/full-refactor/evidence/verification").glob("*.json")):
    if path.name in ("timeout-process-group.json", "exec-cancellation.json", "output-bound.json"):
        try:
            val = json.loads(path.read_text())
            sid = val.get("sandbox_id") or val.get("immutable_sandbox_id")
            if sid:
                ids.append(sid)
        except json.JSONDecodeError:
            pass
    else:
        try:
            val = json.loads(path.read_text())
            sid = val.get("get_result", {}).get("sandbox_id") or val.get("sandbox_id")
            if sid:
                ids.append(sid)
        except json.JSONDecodeError:
            pass
ids = sorted(set(ids))
list_run = subprocess.run([str(client), "sandbox", "list", "--output", "json", "--all-workspaces"], capture_output=True, check=False)
try:
    list_json = json.loads(list_run.stdout)
except json.JSONDecodeError:
    list_json = {"sandboxes": []}
listed = [{
    "id": x.get("id"),
    "name": x.get("name"),
    "phase": x.get("phase"),
    "runtime_generation": x.get("annotations", {}).get("internal.openshell.ai/runtime-generation"),
} for x in list_json.get("sandboxes", [])]
inventory = []
for sid in ids:
    for resource, cmd in (
        ("containers", ["docker", "ps", "--all", "--filter", f"label=openshell.ai/sandbox-id={sid}", "--format", "{{.ID}} {{.Names}} {{.State}}"]),
        ("volumes", ["docker", "volume", "ls", "--quiet", "--filter", f"label=openshell.ai/sandbox-id={sid}"]),
    ):
        run = subprocess.run(cmd, capture_output=True, check=False)
        inventory.append({
            "sandbox_id": sid,
            "resource_kind": resource,
            "command": cmd,
            "exit_status": run.returncode,
            "owned_resources": run.stdout.decode(errors="replace").splitlines(),
            "stderr": run.stderr.decode(errors="replace"),
        })
record = {
    "recorded_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "scope": {"gateway": "jrr24-worker", "workspace": "default", "driver_namespace": "jrr24-worker-poc"},
    "gateway_list_status": list_run.returncode,
    "gateway_inventory_sanitized": listed,
    "tested_sandbox_ids": ids,
    "uuid_scoped_compute_inventory_after_delete": inventory,
    "conclusion": "Only these experiment-owned UUIDs were queried. Empty host inventory does not authorize deleting retained host project/account data.",
}
out = repo / "research/full-refactor/evidence/control/cleanup-receipt.json"
out.write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps({"output": str(out), "tested_ids": len(ids), "gateway_sandboxes": len(listed), "remaining_owned_resource_entries": sum(bool(x["owned_resources"]) for x in inventory)}, indent=2))
