import json, os, pathlib, pty, select, signal, time
root=pathlib.Path(__file__).resolve().parents[2]
events=[]
for n in range(2):
 pid,fd=pty.fork()
 if pid==0:
  os.execvp('sh',['sh','experiments/os.sh','sandbox','connect','ojp-20261024-repeat'])
 data=bytearray(); start=time.monotonic(); sent=False; detached=False; sent_escape=False
 while time.monotonic()-start<20:
  ready,_,_=select.select([fd],[],[],0.25)
  if not ready:
   if not sent and time.monotonic()-start>3:os.write(fd,f'echo OJP_RECONNECT_{n}\n'.encode());sent=True
   continue
  try: b=os.read(fd,65536)
  except OSError:break
  if not b:break
  data.extend(b)
  if sent and not sent_escape and time.monotonic()-start>7:
   # OpenShell connect escape sequence: Ctrl-P then Ctrl-Q.
   os.write(fd,b'\x10');time.sleep(0.2);os.write(fd,b'\x11');sent_escape=True
 _,status=os.waitpid(pid,os.WNOHANG)
 if status==0:
  os.kill(pid,signal.SIGTERM);_,status=os.waitpid(pid,0)
 events.append({'attempt':n+1,'detached':detached,'exit_status':os.waitstatus_to_exitcode(status),'seconds':time.monotonic()-start,'output':data.decode(errors='replace')})
(root/'results/repeat/connect.json').write_text(json.dumps(events,indent=2)+'\n')
print(json.dumps(events,indent=2))
