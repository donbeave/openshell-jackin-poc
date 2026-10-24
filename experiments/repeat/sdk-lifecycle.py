import json,pathlib,time
from openshell import SandboxClient,TlsConfig
from openshell.sandbox import openshell_pb2
root=pathlib.Path(__file__).resolve().parents[2]
certs=root/'experiments/gateway/certs'
tls=TlsConfig(ca_path=certs/'ca.crt',cert_path=certs/'client/tls.crt',key_path=certs/'client/tls.key')
name='ojp-20261024-sdk'
events=[]
def note(op,fn):
 start=time.monotonic()
 try:
  v=fn();events.append(dict(operation=op,result='PASS',seconds=time.monotonic()-start,output=str(v)));return v
 except Exception as e:
  events.append(dict(operation=op,result='FAIL',seconds=time.monotonic()-start,error=str(e)));raise
try:
 with SandboxClient('127.0.0.1:18770',tls=tls,timeout=60) as c:
  spec=openshell_pb2.SandboxSpec(template={'image':'ojp-20261024-agent:2.1.310'},command=['bash','--noprofile','--norc','-i'],tty=True,environment={'OJP_VALUE':'harmless-value'})
  created=note('SDK create',lambda:c.create(workspace='default',name=name,spec=spec))
  note('SDK wait_ready',lambda:c.wait_ready(name,workspace='default',timeout_seconds=120))
  note('SDK exec',lambda:c.exec(name,['sh','-c','printf sdk-created; exit 0'],workspace='default'))
  note('SDK get',lambda:c.get(name,workspace='default'))
  deleted=note('SDK delete',lambda:c.delete(name,workspace='default'))
  note('SDK wait_deleted',lambda:c.wait_deleted(name,workspace='default',expected_sandbox_id=deleted.sandbox_id,timeout_seconds=60))
finally:
 (root/'results/repeat/sdk-lifecycle.json').write_text(json.dumps(events,indent=2)+'\n')
print(json.dumps(events,indent=2))
