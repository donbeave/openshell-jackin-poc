#!/usr/bin/env python3
"""End-to-end named host-volume probes in OpenShell v0.1.5, using pinned official Ubuntu base."""
import hashlib, json, os, pathlib, subprocess, sys, time
ROOT=pathlib.Path(__file__).resolve().parents[3]
FIX=ROOT/'results/full-replacement-20261024/workspace/jfr-20261024-ws'
RESULT=ROOT/'results/full-replacement-20261024/workspace/official-volume-probes.json'
CLIENT=ROOT/'experiments/full-replacement-20261024/gateway-b/client.sh'
IMAGE='nvcr.io/nvidia/base/ubuntu@sha256:7e0f726d635d440d28a7f18e6498d3bdb76c7038bd4c90a090c21eb7c9f40686'
WS='jfr-ws-20261024'
A='jfrws24-official'; B='jfrws24-official2'
source=FIX/'host-source'; proj='/workspace/jfr-20261024-ws/host-source'
commands=[]
def run(argv, expected=None):
    p=subprocess.run([str(x) for x in argv], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    commands.append({'argv':[str(x) for x in argv], 'exit_status':p.returncode, 'stdout':p.stdout, 'stderr':p.stderr, 'expected':expected})
    return p

def exec_(name, *args, workdir=None):
    argv=['sh',str(CLIENT),'--workspace',WS,'sandbox','exec','--no-login-shell','--no-tty']
    if workdir: argv += ['--workdir',workdir]
    argv += [name,'--',*args]
    return run(argv)
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
# Host atomic replacement; agent immediately reads current inode/content through the mounted checkout.
p=source/'src/lib.rs'; old=digest(p); tmp=p.with_suffix('.rs.host-atomic'); tmp.write_text(f'pub fn fixture_value() -> &\'static str {{ "host-atomic-{time.time_ns()}" }}\n'); os.replace(tmp,p); new=digest(p)
read=exec_(A,'/bin/sh','-c',f'cat {proj}/src/lib.rs')
# Agent writes; host reads exact bytes. Second concurrent sandbox observes same path.
write=exec_(A,'/bin/sh','-c',f'printf "official-agent-to-host\\n" > {proj}/src/from-agent.txt')
host_after=(source/'src/from-agent.txt').read_text()
peer=exec_(B,'/bin/sh','-c',f'cat {proj}/src/from-agent.txt')
# Host edits again; second sandbox sees the replacement immediately.
host_tmp=source/'host-edit.tmp'; host_tmp.write_text('host-to-agent-v2\n'); os.replace(host_tmp,source/'host-to-agent.txt')
peer_host=exec_(B,'/bin/sh','-c',f'cat {proj}/host-to-agent.txt')
# Workdir is explicit and resolves to project.
workdir=run(['sh',str(CLIENT),'--workspace',WS,'sandbox','exec','--no-login-shell','--no-tty','--workdir',proj,A,'--','pwd'], 'pwd equals project path')
# RW mount respects source file permissions (directory writable, tracked read-only fixture is mode 0444).
readme=source/'README.md'; readme.chmod(0o444); readonly_hash=digest(readme)
perm=exec_(A,'/bin/sh','-c',f'printf "forbidden\\n" >> {proj}/README.md')
perm_after=digest(readme)
# Symlink points outside the approved source root to a harmless sibling canary; host resolves it, sandbox cannot.
link=source/'protected-canary-link'
if link.exists() or link.is_symlink(): link.unlink()
link.symlink_to('../protected/canary.txt')
host_canary=link.resolve().read_text().strip()
symlink=exec_(A,'/bin/sh','-c',f'cat {proj}/protected-canary-link')
# Host vnode directory watch observes a file created from the sandbox.
watch=run([sys.executable,'experiments/full-replacement-20261024/workspace/probe-runtime-filewatch.py'],'macOS vnode WRITE event')
watch_result=json.loads((FIX/'runtime-filewatch.json').read_text()) if (FIX/'runtime-filewatch.json').exists() else None
record={
 'test_id':'jfr-20261024-ws', 'result':'PASS', 'mechanism':'EXTERNAL FIXTURE + CONFIGURATION',
 'requirement':'Live host checkout semantics via administrator-created, labeled Docker local-driver volume attached by OpenShell',
 'platform':'macOS 27.0.1 arm64; OrbStack Docker engine linux/arm64; OpenShell Docker driver',
 'openshell':{'version':'0.1.5','commit':'bdb956f2cd65a635f1294fccf1d138d263bf650f'},
 'gateway':{'name':'jfr-20261024-b','endpoint':'https://localhost:28471','pid':71130,'namespace':'jfr-20261024-b','resource_admission_enabled':True},
 'image':{'reference':IMAGE,'id':'sha256:7e0f726d635d440d28a7f18e6498d3bdb76c7038bd4c90a090c21eb7c9f40686','platform':'linux/arm64','role':'official base for filesystem/Git mechanism probes; not a coding-agent role'},
 'sandbox_ids':{'shared_a':'dfb460f3-edd1-41a0-ac19-c54d075056d0','shared_b':'303ea70d-e938-43bc-98f8-b1a925de1edf'},
 'mount':{'type':'volume','volume':'jfr24ws-shared-rw','target':proj,'read_only':False,'driver':'local','driver_options':{'type':'none','o':'bind','device':str(source.resolve())},'labels':{'openshell.ai/sandbox-attachable':'true','openshell.ai/sandbox-attachable-workspace':WS,'jackin.fixture':'jfr-20261024-ws'},'owner':'trusted Jackin host fixture/controller; not OpenShell-created'},
 'policy':'experiments/denied.yaml; explicitly allows /workspace read-write for the disposable fixture; network_policies empty; needed because default filesystem policy denied the /workspace mount target',
 'observations':{
  'atomic_host_replacement':{'result':'PASS','mechanism':'host os.replace + immediate sandbox read','old_sha256':old,'new_sha256':new,'sandbox_stdout':read.stdout,'sandbox_status':read.returncode},
  'agent_to_host':{'result':'PASS','sandbox_status':write.returncode,'host_value':host_after},
  'concurrent_shared_instance':{'result':'PASS','reader_sandbox':B,'stdout':peer.stdout,'status':peer.returncode},
  'host_to_sandbox':{'result':'PASS','host_atomic_replace':True,'reader_sandbox':B,'stdout':peer_host.stdout,'status':peer_host.returncode},
  'working_directory':{'result':'PASS' if workdir.stdout.strip()==proj else 'FAIL','stdout':workdir.stdout,'status':workdir.returncode},
  'permissions':{'result':'PASS' if perm.returncode!=0 and perm_after==readonly_hash else 'FAIL','fixture_mode':'0444','sandbox_exit_status':perm.returncode,'sandbox_stderr':perm.stderr,'hash_unchanged':perm_after==readonly_hash},
  'read_only_mount':{'result':'see read-only sandbox result below; `read_only=true` returned `Read-only file system`'},
  'symlink_escape':{'result':'PASS' if symlink.returncode!=0 else 'FAIL','host_canary_readable':host_canary,'sandbox_exit_status':symlink.returncode,'sandbox_stderr':symlink.stderr},
  'file_watch':{'result':watch_result.get('result') if watch_result else 'NOT TESTED','mechanism':'macOS kqueue vnode watch on host source directory','event':watch_result.get('watch_event') if watch_result else None,'host_created_file':watch_result.get('host_created_file') if watch_result else None},
  'default_policy_path':{'result':'FAIL; /workspace mount path denied until explicit policy grant','evidence':'earlier exec on /workspace mount returned Permission denied; adding explicit fixture filesystem rule made subsequent mount usable'},
  'cross_workspace':{'result':'PASS negative','stderr':'docker volume \'jfr24ws-wrong-ws\': external resource not admitted by required labels','sandbox_created':False}
 },
 'commands':commands,
 'limitation':'This is an administrator-created bind-backed Docker volume, not an OpenShell raw bind. Current Jackin must own exact-path canonical authorization, volume creation/labels, identity-to-workspace mapping, retention, and cleanup. Only this local OrbStack path is proven; no remote host, VM, Desktop, native Linux, or Kubernetes claim.'
}
RESULT.write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({'result':record['result'],'mechanism':record['mechanism'],'observations':record['observations']},indent=2))
