"""Remove only the verified, unconsumed Capsule-root fixture image tag."""
import json
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
OUT = REPO / "results/full-refactor-20261024/agents/owned-image-cleanup"
OUT.mkdir(parents=True, exist_ok=True)
TAG = "jfr-20261024-capsule-root-6e:fixture"
EXPECTED_ID = "sha256:c8f1f20f48889d8ced6af633778663bdde90a1b659c8ab4ff08d624e0b6f2d88"

def run(label, args):
    p = subprocess.run(args, cwd=REPO, capture_output=True, text=True)
    (OUT / f"capsule-root-{label}.stdout.txt").write_text(p.stdout)
    (OUT / f"capsule-root-{label}.stderr.txt").write_text(p.stderr)
    (OUT / f"capsule-root-{label}.exit").write_text(f"{p.returncode}\n")
    return p

inspect = run("before-inspect", ["docker", "--context", "orbstack", "image", "inspect", TAG,
                                "--format", "{{.RepoTags}} {{.Id}} {{.Os}}/{{.Architecture}} {{.Size}}"])
if inspect.returncode or EXPECTED_ID not in inspect.stdout or inspect.stdout.count(TAG) != 1:
    raise SystemExit("exact tag/image identity check failed; no removal")
consumers = run("before-containers", ["docker", "--context", "orbstack", "ps", "-a", "--filter",
                                     f"ancestor={EXPECTED_ID}", "--format", "{{.ID}} {{.Names}} {{.Status}}"])
if consumers.returncode or consumers.stdout.strip():
    raise SystemExit("consumer exists or cannot be checked; no removal")
remove = run("remove", ["docker", "--context", "orbstack", "image", "rm", TAG])
if remove.returncode:
    raise SystemExit(remove.returncode)
after = run("after-inspect", ["docker", "--context", "orbstack", "image", "inspect", TAG,
                              "--format", "{{.RepoTags}} {{.Id}} {{.Os}}/{{.Architecture}} {{.Size}}"])
receipt = {
    "docker_context": "orbstack",
    "owner": "experiment-owned Capsule root fixture; root explicitly authorized exact-tag cleanup",
    "tag": TAG,
    "expected_image_id": EXPECTED_ID,
    "pre_delete_inspect_exit": inspect.returncode,
    "pre_delete_container_reference_exit": consumers.returncode,
    "pre_delete_container_references": consumers.stdout.strip(),
    "delete_exit": remove.returncode,
    "post_delete_inspect_exit": after.returncode,
    "post_delete_stderr": after.stderr.strip(),
    "force": False,
    "shared_cache_prune": "not run",
    "result": "PASS" if after.returncode != 0 else "FAIL: tag remains",
}
(OUT / "capsule-root-cleanup-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
print(json.dumps(receipt, indent=2))
raise SystemExit(0 if receipt["result"] == "PASS" else 1)
