"""A single SDK lifecycle probe against the isolated mTLS gateway."""
from pathlib import Path
from dataclasses import asdict, is_dataclass
import json
import sys
import time
from openshell import SandboxClient, TlsConfig

root = Path(__file__).resolve().parents[1]
certs = root / "experiments/gateway/certs"
tls = TlsConfig(ca_path=certs / "ca.crt", cert_path=certs / "client/tls.crt", key_path=certs / "client/tls.key")
events = []
def call(name, f):
    started = time.monotonic()
    try:
        value = f()
        events.append(dict(operation=name, result="PASS", seconds=time.monotonic()-started, value=str(value)))
        return value
    except Exception as e:
        events.append(dict(operation=name, result="FAIL", seconds=time.monotonic()-started, error=str(e)))
        raise

name = sys.argv[1]
try:
    with SandboxClient("127.0.0.1:18770", tls=tls, timeout=60) as client:
        call("health", client.health)
        call("list", lambda: list(client.list(workspace="default")))
        call("get", lambda: client.get(name, workspace="default"))
        result = call("exec", lambda: client.exec(name, ["sh", "-c", "printf sdk-stdout; printf sdk-stderr >&2; exit 7"], workspace="default"))
        assert result.exit_code == 7, result
        call("stop", lambda: client.stop(name, workspace="default"))
        call("start", lambda: client.start(name, workspace="default"))
        call("wait_ready", lambda: client.wait_ready(name, workspace="default", timeout_seconds=180))
finally:
    (root / "results/sdk-probe.json").write_text(json.dumps(events, indent=2)+"\n")
