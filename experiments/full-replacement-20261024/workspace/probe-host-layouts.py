#!/usr/bin/env python3
"""Host-only fixture checks. Never invokes OpenShell and never edits user repositories."""
import hashlib, json, pathlib, subprocess
root = pathlib.Path(__file__).resolve().parents[3]
out = root / "results/full-replacement-20261024/workspace/jfr-20261024-ws"
repo, worktree, clone = (out / x for x in ("host-source", "worktree", "clone"))
commands = []
def run(args, cwd):
    p = subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    commands.append({"argv": args, "cwd": str(cwd), "exit_status": p.returncode, "stdout": p.stdout, "stderr": p.stderr})
    if p.returncode:
        raise RuntimeError(f"{args!r} failed: {p.stderr}")
    return p.stdout.strip()
def commit_fixture(path, marker):
    (path / marker).write_text(marker + "\n")
    run(["git", "add", marker], path)
    run(["git", "commit", "-qm", "fixture " + marker], path)

baseline = run(["git", "rev-parse", "HEAD"], repo)
commit_fixture(worktree, "worktree-only.txt")
worktree_head = run(["git", "rev-parse", "HEAD"], worktree)
worktree_gitdir = run(["git", "rev-parse", "--git-dir"], worktree)
worktree_isolated = not (repo / "worktree-only.txt").exists() and worktree_head != baseline
commit_fixture(clone, "clone-only.txt")
clone_head = run(["git", "rev-parse", "HEAD"], clone)
clone_isolated = not (repo / "clone-only.txt").exists() and clone_head != baseline
# Atomic replacement inside the Shared source path; later runtime test must prove propagation.
old = hashlib.sha256((repo / "src/lib.rs").read_bytes()).hexdigest()
tmp = repo / "src/lib.rs.probe-tmp"
tmp.write_text('pub fn fixture_value() -> &\'static str { "shared-host-atomic" }\n')
tmp.replace(repo / "src/lib.rs")
new = hashlib.sha256((repo / "src/lib.rs").read_bytes()).hexdigest()
run(["git", "checkout", "--", "src/lib.rs"], repo)
result = {
  "fixture_id": "jfr-20261024-ws", "classification": "HOST_FIXTURE_ONLY; no OpenShell sandbox or mount",
  "shared": {"canonical_path": str(repo), "atomic_replace": "PASS on host only", "before_sha256": old, "after_sha256": new, "same_path_is_shared": True},
  "worktree": {"path": str(worktree), "linked_git_dir": worktree_gitdir, "independent_commit": worktree_isolated, "head": worktree_head, "source_unchanged": not (repo/"worktree-only.txt").exists()},
  "clone": {"path": str(clone), "independent_commit": clone_isolated, "head": clone_head, "source_unchanged": not (repo/"clone-only.txt").exists()},
  "read_only_mount": "NOT TESTED; file mode is not equivalent to driver read_only mount flag",
  "file_watch": "NOT TESTED; no watcher utility installed",
  "symlink_escape": "fixture present; sandbox access/confinement NOT TESTED",
  "commands": commands
}
(out / "host-layout-probes.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({k:v for k,v in result.items() if k != "commands"}, indent=2))
