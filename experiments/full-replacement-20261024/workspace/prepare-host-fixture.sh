#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
FIXTURE_ID="jfr-20261024-ws"
OUT="$ROOT/results/full-replacement-20261024/workspace/$FIXTURE_ID"
REPO="$OUT/host-source"
mkdir -p "$OUT"
if [[ -e "$REPO/.git" || -e "$OUT/worktree" || -e "$OUT/clone" ]]; then
  printf 'fixture already exists; refusing to overwrite: %s\n' "$OUT" >&2
  exit 2
fi
mkdir -p "$REPO/src" "$OUT/protected"
printf 'workspace fixture %s\n' "$FIXTURE_ID" > "$REPO/README.md"
printf "pub fn fixture_value() -> &'static str { \"initial\" }\n" > "$REPO/src/lib.rs"
printf 'protected fixture %s\n' "$FIXTURE_ID" > "$OUT/protected/canary.txt"
chmod 0444 "$REPO/README.md"
ln -s "$OUT/protected/canary.txt" "$REPO/protected-canary-link"
git -C "$REPO" init -q
git -C "$REPO" config user.name 'OpenShell Jackin PoC'
git -C "$REPO" config user.email 'poc@example.invalid'
git -C "$REPO" add README.md src/lib.rs protected-canary-link
git -C "$REPO" commit -qm 'fixture baseline'
git -C "$REPO" worktree add -qb "jfr/$FIXTURE_ID" "$OUT/worktree"
git clone -q --no-hardlinks "$REPO" "$OUT/clone"

python3 - "$OUT" "$REPO" <<'PY'
import hashlib, json, os, pathlib, platform, shutil, subprocess, sys, time
out = pathlib.Path(sys.argv[1])
repo = pathlib.Path(sys.argv[2])
commands = []
def run(argv, cwd=None):
    p = subprocess.run(argv, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    commands.append({"argv": argv, "cwd": str(cwd or pathlib.Path.cwd()), "exit_status": p.returncode,
                     "stdout": p.stdout, "stderr": p.stderr})
    if p.returncode:
        raise SystemExit(f"host fixture command failed: {argv!r}, status={p.returncode}")
    return p.stdout.strip()

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
# Baseline host-only comparisons, no sandbox mount attempted.
for label, path in [("shared", repo), ("worktree", out/"worktree"), ("clone", out/"clone")]:
    run(["git", "status", "--porcelain=v1"], cwd=path)
    run(["git", "rev-parse", "HEAD"], cwd=path)
    (out/f"{label}-host-baseline.json").write_text(json.dumps({
        "fixture_id": "jfr-20261024-ws", "host_only": True, "path": str(path),
        "git_head": run(["git", "rev-parse", "HEAD"], cwd=path),
        "tracked_readme_sha256": sha(path/"README.md"),
        "readme_mode": oct((path/"README.md").stat().st_mode & 0o777),
        "symlink_target": os.readlink(path/"protected-canary-link") if (path/"protected-canary-link").is_symlink() else None,
        "resolved_symlink_target": str((path/"protected-canary-link").resolve()) if (path/"protected-canary-link").is_symlink() else None
    }, indent=2)+"\n")
# Host-side atomic replacement demonstrates fixture mechanism only.
tmp = repo/"src/lib.rs.next"
tmp.write_text("pub fn fixture_value() -> &'static str { \"host-atomic-v1\" }\n")
os.replace(tmp, repo/"src/lib.rs")
atomic = {"host_only": True, "replacement": "os.replace", "path": str(repo/"src/lib.rs"), "sha256": sha(repo/"src/lib.rs"),
          "content": (repo/"src/lib.rs").read_text()}
(out/"host-atomic-replace.json").write_text(json.dumps(atomic, indent=2)+"\n")
# Restore baseline so later runtime cases begin from known source.
run(["git", "checkout", "--", "src/lib.rs"], cwd=repo)
watchers = {name: shutil.which(name) for name in ("fswatch", "watchman", "inotifywait")}
record = {"fixture_id":"jfr-20261024-ws", "classification":"HOST_FIXTURE_ONLY; no OpenShell sandbox or mount", "os":platform.platform(),
          "architecture":platform.machine(), "git_version":run(["git","--version"]), "paths":{"shared":str(repo),"worktree":str(out/"worktree"),"clone":str(out/"clone"),"protected":str(out/"protected")},
          "git_worktree_list":run(["git","worktree","list","--porcelain"],cwd=repo), "watcher_tools":watchers,
          "watch_event_result":"NOT TESTED: no fswatch/watchman/inotifywait installed" if not any(watchers.values()) else "tool available; runtime event propagation still untested",
          "read_only_fixture":"README.md mode 0444; sandbox denial not tested", "symlink_fixture":"project symlink resolves to protected sibling canary; sandbox confinement not tested",
          "atomic_replace_result":"host os.replace succeeded; sandbox/host visibility not tested", "commands":commands}
(out/"host-fixture-setup.json").write_text(json.dumps(record, indent=2)+"\n")
PY
