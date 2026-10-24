#!/usr/bin/env python3
"""Build and time pinned OpenShell agent fixture images."""
import datetime
import json
import pathlib
import subprocess
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results" / "image"
RESULTS.mkdir(parents=True, exist_ok=True)
DOCKERFILE = ROOT / "experiments" / "image" / "Dockerfile"
CONTEXT = ROOT / "experiments" / "rust-project"
runs = [
    ("warm", "2.1.310", []),
    ("forced", "2.1.310", ["--no-cache"]),
    ("agent-version-change", "2.1.309", []),
]
records = []
for label, version, extra in runs:
    command = ["docker", "buildx", "build", "--load", "--progress=plain", *extra,
               "--build-arg", f"CLAUDE_VERSION={version}", "-t",
               f"ojp-20261024-agent:{version}-tools", "-f", str(DOCKERFILE), str(CONTEXT)]
    start = time.monotonic()
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    records.append({"label": label, "command": command, "exit_status": result.returncode,
                    "seconds": round(time.monotonic() - start, 3),
                    "stdout": result.stdout, "stderr": result.stderr,
                    "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat()})
    (RESULTS / f"{label}-{version}.json").write_text(json.dumps(records[-1], indent=2))
    if result.returncode:
        print(json.dumps({"label": label, "exit_status": result.returncode,
                          "seconds": records[-1]["seconds"], "stderr_tail": result.stderr[-2000:]}, indent=2))
        break
    inspect = subprocess.run(["docker", "image", "inspect", f"ojp-20261024-agent:{version}-tools",
                              "--format", "{{.Id}} {{.RepoDigests}} {{.Os}}/{{.Architecture}}"],
                             capture_output=True, text=True, check=False)
    records[-1]["image_inspect_exit_status"] = inspect.returncode
    records[-1]["image_identity"] = inspect.stdout.strip()
    (RESULTS / f"{label}-{version}.json").write_text(json.dumps(records[-1], indent=2))
    print(json.dumps({"label": label, "version": version, "exit_status": result.returncode,
                      "seconds": records[-1]["seconds"], "image": inspect.stdout.strip()}, indent=2))
(RESULTS / "build-matrix.json").write_text(json.dumps(records, indent=2))
