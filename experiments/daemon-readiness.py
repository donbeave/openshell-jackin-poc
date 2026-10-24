"""Startup-log measurement and one warm restart of the empty Engine B fixture."""
import datetime,json,pathlib,re,subprocess,time
root=pathlib.Path(__file__).resolve().parents[1];rows=[]
def run(args):
 t=time.monotonic();p=subprocess.run(args,capture_output=True,text=True,timeout=30);r=dict(command=args,exit_status=p.returncode,stdout=p.stdout,stderr=p.stderr,seconds=time.monotonic()-t);rows.append(r);return r
start=run(['docker','inspect','--format','{{.State.StartedAt}}','ojp-20261024-engine-b'])
logs=run(['docker','logs','ojp-20261024-engine-b'])
timestamps=re.findall(r'time="([^"]+)"[^\n]*API listen on',logs['stdout']+logs['stderr'])
if timestamps:
 elapsed=(datetime.datetime.fromisoformat(timestamps[0].replace('Z','+00:00'))-datetime.datetime.fromisoformat(start['stdout'].strip().replace('Z','+00:00'))).total_seconds()
 rows.append(dict(measurement='initial empty daemon API listener from logs',seconds=elapsed,cache='cached host image; fresh daemon data at container creation',limitation='listener readiness, not first externally authenticated API request'))
cmd=['docker','--host','tcp://127.0.0.1:18777','--tlsverify','--tlscacert',str(root/'experiments/engines/private/engine-b/client/ca.pem'),'--tlscert',str(root/'experiments/engines/private/engine-b/client/cert.pem'),'--tlskey',str(root/'experiments/engines/private/engine-b/client/key.pem'),'info','--format','{{.ID}}']
run(['docker','exec','ojp-20261024-engine-b','docker','ps','-a','--format','{{.Names}}'])
t=time.monotonic();run(['docker','restart','ojp-20261024-engine-b'])
for _ in range(30):
 p=run(cmd)
 if p['exit_status']==0:break
 time.sleep(.2)
rows.append(dict(measurement='warm restart to first authenticated API success',seconds=time.monotonic()-t,result='PASS' if p['exit_status']==0 else 'BLOCKED',cache='existing daemon data and image cache retained'))
(root/'results/measurements/daemon-readiness.json').write_text(json.dumps(rows,indent=2)+'\n');print(rows[-1])
