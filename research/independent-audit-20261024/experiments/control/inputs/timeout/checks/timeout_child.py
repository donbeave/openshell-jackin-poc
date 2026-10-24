from pathlib import Path
import subprocess
import sys
import time

subprocess.Popen([
    sys.executable,
    "-c",
    "import time; from pathlib import Path; time.sleep(8); Path('/tmp/jackin-worker-grandchild-marker').write_text('escaped')",
])
time.sleep(30)
