#!/usr/bin/env python3
import hashlib, json, os, platform, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path

if len(sys.argv) != 2 or sys.argv[1] not in {"amp", "kimi", "grok"}:
    raise SystemExit("usage: prewarm-selected-agent-6e.py amp|kimi|grok")
agent = sys.argv[1]
repo = Path(__file__).resolve().parents[3]
root = repo / f"experiments/full-refactor-20261024/agents/jackin-state-{agent}"
binary = repo / "experiments/full-refactor-20261024/agents/jackin-target-cli/release/jackin"
capsule = repo / "results/full-refactor-20261024/agents/capsule-build-6e/jackin-capsule-linux-arm64"
role = repo / "experiments/full-replacement-20261024/role/architect-derived"
out = repo / f"results/full-refactor-20261024/agents/architect-{agent}-image-6e"
out.mkdir(parents=True, exist_ok=True)
for d in (root / "home/.jackin", root / "config"):
    d.mkdir(parents=True, exist_ok=True)
    if d.name == "config" and not (d / "config.toml").exists():
        (d / "config.toml").write_text("\n")
env = os.environ.copy()
env.update({
    "JACKIN_HOME_DIR": str(root / "home/.jackin"),
    "JACKIN_CONFIG_DIR": str(root / "config"),
    "JACKIN_CAPSULE_BIN": str(capsule),
    "DOCKER_CONTEXT": "orbstack",
    "NO_COLOR": "1",
})
cmd = [str(binary), "prewarm", "--agent", agent, "--image", "--role", "jfr24/architect", "--role-git", str(role)]
started = datetime.now(timezone.utc).isoformat()
t0 = time.monotonic()
p = subprocess.run(cmd, cwd=repo, env=env, capture_output=True, text=True)
(out / "prewarm.stdout.txt").write_text(p.stdout)
(out / "prewarm.stderr.txt").write_text(p.stderr)
role_commit = subprocess.run(["git", "-C", str(role), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
role_tree = subprocess.run(["git", "-C", str(role), "rev-parse", "HEAD^{tree}"], check=True, capture_output=True, text=True).stdout.strip()
tag = "jk_jfr24_architect:93a46c2"
image = subprocess.run(["docker", "image", "inspect", tag, "--format", "{{.Id}} {{.Os}}/{{.Architecture}} {{.Size}} {{.Config.User}} {{json .Config.Entrypoint}} {{index .Config.Labels \"jackin.image.recipe.hash\"}} {{index .Config.Labels \"jackin.role.git.sha\"}}"], capture_output=True, text=True)
retag = None
if p.returncode == 0 and image.returncode == 0:
    immutable_tag = f"jfr24-architect-{agent}:93a46c2"
    retag = subprocess.run(["docker", "tag", tag, immutable_tag], capture_output=True, text=True)
res = {
    "command": ["<experiment>/jackin", "prewarm", "--agent", agent, "--image", "--role", "jfr24/architect", "--role-git", "<experiment>/architect-derived"],
    "started_utc": started,
    "duration_seconds": round(time.monotonic() - t0, 3),
    "exit_status": p.returncode,
    "source_commit": subprocess.run(["git", "-C", str(repo / "experiments/full-replacement-20261024/role/jackin-source"), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip(),
    "role_commit": role_commit,
    "role_tree": role_tree,
    "jackin_version": subprocess.run([str(binary), "--version"], capture_output=True, text=True).stdout.strip(),
    "capsule_sha256": hashlib.sha256(capsule.read_bytes()).hexdigest(),
    "image_tag": tag if image.returncode == 0 else None,
    "image_identity": image.stdout.strip() if image.returncode == 0 else None,
    "immutable_retag": f"jfr24-architect-{agent}:93a46c2" if retag and retag.returncode == 0 else None,
    "retag_status": retag.returncode if retag else None,
    "expected": f"Pinned Jackin 6e prewarm builds actual pinned Architect role with {agent} selected and Linux ARM64 Capsule artifact before OpenShell sandbox creation; no authentication implied.",
    "host_platform": platform.platform(),
    "stdout_file": "prewarm.stdout.txt",
    "stderr_file": "prewarm.stderr.txt"
}
(out / "prewarm.json").write_text(json.dumps(res, indent=2) + "\n")
print(json.dumps(res, indent=2))
raise SystemExit(p.returncode)
