# Publication security review

Review target: frozen publication worktree `/Users/example/openshell-jackin-full-refactor-public` at baseline commit `2315e6a278231854b3139b1ca32402777ff3cd01`. Review scope was the staged follow-up files and their sanitization, not modification of the original public baseline. No cleanup or restore script was run.

## Decision

**CONDITIONAL CLEARANCE for publication of the reviewed frozen stage.** I found no actual credential, private key, certificate private material, personal home path, or host environment file in the reviewed staged evidence. Do not report the directory scan as a clean scanner pass: strict Gitleaks still exits 1 on five manually classified false positives. The full Git-history scan exits 0 with no findings (one commit scanned; this covers committed history, while the directory scan covers the refreshed worktree). No allowlist, baseline, ignore file, or Gitleaks config was used.

The final staged manifest records 1,754 included files, 33 excluded files, and 6,718,476 published bytes. It excludes `config/fleet/velnor-host.env` before reading its contents. That file is absent from the stage. No nested Git repositories were found. A deterministic 256-byte `results/ownership/export.bin` fixture contains byte values 0 through 255 and is test data, not an executable or private payload.

## Strict secret scan

Gitleaks 8.30.1 was run on the staged directory with environment config variables unset, `--gitleaks-ignore-path /dev/null`, `--ignore-gitleaks-allow`, and `--redact=100`. The redacted JSON report is stored outside the publication tree at `results/full-refactor-20261024/security-publication-review/gitleaks-current-redacted.json`; SHA-256: `77d536f1d624183dba7da2e2d9e5dda9e2701d7df0202814a7491918636c615d`. Exit status 1, five findings. `Secret` values were redacted in every finding; the remaining match context includes only field labels and redaction markers.

The five findings are manually classified as non-secrets:

- Three `GPG_KEY` values are public signing-key IDs from official Docker image inspection output.
- One `authenticated_subject` is a synthetic mTLS test identity, needed to document the wrong-identity test; it does not identify a real user.
- One prose match uses the ordinary word “credentials” and contains no credential value.

The findings are deliberately preserved, with their redacted report, rather than suppressed through an allowlist. The directory scan must therefore continue to be described as “five manually reviewed false positives; scanner exit 1.” The separate `gitleaks git` scan found zero findings and exited 0.

## Manual review entries

The final manifest lists five manual-review files. Three source-evidence files were inspected and are safe public-source material: `results/full-refactor-20261024/openshell-main-comparison.json`, `results/full-refactor-20261024/rawmatches/cli-host-fleet.txt`, and `results/full-replacement-20261024/agents-source.md`. Their credential-like matches are identifiers, source expressions, or prose; strict per-file Gitleaks scans found no secrets. They can remain included where present in the publication worktree. The other two entries are redacted diagnostic scan reports (including the former `gitleaks-dir-redacted.json`); they are correctly withheld from the stage. Keep the latest redacted report and scan metadata outside the publication tree. The manifest's manual-review count includes these withheld diagnostics, so it is an inventory count, not five unresolved publication files.

The earlier seven prewarm stderr candidates were inspected: they contain Docker secret-mount command expressions referring to a token file, not token values. Those are source/config expressions, not credentials, and do not require broad assignment redaction.

## Remaining path normalization

Before refresh, `results/full-replacement-20261024/targets/cleanup/commands/vm-runtime-inventory-before-delete.json` contained two unique `/private/tmp/jfr-20261024-*` paths in recorded stdout. The preparer replaced those output values with `<TEMP_PATH>` and recorded one normalization in the refreshed manifest. The evidence’s other command and result data stayed unchanged. The analogous `/tmp/...` values in captured argv are generic test paths.

A full-stage search found no `/Users/example` path or actual machine hostname. `/Users/example` occurrences are the declared placeholder. `/home/agent` is sandbox runtime evidence. The excluded fleet env path appears only as a filename in documentation and manifest; no contents were read.

## Format and artifact checks

All Python files passed AST parsing. Shell scripts passed `sh -n`. No nested `.git` directories were present. JSON parsing found eight format exceptions, all intentional raw command outcomes rather than secret corruption: six zero-byte stdout/inspect captures; one Docker container listing saved with a `.json` suffix; and one file containing three concatenated JSON command outputs. Preserve these bytes because empty output and raw stream boundaries are evidence. The exact paths are:

- `results/full-replacement-20261024/repeat/post-cleanup-sandbox-list.json` (empty)
- `results/full-replacement-20261024/docker/on-inspect.json` (empty)
- `results/full-replacement-20261024/docker/cleanup-gateway-d-list-final.json` (empty)
- `results/full-replacement-20261024/docker/engine-b-service-forward-inspect.json` (line-oriented container listing)
- `results/full-replacement-20261024/control/lifecycle-main-retry.stdout.json` (empty)
- `results/full-replacement-20261024/control/tls-linux-endpoint.stdout.json` (empty)
- `results/full-refactor-20261024/agents/opencode-gid-workaround/openshell-inspect.json` (empty)
- `results/full-refactor-20261024/verification-worker/landlock/image-provenance.json` (concatenated JSON outputs)

## Existing baseline caveat

The historical `cleanup.sh` uses prefix matching, and the historical collateral restoration artifacts include generic names for prior workloads. These files were already present in the original public baseline and were not changed by this review. The new handoff explicitly forbids running those historical scripts. Do not use them as current cleanup instructions; retain the baseline as historical evidence and keep the explicit warning in the new handoff.

## Final refresh scan

The preparer replaced the two host-specific `/private/tmp` outputs with `<TEMP_PATH>` and refreshed/froze the stage. Final stage HEAD remains `2315e6a278231854b3139b1ca32402777ff3cd01`; manifest records one `temporary-vm-path` normalization. The same strict Gitleaks directory scan ran against the final stage with exit status 1 and five findings; every `Secret` field is `REDACTED`, and all match strings contain redaction markers with only surrounding labels/context. Final report SHA-256: `77d536f1d624183dba7da2e2d9e5dda9e2701d7df0202814a7491918636c615d`. The five findings and manual dispositions are listed above. This is conditional publication clearance with documented false positives, not a zero-finding scan. The separate strict Gitleaks Git-history scan exited 0 with zero findings (one commit scanned). The stage was not modified by this reviewer.
