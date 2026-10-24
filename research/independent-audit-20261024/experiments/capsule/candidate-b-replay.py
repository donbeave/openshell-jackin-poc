#!/usr/bin/env python3
"""Replay bounded Candidate B sandbox test with ownership-bound cleanup."""
import json
import os
import pathlib
import subprocess
import sys
import time
import tomllib
import uuid

BASE = pathlib.Path(__file__).resolve().parent
CLIENT = BASE / "client.sh"
IMAGE = "alpine@sha256:2e0b81d60597f449baa56dc25d355367869d2dca4cd57e866f1e2b52af3eb55f"
RUN_ID = sys.argv[1] if len(sys.argv) > 1 else uuid.uuid4().hex[:15]
if not RUN_ID or len(RUN_ID) > 15 or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for c in RUN_ID):
    raise SystemExit("invalid run id")
AGENT = f"jba-{RUN_ID}"
SHELL = f"jbs-{RUN_ID}"
gateway_config = tomllib.loads((BASE / "gateway.toml").read_text())
gateway_settings = gateway_config["openshell"]["gateway"]
docker_settings = gateway_config["openshell"]["drivers"]["docker"]
TARGET = os.environ.get("TARGET_NAME", gateway_settings["name"])
ENDPOINT = os.environ.get("TARGET_ENDPOINT", "https://" + gateway_settings["bind_address"])
NAMESPACE = os.environ.get("SANDBOX_NAMESPACE", docker_settings["sandbox_label"])
GATEWAY_ID = gateway_config["openshell"]["gateway"]["gateway_jwt"]["gateway_id"]
if TARGET != gateway_settings["name"] or NAMESPACE != docker_settings["sandbox_label"]:
    raise SystemExit("target name or namespace does not match isolated gateway.toml")
OUT = BASE / "../../evidence/capsule" / f"replay-{RUN_ID}"
OUT.mkdir(parents=True, exist_ok=False)
RECEIPT = OUT / "ownership-receipt.json"
receipt = {
    "run_id": RUN_ID,
    "target": {"name": TARGET, "gateway_id": GATEWAY_ID, "endpoint": ENDPOINT, "workspace": "default"},
    "namespace": NAMESPACE,
    "image": IMAGE,
    "name_reuse_authority": "Unique run id; one script owner; no concurrent actor may create these names. OpenShell delete is name-based, not an atomic UUID precondition.",
    "sandboxes": [
        {"domain": "agent", "name": AGENT, "sandbox_id": None, "runtime_generation": None, "state": "intent-recorded"},
        {"domain": "generic-shell", "name": SHELL, "sandbox_id": None, "runtime_generation": None, "state": "intent-recorded"},
    ],
    "cleanup": {"delete_requests": [], "polls": [], "result": "pending"},
}


def save_receipt():
    RECEIPT.write_text(json.dumps(receipt, indent=2) + "\n")


def call(label, args, *, expected=(0,), input_bytes=None):
    result = subprocess.run([str(CLIENT), *args], input=input_bytes, capture_output=True)
    (OUT / f"{label}.stdout").write_bytes(result.stdout)
    (OUT / f"{label}.stderr").write_bytes(result.stderr)
    (OUT / f"{label}.exit").write_text(f"{result.returncode}\n")
    if result.returncode not in expected:
        raise RuntimeError(f"{label} returned {result.returncode}")
    return result


def cli_json(label, args):
    result = call(label, args)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{label} returned invalid JSON") from exc


def remember(domain, observation):
    entry = next(item for item in receipt["sandboxes"] if item["domain"] == domain)
    entry["sandbox_id"] = observation.get("id")
    entry["runtime_generation"] = observation.get("annotations", {}).get("internal.openshell.ai/runtime-generation")
    entry["state"] = observation.get("phase", "observed")
    save_receipt()


def inventory(label):
    listed = cli_json(label + "-authorized-list", ["sandbox", "list", "--workspace", "default", "-o", "json"])
    docker = subprocess.run(
        ["docker", "ps", "-a", "--filter", f"label=openshell.ai/sandbox-namespace={NAMESPACE}", "--format", "{{.ID}} {{.Names}}"],
        capture_output=True,
    )
    (OUT / f"{label}-namespace.stdout").write_bytes(docker.stdout)
    (OUT / f"{label}-namespace.stderr").write_bytes(docker.stderr)
    (OUT / f"{label}-namespace.exit").write_text(f"{docker.returncode}\n")
    if docker.returncode:
        raise RuntimeError(f"{label}: namespace inventory failed")
    return listed.get("sandboxes", []), docker.stdout.decode().splitlines()


def belongs_to_run(sandboxes, containers):
    names = {AGENT, SHELL}
    ids = {item["sandbox_id"] for item in receipt["sandboxes"] if item["sandbox_id"]}
    api_owned = [s for s in sandboxes if s.get("name") in names or s.get("id") in ids]
    driver_owned = [row for row in containers if any(name in row for name in names) or any(i in row for i in ids)]
    return api_owned, driver_owned


def cleanup_all():
    cleanup_errors = []
    for item in reversed(receipt["sandboxes"]):
        name = item["name"]
        domain = item["domain"]
        get_result = subprocess.run(
            [str(CLIENT), "sandbox", "get", name, "--workspace", "default", "-o", "json"],
            capture_output=True,
        )
        (OUT / f"cleanup-get-{domain}.stdout").write_bytes(get_result.stdout)
        (OUT / f"cleanup-get-{domain}.stderr").write_bytes(get_result.stderr)
        (OUT / f"cleanup-get-{domain}.exit").write_text(f"{get_result.returncode}\n")
        observed = None
        if get_result.returncode == 0:
            observed = json.loads(get_result.stdout)
        else:
            try:
                sandboxes, containers = inventory(f"cleanup-get-fallback-{domain}")
            except Exception as exc:
                cleanup_errors.append(f"{name}: Get and authorized inventory failed: {exc}")
                continue
            observed = next((s for s in sandboxes if s.get("name") == name), None)
            if observed is None:
                known_id = item.get("sandbox_id")
                matching_driver = [row for row in containers if name in row or (known_id and known_id in row)]
                if matching_driver:
                    cleanup_errors.append(f"{name}: no API identity, matching driver resources remain; preserving resources")
                    continue
                item["state"] = "absent-confirmed-by-list-and-no-matching-driver-resource"
                save_receipt()
                continue

        observed_id = observed.get("id")
        generation = observed.get("annotations", {}).get("internal.openshell.ai/runtime-generation")
        if not observed_id or (item["sandbox_id"] and observed_id != item["sandbox_id"]):
            cleanup_errors.append(f"{name}: immutable sandbox identity missing or changed; refusing delete")
            continue
        item["sandbox_id"] = observed_id
        item["runtime_generation"] = generation
        item["state"] = "delete-request-pending"
        save_receipt()
        delete_result = subprocess.run(
            [str(CLIENT), "sandbox", "delete", name, "--workspace", "default"],
            capture_output=True,
        )
        (OUT / f"delete-{domain}.stdout").write_bytes(delete_result.stdout)
        (OUT / f"delete-{domain}.stderr").write_bytes(delete_result.stderr)
        (OUT / f"delete-{domain}.exit").write_text(f"{delete_result.returncode}\n")
        if delete_result.returncode:
            cleanup_errors.append(f"{name}: delete request failed with {delete_result.returncode}")
            continue
        receipt["cleanup"]["delete_requests"].append({"name": name, "sandbox_id": observed_id, "runtime_generation": generation, "result": "accepted"})
        save_receipt()

    for attempt in range(1, 31):
        try:
            sandboxes, containers = inventory(f"cleanup-poll-{attempt:02d}")
        except Exception as exc:
            cleanup_errors.append(f"poll {attempt}: authorized inventory unavailable: {exc}")
            break
        api_owned, driver_owned = belongs_to_run(sandboxes, containers)
        receipt["cleanup"]["polls"].append({"attempt": attempt, "api_owned_count": len(api_owned), "driver_namespace_count": len(containers), "driver_owned_count": len(driver_owned), "authorized_scope": "gateway target + default workspace", "driver_scope": NAMESPACE})
        save_receipt()
        foreign_namespace_rows = [row for row in containers if row not in driver_owned]
        if foreign_namespace_rows:
            cleanup_errors.append("unique namespace contains unowned resources; preserving them and the receipt")
            break
        if not api_owned and not driver_owned:
            for item in receipt["sandboxes"]:
                if item["state"] != "absent-confirmed-by-list-and-no-matching-driver-resource":
                    item["state"] = "deleted-and-confirmed"
            save_receipt()
            break
        time.sleep(1)
    else:
        cleanup_errors.append("owned resources remain after 30 authorized and namespace-scoped polls")
    return cleanup_errors


failed = False
try:
    save_receipt()  # ownership intent recorded before sandbox creation effects
    call("gateway-info", ["gateway", "info"])
    for domain, name in (("agent", AGENT), ("generic-shell", SHELL)):
        call(f"create-{domain}", ["sandbox", "create", "--workspace", "default", "--name", name, "--from", IMAGE, "--detach", "-o", "json", "--", "/bin/sh", "-c", "exec sleep infinity"])
        remember(domain, cli_json(f"get-{domain}", ["sandbox", "get", name, "--workspace", "default", "-o", "json"]))
    call("agent-create-marker", ["sandbox", "exec", AGENT, "--", "/bin/sh", "-c", "umask 077; printf account-A > /tmp/private-domain-marker; printf agent-ready; printf diagnostic >&2; exit 7"], expected=(7,))
    call("agent-private-read", ["sandbox", "exec", AGENT, "--", "/bin/sh", "-c", "cat /tmp/private-domain-marker"])
    call("shell-cross-domain-denial", ["sandbox", "exec", SHELL, "--", "/bin/sh", "-c", "test -e /tmp/private-domain-marker"], expected=(1,))
    call("agent-boundary", ["sandbox", "exec", AGENT, "--", "/bin/sh", "-c", "id; ps -o pid,ppid,comm; test ! -S /run/openshell.sock && test ! -S /run/docker.sock"])
except Exception as exc:
    failed = True
    (OUT / "replay-error.txt").write_text(f"{type(exc).__name__}: {exc}\n")
finally:
    cleanup_errors = cleanup_all()
    cleanup_failed = bool(cleanup_errors)
    if cleanup_errors:
        (OUT / "cleanup-errors.txt").write_text("\n".join(cleanup_errors) + "\n")
    receipt["cleanup"]["result"] = "failed; receipt and logs retained" if cleanup_failed else "confirmed-empty"
    save_receipt()

raise SystemExit(1 if failed or cleanup_failed else 0)
