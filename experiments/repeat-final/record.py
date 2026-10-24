#!/usr/bin/env python3
"""Record a command run in the independent final-path repeat."""
import argparse, datetime, json, pathlib, subprocess, time
p=argparse.ArgumentParser();p.add_argument('name');p.add_argument('command',nargs=argparse.REMAINDER);a=p.parse_args()
command=a.command[1:] if a.command[:1]==['--'] else a.command
root=pathlib.Path(__file__).resolve().parents[2]
out=root/'results/repeat-final';out.mkdir(parents=True,exist_ok=True)
start=time.monotonic();result={'command':command,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
try:
 r=subprocess.run(command,capture_output=True,timeout=900)
 result.update(exit_status=r.returncode,stdout=r.stdout.decode(errors='replace'),stderr=r.stderr.decode(errors='replace'))
except subprocess.TimeoutExpired as e:
 result.update(exit_status=124,stdout=(e.stdout or b'').decode(errors='replace'),stderr=(e.stderr or b'').decode(errors='replace'),timeout=True)
except OSError as e:result.update(exit_status=127,stdout='',stderr=str(e))
result['seconds']=time.monotonic()-start
(out/(a.name+'.json')).write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
raise SystemExit(result['exit_status'])
