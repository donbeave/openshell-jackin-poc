#!/usr/bin/env python3
"""Record one disposable experiment command. Never pass real secrets."""
import argparse
import datetime
import json
import pathlib
import subprocess
import time

p = argparse.ArgumentParser()
p.add_argument("name")
p.add_argument("--timeout", type=int, default=180)
p.add_argument("command", nargs=argparse.REMAINDER)
a = p.parse_args()
command = a.command[1:] if a.command[:1] == ["--"] else a.command
root = pathlib.Path(__file__).resolve().parents[1]
out = root / "results" / a.name
out.parent.mkdir(parents=True, exist_ok=True)
start = time.monotonic()
result = {"command": command, "utc": datetime.datetime.now(datetime.timezone.utc).isoformat()}
try:
    run = subprocess.run(command, capture_output=True, timeout=a.timeout)
    result.update(exit_status=run.returncode, stdout=run.stdout.decode(errors="replace"), stderr=run.stderr.decode(errors="replace"))
except subprocess.TimeoutExpired as e:
    result.update(exit_status=124, stdout=(e.stdout or b"").decode(errors="replace"), stderr=(e.stderr or b"").decode(errors="replace"), timeout=True)
except OSError as e:
    result.update(exit_status=127, stdout="", stderr=str(e))
result["seconds"] = time.monotonic() - start
out.with_suffix(".json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result))
raise SystemExit(result["exit_status"])
