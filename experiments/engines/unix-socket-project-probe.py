#!/usr/bin/env python3
import datetime,json,pathlib,subprocess,time
ROOT=pathlib.Path(__file__).resolve().parent;OUT=ROOT.parents[1]/'results'/'engines';OUT.mkdir(parents=True,exist_ok=True)
host='unix:///var/run/ojp-docker-socket/docker.sock'; checks=[]
def call(name,args,expected=0):
 t=time.monotonic();p=subprocess.run(args,capture_output=True,text=True,timeout=120);checks.append({'name':name,'command':args,'expected_exit_status':expected,'exit_status':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'seconds':time.monotonic()-t});return p
call('project-volume-labels',['docker','volume','inspect','ojp-20261024-sock-project','--format','{{.Name}} {{json .Labels}}'])
call('fixture-mounts-and-port',['docker','inspect','ojp-20261024-sock','--format','{{.Id}} {{json .Mounts}} {{json .HostConfig.PortBindings}} {{json .HostConfig.Sysctls}} {{.HostConfig.NanoCpus}} {{.HostConfig.Memory}}'])
call('uid1000-project-root-and-source',['docker','exec','ojp-20261024-sock','sh','-c','stat -c "%a %u:%g" /sandbox/ojp-project; sha256sum /sandbox/ojp-project/Cargo.toml; find /sandbox/ojp-project -maxdepth 2 -type f | sort'])
call('uid1000-project-write',['docker','exec','--user','1000:1000','ojp-20261024-sock','sh','-c','printf "uid1000-write\\n" > /sandbox/ojp-project/from-sandbox-user.txt'])
call('uid1000-project-write-owner',['docker','exec','ojp-20261024-sock','stat','-c','%a %u:%g','/sandbox/ojp-project/from-sandbox-user.txt'])
call('uid1000-unix-docker-api',['docker','exec','--user','1000:1000','--env','DOCKER_HOST='+host,'ojp-20261024-sock','docker','info','--format','{{.ID}} {{.ServerVersion}} {{.DockerRootDir}}'])
call('redis-image-identity',['docker','exec','--env','DOCKER_HOST='+host,'ojp-20261024-sock','docker','image','inspect','redis:7.4-alpine','--format','{{.Id}} {{json .RepoDigests}}'])
call('unix-only-listener',['docker','logs','ojp-20261024-sock'])
(OUT/'unix-socket-project.json').write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'fixture':'external dedicated Docker daemon over Unix socket; approved project named volume shared with OpenShell at the same path','sandbox_target':'/sandbox/ojp-project','socket_sandbox_target':'/sandbox/docker/docker.sock','child_service_port_forward':'host 18090 -> outer DinD 18090; inner allocator range is only 18090','owner':'outer OrbStack Docker daemon owns DinD container and approved socket/project volumes; sandbox deletion does not imply fixture cleanup','checks':checks},indent=2)+'\n')
print(OUT/'unix-socket-project.json')
print('checks',len(checks),'failures',sum(x['exit_status']!=x['expected_exit_status'] for x in checks))
for x in checks: print(x['name'],x['exit_status'],x['stdout'][:160].replace('\n',' '),x['stderr'][:120].replace('\n',' '))
