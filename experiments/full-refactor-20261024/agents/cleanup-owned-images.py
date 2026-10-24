"""Remove only listed, ID-verified experiment tags; never prune shared caches."""
import json
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
MANIFEST = REPO / "experiments/full-refactor-20261024/agents/owned-image-cleanup-manifest.json"
OUT = REPO / "results/full-refactor-20261024/agents/owned-image-cleanup"
OUT.mkdir(parents=True, exist_ok=True)
manifest = json.loads(MANIFEST.read_text())
images = manifest["images"]
tags = [i["tag"] for i in images]
if len(set(tags)) != len(tags):
    raise SystemExit("duplicate tags in cleanup manifest")

def call(label, args):
    p = subprocess.run(args, cwd=REPO, capture_output=True, text=True)
    (OUT / f"{label}.stdout.txt").write_text(p.stdout)
    (OUT / f"{label}.stderr.txt").write_text(p.stderr)
    (OUT / f"{label}.exit").write_text(f"{p.returncode}\n")
    return p

before = []
for item in images:
    p = subprocess.run(["docker", "--context", "orbstack", "image", "inspect", item["tag"], "--format", "{{.Id}}"], cwd=REPO, capture_output=True, text=True)
    before.append({"tag": item["tag"], "expected_id": item["id"], "actual_id": p.stdout.strip(), "inspect_exit": p.returncode})
if any(r["inspect_exit"] != 0 or r["actual_id"] != r["expected_id"] for r in before):
    (OUT / "precondition-failure.json").write_text(json.dumps(before, indent=2) + "\n")
    raise SystemExit("tag identity check failed; no image removed")
(OUT / "before-images.json").write_text(json.dumps({"docker_context": "orbstack", "images": before}, indent=2) + "\n")

container_rows = []
for image_id in sorted({i["id"] for i in images}):
    p = subprocess.run(["docker", "--context", "orbstack", "ps", "-a", "--filter", f"ancestor={image_id}", "--format", "{{.ID}} {{.Names}} {{.Status}}"], cwd=REPO, capture_output=True, text=True)
    container_rows.append({"image_id": image_id, "exit": p.returncode, "containers": p.stdout.strip(), "stderr": p.stderr.strip()})
if any(r["exit"] != 0 or r["containers"] for r in container_rows):
    (OUT / "container-dependencies.json").write_text(json.dumps(container_rows, indent=2) + "\n")
    raise SystemExit("a container references a listed image; no image tag removed")
(OUT / "container-dependencies.json").write_text(json.dumps(container_rows, indent=2) + "\n")

removed = call("remove-tags", ["docker", "--context", "orbstack", "image", "rm", *tags])
if removed.returncode:
    raise SystemExit(removed.returncode)

after = []
for item in images:
    p = subprocess.run(["docker", "--context", "orbstack", "image", "inspect", item["tag"], "--format", "{{.Id}}"], cwd=REPO, capture_output=True, text=True)
    after.append({"tag": item["tag"], "expected_old_id": item["id"], "inspect_exit": p.returncode,
                  "remaining_id": p.stdout.strip(), "stderr": p.stderr.strip()})
remaining = [r for r in after if r["inspect_exit"] == 0]
receipt = {
    "docker_context": "orbstack",
    "release_confirmation": manifest["docker_experiment_release"],
    "removed_tag_count": len(tags),
    "removed_tags": tags,
    "preserved_shared_base": manifest["preserved"][0],
    "shared_cache_prune": "not run",
    "after": after,
    "remaining_experiment_tags": remaining,
    "result": "PASS" if not remaining else "FAIL: some listed tags remain",
}
(OUT / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
print(json.dumps(receipt, indent=2))
raise SystemExit(0 if not remaining else 1)
