#!/usr/bin/env python3
"""Remove only gateway-C sandbox/volume/workspace fixture after identity checks."""
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
OUT = ROOT / "results/full-replacement-20261024/repeat"
CLIENT = ROOT / "experiments/full-replacement-20261024/gateway-c/client.sh"
WORKSPACE = "jfr-ws-repeat24"
EXPECTED = {
    "jfr24volpos": "21acc0ed-20bd-4087-b2c4-951247bd9050",
    "jfr24volro": "224e4791-1267-44f9-ba75-592ebf9b14be",
}
VOLUMES = {
    "jfr24repeat-host-rw": "jfr-ws-repeat24",
    "jfr24repeat-wrong-workspace": "jfr-ws-other24",
}

def run(argv):
    p = subprocess.run([str(x) for x in argv], cwd=ROOT, capture_output=True, text=True)
    return {"argv": [str(x) for x in argv], "status": p.returncode, "stdout": p.stdout, "stderr": p.stderr}

listed = run(["sh", CLIENT, "--workspace", WORKSPACE, "sandbox", "list", "-o", "json"])
if listed["status"]:
    raise SystemExit("sandbox inventory failed; refusing cleanup")
items = json.loads(listed["stdout"])["sandboxes"]
found = {x["name"]: x["id"] for x in items if x.get("name") in EXPECTED}
if found != EXPECTED:
    raise SystemExit(f"sandbox identity mismatch; refusing cleanup: {found!r}")
(OUT / "cleanup-pre-sandbox-inventory.json").write_text(json.dumps(listed, indent=2) + "\n")
actions = []
for name in EXPECTED:
    action = run(["sh", CLIENT, "--workspace", WORKSPACE, "sandbox", "delete", name])
    actions.append(action)
    if action["status"]:
        raise SystemExit(f"OpenShell delete failed for owned fixture {name}; inspect before continuing")
after = run(["sh", CLIENT, "--workspace", WORKSPACE, "sandbox", "list", "-o", "json"])
if after["status"] or any(x.get("id") in EXPECTED.values() for x in json.loads(after["stdout"])["sandboxes"]):
    raise SystemExit("sandbox deletion not confirmed; retaining volume fixtures")
actions.append(after)

for name, workspace in VOLUMES.items():
    inspection = run(["docker", "volume", "inspect", name])
    if inspection["status"]:
        raise SystemExit(f"expected owned volume missing: {name}")
    volume = json.loads(inspection["stdout"])[0]
    labels = volume.get("Labels") or {}
    options = volume.get("Options") or {}
    expected_source = str((OUT / "source").resolve(strict=True))
    if (volume.get("Driver") != "local" or options != {"type": "none", "o": "bind", "device": expected_source}
        or labels.get("openshell.ai/sandbox-attachable") != "true"
        or labels.get("openshell.ai/sandbox-attachable-workspace") != workspace
        or labels.get("jackin.fixture") != "jfr-20261024-repeat"):
        raise SystemExit(f"volume ownership/options mismatch; refusing removal: {name}")
    actions.append(inspection)
    removed = run(["docker", "volume", "rm", name])
    actions.append(removed)
    if removed["status"]:
        raise SystemExit(f"Docker volume removal failed; inspect: {name}")
    if run(["docker", "volume", "inspect", name])["status"] == 0:
        raise SystemExit(f"volume still exists after removal: {name}")

workspace = run(["sh", CLIENT, "workspace", "delete", WORKSPACE])
actions.append(workspace)
if workspace["status"]:
    raise SystemExit("workspace delete failed; inspect result")
(OUT / "cleanup-actions.json").write_text(json.dumps(actions, indent=2) + "\n")
print(json.dumps({"result": "PASS", "removed_sandbox_ids": list(EXPECTED.values()), "removed_volumes": list(VOLUMES), "removed_workspace": WORKSPACE, "note": "OpenShell sandbox mutation is name-based; this script verified immutable sandbox IDs immediately before deletion but cannot make the gateway mutation atomic. Docker local volumes expose name/options/labels, not a separate immutable ID. Exact options and ownership labels were rechecked before removal."}, indent=2))
