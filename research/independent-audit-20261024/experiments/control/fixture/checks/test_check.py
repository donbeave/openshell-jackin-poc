from pathlib import Path
import runpy

source = Path("/workspace/candidate.py")
assert source.read_text() == 'def value():\n    return "approved"\n'
result = runpy.run_path(str(source))
assert result["value"]() == "approved"
for path in (source, Path("/jackin/checks/test_check.py"), Path("/etc/hosts")):
    try:
        path.write_text("tamper")
    except (PermissionError, OSError):
        pass
    else:
        raise AssertionError(f"write unexpectedly allowed: {path}")
Path("/tmp/jackin-worker-scratch").write_text("scratch")
Path("/build/jackin-worker-scratch").write_text("scratch")
print("worker-policy-pass")
