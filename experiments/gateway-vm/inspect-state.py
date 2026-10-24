#!/usr/bin/env python3
"""Print resource ownership facts for the disposable VM profile."""

import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / "experiments/gateway-vm/state/runtime"
SANDBOX_ID = "c87a19b1-d941-4e22-a9cc-68d00be18b0f"
SANDBOX_DIR = STATE / "sandboxes" / SANDBOX_ID

processes = subprocess.run(
    ["ps", "-axo", "pid=,command="], check=True, capture_output=True, text=True
).stdout.splitlines()
matches = []
for line in processes:
    parts = line.strip().split(maxsplit=1)
    if not parts or int(parts[0]) in {os.getpid(), os.getppid()}:
        continue
    if SANDBOX_ID in line:
        matches.append(line.strip())

cache_disks = []
images = STATE / "images"
if images.exists():
    for disk in images.glob("*/rootfs.ext4"):
        stat = disk.stat()
        cache_disks.append(
            {"path": str(disk.relative_to(ROOT)), "logical_bytes": stat.st_size}
        )

result = {
    "sandbox_id": SANDBOX_ID,
    "sandbox_state_exists": SANDBOX_DIR.exists(),
    "overlay_exists": (SANDBOX_DIR / "overlay.ext4").exists(),
    "live_process_matches": matches,
    "prepared_and_bootstrap_image_disks": cache_disks,
    "driver_socket_exists": (STATE / "run/compute-driver.sock").exists(),
}
print(json.dumps(result, indent=2, sort_keys=True))
