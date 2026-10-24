#!/usr/bin/env python3
"""Remove only repeat-control ephemeral gateway credentials and state."""
from pathlib import Path
import json
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[3]
BASE = (ROOT / "experiments/full-replacement-20261024/repeat-control/gateway-rctl").resolve()
OUT = ROOT / "results/full-replacement-20261024/repeat-control"
CLIENT = BASE / "client.sh"
WORKSPACE = "default"
NAMESPACE = "jfr-20261024-rctl"

def run(argv):
    p = subprocess.run([str(x) for x in argv], cwd=ROOT, capture_output=True, text=True)
    return {"argv": [str(x) for x in argv], "exit_status": p.returncode, "stdout": p.stdout, "stderr": p.stderr}

context = json.loads((OUT / "run-context.json").read_text())
inventory = context["commands"]["sandbox-list"]
if inventory["exit_status"]:
    raise SystemExit("saved sandbox inventory failed; refusing to remove gateway state")
items = json.loads(inventory["stdout"])["sandboxes"]
owned = [item for item in items if item.get("name", "").startswith("jfrctl24")]
if owned:
    raise SystemExit(f"owned sandboxes remain; clean them by verified identity first: {owned!r}")
containers = run(["docker", "ps", "-a", "--filter", f"label=openshell.ai/sandbox-namespace={NAMESPACE}", "--format", "{{json .}}"])
if containers["exit_status"] or containers["stdout"].strip():
    raise SystemExit("owned Docker containers remain or inventory failed; refusing credential/state cleanup")
listener = run(["lsof", "-nP", "-iTCP:28600", "-sTCP:LISTEN"])
if listener["exit_status"] == 0:
    raise SystemExit("gateway listener still active; stop only the experiment-owned process first")
if listener["exit_status"] not in (1,):
    raise SystemExit("listener check failed unexpectedly; refusing cleanup")

paths = [BASE / "certs", BASE / "config", BASE / "state", BASE / "gateway.toml", ROOT / "experiments/full-replacement-20261024/repeat-control/private"]
allowed_paths = {BASE / "certs", BASE / "config", BASE / "state", BASE / "gateway.toml", BASE.parent / "private"}
removed = []
already_absent = []
for path in paths:
    if not path.exists():
        already_absent.append(str(path.relative_to(ROOT)))
        continue
    if path.is_symlink() or path.resolve() not in allowed_paths:
        raise SystemExit(f"refusing unexpected path: {path}")
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()
    removed.append(str(path.relative_to(ROOT)))
(OUT / "cleanup.json").write_text(json.dumps({"result":"PASS","mechanism":"CONFIGURATION","inventory_before_cleanup":inventory,"docker_containers_before_cleanup":containers,"listener_check":listener,"removed_exact_paths":removed,"already_absent_paths":already_absent,"retained":["Rust source/build files","gateway reproduction scripts","raw result JSON and logs","pinned image cache"]},indent=2)+"\n")
print(json.dumps({"result":"PASS","removed":removed,"already_absent":already_absent},indent=2))
