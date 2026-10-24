#!/usr/bin/env python3
"""Host-side controls for separately owned Docker daemon fixtures."""
import datetime,json,pathlib,subprocess,time
ROOT=pathlib.Path(__file__).resolve().parent
OUT=ROOT.parents[1]/'results'/'engines'; OUT.mkdir(parents=True,exist_ok=True)
rows=[]
def call(name,args,expected=0):
 t=time.monotonic(); p=subprocess.run(args,capture_output=True,text=True,timeout=180)
 rows.append({'name':name,'command':args,'expected_exit_status':expected,'exit_status':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'seconds':time.monotonic()-t})
 if p.returncode!=expected: print('FAILED',name,p.returncode,p.stderr[:300])
 return p
for name,api,fixed,auto in [('engine-a',18776,15432,18080),('engine-b',18777,15433,18085)]:
 cert=ROOT/'private'/name/'client'
 cli=['docker','--host',f'tcp://127.0.0.1:{api}','--tlsverify','--tlscacert',str(cert/'ca.pem'),'--tlscert',str(cert/'cert.pem'),'--tlskey',str(cert/'key.pem')]
 project=ROOT.parent/'rust-project'
 call(name+'-seed-project-volume', ['docker','cp',str(project)+'/.', 'ojp-20261024-'+name+':/sandbox/ojp-project/'])
 call(name+'-preloaded-nginx-image',cli+['image','inspect','nginx:1.29.3-alpine','--format','{{.Id}} {{json .RepoDigests}}'])
 call(name+'-daemon-port-range',['docker','exec','ojp-20261024-'+name,'cat','/proc/sys/net/ipv4/ip_local_port_range'])
 image='ojp-20261024-'+name+'-project:context-control'
 call(name+'-build-from-project-context',cli+['build','--file',str(ROOT/'Child.Dockerfile'),'-t',image,str(project)])
 call(name+'-run-built-project-context',cli+['run','--rm',image])
 for mode,publish in [('fixed',f'{fixed}:80'),('auto','80')]:
  cname='ojp-20261024-'+name+'-'+mode
  call(cname+'-run',cli+['run','--detach','--name',cname,'--publish',publish,'--entrypoint','sh','nginx:1.29.3-alpine','-c',"echo "+name+'-'+mode+" > /usr/share/nginx/html/index.html; echo ready; exec nginx -g 'daemon off;'"])
  inspected=call(cname+'-port',cli+['port',cname,'80/tcp'])
  port=int(inspected.stdout.strip().rsplit(':',1)[-1]) if inspected.returncode==0 else (fixed if mode=='fixed' else -1)
  call(cname+'-http', ['curl','--silent','--show-error','--max-time','8',f'http://127.0.0.1:{port}/'])
  call(cname+'-logs',cli+['logs',cname])
  call(cname+'-exec',cli+['exec',cname,'cat','/usr/share/nginx/html/index.html'])
  if mode=='fixed':
   call(cname+'-bind-volume-write',cli+['run','--rm','--mount','type=bind,src=/sandbox/ojp-project,dst=/project','--entrypoint','sh','nginx:1.29.3-alpine','-c',"sha256sum /project/Cargo.toml; printf 'child-volume-write\\n' > /project/from-inner-child.txt"])
   call(cname+'-shared-volume-read',['docker','exec','ojp-20261024-'+name,'cat','/sandbox/ojp-project/from-inner-child.txt'])
   vname='ojp-20261024-'+name+'-inner-volume'
   call(cname+'-named-volume-create',cli+['volume','create',vname])
   call(cname+'-named-volume-write',cli+['run','--rm','--mount',f'type=volume,src={vname},dst=/data','--entrypoint','sh','nginx:1.29.3-alpine','-c',"echo volume-ok > /data/proof.txt; cat /data/proof.txt"])
   call(cname+'-named-volume-inspect',cli+['volume','inspect',vname])
  call(cname+'-remove',cli+['rm','--force',cname])
(OUT/'api-probes.json').write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'host client to dedicated engine; not sandbox evidence','checks':rows},indent=2)+'\n')
print(OUT/'api-probes.json')
print('checks',len(rows),'failed',sum(r['expected_exit_status']!=r['exit_status'] for r in rows))
