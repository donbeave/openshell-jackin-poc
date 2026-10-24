"""Interactive terminal input, resize, interrupt, disconnect and reconnect probe."""
import fcntl,json,os,pathlib,pty,select,signal,struct,subprocess,termios,time
root=pathlib.Path(__file__).resolve().parents[1]
name='ojp-20261024-basic'
events=[]
def session(command,steps):
 master,slave=pty.openpty()
 p=subprocess.Popen(command,stdin=slave,stdout=slave,stderr=slave,preexec_fn=lambda: (os.setsid(), fcntl.ioctl(0, termios.TIOCSCTTY, 0)),cwd=root)
 os.close(slave); output=bytearray()
 def read(seconds):
  end=time.monotonic()+seconds
  while time.monotonic()<end:
   ready,_,_=select.select([master],[],[],max(0,end-time.monotonic()))
   if ready:
    try: data=os.read(master,65536)
    except OSError:break
    if not data:break
    output.extend(data)
 read(2)
 for kind,value in steps:
  if kind=='input':os.write(master,value)
  if kind=='resize':
   fcntl.ioctl(master,termios.TIOCSWINSZ,struct.pack('HHHH',*value,0,0));os.killpg(p.pid,signal.SIGWINCH)
  read(1)
 if p.poll() is None:
  os.write(master,b'\x10\x11');read(1)
 if p.poll() is None:p.terminate()
 try:code=p.wait(timeout=5)
 except subprocess.TimeoutExpired:p.kill();code=p.wait()
 os.close(master)
 events.append(dict(command=command,steps=[(k,repr(v)) for k,v in steps],exit_status=code,output=output.decode(errors='replace')))

session(['sh','experiments/os.sh','sandbox','exec',name,'--tty','--no-login-shell','--','bash','--noprofile','--norc','-i'], [('input',b'echo OJP_INPUT_OK\n'),('resize',(33,101)),('input',b'stty size\n'),('input',b'sleep 30\n'),('input',b'\x03'),('input',b'echo OJP_INTERRUPT_OK\n'),('input',b'exit\n')])
for _ in range(2):
 session(['sh','experiments/os.sh','sandbox','connect',name],[('input',b'echo OJP_CONNECT_OK\n'),('input',b'\x10\x11')])
(root/'results/basic/terminal-controlling-tty.json').write_text(json.dumps(events,indent=2)+'\n')
for e in events:print(e)
