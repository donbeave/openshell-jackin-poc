"""Experiment F: observe active streams without reconnecting or retrying."""
import json,pathlib,subprocess,time
root=pathlib.Path(__file__).resolve().parents[1]; out=root/'results/policy-streams';out.mkdir(exist_ok=True)
base=['sh','experiments/os.sh'];name='ojp-20261024-main';events=[]
def command(args):
 start=time.monotonic();r=subprocess.run(base+args,cwd=root,capture_output=True,text=True,timeout=45);events.append(dict(command=base+args,exit_status=r.returncode,stdout=r.stdout,stderr=r.stderr,seconds=time.monotonic()-start));return r
command(['sandbox','exec',name,'--no-login-shell','--','docker','run','-d','--name','ojp-policy-db','-p','18084:6379','redis:7.4-alpine'])
(root/'experiments/engine-unrelated.yaml').write_text((root/'experiments/engine.yaml').read_text()+'''\n  unrelated_public_docs:\n    endpoints:\n      - {host: example.com, port: 443}\n    binaries:\n      - {path: /usr/bin/curl}\n''')
db_code='''import socket,time
s=socket.create_connection(("host.docker.internal",18084),timeout=5)
print("CONNECTED",flush=True)
for i in range(30):
 s.sendall(b"PING\\r\\n")
 data=s.recv(128)
 print(i,repr(data),flush=True)
 if not data: raise RuntimeError("connection closed")
 time.sleep(1)
'''
stream=['docker','exec','ojp-policy-db','sh','-c','i=0; while [ "$i" -lt 30 ]; do echo stream-$i; i=$((i+1)); sleep 1; done']
for phase,policy in [('unrelated','experiments/engine-unrelated.yaml'),('revoke','experiments/denied.yaml')]:
 command(['policy','set',name,'--policy','experiments/engine.yaml','--wait'])
 processes=[]
 for label,args in [('docker',stream),('database',['python3','-u','-c',db_code])]:
  stdout=(out/f'{phase}-{label}.stdout').open('w');stderr=(out/f'{phase}-{label}.stderr').open('w')
  cmd=base+['sandbox','exec',name,'--no-login-shell','--']+args
  p=subprocess.Popen(cmd,cwd=root,stdout=stdout,stderr=stderr)
  processes.append((label,p,stdout,stderr,cmd))
 time.sleep(3)
 before={label:p.poll() for label,p,*_ in processes}
 change=command(['policy','set',name,'--policy',policy,'--wait'])
 time.sleep(6)
 after={label:p.poll() for label,p,*_ in processes}
 events.append(dict(phase=phase,before=before,after=after,policy_exit_status=change.returncode,observation_seconds=6,no_reconnect=True))
 for label,p,stdout,stderr,cmd in processes:
  if p.poll() is None:p.terminate()
  try:code=p.wait(timeout=5)
  except subprocess.TimeoutExpired:p.kill();code=p.wait()
  stdout.close();stderr.close();events.append(dict(phase=phase,stream=label,command=cmd,exit_status=code))
command(['policy','set',name,'--policy','experiments/engine.yaml','--wait'])
command(['sandbox','exec',name,'--no-login-shell','--','docker','rm','-f','ojp-policy-db'])
(out/'events.json').write_text(json.dumps(events,indent=2)+'\n')
print(json.dumps(events))
