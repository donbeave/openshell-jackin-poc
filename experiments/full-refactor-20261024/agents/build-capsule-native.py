#!/usr/bin/env python3
import hashlib, json, platform, subprocess, time
from datetime import datetime, timezone
from pathlib import Path

repo = Path(__file__).resolve().parents[3]
source = repo / 'experiments/full-replacement-20261024/role/jackin-source'
out = repo / 'results/full-refactor-20261024/agents/capsule-build-6e'
target = repo / 'experiments/full-refactor-20261024/agents/jackin-target-native'
out.mkdir(parents=True, exist_ok=True)
command = ['mise', 'exec', '--', 'cargo', 'build', '--locked', '--release', '--target-dir', str(target), '-p', 'jackin-capsule', '--bin', 'jackin-capsule']
started = datetime.now(timezone.utc).isoformat()
t0 = time.monotonic()
proc = subprocess.run(command, cwd=source, capture_output=True, text=True)
(out / 'native-build.stdout.txt').write_text(proc.stdout)
(out / 'native-build.stderr.txt').write_text(proc.stderr)
binary = target / 'release/jackin-capsule'
commit = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=source, capture_output=True, text=True, check=True).stdout.strip()
tree = subprocess.run(['git', 'rev-parse', 'HEAD^{tree}'], cwd=source, capture_output=True, text=True, check=True).stdout.strip()
rustc = subprocess.run(['mise', 'exec', '--', 'rustc', '--version'], cwd=source, capture_output=True, text=True).stdout.strip()
cargo = subprocess.run(['mise', 'exec', '--', 'cargo', '--version'], cwd=source, capture_output=True, text=True).stdout.strip()
res = {'command': command, 'cwd': '<pinned-jackin-source>', 'source_commit': commit, 'source_tree': tree, 'started_utc': started, 'duration_seconds': round(time.monotonic()-t0, 3), 'exit_status': proc.returncode, 'host_platform': platform.platform(), 'rustc': rustc, 'cargo': cargo, 'binary_path': '<experiment>/jackin-target-native/release/jackin-capsule' if binary.is_file() else None, 'binary_size_bytes': binary.stat().st_size if binary.is_file() else None, 'binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest() if binary.is_file() else None}
(out / 'native-build.json').write_text(json.dumps(res, indent=2) + '\n')
print(json.dumps(res, indent=2))
raise SystemExit(proc.returncode)
