#!/usr/bin/env python3
import datetime,json,pathlib,subprocess,time
root=pathlib.Path(__file__).resolve().parent; out=root.parents[1]/'results'/'engines'; out.mkdir(parents=True,exist_ok=True)
checks=[]
def call(n,args,expected=0):
 t=time.monotonic();p=subprocess.run(args,capture_output=True,text=True,timeout=90);checks.append({'name':n,'command':args,'expected_exit_status':expected,'exit_status':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'seconds':time.monotonic()-t});return p
base=['docker','--host','tcp://127.0.0.1:18776','--tlsverify','--tlscacert',str(root/'private/engine-a/client/ca.pem'),'--tlscert',str(root/'private/engine-a/client/cert.pem'),'--tlskey',str(root/'private/engine-a/client/key.pem')]
name='ojp-20261024-engine-a-limits'
call('child-with-small-limit',base+['run','--detach','--name',name,'--memory=128m','--cpus=0.5','alpine:3.22','sh','-c','sleep 300'])
call('child-configured-cgroup-limits',base+['inspect',name,'--format','memory={{.HostConfig.Memory}} nano_cpus={{.HostConfig.NanoCpus}} cpu_quota={{.HostConfig.CpuQuota}} cpu_period={{.HostConfig.CpuPeriod}} cpu_shares={{.HostConfig.CpuShares}}'])
call('child-cgroup-visible-limits',base+['exec',name,'sh','-c','cat /sys/fs/cgroup/memory.max /sys/fs/cgroup/cpu.max'])
call('child-limit-remove',base+['rm','--force',name])
call('outer-engine-cgroup-cap',['docker','inspect','ojp-20261024-engine-a','--format','container_cpu_nanos={{.HostConfig.NanoCpus}} memory_bytes={{.HostConfig.Memory}}'])
(out/'resource-limits.json').write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'DinD outer container plus its nested child container; OpenShell sandbox was not available for comparison','checks':checks},indent=2)+'\n')
print(out/'resource-limits.json');print('checks',len(checks),'failures',sum(x['exit_status']!=x['expected_exit_status'] for x in checks))
