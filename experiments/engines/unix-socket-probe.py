#!/usr/bin/env python3
import datetime,json,pathlib,subprocess,time
root=pathlib.Path(__file__).resolve().parent
out=root.parents[1]/'results'/'engines'; out.mkdir(parents=True,exist_ok=True)
socket='unix:///var/run/ojp-docker-socket/docker.sock'
checks=[]
def call(name,args,expected=0):
 t=time.monotonic(); p=subprocess.run(args,capture_output=True,text=True,timeout=90)
 checks.append({'name':name,'command':args,'expected_exit_status':expected,'exit_status':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'seconds':time.monotonic()-t})
 return p
call('restrict-socket-for-nonroot-negative-test', ['docker','exec','ojp-20261024-sock','chmod','0660','/var/run/ojp-docker-socket/docker.sock'])
call('socket-mode-before-nonroot', ['docker','exec','ojp-20261024-sock','stat','-c','%a %u:%g','/var/run/ojp-docker-socket/docker.sock'])
call('uid-1000-before-chmod-denied', ['docker','exec','--user','1000:1000','--env','DOCKER_HOST='+socket,'ojp-20261024-sock','docker','info'],1)
call('open-socket-for-nonroot-test', ['docker','exec','ojp-20261024-sock','chmod','0666','/var/run/ojp-docker-socket/docker.sock'])
call('socket-mode-after-chmod', ['docker','exec','ojp-20261024-sock','stat','-c','%a %u:%g','/var/run/ojp-docker-socket/docker.sock'])
call('uid-1000-after-chmod-api', ['docker','exec','--user','1000:1000','--env','DOCKER_HOST='+socket,'ojp-20261024-sock','docker','info','--format','{{.ID}} {{.ServerVersion}} {{.OperatingSystem}}'])
call('daemon-resource-identity', ['docker','exec','--env','DOCKER_HOST='+socket,'ojp-20261024-sock','docker','info','--format','{{.ID}} {{.ServerVersion}} {{.DockerRootDir}}'])
call('daemon-listen-logs',['docker','logs','ojp-20261024-sock'])
call('outer-socket-volume',['docker','volume','inspect','ojp-20261024-sock-dockersock','--format','{{.Name}} {{json .Labels}}'])
call('outer-container',['docker','inspect','ojp-20261024-sock','--format','{{.Name}} {{.Id}} {{.Image}} {{json .HostConfig.PortBindings}} {{json .Mounts}} {{.HostConfig.NanoCpus}} {{.HostConfig.Memory}}'])
(out/'unix-socket-probes.json').write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'fixture':'external DinD, Unix socket only, no TCP exposure','sandbox_mount_target':'/sandbox/docker (parent should mount approved volume here; socket path /sandbox/docker/docker.sock)','daemon_path_inside_fixture':'/var/run/ojp-docker-socket/docker.sock','ownership':'outer OrbStack Docker daemon owns the DinD container and socket volume; socket grants full inner Docker daemon authority','checks':checks},indent=2)+'\n')
print(out/'unix-socket-probes.json')
print('checks',len(checks),'failures',sum(x['exit_status']!=x['expected_exit_status'] for x in checks))
