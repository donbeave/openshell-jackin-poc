#!/usr/bin/env python3
"""Identity-check then delete exactly the resources in owned-sandbox-cleanup-manifest.json."""
import json
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
EXPERIMENT = REPO / "experiments/full-refactor-20261024/agents"
MANIFEST = EXPERIMENT / "owned-sandbox-cleanup-manifest.json"
CLIENT = REPO / "experiments/full-replacement-20261024/gateway-a/client.sh"
OUT = REPO / "results/full-refactor-20261024/agents/owned-sandbox-cleanup"
OUT.mkdir(parents=True, exist_ok=True)
manifest = json.loads(MANIFEST.read_text())
resources = manifest["resources"]
expected = {r["name"]: r["id"] for r in resources}
if len(expected) != len(resources):
    raise SystemExit("manifest contains duplicate resource names")

def call(label, argv):
    p = subprocess.run(argv, cwd=REPO, capture_output=True, text=True)
    (OUT / f"{label}.stdout.txt").write_text(p.stdout)
    (OUT / f"{label}.stderr.txt").write_text(p.stderr)
    (OUT / f"{label}.exit").write_text(f"{p.returncode}\n")
    return p

listed = call("before-list", ["sh", str(CLIENT), "sandbox", "list", "--output", "json"])
if listed.returncode:
    raise SystemExit(listed.returncode)
payload = json.loads(listed.stdout)
found = {s["name"]: s for s in payload.get("sandboxes", []) if s.get("name") in expected}
if set(found) != set(expected):
    raise SystemExit(f"identity guard: expected names {sorted(expected)}, found {sorted(found)}")
for name, expected_id in expected.items():
    actual_id = found[name].get("id")
    if actual_id != expected_id:
        raise SystemExit(f"identity guard: {name} expected {expected_id}, found {actual_id}; no deletion performed")

receipt = {
    "gateway": manifest["gateway"],
    "endpoint": manifest["gateway_endpoint"],
    "authority_assumption": manifest["authority"],
    "pre_delete": [{"name": n, "expected_id": expected[n], "phase": found[n].get("phase"), "exit_code": found[n].get("exit_code")} for n in expected],
    "delete_command_scope": list(expected),
}
(OUT / "manifest-pre-delete.json").write_text(json.dumps(receipt, indent=2) + "\n")

deleted = call("delete", ["sh", str(CLIENT), "sandbox", "delete", *expected.keys()])
if deleted.returncode:
    receipt["delete_exit"] = deleted.returncode
    receipt["result"] = "FAIL"
    (OUT / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    raise SystemExit(deleted.returncode)

verified = call("after-list", ["sh", str(CLIENT), "sandbox", "list", "--output", "json"])
if verified.returncode:
    receipt["delete_exit"] = deleted.returncode
    receipt["after_list_exit"] = verified.returncode
    receipt["result"] = "FAIL: unable to verify absence"
    (OUT / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    raise SystemExit(verified.returncode)
after = json.loads(verified.stdout)
remaining = [{"name": s.get("name"), "id": s.get("id")} for s in after.get("sandboxes", []) if s.get("name") in expected]
receipt["delete_exit"] = deleted.returncode
receipt["after_list_exit"] = verified.returncode
receipt["remaining"] = remaining
receipt["result"] = "PASS" if not remaining else "FAIL: listed resource remains"
(OUT / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
print(json.dumps(receipt, indent=2))
raise SystemExit(0 if not remaining else 1)
