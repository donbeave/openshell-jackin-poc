"""Experiment D commands in one explicitly selected sandbox."""
import json,pathlib,subprocess,time
root=pathlib.Path(__file__).resolve().parents[1]; name='ojp-20261024-v2'
commands=[
 ['docker','info','--format','{{.ID}} {{.Name}}'],
 ['docker','--host','tcp://host.docker.internal:18777','version'],
 ['docker','--tlscert','/dev/null','--tlskey','/dev/null','version'],
 ['sh','-ec','mkdir -p /workspace/ojp-project; printf "FROM scratch\\nCOPY result.txt /result.txt\\n" > /workspace/ojp-project/Dockerfile; printf build-context-bytes > /workspace/ojp-project/result.txt; docker build -t ojp-d-context /workspace/ojp-project'],
 ['docker','run','-d','--name','ojp-d-child','nginx:1.29.3-alpine'],
 ['docker','logs','ojp-d-child'],
 ['docker','exec','ojp-d-child','sh','-c','echo child-exec-ok'],
 ['sh','-c','timeout 2 docker exec ojp-d-child sh -c "echo stream-start; sleep 20; echo stream-end"; code=$?; echo client_cancel_status=$code; docker exec ojp-d-child ps'],
 ['docker','volume','create','ojp-d-volume'],
 ['docker','run','--rm','-v','ojp-d-volume:/data','nginx:1.29.3-alpine','sh','-ec','echo volume-data > /data/value; cat /data/value'],
 ['docker','run','--rm','-v','ojp-d-volume:/data','nginx:1.29.3-alpine','cat','/data/value'],
 ['docker','rm','-f','ojp-d-child'],
 ['docker','rmi','ojp-d-context'],
 ['docker','volume','rm','ojp-d-volume'],
]
events=[]
for args in commands:
 cmd=['sh','experiments/os.sh','sandbox','exec',name,'--no-login-shell','--']+args
 start=time.monotonic()
 try:
  r=subprocess.run(cmd,cwd=root,capture_output=True,text=True,timeout=60)
  events.append(dict(command=cmd,exit_status=r.returncode,stdout=r.stdout,stderr=r.stderr,seconds=time.monotonic()-start))
 except subprocess.TimeoutExpired as e:events.append(dict(command=cmd,exit_status=124,error=str(e)))
 print(events[-1],flush=True)
(root/'results/engine/docker-operations.json').write_text(json.dumps(events,indent=2)+'\n')
