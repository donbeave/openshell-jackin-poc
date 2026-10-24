#!/usr/bin/env python3
"""Fresh, isolated reproduction of selected-agent image reuse."""
import hashlib
import json
import os
import platform
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
ROOT = REPO / "experiments/full-refactor-20261024/agents/cache-agent-switch-confirm"
OUT = REPO / "results/full-refactor-20261024/agents/cache-agent-switch-confirm"
ROOT.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)
HOME = ROOT / "jackin-home"
CONFIG = ROOT / "jackin-config"
HOME.mkdir(exist_ok=True)
CONFIG.mkdir(exist_ok=True)
(CONFIG / "config.toml").write_text("\n")
binary = REPO / "experiments/full-refactor-20261024/agents/jackin-target-cli/release/jackin"
capsule = REPO / "results/full-refactor-20261024/agents/capsule-build-6e/jackin-capsule-linux-arm64"
role = REPO / "experiments/full-replacement-20261024/role/architect-derived"
client = REPO / "experiments/full-replacement-20261024/gateway-a/client.sh"
mutable = "jk_jfr24_architect:93a46c2"
immutable_grok = "jfr24-architect-grok:93a46c2"

def run(label, argv, *, env=None, cwd=REPO):
    t0 = time.monotonic()
    p = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, text=True)
    (OUT / f"{label}.stdout.txt").write_text(p.stdout)
    (OUT / f"{label}.stderr.txt").write_text(p.stderr)
    (OUT / f"{label}.exit").write_text(f"{p.returncode}\n")
    return {"argv": [str(a) for a in argv], "exit": p.returncode,
            "duration_seconds": round(time.monotonic() - t0, 3),
            "stdout": f"{label}.stdout.txt", "stderr": f"{label}.stderr.txt"}

def image(ref):
    p = subprocess.run(["docker", "image", "inspect", ref, "--format",
        "{{.Id}} {{.Os}}/{{.Architecture}} {{.Size}} {{.Config.User}} {{json .Config.Entrypoint}} {{index .Config.Labels \"jackin.agent\"}} {{index .Config.Labels \"jackin.image.recipe.hash\"}}"],
        capture_output=True, text=True)
    return {"ref": ref, "exit": p.returncode, "identity": p.stdout.strip(), "stderr": p.stderr.strip()}

started = datetime.now(timezone.utc).isoformat()
before_mutable = image(mutable)
before_grok = image(immutable_grok)
(OUT / "before-images.json").write_text(json.dumps({"mutable": before_mutable, "immutable_grok": before_grok}, indent=2) + "\n")
if before_mutable["exit"] != 0 or before_grok["exit"] != 0:
    raise SystemExit("Expected existing mutable and immutable Grok images; stop without mutation")
if before_mutable["identity"].split()[0] != before_grok["identity"].split()[0]:
    raise SystemExit("Mutable tag is not the preserved Grok image; stop without mutation")

env = os.environ.copy()
env.update({"JACKIN_HOME_DIR": str(HOME), "JACKIN_CONFIG_DIR": str(CONFIG),
            "JACKIN_CAPSULE_BIN": str(capsule), "DOCKER_CONTEXT": "orbstack", "NO_COLOR": "1"})
command = [str(binary), "prewarm", "--agent", "amp", "--image", "--role", "jfr24/architect", "--role-git", str(role)]
prewarm = run("amp-prewarm", command, env=env)
after_mutable = image(mutable)
after_grok = image(immutable_grok)
(OUT / "after-images.json").write_text(json.dumps({"mutable": after_mutable, "immutable_grok": after_grok}, indent=2) + "\n")

# Use a separate, no-capability policy to accommodate the source image's GID-0
# USER without changing its layers. The exact original image remains under both
# mutable and immutable refs; no derived image is used for the binary check.
policy = OUT / "run-nonzero-identity-policy.yaml"
policy.write_text("""version: 1
process:
  run_as_user: "1000"
  run_as_group: "1000"
filesystem_policy:
  include_workdir: true
  read_only: [/jackin, /bin, /sbin, /usr, /usr/local, /lib, /lib64, /etc, /proc, /sys, /dev/urandom, /opt]
  read_write: [/workspace, /sandbox, /tmp, /home, /dev/null]
landlock:
  compatibility: best_effort
network_policies: {}
""")
test_image = after_mutable["identity"].split()[0] if after_mutable["exit"] == 0 else mutable
name = "jfr24-cache-confirm-amp"
create = run("openshell-create", ["sh", str(client), "sandbox", "create", "--name", name,
    "--from", test_image, "--policy", str(policy), "--no-tty", "--", "/bin/sh", "-lc",
    "printf 'PATH=%s\\n' \"$PATH\"; printf 'USER=%s UID=%s GID=%s\\n' \"$(id -un)\" \"$(id -u)\" \"$(id -g)\"; command -v amp || true; command -v grok || true; amp --version; printf 'AMP_EXIT=%s\\n' \"$?\"; grok --version; printf 'GROK_EXIT=%s\\n' \"$?\""])

result = {
    "started_utc": started,
    "frozen_versions": {"jackin": "6e266406b49da2ab3c55355f3b7d33d1643ee6cd", "architect": "7b72b38fe1d66e35c0931899c53bf3719592bbcc", "openshell": "bdb956f2cd65a635f1294fccf1d138d263bf650f"},
    "platform": platform.platform(),
    "expected": "Fresh state: selected Amp prewarm should produce an Amp image; if the exact image it reports reused is tested in OpenShell, Amp CLI should exist. Grok is checked as a positive identity control.",
    "mutable_tag_before": before_mutable,
    "preserved_grok_tag_before": before_grok,
    "prewarm": prewarm,
    "mutable_tag_after": after_mutable,
    "preserved_grok_tag_after": after_grok,
    "openshell_image": test_image,
    "sandbox_name": name,
    "sandbox_create_and_command": create,
    "capsule_sha256": hashlib.sha256(capsule.read_bytes()).hexdigest(),
    "source_commit": subprocess.run(["git", "-C", str(REPO / "experiments/full-replacement-20261024/role/jackin-source"), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip(),
    "role_commit": subprocess.run(["git", "-C", str(role), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip(),
    "auth": "NOT TESTED; no approved live credentials used",
}
(OUT / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
raise SystemExit(prewarm["exit"] or create["exit"])
