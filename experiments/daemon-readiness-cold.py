"""Time cold/warm authenticated readiness of one disposable dedicated engine."""
import datetime,json,pathlib,shutil,subprocess,time
root=pathlib.Path(__file__).resolve().parents[1];private=root/'experiments/readiness-private';private.mkdir(mode=0o700,exist_ok=False)
rows=[];name='ojp-20261024-time'
def run(args,timeout=30):
 t=time.monotonic();p=subprocess.run(args,capture_output=True,text=True,timeout=timeout);r=dict(command=args,exit_status=p.returncode,stdout=p.stdout,stderr=p.stderr,seconds=time.monotonic()-t);rows.append(r);return r
try:
 for kind in ['ca','server','client']:
  run(['openssl','ecparam','-name','prime256v1','-genkey','-noout','-out',str(private/(kind+'.key'))])
 run(['openssl','req','-new','-x509','-key',str(private/'ca.key'),'-days','1','-subj','/CN=ojp-readiness-ca','-out',str(private/'ca.pem')])
 for kind in ['server','client']:
  run(['openssl','req','-new','-key',str(private/(kind+'.key')),'-subj','/CN=localhost','-out',str(private/(kind+'.csr'))])
  ext=private/(kind+'.ext');ext.write_text('extendedKeyUsage='+('serverAuth\nsubjectAltName=DNS:localhost,IP:127.0.0.1\n' if kind=='server' else 'clientAuth\n'))
  run(['openssl','x509','-req','-in',str(private/(kind+'.csr')),'-CA',str(private/'ca.pem'),'-CAkey',str(private/'ca.key'),'-CAcreateserial','-days','1','-extfile',str(ext),'-out',str(private/(kind+'.pem'))])
 cli=['docker','--host','tcp://127.0.0.1:18779','--tlsverify','--tlscacert',str(private/'ca.pem'),'--tlscert',str(private/'client.pem'),'--tlskey',str(private/'client.key'),'info','--format','{{.ID}} {{.ServerVersion}}']
 for phase in ['cold','warm']:
  start=time.monotonic()
  if phase=='cold':
   r=run(['docker','run','-d','--name',name,'--privileged','--cpus=1','--memory=512m','--label','ojp.test-id=ojp-20261024','--publish','127.0.0.1:18779:2376','--mount','type=bind,src='+str(private)+',dst=/certs,readonly','--entrypoint','dockerd','docker:29.8.2-dind@sha256:1e08cdb63405ca788aea94ef35b792d1e299607c667d33d7bcbcae1fd2611ced','--tlsverify','--tlscacert=/certs/ca.pem','--tlscert=/certs/server.pem','--tlskey=/certs/server.key','--host=tcp://0.0.0.0:2376','--host=unix:///var/run/docker.sock'])
  else:r=run(['docker','restart',name])
  if r['exit_status']!=0:raise RuntimeError(r['stderr'])
  for _ in range(50):
   r=run(cli)
   if r['exit_status']==0:break
   time.sleep(.1)
  rows.append(dict(phase=phase,result='PASS' if r['exit_status']==0 else 'BLOCKED',mechanism='EXTERNAL FIXTURE',seconds=time.monotonic()-start,criterion='first successful mutual-TLS Docker info response',cache='host image cached; '+('fresh empty daemon data' if phase=='cold' else 'same daemon data retained')))
 run(['docker','inspect','--format','{{.Id}} {{json .Mounts}}',name])
finally:
 run(['docker','rm','-fv',name])
 run(['docker','ps','-a','--filter','name='+name,'--format','{{.ID}}'])
 shutil.rmtree(private)
 (root/'results/measurements/daemon-authenticated-readiness.json').write_text(json.dumps(rows,indent=2)+'\n')
 print([r for r in rows if 'phase' in r])
