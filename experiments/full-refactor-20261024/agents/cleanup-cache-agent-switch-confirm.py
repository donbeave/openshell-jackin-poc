#!/usr/bin/env python3
"""Delete only the two completed sandboxes created by cache confirmation."""
import json
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
CLIENT = REPO / "experiments/full-replacement-20261024/gateway-a/client.sh"
OUT = REPO / "results/full-refactor-20261024/agents/cache-agent-switch-confirm-cleanup"
OUT.mkdir(parents=True, exist_ok=True)
NAMES = ["jfr24-ca-amp", "jfr24-ca-paths"]
EXPECTED_IDS = {
    "jfr24-ca-amp": "a54ef537-1a3d-4009-be1c-77bc4bc2a451",
    "jfr24-ca-paths": "4047104e-7cbc-4c7c-a3c3-88356aaf9d54",
}

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
found = {s["name"]: s for s in payload.get("sandboxes", []) if s.get("name") in NAMES}
if set(found) != set(NAMES):
    raise SystemExit(f"expected exactly our two probe sandboxes to remain; found {sorted(found)}")
for name in NAMES:
    if found[name].get("id") != EXPECTED_IDS[name] or found[name].get("phase") != "Completed":
        raise SystemExit(f"identity/state guard failed for {name}: {found[name].get('id')} {found[name].get('phase')}")

deleted = call("delete", ["sh", str(CLIENT), "sandbox", "delete", *NAMES])
verified = call("after-list", ["sh", str(CLIENT), "sandbox", "list", "--output", "json"])
if verified.returncode:
    raise SystemExit(verified.returncode)
remaining = [s.get("name") for s in json.loads(verified.stdout).get("sandboxes", []) if s.get("name") in NAMES]
receipt = {
    "gateway": "jfr-20261024-a",
    "scope": "only the two completed cache reproduction sandboxes; no images or Docker cache touched",
    "resources": [{"name": n, "id": EXPECTED_IDS[n], "pre_delete_phase": found[n].get("phase")} for n in NAMES],
    "delete_exit": deleted.returncode,
    "remaining_after_delete": remaining,
    "result": "PASS" if deleted.returncode == 0 and not remaining else "FAIL",
}
(OUT / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
print(json.dumps(receipt, indent=2))
raise SystemExit(0 if receipt["result"] == "PASS" else 1)
