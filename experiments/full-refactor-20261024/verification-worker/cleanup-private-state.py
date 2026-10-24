from pathlib import Path
import json
import shutil
import subprocess

repo = Path(__file__).resolve().parents[3]
expected = [
    repo / "experiments/full-refactor-20261024/verification-worker/gateway/private",
    repo / "experiments/full-refactor-20261024/verification-worker/gateway/state",
    repo / "experiments/full-refactor-20261024/verification-worker/gateway/config",
    repo / "experiments/full-refactor-20261024/verification-worker/patch-tmpfs/gateway/private",
    repo / "experiments/full-refactor-20261024/verification-worker/patch-tmpfs/gateway/state",
    repo / "experiments/full-refactor-20261024/verification-worker/patch-tmpfs/gateway/config",
]
for port in (28630, 28631):
    listener = subprocess.run(
        ["lsof", "-nP", f"-iTCP:{port}", "-sTCP:LISTEN"],
        text=True, capture_output=True, check=False,
    )
    if listener.stdout.strip():
        raise SystemExit(f"refusing cleanup: TCP {port} still has a listener")

root = repo / "experiments/full-refactor-20261024/verification-worker"
if any(path.parent.parent != root and path.parent.parent.parent != root for path in expected):
    raise SystemExit("refusing cleanup: target path escaped the assigned worker gateway directories")

rows = []
for path in expected:
    if not path.exists():
        rows.append({"path": str(path.relative_to(repo)), "before": "absent", "after": "absent"})
        continue
    size = sum(item.stat().st_size for item in path.rglob("*") if item.is_file())
    rows.append({"path": str(path.relative_to(repo)), "before_bytes": size})
    shutil.rmtree(path)
    if path.exists():
        raise SystemExit(f"cleanup failed for {path}")
    rows[-1]["after"] = "absent"

out = repo / "results/full-refactor-20261024/verification-worker/cleanup/private-state-cleanup.json"
out.write_text(json.dumps({"removed": rows}, indent=2) + "\n")
print(out)
