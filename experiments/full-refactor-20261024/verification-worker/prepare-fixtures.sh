#!/bin/sh
set -eu
BASE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$BASE/../../.." && pwd)
OUT="$BASE/fixture"
SRC="$REPO_ROOT/results/full-replacement-20261024/docker/host-source"
mkdir -p "$OUT"
if [ -e "$OUT/candidate" ] || [ -e "$OUT/trusted-bundle" ]; then
    echo "refusing to overwrite fixture paths" >&2
    exit 2
fi
git clone --no-hardlinks --no-checkout "$SRC" "$OUT/candidate"
git -C "$OUT/candidate" checkout --detach HEAD
test -z "$(git -C "$OUT/candidate" status --porcelain)"
mkdir "$OUT/trusted-bundle"
cat > "$OUT/trusted-bundle/verify.py" <<'PY'
import hashlib
import json
import os
import pathlib
import socket
import sys

mode = sys.argv[1]
repo = pathlib.Path(sys.argv[2])
report = {"mode": mode, "uid": os.getuid(), "gid": os.getgid()}

if mode == "success":
    cargo = (repo / "Cargo.toml").read_bytes()
    rust = (repo / "src/lib.rs").read_bytes()
    assert b"runtime-probe" in cargo
    assert b"hello from runtime-probe" in rust
    report["candidate_sha256"] = hashlib.sha256(rust).hexdigest()
    checks = {}
    for path in (repo / "src/lib.rs", pathlib.Path("/jackin/checks/verify.py")):
        try:
            path.write_bytes(b"must not write")
            checks[str(path)] = "UNEXPECTED_WRITE_SUCCESS"
        except OSError as error:
            checks[str(path)] = {"denied": True, "errno": error.errno}
    try:
        pathlib.Path("/etc/jfr-worker-probe").write_text("no")
        checks["rootfs"] = "UNEXPECTED_WRITE_SUCCESS"
    except OSError as error:
        checks["rootfs"] = {"denied": True, "errno": error.errno}
    checks["tmp_write"] = pathlib.Path("/tmp/worker.tmp").write_text("ok") == 2
    checks["build_write"] = pathlib.Path("/build/worker.tmp").write_text("ok") == 2
    executable = pathlib.Path("/tmp/noexec-probe")
    executable.write_text("#!/bin/sh\nexit 0\n")
    executable.chmod(0o755)
    try:
        os.execve(str(executable), [str(executable)], os.environ.copy())
    except OSError as error:
        checks["tmp_noexec"] = {"denied": True, "errno": error.errno}
    report["filesystem_checks"] = checks
    sock = socket.socket()
    sock.settimeout(0.5)
    try:
        sock.connect(("192.0.2.1", 443))
        report["network"] = "UNEXPECTED_CONNECT_SUCCESS"
    except OSError as error:
        report["network"] = {"denied_or_unroutable": True, "errno": error.errno}
    report["cgroup"] = {}
    for name in ("cpu.max", "memory.max", "pids.max"):
        path = pathlib.Path("/sys/fs/cgroup") / name
        try:
            report["cgroup"][name] = path.read_text().strip()
        except OSError as error:
            report["cgroup"][name] = {"error": str(error)}
    status = pathlib.Path("/proc/self/status").read_text()
    report["status_security"] = {line.split(":",1)[0]: line.split(":",1)[1].strip() for line in status.splitlines() if line.startswith(("CapEff:", "CapBnd:", "NoNewPrivs:"))}
    print(json.dumps(report, sort_keys=True))
elif mode == "fail":
    print("intentional verification failure", file=sys.stderr)
    print("failure-marker")
    sys.exit(7)
elif mode == "missing-runtime":
    print("placeholder")
elif mode == "abnormal-child":
    os.kill(os.getpid(), 6)
elif mode == "timeout-child":
    import subprocess, time
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(300)"])
    pathlib.Path("/tmp/timeout-pids").write_text(f"{os.getpid()} {child.pid}\n")
    time.sleep(300)
elif mode == "output":
    sys.stdout.write("O" * (128 * 1024))
    sys.stderr.write("E" * (128 * 1024))
    sys.exit(0)
elif mode == "tmpfs-fill":
    target = pathlib.Path(sys.argv[3])
    allocated = 0
    try:
        with target.open("wb") as stream:
            while allocated < 300 * 1024 * 1024:
                stream.write(b"x" * (1024 * 1024))
                stream.flush()
                allocated += 1024 * 1024
    except OSError as error:
        report.update({"allocated_bytes": allocated, "errno": error.errno, "expected_enospc": error.errno == 28})
        print(json.dumps(report, sort_keys=True))
        sys.exit(0 if error.errno == 28 else 1)
    print(json.dumps({"allocated_bytes": allocated, "unexpected_no_exhaustion": True}))
    sys.exit(1)
elif mode == "pids-fill":
    import subprocess
    children = []
    failures = []
    for _ in range(100):
        try:
            children.append(subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"]))
        except OSError as error:
            failures.append({"errno": error.errno, "error": str(error)})
            break
    for child in children:
        child.terminate()
    for child in children:
        child.wait()
    report.update({"children_created": len(children), "spawn_denials": failures, "pids_max": pathlib.Path("/sys/fs/cgroup/pids.max").read_text().strip()})
    print(json.dumps(report, sort_keys=True))
    sys.exit(0 if failures else 1)
PY
chmod 0755 "$OUT/candidate" "$OUT/candidate/src" "$OUT/trusted-bundle"
find "$OUT/candidate" -type f -exec chmod 0644 {} \;
chmod 0444 "$OUT/trusted-bundle/verify.py"
git -C "$OUT/candidate" rev-parse HEAD > "$OUT/candidate-commit.txt"
git -C "$OUT/candidate" rev-parse HEAD^{tree} > "$OUT/candidate-tree.txt"
shasum -a 256 "$OUT/trusted-bundle/verify.py" | awk '{print $1}' > "$OUT/trusted-bundle-sha256.txt"
printf 'candidate_commit=%s\ncandidate_tree=%s\nbundle_sha256=%s\n' \
  "$(cat "$OUT/candidate-commit.txt")" "$(cat "$OUT/candidate-tree.txt")" "$(cat "$OUT/trusted-bundle-sha256.txt")"
