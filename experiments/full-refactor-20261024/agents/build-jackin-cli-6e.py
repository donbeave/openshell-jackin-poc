#!/usr/bin/env python3
import hashlib, json, platform, subprocess, time
from datetime import datetime, timezone
from pathlib import Path
repo = Path(__file__).resolve().parents[3]
source = repo / 'experiments/full-replacement-20261024/role/jackin-source'
out = repo / 'results/full-refactor-20261024/agents/jackin-cli-6e'
target = repo / 'experiments/full-refactor-20261024/agents/jackin-target-cli'
out.mkdir(parents=True, exist_ok=True)
cmd = ['mise','exec','--','cargo','build','--locked','--release','--target-dir',str(target),'-p','jackin']
started=datetime.now(timezone.utc).isoformat(); t=time.monotonic()
p=subprocess.run(cmd,cwd=source,capture_output=True,text=True)
(out/'build.stdout.txt').write_text(p.stdout); (out/'build.stderr.txt').write_text(p.stderr)
binary=target/'release/jackin'
commit=subprocess.run(['git','rev-parse','HEAD'],cwd=source,capture_output=True,text=True,check=True).stdout.strip()
tree=subprocess.run(['git','rev-parse','HEAD^{tree}'],cwd=source,capture_output=True,text=True,check=True).stdout.strip()
rustc=subprocess.run(['mise','exec','--','rustc','--version'],cwd=source,capture_output=True,text=True).stdout.strip()
cargo=subprocess.run(['mise','exec','--','cargo','--version'],cwd=source,capture_output=True,text=True).stdout.strip()
version=subprocess.run([str(binary),'--version'],capture_output=True,text=True) if binary.is_file() else None
res={'command':['mise','exec','--','cargo','build','--locked','--release','--target-dir','<experiment>/jackin-target-cli','-p','jackin'],'cwd':'<pinned-jackin-source>','source_commit':commit,'source_tree':tree,'started_utc':started,'duration_seconds':round(time.monotonic()-t,3),'exit_status':p.returncode,'host_platform':platform.platform(),'rustc':rustc,'cargo':cargo,'binary_path':'<experiment>/jackin-target-cli/release/jackin' if binary.is_file() else None,'binary_size_bytes':binary.stat().st_size if binary.is_file() else None,'binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest() if binary.is_file() else None,'version_status':version.returncode if version else None,'version_stdout':version.stdout.strip() if version else None,'version_stderr':version.stderr.strip() if version else None}
(out/'build.json').write_text(json.dumps(res,indent=2)+'\n'); print(json.dumps(res,indent=2)); raise SystemExit(p.returncode)
