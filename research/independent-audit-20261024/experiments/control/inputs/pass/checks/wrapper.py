import os
import signal
import subprocess
import sys
import time

deadline = float(sys.argv[1])
argv = sys.argv[2:]
remaining = deadline - time.time()
if remaining <= 0:
    raise SystemExit(124)
try:
    child = subprocess.Popen(argv, start_new_session=True)
except OSError as error:
    print(error, file=sys.stderr)
    raise SystemExit(125)
try:
    code = child.wait(timeout=remaining)
except subprocess.TimeoutExpired:
    try:
        os.killpg(child.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    child.wait()
    raise SystemExit(124)
raise SystemExit(code)
