#!/usr/bin/env python3
"""Observe macOS vnode notifications while a sandbox writes the mounted file."""
import json, os, pathlib, select, subprocess, sys, time
ROOT = pathlib.Path(__file__).resolve().parents[3]
FIX = ROOT / "results/full-replacement-20261024/workspace/jfr-20261024-ws"
FILE = FIX / "host-source/src/lib.rs"
CREATED = FILE.parent / "agent-dirwatch-created-official.txt"
CLIENT = ROOT / "experiments/full-replacement-20261024/gateway-b/client.sh"
WORKSPACE = "jfr-ws-20261024"
SANDBOX = sys.argv[1] if len(sys.argv) > 1 else "jfrws24-official"

def watch_child(path, seconds=6):
    if not hasattr(select, "kqueue"):
        print(json.dumps({"watcher":"kqueue unavailable","result":"NOT TESTED"}), flush=True)
        return 0
    flags = getattr(os, "O_EVTONLY", os.O_RDONLY)
    fd = os.open(path, flags)
    q = select.kqueue()
    mask = select.KQ_NOTE_WRITE | select.KQ_NOTE_EXTEND | select.KQ_NOTE_ATTRIB | select.KQ_NOTE_RENAME | select.KQ_NOTE_DELETE
    registration = select.kevent(fd, filter=select.KQ_FILTER_VNODE,
        flags=select.KQ_EV_ADD | select.KQ_EV_CLEAR, fflags=mask)
    q.control([registration], 0, 0)
    print(json.dumps({"ready":True,"watched_path":str(path),"watcher":"macOS kqueue vnode"}), flush=True)
    events = q.control(None, 8, seconds)
    names=[]
    bits=[("WRITE",select.KQ_NOTE_WRITE),("EXTEND",select.KQ_NOTE_EXTEND),("ATTRIB",select.KQ_NOTE_ATTRIB),("RENAME",select.KQ_NOTE_RENAME),("DELETE",select.KQ_NOTE_DELETE)]
    for event in events:
        names.extend(name for name,bit in bits if event.fflags & bit)
    print(json.dumps({"events":names,"event_count":len(events)}), flush=True)
    q.close(); os.close(fd)
    return 0

if len(sys.argv)>1 and sys.argv[1]=="watch":
    raise SystemExit(watch_child(pathlib.Path(sys.argv[2]),float(sys.argv[3])))

if CREATED.exists(): CREATED.unlink()
watcher = subprocess.Popen([sys.executable,str(pathlib.Path(__file__).resolve()),"watch",str(FILE.parent),"6"], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
ready_line = watcher.stdout.readline()
ready = json.loads(ready_line) if ready_line else {"ready":False}
command = ["sh",str(CLIENT),"--workspace",WORKSPACE,"sandbox","exec","--no-login-shell","--no-tty",SANDBOX,"--","/bin/sh","-c",'printf "agent-dirwatch-official-v1\\n" > /workspace/jfr-20261024-ws/host-source/src/agent-dirwatch-created-official.txt']
run = subprocess.run(command,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
remaining, stderr = watcher.communicate(timeout=8)
event_record = json.loads(remaining.splitlines()[-1]) if remaining.strip() else {"events":[]}
record={"fixture_id":"jfr-20261024-ws","classification":"OpenShell sandbox host-checkout watcher probe","watch_setup":ready,"watch_event":event_record,"sandbox_command":command,"exit_status":run.returncode,"stdout":run.stdout,"stderr":run.stderr,"watcher_stderr":stderr,"host_file_after":FILE.read_text(),"host_created_file":CREATED.read_text() if CREATED.exists() else None,"created_path_was_absent_before_probe":True}
record["result"]="PASS" if run.returncode==0 and event_record.get("event_count",0)>0 else "FAIL"
(FIX/"runtime-filewatch.json").write_text(json.dumps(record,indent=2)+"\n")
print(json.dumps(record,indent=2))
