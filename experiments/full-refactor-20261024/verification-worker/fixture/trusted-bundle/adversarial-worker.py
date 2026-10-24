import ctypes
import errno
import fcntl
import json
import os
import pathlib
import stat
import time

TARGET_DIRS = [
    "/home/jackin-test/landlock-probe",
    "/opt/landlock-probe",
    "/var/tmp/landlock-probe",
    "/run/landlock-probe",
    "/work/landlock-probe",
    "/sandbox/landlock-probe",
    "/usr/local/share/landlock-probe",
]
DENIAL_ERRNOS = {errno.EACCES, errno.EPERM, errno.EROFS}
OPERATIONS = ("create", "mkdir", "write-existing", "truncate-existing", "rename-over-existing", "chmod-existing", "unlink-existing", "hardlink-existing")


def writable_regular_fds():
    rows, outside = [], []
    for entry in pathlib.Path("/proc/self/fd").iterdir():
        try:
            fd = int(entry.name)
            if fd <= 2:
                continue
            st = os.fstat(fd)
            if not stat.S_ISREG(st.st_mode):
                continue
            flags = fcntl.fcntl(fd, fcntl.F_GETFL)
            if flags & os.O_ACCMODE == os.O_RDONLY:
                continue
            target = os.readlink(entry)
            in_tmpfs = target == "/tmp" or target.startswith("/tmp/") or target == "/build" or target.startswith("/build/")
            row = {"fd": fd, "writable_regular": True, "path_class": "tmp_or_build" if in_tmpfs else "outside_tmpfs"}
            rows.append(row)
            if not in_tmpfs:
                outside.append(row)
        except (OSError, ValueError):
            continue
    return {"writable_regular_fds": rows, "outside_tmpfs_writable_regular_fds": outside}


def run_operation(path, operation):
    path = pathlib.Path(path)
    try:
        if operation == "create":
            with (path / "created-by-agent").open("xb") as stream:
                stream.write(b"probe")
        elif operation == "mkdir":
            (path / "dir-by-agent").mkdir()
        elif operation == "write-existing":
            with (path / "write-canary").open("r+b") as stream:
                stream.write(b"probe")
        elif operation == "truncate-existing":
            with (path / "truncate-canary").open("wb") as stream:
                stream.write(b"probe")
        elif operation == "rename-over-existing":
            os.replace(path / "rename-source", path / "rename-target")
        elif operation == "chmod-existing":
            os.chmod(path / "chmod-canary", 0o600)
        elif operation == "unlink-existing":
            os.unlink(path / "unlink-canary")
        elif operation == "hardlink-existing":
            os.link(path / "hardlink-source", path / "hardlink-by-agent")
        else:
            raise ValueError(operation)
        # No destructive result is retained. A successful operation is still
        # an immediate, recorded boundary failure.
        if operation == "create":
            (path / "created-by-agent").unlink(missing_ok=True)
        elif operation == "mkdir":
            (path / "dir-by-agent").rmdir()
        elif operation == "hardlink-existing":
            (path / "hardlink-by-agent").unlink(missing_ok=True)
        return {"denied": False, "errno": None}
    except OSError as error:
        return {"denied": error.errno in DENIAL_ERRNOS, "errno": error.errno}


def landlock_abi():
    libc = ctypes.CDLL(None, use_errno=True)
    result = libc.syscall(444, ctypes.c_void_p(), 0, 1)
    return result if result >= 0 else None


def process_state():
    keep = {"Uid", "Gid", "Groups", "CapEff", "CapBnd", "NoNewPrivs", "Seccomp", "Seccomp_filters", "PPid"}
    fields = {}
    for line in pathlib.Path("/proc/self/status").read_text().splitlines():
        key, sep, value = line.partition(":")
        if sep and key in keep:
            fields[key] = value.strip()
    ancestors, pid = [], os.getpid()
    for _ in range(5):
        try:
            content = pathlib.Path(f"/proc/{pid}/status").read_text()
            parent = next((int(line.split()[1]) for line in content.splitlines() if line.startswith("PPid:")), 0)
            comm = pathlib.Path(f"/proc/{pid}/comm").read_text().strip()
        except (OSError, ValueError):
            break
        ancestors.append({"pid": pid, "comm": comm})
        if parent <= 0 or parent == pid:
            break
        pid = parent
    return {"uid": os.getuid(), "euid": os.geteuid(), "gid": os.getgid(), "egid": os.getegid(), "status": fields, "ancestry": ancestors, "landlock_kernel_abi": landlock_abi()}


def first_violation(report, where, operation, result):
    if result.get("denied"):
        return False
    report["first_violation"] = {"where": where, "operation": operation, "errno": result.get("errno")}
    report["boundary_summary"] = {"all_outside_denied": False, "stopped_after_first_success": True}
    print(json.dumps(report, sort_keys=True))
    raise SystemExit(10)


def fork_child_checks(report):
    read_end, write_end = os.pipe()
    pid = os.fork()
    if pid == 0:
        os.close(read_end)
        violation = None
        for directory in TARGET_DIRS:
            for op in OPERATIONS:
                result = run_operation(directory, op)
                if not result["denied"]:
                    violation = {"where": directory, "operation": op, "errno": result.get("errno")}
                    break
            if violation:
                break
        os.write(write_end, json.dumps({"violation": violation}).encode())
        os.close(write_end)
        os._exit(0)
    os.close(write_end)
    deadline = time.monotonic() + 5
    status = None
    finished = 0
    while time.monotonic() < deadline:
        finished, status = os.waitpid(pid, os.WNOHANG)
        if finished:
            break
        time.sleep(0.02)
    if not finished:
        os.kill(pid, 9)
        os.waitpid(pid, 0)
        raise RuntimeError("forked adversarial child exceeded the 5 second bound")
    data = bytearray()
    while True:
        chunk = os.read(read_end, 4096)
        if not chunk:
            break
        data.extend(chunk)
    os.close(read_end)
    observed = json.loads(data)
    report["fork_child"] = {"pid": pid, "wait_status": status, **observed}
    if observed["violation"]:
        report["first_violation"] = {"process": "fork-child", **observed["violation"]}
        report["boundary_summary"] = {"all_outside_denied": False, "stopped_after_first_success": True}
        print(json.dumps(report, sort_keys=True))
        raise SystemExit(10)


report = {"process": process_state(), "fd_audit": writable_regular_fds(), "parent_operations": {}, "proc_root_aliases": {}, "tmp_symlink_aliases": {}, "dotdot_aliases": {}}
if report["fd_audit"]["outside_tmpfs_writable_regular_fds"]:
    report["boundary_summary"] = {"no_outside_tmpfs_writable_regular_fds": False, "stopped_after_first_violation": True}
    print(json.dumps(report, sort_keys=True))
    raise SystemExit(10)

for directory in TARGET_DIRS:
    for op in OPERATIONS:
        result = run_operation(directory, op)
        report["parent_operations"][f"{directory}:{op}"] = result
        first_violation(report, directory, op, result)

# Follow /proc/self/root and symlink paths that begin inside both writable tmpfs.
for index, directory in enumerate(TARGET_DIRS):
    result = run_operation(f"/proc/self/root{directory}", "create")
    report["proc_root_aliases"][directory] = result
    first_violation(report, f"/proc/self/root{directory}", "create", result)

    alias = f"/tmp/jfr-landlock-alias-{index}"
    os.symlink(directory, alias)
    result = run_operation(alias, "write-existing")
    report["tmp_symlink_aliases"][directory] = result
    os.unlink(alias)
    first_violation(report, alias, "write-existing", result)

    # Retarget one alias to a second DAC-writable directory and try again.
    if index == 0:
        retarget = "/tmp/jfr-landlock-retarget"
        os.symlink(directory, retarget)
        os.unlink(retarget)
        os.symlink(TARGET_DIRS[1], retarget)
        result = run_operation(retarget, "write-existing")
        report["retargeted_symlink"] = result
        os.unlink(retarget)
        first_violation(report, retarget, "write-existing", result)

    for base in ("/tmp", "/build"):
        traversal = f"{base}/../..{directory}"
        result = run_operation(traversal, "create")
        report["dotdot_aliases"][f"{base}->{directory}"] = result
        first_violation(report, traversal, "create", result)

# Docker supplies /dev/shm as a DAC-writable tmpfs, but it is outside the grants.
result = run_operation("/dev/shm", "create")
report["dev_shm_create"] = result
first_violation(report, "/dev/shm", "create", result)

# No protected control sockets are enumerated or read; test only path admission.
try:
    os.scandir("/.openshell/channel").close()
    control_denied = False
except OSError as error:
    control_denied = error.errno in DENIAL_ERRNOS
report["control_mount_directory_denied"] = control_denied
if not control_denied:
    report["first_violation"] = {"where": "/.openshell/channel", "operation": "scandir"}
    report["boundary_summary"] = {"all_outside_denied": False, "stopped_after_first_success": True}
    print(json.dumps(report, sort_keys=True))
    raise SystemExit(10)

fork_child_checks(report)

report["tmp_positive"] = pathlib.Path("/tmp/jfr-landlock-positive").write_bytes(b"ok") == 2
pathlib.Path("/tmp/jfr-landlock-positive").unlink()
report["build_positive"] = pathlib.Path("/build/jfr-landlock-positive").write_bytes(b"ok") == 2
pathlib.Path("/build/jfr-landlock-positive").unlink()

import subprocess
helper = subprocess.run(["/usr/local/bin/jfr-setuid-probe"], capture_output=True, text=True, timeout=3)
report["setuid_helper"] = {"exit_code": helper.returncode, "stdout": helper.stdout.strip(), "stderr": helper.stderr.strip()}
report["boundary_summary"] = {
    "all_outside_denied": True,
    "tmp_and_build_writable": report["tmp_positive"] and report["build_positive"],
    "no_outside_tmpfs_writable_regular_fds": not report["fd_audit"]["outside_tmpfs_writable_regular_fds"],
    "setuid_not_elevated": helper.returncode == 0 and "uid=1000 euid=1000 setuid_root_rc=-1 setuid_root_errno=1" in helper.stdout,
    "identity_nonroot": report["process"]["uid"] == 1000 and report["process"]["euid"] == 1000,
    "nnp_enabled": report["process"]["status"].get("NoNewPrivs") == "1",
    "capabilities_zero": report["process"]["status"].get("CapEff") == "0000000000000000" and report["process"]["status"].get("CapBnd") == "0000000000000000",
    "landlock_kernel_abi_detected": isinstance(report["process"]["landlock_kernel_abi"], int) and report["process"]["landlock_kernel_abi"] >= 1,
    "control_mount_directory_denied": report["control_mount_directory_denied"],
    "fork_child_stayed_confined": report["fork_child"]["violation"] is None,
}
print(json.dumps(report, sort_keys=True))
