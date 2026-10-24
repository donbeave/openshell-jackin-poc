#!/usr/bin/env python3
import datetime,json,pathlib,subprocess,time
ROOT=pathlib.Path(__file__).resolve().parent
OUT=ROOT.parents[1]/'results'/'engines';OUT.mkdir(parents=True,exist_ok=True)
name='ojp-20261024-interrupted';volume='ojp-20261024-interrupted-run'
image='docker:29.8.2-dind@sha256:1e08cdb63405ca788aea94ef35b792d1e299607c667d33d7bcbcae1fd2611ced'
rows=[]
def call(n,args,timeout=120):
 t=time.monotonic();p=subprocess.run(args,capture_output=True,text=True,timeout=timeout)
 rows.append({'name':n,'command':args,'exit_status':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'seconds':time.monotonic()-t})
 return p
call('create-approved-socket-volume',['docker','volume','create','--label','openshell.ai/sandbox-attachable=true','--label','openshell.ai/sandbox-attachable-workspace=default','--label','ojp.test-id=ojp-20261024',volume])
call('start-delayed-daemon-provisioning',['docker','run','--detach','--name',name,'--privileged','--label','ojp.test-id=ojp-20261024','--label','ojp.owner=experiments/engines/interrupt-provision.py','--mount',f'type=volume,src={volume},dst=/var/run/ojp-docker-socket','--env','DOCKER_TLS_CERTDIR=',image,'sh','-c','echo provisioning-start; sleep 30; exec dockerd --host=unix:///var/run/ojp-docker-socket/docker.sock'])
time.sleep(0.2)
call('interrupt-provisioning',['docker','kill','--signal=KILL',name])
call('interrupted-container-remains',['docker','inspect',name,'--format','{{.Name}} {{.Id}} state={{.State.Status}} exit={{.State.ExitCode}} mounts={{json .Mounts}}'])
call('interrupted-volume-remains',['docker','volume','inspect',volume,'--format','{{.Name}} {{json .Labels}}'])
call('interrupted-startup-logs',['docker','logs',name])
call('cleanup-interrupted-container',['docker','rm','--force','--volumes',name])
call('cleanup-interrupted-named-volume',['docker','volume','rm',volume])
call('post-cleanup-container-absence',['docker','inspect',name],1)
call('post-cleanup-volume-absence',['docker','volume','inspect',volume],1)
(OUT/'interrupted-provision.json').write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'result':'provision interrupted with SIGKILL before dockerd startup; container and approved socket volume were inspected before fixture-only cleanup','mechanism':'EXTERNAL FIXTURE','owner':'outer OrbStack Docker daemon; no OpenShell recovery or cleanup claim','checks':rows},indent=2)+'\n')
print(OUT/'interrupted-provision.json')
print('checks',len(rows))
