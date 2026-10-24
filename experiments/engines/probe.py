#!/usr/bin/env python3
import datetime, json, pathlib, subprocess, time
root=pathlib.Path(__file__).resolve().parent
out=root.parents[1]/'results'/'engines'
out.mkdir(parents=True,exist_ok=True)
def call(name, args, timeout=30):
 start=time.monotonic()
 p=subprocess.run(args, capture_output=True, text=True, timeout=timeout)
 return {'name':name,'command':args,'exit_status':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'seconds':time.monotonic()-start}
def docker(name,port,ca,cert=None,key=None):
 args=['docker','--host',f'tcp://127.0.0.1:{port}','--tlsverify','--tlscacert',str(ca)]
 if cert: args += ['--tlscert',str(cert),'--tlskey',str(key)]
 return args
checks=[]
for name,port in [('engine-a',18776),('engine-b',18777)]:
 d=root/'private'/name/'client'
 base=docker(name,port,d/'ca.pem',d/'cert.pem',d/'key.pem')
 checks.append(call(name+'-valid-mtls',base+['info','--format','{{.ID}} {{.ServerVersion}} {{.OperatingSystem}}']))
checks.append(call('engine-a-no-client-certificate',docker('engine-a',18776,root/'private/engine-a/client/ca.pem')+['info','--format','{{.ID}}']))
checks.append(call('engine-b-rejects-engine-a-client',docker('engine-b',18777,root/'private/engine-b/client/ca.pem',root/'private/engine-a/client/cert.pem',root/'private/engine-a/client/key.pem')+['info','--format','{{.ID}}']))
(out/'tls-probes.json').write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':checks},indent=2)+'\n')
for x in checks: print(x['name'],x['exit_status'],x['stdout'][:120].replace('\n',' '),x['stderr'][:250].replace('\n',' '))
