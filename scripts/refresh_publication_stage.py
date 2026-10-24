#!/usr/bin/env python3
"""Copy redacted, non-generated research files into the publication worktree.

Run from any directory:
  python3 scripts/refresh_publication_stage.py --source /path/to/source-repo

The destination is this repository. It never reads excluded environment files,
keys, nested Git trees, binaries, private state, or VM images. It copies only
source files reported by `git ls-files --others --exclude-standard`.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import os
import platform
import re
import shutil
import socket
import stat
import subprocess
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

BASELINE = "2315e6a278231854b3139b1ca32402777ff3cd01"
BRANCH = "research/full-openshell-refactor-20261024"
MANIFEST_NAME = "PUBLICATION_MANIFEST.json"
FOLLOWUP_NAME = "PUBLICATION_FOLLOWUP.md"
WITHHELD_DIAGNOSTICS = {
    "results/full-refactor-20261024/security-publication-review/gitleaks-dir-redacted.json",
    "results/full-refactor-20261024/security-publication-review/gitleaks-current-redacted.json",
    "results/full-refactor-20261024/security-publication-review/gitleaks-dir-refresh-redacted.json",
    "results/full-refactor-20261024/security-publication-review/gitleaks-final-redacted.json",
    "results/full-refactor-20261024/security-publication-review/gitleaks-git-final-redacted.json",
    "results/full-refactor-20261024/security-publication-review/gitleaks-git-redacted.json",
    "results/full-refactor-20261024/security-publication-review/gitleaks-git-refresh-redacted.json",
}
REVIEWED_SAFE_SOURCE_HASHES = {
    "results/full-refactor-20261024/openshell-main-comparison.json": "f47e4eea429a18be0f6e240b6eb8a132c647eba7a71cdbf055f670b51551b314",
    "results/full-refactor-20261024/rawmatches/cli-host-fleet.txt": "4c7e5349a6b9b296c12e436d9922b2a03d544ab4b31a25916c0d0d6509d9369b",
    "results/full-replacement-20261024/agents-source.md": "d9a1a59837d70badeb8bdc80ab2a91346a13bab6a898319af5e3c7d0a736e541",
}
VM_INVENTORY_PATH = "results/full-replacement-20261024/targets/cleanup/commands/vm-runtime-inventory-before-delete.json"
VM_TEMP_PATHS = (
    "/private/tmp/jfr-20261024-vm",
    "/private/tmp/jfr-20261024-vmbind",
)

EXACT_EXCLUDED_FILES = {
    "config/fleet/velnor-host.env",
}
EXCLUDED_SUFFIXES = {
    ".pem", ".key", ".p12", ".pfx", ".crt", ".der", ".jks", ".keystore",
    ".qcow", ".qcow2", ".vmdk", ".vdi", ".vhd", ".vhdx", ".img", ".raw",
    ".bin", ".tar", ".gz", ".zip", ".xz", ".bz2", ".lz4", ".zst", ".7z", ".rar",
    ".db", ".sqlite", ".sqlite3", ".dmg", ".app", ".xcarchive", ".o", ".a", ".so", ".dylib", ".dll", ".exe", ".class", ".pyc",
    ".dSYM", ".pid",
}
EXCLUDED_NAMES = {
    ".env", ".env.local", ".env.production", "gateway.log", "gateway.pid",
    "id_rsa", "id_ed25519", "credentials.json", "token.json", "secrets.json",
}
EXCLUDED_DIR_NAMES = {
    ".git", ".cache", ".venv", "node_modules", "target", "build-output",
    "jackin-home", "jackin-config", "certs", "private", "secrets", "credentials",
}
EXCLUDED_CHECKOUT_DIRS = {
    "jackin-source", "architect", "architect-derived", "jackin-6e",
    "jackin-target", "jackin-target-cli", "jackin-target-native",
    "capsule-target",
    "tailrocks-rust-skills-source", "vendor",
}
EXCLUDED_EXACT_PREFIXES = {
    "experiments/full-replacement-20261024/role/architect",
    "experiments/full-replacement-20261024/role/architect-derived",
    "experiments/full-replacement-20261024/role/jackin-source",
    "experiments/full-replacement-20261024/role/jackin-target",
    "experiments/full-replacement-20261024/role/capsule-target",
    "experiments/full-replacement-20261024/role/capsule-build",
    "experiments/full-replacement-20261024/role/toolchain-fixture",
}
CREDENTIAL_ASSIGNMENT = re.compile(
    r'''(?i)(?<![\w-])(?P<key>(?:[A-Za-z0-9]+[_-])?(?:api[_-]?key|access[_-]?token|refresh[_-]?token|client[_-]?secret|password|secret|authorization|token|token[-_]reference))(?![\w-])\s*[:=]\s*(?P<value>[^,\r\n]+)'''
)
IDENTIFIER_UUID = re.compile(r"(?i)\b[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b")
TOKEN_REFERENCE_FIELD = re.compile(
    r'''(?i)(?P<prefix>"(?:[^" ]*(?:/|\\/))?(?:gateway-token-id|token-reference|token_reference)"\s*:\s*")(?P<value>[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12})(?P<suffix>")'''
)
TOKEN_PATTERNS = [
    re.compile(r"(?i)\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-ant-[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9_-]{24,}|xox[baprs]-[A-Za-z0-9-]{20,}|ya29\.[A-Za-z0-9_-]{20,}|AIza[A-Za-z0-9_-]{30,})\b"),
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/-]{16,}={0,2}"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{24,}\.[A-Za-z0-9_-]{16,}\.[A-Za-z0-9_-]{16,}\b"),
]
PLACEHOLDER_WORDS = ("fixture", "fake", "dummy", "example", "placeholder", "invalid", "test-only", "no-network", "redacted", "not-a-real", "not-a-secret", "unset", "changeme", "sample")


def git(root: Path, *args: str, data: bytes | None = None) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(["git", "-C", str(root), *args], input=data, capture_output=True, check=False)


def sanitized_path(value: str, replacements: list[tuple[str, str]]) -> str:
    result = value
    for source, replacement in replacements:
        if source:
            result = result.replace(source, replacement)
    return result


def skip_reason(rel: str, source_root: Path) -> str | None:
    p = PurePosixPath(rel)
    if any(rel == x or rel.startswith(x + "/") for x in EXACT_EXCLUDED_FILES):
        return "explicitly-excluded-host-environment-file"
    if rel in WITHHELD_DIAGNOSTICS:
        return "raw-security-scan-diagnostic-withheld-metadata-only"
    if rel.endswith("/config/fleet/velnor-host.env") or rel == "config/fleet/velnor-host.env":
        return "explicitly-excluded-host-environment-file"
    if any(rel == prefix or rel.startswith(prefix + "/") for prefix in EXCLUDED_EXACT_PREFIXES):
        return "source-checkout-or-build-tree"
    if any(part in EXCLUDED_DIR_NAMES for part in p.parts):
        return "private-or-generated-state-directory"
    if any(part in EXCLUDED_CHECKOUT_DIRS for part in p.parts):
        return "source-checkout-or-vendored-tree"
    if any(part in {"target", "debug", "release"} for part in p.parts):
        return "compiled-build-output"
    if p.name in EXCLUDED_NAMES or p.name.lower().startswith(".env"):
        return "credential-or-environment-file"
    if p.suffix.lower() in {s.lower() for s in EXCLUDED_SUFFIXES}:
        return "binary-key-or-disk-artifact"
    if p.name.endswith((".dSYM", ".core", ".dump")):
        return "binary-or-crash-dump"
    if "gateway" in p.parts and any(part in {"config", "state", "certs"} for part in p.parts):
        return "gateway-private-state-or-certificate"
    if any("vm-disk" in part.lower() or "virtual-disk" in part.lower() for part in p.parts):
        return "virtual-machine-disk"
    # A nested Git repository is a generated checkout/fixture. Inspect only
    # directory metadata; never read its Git database or working files.
    for i in range(1, len(p.parts)):
        parent = source_root.joinpath(*p.parts[:i])
        marker = parent / ".git"
        if marker.exists():
            return "nested-git-fixture-or-source-checkout"
    return None


def redact_text(text: str, replacements: list[tuple[str, str]], rel: str = "") -> tuple[str, list[str]]:
    changed: list[str] = []
    for source, replacement in replacements:
        if source and source in text:
            text = text.replace(source, replacement)
            changed.append("local-path-or-machine-name")
    temp_dir = tempfile.gettempdir()
    if temp_dir not in {"/tmp", "/private/tmp"} and temp_dir in text:
        text = text.replace(temp_dir, "<TEMP_DIR>")
        changed.append("temporary-directory")
    text, count = re.subn(r"/(?:private/)?var/folders/[^\s\"'<>]+", "<TEMP_PATH>", text)
    if count:
        changed.append("temporary-machine-path")
    text, count = TOKEN_REFERENCE_FIELD.subn(r'\g<prefix>00000000-0000-0000-0000-000000000000\g<suffix>', text)
    if count:
        changed.append(f"token-reference-uuid:{count}")
    if rel == VM_INVENTORY_PATH:
        for machine_path in VM_TEMP_PATHS:
            if machine_path in text:
                text = text.replace(machine_path, "<TEMP_PATH>")
                changed.append("temporary-vm-path")
    for pattern in TOKEN_PATTERNS:
        def redact_match(match: re.Match[str]) -> str:
            value = match.group(0)
            if any(marker in value.lower() for marker in PLACEHOLDER_WORDS):
                return value
            return "<REDACTED_TOKEN>"
        text, count = pattern.subn(redact_match, text)
        if count:
            changed.append(f"token-pattern:{count}")
    return text, changed


def inventory_credential_assignments(text: str, rel: str) -> tuple[list[dict], list[dict]]:
    """Record key names and line numbers only; never persist candidate values."""
    inventory: list[dict] = []
    unresolved: list[dict] = []
    for line_no, line in enumerate(text.splitlines(), 1):
        for match in CREDENTIAL_ASSIGNMENT.finditer(line):
            key = match.group("key")
            value = match.group("value").strip().strip("\\\"'` ").rstrip(",; ")
            lower = value.lower()
            if any(pattern.search(value) for pattern in TOKEN_PATTERNS):
                classification = "recognized-secret-pattern-redacted"
            elif IDENTIFIER_UUID.fullmatch(value):
                classification = "resource-or-request-identifier-preserved"
            elif not value or lower in {"none", "null", "false", "true", "0", "1", "<redacted>"} or any(word in lower for word in PLACEHOLDER_WORDS):
                classification = "empty-placeholder-or-disposable-fixture"
            elif any(marker in lower for marker in ("${", "$env", "$(", "std::env", "env::var", "getenv", "get_env", "os.environ", "credential", "provider", "token_value", "secret_value", "api_key_value", "api-key-value", ".id", ".token", ".value", "::", "->", "&", "string", "option", "result", "header")) or re.fullmatch(r"[A-Z_][A-Z0-9_]*", value):
                classification = "environment-reference-or-expression"
            elif re.fullmatch(r"(?:key|token|secret|value|auth|credential)(?:_value)?", lower):
                classification = "symbolic-variable-reference"
            else:
                classification = "manual-review-needed"
                unresolved.append({"source_path": rel, "line": line_no, "key": key})
            inventory.append({"source_path": rel, "line": line_no, "key": key, "classification": classification})
    return inventory, unresolved


def mime_type(rel: str, data: bytes) -> str:
    guessed, _ = mimetypes.guess_type(rel)
    if guessed:
        return guessed
    if data.startswith(b"#!"):
        return "text/x-script"
    return "text/plain"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, help="source repository with untracked research evidence")
    args = parser.parse_args()
    source = Path(args.source).resolve()
    dest = Path(__file__).resolve().parents[1]
    if not (source / ".git").exists() and git(source, "rev-parse", "--show-toplevel").returncode:
        raise SystemExit("source path is not a Git worktree")
    if git(source, "rev-parse", "HEAD").stdout.decode().strip() != BASELINE:
        raise SystemExit("source HEAD does not match evidence baseline")
    if git(dest, "rev-parse", "HEAD").stdout.decode().strip() != BASELINE:
        raise SystemExit("destination baseline changed; refusing to stage")
    if git(dest, "branch", "--show-current").stdout.decode().strip() != BRANCH:
        raise SystemExit("destination branch mismatch; refusing to stage")

    prior_path = dest / MANIFEST_NAME
    prior = json.loads(prior_path.read_text()) if prior_path.exists() else {"files": []}
    prior_files = {row["destination_path"]: row for row in prior.get("files", [])}

    status = git(source, "ls-files", "--others", "--exclude-standard", "-z")
    if status.returncode:
        raise SystemExit("failed to enumerate untracked source files")
    paths = sorted(x.decode("utf-8", "surrogateescape") for x in status.stdout.split(b"\0") if x)

    hostname_values = {socket.gethostname(), socket.getfqdn(), platform.node()}
    hostname_values.discard("")
    hostname_values -= {"localhost", "localhost.localdomain", "127.0.0.1", "::1"}
    local_home = str(Path.home())
    public_home = "/Users/example" if local_home.startswith("/Users/") else "<HOME>"
    replacements = [(local_home, public_home)]
    replacements.extend((h, "<HOST>") for h in sorted(hostname_values, key=len, reverse=True))

    # Respect destination ignore rules too, without allowing ignored paths to
    # appear in the staged copy.
    check = git(dest, "check-ignore", "--no-index", "-z", "--stdin", data=b"\0".join(p.encode("utf-8", "surrogateescape") for p in paths) + b"\0")
    ignored = {x.decode("utf-8", "surrogateescape") for x in check.stdout.split(b"\0") if x}

    included: list[dict] = []
    excluded: list[dict] = []
    type_counts: Counter[str] = Counter()
    redaction_counts: Counter[str] = Counter()
    total_bytes = 0
    baseline_collisions = 0
    credential_inventory: list[dict] = []
    credential_review_files: set[str] = set()
    for rel in paths:
        reason = skip_reason(rel, source)
        if reason:
            excluded.append({"source_path": sanitized_path(rel, replacements), "reason": reason})
            continue
        if rel in ignored:
            excluded.append({"source_path": sanitized_path(rel, replacements), "reason": "destination-gitignore"})
            continue
        src = source / rel
        try:
            mode = src.lstat().st_mode
            size = src.lstat().st_size
        except OSError:
            excluded.append({"source_path": sanitized_path(rel, replacements), "reason": "source-stat-failed"})
            continue
        if stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
            excluded.append({"source_path": sanitized_path(rel, replacements), "reason": "symlink-or-nonregular-file"})
            continue
        if size > 20 * 1024 * 1024:
            excluded.append({"source_path": sanitized_path(rel, replacements), "reason": "large-generated-artifact-over-20MiB"})
            continue

        try:
            raw = src.read_bytes()
        except OSError:
            excluded.append({"source_path": sanitized_path(rel, replacements), "reason": "source-read-failed"})
            continue
        if b"\0" in raw or (raw and sum(b < 9 or (13 < b < 32) for b in raw[:8192]) > min(32, len(raw[:8192]) // 20)):
            excluded.append({"source_path": sanitized_path(rel, replacements), "reason": "binary-content"})
            continue
        decoded = raw.decode("utf-8", "replace")
        if "-----BEGIN " in decoded and ("PRIVATE KEY-----" in decoded or "CERTIFICATE-----" in decoded):
            excluded.append({"source_path": sanitized_path(rel, replacements), "reason": "key-or-certificate-material"})
            continue
        if re.search(r"(?m)^\s*ssh-(?:rsa|ed25519|ecdsa-sha2-)", decoded):
            excluded.append({"source_path": sanitized_path(rel, replacements), "reason": "public-key-material"})
            continue
        assignments, unresolved = inventory_credential_assignments(decoded, sanitized_path(rel, replacements))
        credential_inventory.extend(assignments)
        source_digest = hashlib.sha256(raw).hexdigest()
        reviewed_digest = REVIEWED_SAFE_SOURCE_HASHES.get(rel)
        if reviewed_digest and source_digest == reviewed_digest:
            unresolved = []
        if unresolved:
            credential_review_files.add(rel)
            excluded.append({"source_path": sanitized_path(rel, replacements), "reason": "manual-review-secret-assignment"})
            continue
        published, transformations = redact_text(decoded, replacements, rel)
        output = published.encode("utf-8")

        dest_rel = sanitized_path(rel, replacements)
        target = dest / dest_rel
        prior_row = prior_files.get(dest_rel)
        if target.exists():
            if not prior_row:
                excluded.append({"source_path": sanitized_path(rel, replacements), "reason": "baseline-or-unowned-destination-collision"})
                baseline_collisions += 1
                continue
            current_hash = hashlib.sha256(target.read_bytes()).hexdigest()
            if current_hash != prior_row.get("sha256_published"):
                excluded.append({"source_path": sanitized_path(rel, replacements), "reason": "destination-edited-since-last-refresh"})
                continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(output)
        os.chmod(target, stat.S_IMODE(mode) & 0o755)
        digest = hashlib.sha256(output).hexdigest()
        ftype = mime_type(rel, output)
        row = {
            "source_path": sanitized_path(rel, replacements),
            "destination_path": dest_rel,
            "sha256_published": digest,
            "size_bytes": len(output),
            "file_type": ftype,
            "redactions": transformations,
        }
        included.append(row)
        type_counts[ftype] += 1
        total_bytes += len(output)
        for item in transformations:
            redaction_counts[item.split(":", 1)[0]] += int(item.rsplit(":", 1)[1]) if ":" in item else 1

    manifest = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source_repo_label": "local OpenShell Jackin research checkout",
        "source_head": BASELINE,
        "destination_head": BASELINE,
        "destination_branch": BRANCH,
        "copy_method": "git ls-files --others --exclude-standard; source and destination ignore rules respected",
        "personal_path_replacement": "local home directory -> /Users/example or <HOME>",
        "machine_identifier_replacements": ["local hostnames -> <HOST>", "temporary machine paths -> <TEMP_PATH>", "temp root -> <TEMP_DIR>"],
        "identifier_redaction": "only UUID values attached to quoted gateway-token-id or token-reference fields are replaced with the fixed zero UUID; sandbox, request, generation, and TLS subject identifiers are preserved",
        "withheld_security_diagnostic": "results/full-refactor-20261024/security-publication-review/gitleaks-dir-redacted.json is excluded; reviewer scan findings are summarized without publishing this raw diagnostic",
        "excluded_host_environment_file": "config/fleet/velnor-host.env; path excluded before any content read",
        "prohibited_artifacts": ["source checkouts", "nested Git fixtures", "binaries", "compiled outputs", "private state", "credentials", "keys/certificates", "VM disks"],
        "included_file_count": len(included),
        "excluded_file_count": len(excluded),
        "baseline_collisions_skipped": baseline_collisions,
        "total_published_bytes": total_bytes,
        "file_type_counts": dict(sorted(type_counts.items())),
        "redaction_counts": dict(sorted(redaction_counts.items())),
        "credential_assignment_inventory": credential_inventory,
        "reviewed_safe_source_hashes": {
            sanitized_path(path, replacements): digest
            for path, digest in REVIEWED_SAFE_SOURCE_HASHES.items()
        },
        "credential_assignment_manual_review_file_count": len(credential_review_files),
        "control_files": [
            {"path": rel, "size_bytes": (dest / rel).stat().st_size, "sha256_published": hashlib.sha256((dest / rel).read_bytes()).hexdigest(), "file_type": mime_type(rel, (dest / rel).read_bytes())}
            for rel in [FOLLOWUP_NAME, "scripts/refresh_publication_stage.py"]
            if (dest / rel).exists()
        ],
        "manifest_self_hash": "not recorded; this file is self-describing",
        "files": included,
        "excluded": excluded,
    }
    (dest / MANIFEST_NAME).write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({k: manifest[k] for k in ["destination_branch", "included_file_count", "excluded_file_count", "credential_assignment_manual_review_file_count", "baseline_collisions_skipped", "total_published_bytes", "file_type_counts", "redaction_counts"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
