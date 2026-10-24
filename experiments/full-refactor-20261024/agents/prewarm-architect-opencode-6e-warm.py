#!/usr/bin/env python3
import hashlib, json, os, platform, subprocess, time
from datetime import datetime, timezone
from pathlib import Path

repo = Path(__file__).resolve().parents[3]
root = repo / "experiments/full-refactor-20261024/agents/jackin-state-opencode"
binary = repo / "experiments/full-refactor-20261024/agents/jackin-target-cli/release/jackin"
capsule = repo / "results/full-refactor-20261024/agents/capsule-build-6e/jackin-capsule-linux-arm64"
role = repo / "experiments/full-replacement-20261024/role/architect-derived"
out = repo / "results/full-refactor-20261024/agents/architect-opencode-image-6e-warm"
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
cmd = [str(binary), "prewarm", "--agent", "opencode", "--image", "--role", "jfr24/architect", "--role-git", str(role)]
started = datetime.now(timezone.utc).isoformat()
t0 = time.monotonic()
p = subprocess.run(cmd, cwd=repo, env=env, capture_output=True, text=True)
(out / "prewarm.stdout.txt").write_text(p.stdout)
(out / "prewarm.stderr.txt").write_text(p.stderr)
role_commit = subprocess.run(["git", "-C", str(role), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
role_tree = subprocess.run(["git", "-C", str(role), "rev-parse", "HEAD^{tree}"], check=True, capture_output=True, text=True).stdout.strip()
base = subprocess.run(["docker", "image", "inspect", "jfr-20261024-architect-base:7b72b38", "--format", "{{.Id}} {{.Os}}/{{.Architecture}}"], capture_output=True, text=True)
res = {
    "command": ["<experiment>/jackin", "prewarm", "--agent", "opencode", "--image", "--role", "jfr24/architect", "--role-git", "<experiment>/architect-derived"],
    "started_utc": started,
    "duration_seconds": round(time.monotonic() - t0, 3),
    "exit_status": p.returncode,
    "source_commit": subprocess.run(["git", "-C", str(repo / "experiments/full-replacement-20261024/role/jackin-source"), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip(),
    "role_commit": role_commit,
    "role_tree": role_tree,
    "jackin_version": subprocess.run([str(binary), "--version"], capture_output=True, text=True).stdout.strip(),
    "capsule_sha256": hashlib.sha256(capsule.read_bytes()).hexdigest(),
    "capsule_artifact": "linux/arm64 ELF; macOS Jackin validates embedded identity/version markers, then copies this Linux artifact into linux/arm64 image",
    "docker_context": "orbstack",
    "docker_endpoint_identity": subprocess.run(["docker", "context", "inspect", "orbstack", "--format", "{{.Endpoints.docker.Host}}"], capture_output=True, text=True).stdout.strip().replace(str(Path.home()), "<home>"),
    "base_image_identity": base.stdout.strip(),
    "host_platform": platform.platform(),
    "expected": "Pinned Jackin 6e prewarm builds actual pinned Architect role with OpenCode selected and Linux ARM64 Capsule artifact before OpenShell sandbox creation. No auth implied.",
    "stdout_file": "prewarm.stdout.txt",
    "stderr_file": "prewarm.stderr.txt",
}
(out / "prewarm.json").write_text(json.dumps(res, indent=2) + "\n")
print(json.dumps(res, indent=2))
raise SystemExit(p.returncode)
