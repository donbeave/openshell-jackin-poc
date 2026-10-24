#!/usr/bin/env python3
"""Guarded OpenShell API restoration for the three original stopped sandboxes.

This script uses the installed gateway's mTLS identity in-place. It does not
read or write the global CLI registration and never controls Docker directly.
It is intentionally inert without --approved.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from openshell import SandboxClient, TlsConfig
from openshell._proto import openshell_pb2

ENDPOINT = "localhost:17670"
WORKSPACE = "default"
TLS = TlsConfig(
    ca_path=Path("/opt/homebrew/var/openshell/tls/ca.crt"),
    cert_path=Path("/opt/homebrew/var/openshell/tls/client/tls.crt"),
    key_path=Path("/opt/homebrew/var/openshell/tls/client/tls.key"),
)
TARGETS = (
    ("coding-agents", "00000000-0000-4000-8000-000000000001"),
    ("preview-docker", "00000000-0000-4000-8000-000000000002"),
    ("preview-openrouter", "00000000-0000-4000-8000-000000000003"),
)
OUTPUT = Path("results/collateral/restore-originals-execution.json")


def enum_name(value: int) -> str:
    return openshell_pb2.SandboxPhase.Name(value)


def state(ref) -> dict:
    return {
        "id": ref.id,
        "name": ref.name,
        "workspace": ref.workspace,
        "phase": enum_name(ref.status.phase),
        "conditions": [
            {"type": c.type, "status": c.status, "reason": c.reason, "message": c.message}
            for c in ref.status.conditions
        ],
    }


def record_step(events: list[dict], action: str, name: str, fn) -> object:
    entry = {
        "at_utc": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "name": name,
    }
    try:
        result = fn()
    except Exception as exc:
        entry.update({"result": "FAIL", "error_type": type(exc).__name__, "error": str(exc)})
        events.append(entry)
        raise
    entry["result"] = "PASS"
    if result is not None:
        entry["state"] = state(result)
    events.append(entry)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--approved",
        action="store_true",
        help="explicitly authorize stopping Error sandboxes then starting these exact IDs",
    )
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()

    if not args.approved:
        print("REFUSED: no API calls made; pass --approved only after explicit user approval.", file=sys.stderr)
        return 2
    if args.output.exists():
        print(f"REFUSED: evidence output already exists: {args.output}", file=sys.stderr)
        return 2
    for path in (TLS.ca_path, TLS.cert_path, TLS.key_path):
        if not path.is_file():
            print(f"REFUSED: required installed gateway TLS file is missing: {path}", file=sys.stderr)
            return 2

    events: list[dict] = []
    result = {
        "release": "OpenShell 0.1.5",
        "gateway_endpoint": "https://localhost:17670",
        "workspace": WORKSPACE,
        "tls_verification": "enabled; installed gateway CA and mTLS client identity used directly",
        "docker_cli_or_socket_used": False,
        "targets": [{"name": name, "id": sid} for name, sid in TARGETS],
        "events": events,
        "final": [],
    }
    client = SandboxClient(ENDPOINT, tls=TLS, timeout=30)
    try:
        # Read-only preflight: require all three expected identities and the
        # exact Error/ControlSupervisorExited condition before any mutation.
        current = {}
        for name, expected_id in TARGETS:
            ref = record_step(events, "preflight_get", name, lambda n=name: client.get(n, workspace=WORKSPACE))
            if ref.id != expected_id:
                raise RuntimeError(f"identity mismatch for {name}; no restoration action taken")
            if enum_name(ref.status.phase) != "SANDBOX_PHASE_ERROR":
                raise RuntimeError(f"unexpected phase for {name}; no restoration action taken")
            if not any(c.reason == "ControlSupervisorExited" for c in ref.status.conditions):
                raise RuntimeError(f"expected supervisor-exit condition absent for {name}; no restoration action taken")
            current[name] = ref

        for name, expected_id in TARGETS:
            before_stop = record_step(events, "pre_stop_get", name, lambda n=name: client.get(n, workspace=WORKSPACE))
            if before_stop.id != expected_id or enum_name(before_stop.status.phase) != "SANDBOX_PHASE_ERROR":
                raise RuntimeError(f"state changed before stop for {name}; aborting")

            record_step(events, "openshell_api_stop", name, lambda n=name: client.stop(n, workspace=WORKSPACE))
            stopped = record_step(
                events,
                "wait_stopped",
                name,
                lambda n=name: client.wait_stopped(n, workspace=WORKSPACE, timeout_seconds=300),
            )
            if stopped.id != expected_id:
                raise RuntimeError(f"identity changed after stop for {name}; aborting")

            before_start = record_step(events, "pre_start_get", name, lambda n=name: client.get(n, workspace=WORKSPACE))
            if before_start.id != expected_id or enum_name(before_start.status.phase) != "SANDBOX_PHASE_STOPPED":
                raise RuntimeError(f"state changed before start for {name}; aborting")

            record_step(events, "openshell_api_start", name, lambda n=name: client.start(n, workspace=WORKSPACE))
            ready = record_step(
                events,
                "wait_ready",
                name,
                lambda n=name: client.wait_ready(n, workspace=WORKSPACE, timeout_seconds=300),
            )
            if ready.id != expected_id or enum_name(ready.status.phase) != "SANDBOX_PHASE_READY":
                raise RuntimeError(f"identity or ready phase mismatch after start for {name}")

        for name, expected_id in TARGETS:
            final = record_step(events, "final_get", name, lambda n=name: client.get(n, workspace=WORKSPACE))
            if final.id != expected_id:
                raise RuntimeError(f"identity mismatch in final state for {name}")
            result["final"].append(state(final))
    except Exception as exc:
        result["result"] = "FAIL"
        result["error_type"] = type(exc).__name__
        result["error"] = str(exc)
    else:
        result["result"] = "PASS"
    finally:
        client.close()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result, indent=2))
    return 0 if result["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
