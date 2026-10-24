#!/usr/bin/env python3
import json, platform, subprocess, time
from datetime import datetime, timezone
from pathlib import Path

repo=Path('/Users/example/openshell-jackin-public/experiments/full-replacement-20261024/role/jackin-source')
out=Path('/Users/example/openshell-jackin-public/results/full-replacement-20261024/role')
target=Path('/Users/example/openshell-jackin-public/experiments/full-replacement-20261024/role/jackin-target')
out.mkdir(parents=True,exist_ok=True)
cmd=['mise','exec','--','cargo','build','--locked','--release','--target-dir',str(target),'-p','jackin']
start=datetime.now(timezone.utc).isoformat(); t=time.monotonic()
p=subprocess.run(cmd,cwd=repo,capture_output=True,text=True)
(out/'jackin-cli-build.stdout.txt').write_text(p.stdout); (out/'jackin-cli-build.stderr.txt').write_text(p.stderr)
bin_path=target/'release/jackin'
res={'command':cmd,'cwd':str(repo),'source_commit':subprocess.run(['git','rev-parse','HEAD'],cwd=repo,capture_output=True,text=True).stdout.strip(),'started_utc':start,'duration_seconds':round(time.monotonic()-t,3),'exit_status':p.returncode,'platform':platform.platform(),'binary_path':str(bin_path) if bin_path.is_file() else None,'binary_size_bytes':bin_path.stat().st_size if bin_path.is_file() else None,'rustc':subprocess.run(['mise','exec','--','rustc','--version'],cwd=repo,capture_output=True,text=True).stdout.strip(),'cargo':subprocess.run(['mise','exec','--','cargo','--version'],cwd=repo,capture_output=True,text=True).stdout.strip()}
(out/'jackin-cli-build.json').write_text(json.dumps(res,indent=2)+'\n'); print(json.dumps(res,indent=2)); raise SystemExit(p.returncode)
