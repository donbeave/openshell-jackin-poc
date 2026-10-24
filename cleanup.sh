#!/bin/sh
# Remove only resources created by this proof-of-concept run.
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
python3 - <<'PY'
import json, os, pathlib, shutil, signal, subprocess, time

root = pathlib.Path.cwd()
prefix = 'ojp-20261024'
events = []
volumes = set()
sandbox_ids = set()
free_before = shutil.disk_usage(root).free

def run(args, timeout=60):
    start = time.monotonic()
    try:
        p = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        row = dict(command=args, exit_status=p.returncode, stdout=p.stdout,
                   stderr=p.stderr, seconds=time.monotonic()-start)
    except (OSError, subprocess.TimeoutExpired) as e:
        row = dict(command=args, exit_status=124, error=str(e))
    events.append(row)
    return row

def owned(name):
    return name.startswith(prefix+'-') or name.startswith('openshell-default--'+prefix+'-')

before = run(['docker', 'ps', '-a', '--format', '{{.Names}}'])
names = [n for n in before.get('stdout','').splitlines() if owned(n)]
for name in names:
    labels = run(['docker','inspect','--format','{{json .Config.Labels}}',name])
    if labels['exit_status'] == 0:
        sandbox_id = (json.loads(labels['stdout']) or {}).get('openshell.ai/sandbox-id')
        if sandbox_id: sandbox_ids.add(sandbox_id)
    mounts = run(['docker','inspect','--format','{{json .Mounts}}',name])
    if mounts['exit_status'] == 0:
        for mount in json.loads(mounts['stdout']):
            if mount.get('Type') == 'volume': volumes.add(mount['Name'])
for fixture in ['engine-a','engine-b','sock']:
    name = prefix+'-'+fixture
    if name in names:
        run(['docker','exec',name,'sh','-c',
             'docker ps -a --format "{{.ID}} {{.Names}} {{.Status}}"; docker volume ls --format "{{.Name}}"; docker images --format "{{.ID}} {{.Repository}}:{{.Tag}}"'])

# Old-namespace resources were preserved during diagnosis. Their recorded mounts
# are included only after checking that no remaining container uses the volume.
old = root/'results/disk-audit/orphan-pre-removal.json'
if old.exists():
    for container in json.loads(old.read_text()).get('containers',[]):
        if owned(container.get('name','')):
            if container.get('sandbox_id'): sandbox_ids.add(container['sandbox_id'])
            for mount in container.get('mounts',[]):
                if mount.get('type') == 'volume' and mount.get('name'):
                    volumes.add(mount['name'])

listing = run(['sh','experiments/os.sh','sandbox','list','-o','json'])
if listing['exit_status'] == 0:
    sandboxes = json.loads(listing['stdout']).get('sandboxes',[])
    for sandbox in sandboxes:
        if sandbox['name'].startswith(prefix+'-'):
            run(['sh','experiments/os.sh','sandbox','delete',sandbox['name']])
    for _ in range(20):
        state = run(['sh','experiments/os.sh','sandbox','list','-o','json'])
        if state['exit_status'] != 0: break
        left = [s for s in json.loads(state['stdout']).get('sandboxes',[])
                if s['name'].startswith(prefix+'-')]
        if not left: break
        time.sleep(1)

if (root/'experiments/gateway-vm/cleanup.sh').exists():
    run(['sh','experiments/gateway-vm/cleanup.sh'])

remaining = run(['docker','ps','-a','--format','{{.Names}}'])
for name in remaining.get('stdout','').splitlines():
    if owned(name): run(['docker','rm','-fv',name])

run(['sh','experiments/engines/cleanup.sh'])
for name in run(['docker','volume','ls','--format','{{.Name}}']).get('stdout','').splitlines():
    if name.startswith(prefix+'-'): volumes.add(name)
    elif name.startswith(('openshell-supervisor-','openshell-channel-')):
        probe = subprocess.run(['docker','volume','inspect','--format','{{json .Labels}}',name],
                               capture_output=True,text=True)
        labels = json.loads(probe.stdout) or {} if probe.returncode == 0 else {}
        if (labels.get('openshell.ai/sandbox-id') in sandbox_ids
                and labels.get('openshell.ai/sandbox-namespace') in ['default',prefix]
                and labels.get('openshell.ai/managed-by') == 'openshell'
                and labels.get('openshell.ai/isolation-backend') == 'openshell-sandbox'):
            volumes.add(name)
            events.append(dict(operation='identified owned internal volume',name=name,labels=labels))
for volume in sorted(volumes):
    exists = run(['docker','volume','inspect','--format','{{.Name}}',volume])
    if exists['exit_status'] != 0: continue
    users = run(['docker','ps','-a','--filter','volume='+volume,'--format','{{.ID}}'])
    if users['exit_status'] == 0 and not users['stdout'].strip():
        run(['docker','volume','rm',volume])
for tag in run(['docker','image','ls','--format','{{.Repository}}:{{.Tag}}']).get('stdout','').splitlines():
    if tag.startswith(prefix+'-agent:'):
        run(['docker','image','rm',tag])

# Listener ownership must match this experiment before it is stopped.
for pid in run(['lsof','-tiTCP:18770','-sTCP:LISTEN']).get('stdout','').split():
    command = subprocess.run(['ps','-p',pid,'-o','command='],capture_output=True,text=True).stdout
    if str(root/'experiments/gateway/gateway.toml') in command:
        os.kill(int(pid),signal.SIGTERM)
        events.append(dict(operation='stop experiment gateway',pid=int(pid),owner='experiment'))
for _ in range(10):
    listener = run(['lsof','-tiTCP:18770','-sTCP:LISTEN'])
    if not listener.get('stdout','').strip(): break
    time.sleep(.5)
else:
    raise RuntimeError('experiment gateway still listens; retaining its state for inspection')
for log in (root/'experiments/gateway').glob('*.log'):
    shutil.copyfile(log,root/'results/gateway'/log.name)
for relative in ['experiments/gateway/certs','experiments/gateway/certs-b',
                 'experiments/gateway/state','experiments/gateway/config',
                 'experiments/sdk-venv']:
    path = root/relative
    if path.exists(): shutil.rmtree(path)

run(['docker','ps','-a','--filter','name='+prefix,'--format','{{.ID}} {{.Names}} {{.Status}}'])
run(['docker','volume','ls','--format','{{.Name}}'])
run(['lsof','-tiTCP:18770','-sTCP:LISTEN'])
run(['lsof','-tiTCP:18771','-sTCP:LISTEN'])
events.append(dict(operation='cleanup owner',owner='experiment scripts',
                   note='External fixture cleanup is not OpenShell-owned cleanup. Shared caches and unrelated resources were preserved.'))
events.append(dict(operation='disk space',free_before=free_before,
                   free_after=shutil.disk_usage(root).free,
                   note='Concurrent activity prevents attributing this difference solely to cleanup.'))
out = root/'results/cleanup'; out.mkdir(exist_ok=True)
target = out/'execution.json'
if target.exists(): target = out/('execution-'+str(time.time_ns())+'.json')
target.write_text(json.dumps(events,indent=2)+'\n')
print('Cleanup evidence:',target)
PY
