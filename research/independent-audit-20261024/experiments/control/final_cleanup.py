#!/usr/bin/env python3
import datetime
import hashlib
import json
import pathlib
import subprocess
import time

repo = pathlib.Path(__file__).resolve().parents[4]
client = repo / "research/full-refactor/experiments/control/client.sh"
allowed = {
    "jrr24-worker-pass4", "jrr24-wpos01", "jrr24-wpass01",
    "jrr24-wfail02", "jrr24-wpass02", "jrr24-wfail03",
}
def cli(args):
    return subprocess.run([str(client), *args], capture_output=True, check=False)
def list_json():
    run = cli(["sandbox", "list", "--all-workspaces", "--output", "json"])
    if run.returncode != 0:
        raise RuntimeError(run.stderr.decode(errors="replace"))
    return json.loads(run.stdout)
def container_inventory():
    run = subprocess.run(["docker", "ps", "--all", "--format", "{{.ID}} {{.Labels}}"], capture_output=True, check=True)
    entries = []
    for line in run.stdout.decode().splitlines():
        if "openshell.ai/sandbox-namespace=jrr24-worker-poc" in line:
            entries.append(line)
    unrelated = [line for line in run.stdout.decode().splitlines() if "openshell.ai/sandbox-namespace=jrr24-worker-poc" not in line]
    unrelated_digest = hashlib.sha256("\n".join(sorted(unrelated)).encode()).hexdigest()
    return entries, len(unrelated), unrelated_digest

before_owned, before_unrelated_count, before_unrelated_hash = container_inventory()
listed = list_json()["sandboxes"]
owned_records = []
for sandbox in listed:
    name = sandbox.get("name", "")
    if name not in allowed:
        continue
    sid = sandbox["id"]
    delete = cli(["sandbox", "delete", name])
    observations = []
    for _ in range(60):
        get = cli(["sandbox", "get", name, "--output", "json"])
        try:
            value = json.loads(get.stdout)
            observations.append({"phase": value.get("phase"), "id": value.get("id")})
        except json.JSONDecodeError:
            error = get.stderr.decode(errors="replace")
            observations.append({"exit_status": get.returncode, "error": error})
            if get.returncode != 0 and "sandbox not found" in error.lower():
                break
        time.sleep(0.5)
    containers = subprocess.run([
        "docker", "ps", "--all", "--filter", f"label=openshell.ai/sandbox-id={sid}",
        "--format", "{{.ID}} {{.Names}} {{.State}}",
    ], capture_output=True, check=True)
    volumes = subprocess.run([
        "docker", "volume", "ls", "--quiet", "--filter", f"label=openshell.ai/sandbox-id={sid}",
    ], capture_output=True, check=True)
    owned_records.append({
        "name": name,
        "sandbox_id": sid,
        "runtime_generation": sandbox.get("annotations", {}).get("internal.openshell.ai/runtime-generation"),
        "delete_result": {
            "exit_status": delete.returncode,
            "stdout": delete.stdout.decode(errors="replace"),
            "stderr": delete.stderr.decode(errors="replace"),
        },
        "delete_completion_observations": observations,
        "get_not_found": bool(observations and "sandbox not found" in observations[-1].get("error", "").lower()),
        "docker_containers_by_sandbox_uuid_after": containers.stdout.decode(errors="replace").splitlines(),
        "docker_volumes_by_sandbox_uuid_after": volumes.stdout.decode(errors="replace").splitlines(),
    })
after_list = list_json()["sandboxes"]
after_owned, after_unrelated_count, after_unrelated_hash = container_inventory()
record = {
    "recorded_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "scope": {"gateway": "jrr24-worker", "workspace": "default", "compute_driver": "docker", "sandbox_namespace": "jrr24-worker-poc"},
    "only_delete_allowlist": sorted(allowed),
    "owned_sandboxes_before_cleanup": [
        {"name": x.get("name"), "id": x.get("id"), "phase": x.get("phase"),
         "runtime_generation": x.get("annotations", {}).get("internal.openshell.ai/runtime-generation")}
        for x in listed if x.get("name") in allowed
    ],
    "owned_cleanup_results": owned_records,
    "owned_sandboxes_remaining_in_gateway_inventory": [
        {"name": x.get("name"), "id": x.get("id"), "phase": x.get("phase")}
        for x in after_list if x.get("name") in allowed
    ],
    "owned_compute_before": before_owned,
    "owned_compute_after": after_owned,
    "unrelated_engine_inventory_comparison": {
        "before_count": before_unrelated_count, "before_sha256": before_unrelated_hash,
        "after_count": after_unrelated_count, "after_sha256": after_unrelated_hash,
        "same": before_unrelated_count == after_unrelated_count and before_unrelated_hash == after_unrelated_hash,
        "scope": "immediately before/after this cleanup only; no baseline was captured before the earlier POC runs",
    },
}
out = repo / "research/full-refactor/evidence/control/final-cleanup.json"
out.write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps({
    "out": str(out),
    "deleted": len(owned_records),
    "all_get_not_found": all(x["get_not_found"] for x in owned_records),
    "remaining_owned": len(record["owned_sandboxes_remaining_in_gateway_inventory"]),
    "remaining_owned_compute": len(after_owned),
    "unrelated_inventory_same": record["unrelated_engine_inventory_comparison"]["same"],
}, indent=2))
