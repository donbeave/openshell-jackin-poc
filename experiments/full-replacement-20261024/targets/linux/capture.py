#!/usr/bin/env python3
"""Record one experiment command with stdout and stderr kept separate."""
import json, os, pathlib, re, subprocess, sys, time
root=pathlib.Path(__file__).resolve().parents[4]
out=pathlib.Path(os.environ.get('JFR_CAPTURE_DIR',str(root/'results/full-replacement-20261024/targets/linux/commands')))
out.mkdir(parents=True,exist_ok=True)
if len(sys.argv)<3 or sys.argv[2] != '--':
    raise SystemExit('usage: capture.py LABEL -- COMMAND [ARG ...]')
label=sys.argv[1]
if not re.fullmatch(r'[a-z0-9-]+',label): raise SystemExit('invalid label')
argv=sys.argv[3:]
start=time.monotonic()
p=subprocess.run(argv,text=True,capture_output=True)
record={'argv':argv,'exit_status':p.returncode,'wall_seconds':round(time.monotonic()-start,3),'stdout':p.stdout,'stderr':p.stderr}
# Gateway token-reference IDs are identifiers, never useful reproduction evidence.
for key in ('stdout','stderr'):
    record[key]=re.sub(r'("internal\.openshell\.ai/gateway-token-id"\s*:\s*")[0-9a-f-]{36}("\s*)',r'\1[REDACTED-ID]\2',record[key],flags=re.I)
(out/f'{label}.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({'label':label,'exit_status':p.returncode,'wall_seconds':record['wall_seconds'],'stdout_bytes':len(p.stdout),'stderr_bytes':len(p.stderr)}))
raise SystemExit(p.returncode)
