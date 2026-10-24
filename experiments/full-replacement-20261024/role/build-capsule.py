#!/usr/bin/env python3
import hashlib, json, platform, subprocess, time
from datetime import datetime, timezone
from pathlib import Path

repo = Path('/Users/example/Projects/jackin-project/jackin')
out = Path('/Users/example/openshell-jackin-public/results/full-replacement-20261024/role')
out.mkdir(parents=True, exist_ok=True)
target_dir = Path('/Users/example/openshell-jackin-public/experiments/full-replacement-20261024/role/capsule-build/target')
cmd = ['mise','exec','--','cargo','zigbuild','--locked','--release','--target','aarch64-unknown-linux-gnu','--target-dir',str(target_dir),'-p','jackin-capsule']
start = datetime.now(timezone.utc).isoformat()
t0=time.monotonic()
proc=subprocess.run(cmd,cwd=repo,capture_output=True,text=True)
elapsed=time.monotonic()-t0
(out/'capsule-build.stdout.txt').write_text(proc.stdout)
(out/'capsule-build.stderr.txt').write_text(proc.stderr)
bin_path=target_dir/'aarch64-unknown-linux-gnu/release/jackin-capsule'
identity=None
if bin_path.is_file():
    identity={'path':str(bin_path),'sha256':hashlib.sha256(bin_path.read_bytes()).hexdigest(),'size_bytes':bin_path.stat().st_size}
res={'command':cmd,'cwd':str(repo),'source_commit':subprocess.run(['git','rev-parse','HEAD'],cwd=repo,capture_output=True,text=True).stdout.strip(),'started_utc':start,'duration_seconds':round(elapsed,3),'exit_status':proc.returncode,'rustc':subprocess.run(['mise','exec','--','rustc','--version'],cwd=repo,capture_output=True,text=True).stdout.strip(),'cargo':subprocess.run(['mise','exec','--','cargo','--version'],cwd=repo,capture_output=True,text=True).stdout.strip(),'cargo_zigbuild':subprocess.run(['mise','exec','--','cargo-zigbuild','--version'],cwd=repo,capture_output=True,text=True).stdout.strip(),'platform':platform.platform(),'binary':identity}
(out/'capsule-build.json').write_text(json.dumps(res,indent=2)+'\n')
print(json.dumps(res,indent=2))
raise SystemExit(proc.returncode)
