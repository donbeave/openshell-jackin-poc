#!/usr/bin/env python3
"""Remove only the original follow-up gateway-A fixture after its sandboxes are gone.

Default is dry run. This is a one-fixture cleanup procedure, not a resource manager.
The recorded process and sole-authority fixture assumption are required. It must
not be adapted into a name-based production teardown operation.
"""
import argparse
import json
import os
from pathlib import Path
import shlex
import signal
import subprocess
import time

parser = argparse.ArgumentParser()
parser.add_argument('--apply', action='store_true')
parser.add_argument('--resume', action='store_true')
args = parser.parse_args()
root = Path(__file__).resolve().parents[2]
gateway = root / 'experiments/full-replacement-20261024/gateway-a'
results = root / 'results/full-refactor-20261024'
manifest_path = root / 'results/full-replacement-20261024/gateway-a-manifest.json'
receipt_path = results / 'root-gateway-a-cleanup.json'
manifest = json.loads(manifest_path.read_text())
assert manifest['test_id'] == 'jfr-20261024-a'
assert manifest['endpoint'] == 'https://localhost:28470'
pid = int(next(line[1:] for line in manifest['process_query']['stdout'].splitlines()
               if line.startswith('p')))
private_dirs = [gateway / part for part in ('certs', 'config', 'state')]
if receipt_path.exists() and json.loads(receipt_path.read_text()).get('complete'):
    assert not any(path.exists() for path in private_dirs), 'fixture was recreated; new manifest required'
    print(json.dumps({'already_clean': True, 'action': 'none'}))
    raise SystemExit(0)

commands = []
def run(argv):
    p = subprocess.run(argv, capture_output=True, text=True, timeout=30)
    commands.append({'command': argv, 'exit_status': p.returncode,
                     'stdout': p.stdout, 'stderr': p.stderr})
    return p

if args.resume:
    assert args.apply, '--resume requires --apply'
    prior = json.loads(receipt_path.read_text())
    assert prior['test_id'] == manifest['test_id'] and prior['pid'] == pid
    old_list = prior['commands'][0]
    assert old_list['exit_status'] == 0
    old_inventory = json.loads(old_list['stdout'])
    assert old_inventory.get('sandboxes') == [] and not old_inventory.get('next_page_token')
    stopped = run(['lsof', '-nP', '-iTCP:28470', '-sTCP:LISTEN', '-Fp'])
    assert stopped.returncode != 0, 'gateway listening; do not resume private cleanup'
    process = run(['ps', '-p', str(pid), '-o', 'command='])
    assert process.returncode != 0, 'recorded PID exists; inspect rather than guessing'
else:
    listed = run(['sh', str(gateway / 'client.sh'), 'sandbox', 'list', '-o', 'json'])
    assert listed.returncode == 0, 'could not authenticate/inventory fixture'
    inventory = json.loads(listed.stdout)
    assert inventory.get('sandboxes') == [], 'sandbox resources remain'
    assert not inventory.get('next_page_token'), 'inventory is incomplete'
    process = run(['ps', '-p', str(pid), '-o', 'command='])
    assert process.returncode == 0, 'recorded process unavailable; inspect rather than guessing'
    argv = shlex.split(process.stdout.strip())
    assert Path(argv[0]).name == 'openshell-gateway', 'process executable mismatch'
    assert '--config' in argv and argv[argv.index('--config') + 1] == str(gateway / 'gateway.toml')
    assert '--port' in argv and argv[argv.index('--port') + 1] == '28470'
    listener = run(['lsof', '-nP', '-iTCP:28470', '-sTCP:LISTEN', '-Fp'])
    assert listener.returncode == 0
    listener_pids = {line for line in listener.stdout.splitlines() if line.startswith('p') and line[1:].isdigit()}
    assert listener_pids == {f'p{pid}'}, 'listener identity mismatch'
for directory in private_dirs:
    assert not directory.is_symlink(), 'private directory replaced by symlink'
receipt = {'test_id': manifest['test_id'], 'pid': pid, 'endpoint': manifest['endpoint'],
           'commands': commands, 'dry_run': not args.apply, 'complete': False,
           'assumption': 'sole-authority disposable fixture; no concurrent recreation',
           'removed_private_paths': [], 'resumed': args.resume}
receipt_path.write_text(json.dumps(receipt, indent=2) + '\n')
if args.apply:
    if not args.resume:
        os.kill(pid, signal.SIGTERM)
    for _ in range(100):
        check = subprocess.run(['lsof', '-nP', '-iTCP:28470', '-sTCP:LISTEN', '-Fp'],
                               capture_output=True, text=True)
        if check.returncode != 0:
            break
        time.sleep(0.05)
    else:
        raise RuntimeError('gateway still listening; private state retained')
    receipt['phase'] = 'gateway_stopped'
    receipt_path.write_text(json.dumps(receipt, indent=2) + '\n')
    for directory in private_dirs:
        if not directory.exists():
            continue
        for current, dirs, files in os.walk(directory, topdown=False, followlinks=False):
            for name in files:
                path = Path(current) / name
                path.unlink()
                receipt['removed_private_paths'].append(str(path.relative_to(root)))
                receipt_path.write_text(json.dumps(receipt, indent=2) + '\n')
            for name in dirs:
                path = Path(current) / name
                if path.is_symlink():
                    path.unlink()
            Path(current).rmdir()
    receipt['complete'] = True
receipt_path.write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps({'dry_run': not args.apply, 'complete': receipt['complete'],
                  'removed_private_file_count': len(receipt['removed_private_paths'])}))
