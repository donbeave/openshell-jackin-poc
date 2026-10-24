#!/usr/bin/env python3
import datetime,json,pathlib,subprocess,time
ROOT=pathlib.Path(__file__).resolve().parent;OUT=ROOT.parents[1]/'results'/'engines';OUT.mkdir(parents=True,exist_ok=True);checks=[]
def call(name,args,expected=0):
 t=time.monotonic();p=subprocess.run(args,capture_output=True,text=True,timeout=60);checks.append({'name':name,'command':args,'expected_exit_status':expected,'exit_status':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'seconds':time.monotonic()-t});return p
call('endpoint-owner-container',['docker','inspect','ojp-20261024-network-endpoint','--format','{{.Name}} {{.Id}} image={{.Image}} ports={{json .HostConfig.PortBindings}} labels={{json .Config.Labels}}'])
call('host-endpoint-response',['curl','--silent','--show-error','--max-time','5','http://127.0.0.1:15434/'])
for name,api in [('engine-a',18776),('engine-b',18777)]:
 c=ROOT/'private'/name/'client';cli=['docker','--host',f'tcp://127.0.0.1:{api}','--tlsverify','--tlscacert',str(c/'ca.pem'),'--tlscert',str(c/'cert.pem'),'--tlskey',str(c/'key.pem')]
 call(name+'-child-egress-to-controlled-host',['docker',*cli[1:],'run','--rm','--entrypoint','sh','alpine:3.22','-c','wget -qO- -T 5 http://host.docker.internal:15434/'])
(OUT/'child-network.json').write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'result':'External fixture only; nested Docker children attempted a connection to an experiment-owned host endpoint; no OpenShell network policy was in effect.','endpoint':'nginx:1.29.3-alpine, host TCP 15434, response body ojp-harmless-local-endpoint','endpoint_owner':'outer OrbStack Docker daemon; exact resource ojp-20261024-network-endpoint','checks':checks},indent=2)+'\n')
print(OUT/'child-network.json')
for x in checks: print(x['name'],x['exit_status'],x['stdout'][:150].replace('\n',' '),x['stderr'][:150].replace('\n',' '))
