"""No-policy-change control for experiment F."""
import subprocess,pathlib,json,time
root=pathlib.Path(__file__).resolve().parents[1];out=root/'results/policy-streams';base=['sh','experiments/os.sh','sandbox','exec','ojp-20261024-main','--no-login-shell','--']
r=subprocess.run(base+['docker','run','-d','--name','ojp-policy-control','-p','18084:6379','redis:7.4-alpine'],cwd=root,capture_output=True,text=True)
events=[dict(command=base+['docker','run','-d','--name','ojp-policy-control','-p','18084:6379','redis:7.4-alpine'],exit_status=r.returncode,stdout=r.stdout,stderr=r.stderr)]
program='import socket,time;s=socket.create_connection(("host.docker.internal",18084),timeout=5);print("CONNECTED",flush=True)\nfor i in range(20):\n s.sendall(b"PING\\r\\n");r=s.recv(128);print(i,repr(r),flush=True)\n if not r:raise RuntimeError("closed")\n time.sleep(1)'
processes=[]
for name,args in [('docker',['docker','exec','ojp-policy-control','sh','-c','i=0; while [ "$i" -lt 20 ]; do echo control-$i; i=$((i+1)); sleep 1; done']),('database',['python3','-u','-c',program])]:
 cmd=base+args;p=subprocess.Popen(cmd,cwd=root,stdout=(out/f'control-{name}.stdout').open('w'),stderr=(out/f'control-{name}.stderr').open('w'));processes.append((name,p,cmd))
for name,p,cmd in processes:
 code=p.wait(timeout=30);events.append(dict(command=cmd,stream=name,exit_status=code,expected_messages=20,no_policy_change=True))
r=subprocess.run(base+['docker','rm','-f','ojp-policy-control'],cwd=root,capture_output=True,text=True);events.append(dict(command=base+['docker','rm','-f','ojp-policy-control'],exit_status=r.returncode,stdout=r.stdout,stderr=r.stderr))
(out/'control.json').write_text(json.dumps(events,indent=2)+'\n');print(events)
