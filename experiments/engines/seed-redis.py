#!/usr/bin/env python3
"""Pull Redis without host credentials and preload dedicated test daemons."""
import datetime,json,os,pathlib,subprocess,tempfile,time

ROOT=pathlib.Path(__file__).resolve().parent
OUT=ROOT.parents[1]/'results'/'engines';OUT.mkdir(parents=True,exist_ok=True)
IMAGE='redis:7.4-alpine'
checks=[]
def call(name,args,expected=0,env=None,stdin=None):
    start=time.monotonic()
    p=subprocess.run(args,capture_output=True,text=True,env=env,stdin=stdin,timeout=300)
    checks.append({'name':name,'command':args,'expected_exit_status':expected,'exit_status':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'seconds':time.monotonic()-start})
    return p
def inspect_remote(name,host=None):
    command=['docker','exec']
    if host: command += ['--env','DOCKER_HOST='+host]
    command += [name,'docker','image','inspect',IMAGE,'--format','{{.Id}} {{json .RepoDigests}}']
    return call(name+'-redis-image-identity',command)
def preload(name,host=None):
    tar='/tmp/ojp-redis-7.4-alpine.tar'
    command=['docker','exec','-i']
    if host: command += ['--env','DOCKER_HOST='+host]
    command += [name,'sh','-c','cat > '+tar]
    start=time.monotonic()
    with image_tar.open('rb') as stream:
        p=subprocess.run(command,stdin=stream,capture_output=True,text=True,timeout=120)
    checks.append({'name':name+'-image-tar-transfer','command':command,'exit_status':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'seconds':time.monotonic()-start})
    if p.returncode: return
    load=['docker','exec']
    if host: load += ['--env','DOCKER_HOST='+host]
    load += [name,'docker','load','--input',tar]
    call(name+'-docker-image-load',load)
    remove=['docker','exec',name,'rm',tar]
    call(name+'-remove-transfer-tar',remove)
    inspect_remote(name,host)

with tempfile.TemporaryDirectory(prefix='ojp-docker-config-') as config, tempfile.TemporaryDirectory(prefix='ojp-redis-image-') as temp:
    env=os.environ.copy();env['DOCKER_CONFIG']=config
    call('pull-public-image-with-empty-docker-config',['docker','pull',IMAGE],env=env)
    pulled=call('host-image-identity',['docker','image','inspect',IMAGE,'--format','{{.Id}} {{json .RepoDigests}}'],env=env)
    image_tar=pathlib.Path(temp)/'redis.image.tar'
    start=time.monotonic()
    p=subprocess.run(['docker','save','--output',str(image_tar),IMAGE],capture_output=True,text=True,env=env,timeout=300)
    checks.append({'name':'host-image-save','command':['docker','save','--output','<temporary>/redis.image.tar',IMAGE],'exit_status':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'seconds':time.monotonic()-start,'byte_size':image_tar.stat().st_size if image_tar.exists() else None})
    if image_tar.exists():
        import hashlib
        checks[-1]['sha256']=hashlib.sha256(image_tar.read_bytes()).hexdigest()
        if p.returncode==0:
            preload('ojp-20261024-engine-a')
            preload('ojp-20261024-engine-b')
            preload('ojp-20261024-sock','unix:///var/run/ojp-docker-socket/docker.sock')

(OUT/'redis-image-seed.json').write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'image':IMAGE,'host_credentials':'DOCKER_CONFIG pointed to an empty temporary directory for the public pull','transport':'docker save stream through docker exec stdin; not a registry pull by the dedicated daemon','targets':{'A':'ojp-20261024-engine-a','B':'ojp-20261024-engine-b','Unix socket':'ojp-20261024-sock'},'checks':checks},indent=2)+'\n')
print(OUT/'redis-image-seed.json')
print('checks',len(checks),'failures',sum(x['exit_status']!=x.get('expected_exit_status',0) for x in checks))
