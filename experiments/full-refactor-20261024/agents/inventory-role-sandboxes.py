#!/usr/bin/env python3
import json, subprocess
from pathlib import Path

repo = Path(__file__).resolve().parents[3]
client = repo / "experiments/full-replacement-20261024/gateway-a/client.sh"
result = subprocess.run(["sh", str(client), "sandbox", "list", "--output", "json"], cwd=repo, capture_output=True, text=True)
if result.returncode:
    raise SystemExit(result.returncode)
payload = json.loads(result.stdout)
names = {"jfr24-openc-01", "jfr24-openc-gid", "jfr24-openc-ro", "jfr24-amp-gid", "jfr24-kimi-gid", "jfr24-grok-gid"}
rows = []
for item in payload.get("sandboxes", []):
    if item.get("name") not in names:
        continue
    annotations = item.get("annotations") or {}
    rows.append({
        "name": item.get("name"),
        "id": item.get("id"),
        "phase": item.get("phase"),
        "created_at": item.get("created_at"),
        "runtime_generation": annotations.get("internal.openshell.ai/runtime-generation"),
        "isolation_backend": annotations.get("internal.openshell.ai/isolation-backend"),
        "auth_epoch": annotations.get("internal.openshell.ai/auth-epoch"),
        "policy_hash": (item.get("configuration_admission") or {}).get("policy_hash"),
        "ready_condition": next((c.get("status") for c in item.get("conditions", []) if c.get("type") == "Ready"), None),
        "ready_reason": next((c.get("reason") for c in item.get("conditions", []) if c.get("type") == "Ready"), None),
        "ready_message": next((c.get("message") for c in item.get("conditions", []) if c.get("type") == "Ready"), None),
    })
out = repo / "results/full-refactor-20261024/agents/role-sandbox-inventory.json"
out.write_text(json.dumps({"gateway": "jfr-20261024-a", "resources": rows}, indent=2) + "\n")
print(json.dumps({"gateway": "jfr-20261024-a", "resources": rows}, indent=2))
