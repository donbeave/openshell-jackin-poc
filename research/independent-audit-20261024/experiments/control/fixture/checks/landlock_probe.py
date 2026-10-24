from pathlib import Path

path = Path("/var/tmp")
print("exists", path.exists(), "symlink", path.is_symlink(), "mode", oct(path.stat().st_mode & 0o777))
probe = path / "jrr24-landlock-probe"
try:
    probe.write_text("unexpected")
    print("unlisted_write", "allowed")
    probe.unlink()
except Exception as error:
    print("unlisted_write", type(error).__name__, str(error))
