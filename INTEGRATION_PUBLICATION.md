# Integration and publication record

This integration is based on public main commit `a94bb70b83cb847f005dc2acde1e9d2fa9742689`, which already published the larger execution follow-up on top of baseline `2315e6a278231854b3139b1ca32402777ff3cd01`. It adds the separate independently reviewed audit snapshot and reconciles the evidence through [RESEARCH_INDEX.md](RESEARCH_INDEX.md). It makes no Jackin product changes or new runtime readiness claim.

## Included and preserved

- The 361-file frozen independent research snapshot is published under `research/independent-audit-20261024/`, with raw results, source/action inventories, scripts, decisions, blocker report, target matrix and detailed plan.
- Its source SHA-256 hashes were verified before copying. `PUBLICATION_PROVENANCE.json` maps source hashes to sanitized publication hashes. Personal home paths, hostnames and authority token-reference values are narrowly normalized; sandbox, generation and request identities remain evidence.
- `SOURCE_ARTIFACT_MANIFEST.json` preserves the original snapshot manifest. Its hashes describe the local source bytes, not the redacted public bytes. The new `ARTIFACT_MANIFEST.json` describes public bundle bytes.
- The earlier 1,768 locally staged files were compared after the same publication redactor and all matched the already published main. They were not copied over newer reviewed evidence.
- Five additional evidence/receipt files omitted from that stage are included. Two streams containing NUL bytes are published as reversible escaped text: backslash becomes two backslashes, and NUL becomes backslash-zero. Privacy redaction precedes escaping. Original and public hashes are recorded in `INTEGRATION_EXTRA_EVIDENCE.json`.
- Existing raw evidence, failed experiments and patch-specific limits are preserved. Later successful primitives supersede older untested statements only within their exact platform/image/policy/authentication scope. No incompatible experiments are combined into a claimed complete architecture.

## Exclusions

Source clones, nested Git/build fixtures, binaries, keys/certificates, credentials, generated gateway/client configuration/state, live logs in private gateway directories, VM disks, interpreter caches and raw security diagnostic reports are excluded. Paths are filtered before content access. Publication does not authorize running old cleanup/restoration scripts or touching unrelated workloads. The original local evidence remains available separately.

The source checkout that held the prior staging files was dirty and was preserved. Integration uses an isolated Git worktree based on published main; no reset or overwrite of that working copy was performed.

## Validation and secret review

The public tree is checked with strict Gitleaks directory scanning, with config environment overrides removed, no allowlist suppression, a null ignore path and full redaction. Scan metadata and manual dispositions are recorded in `INTEGRATION_CHECKS.json`; raw scanner output stays outside the publication tree.

The previously published five non-secret findings remain: three official image GPG signing-key IDs, one synthetic mTLS subject and one prose match. The supplemental Capsule report adds one prose match in its sentence about peer identity and process reaping; it contains no credential. Scanner exit 1 with these reviewed non-secret findings must not be described as a zero-finding scan. A final rescan must retain this exact disposition or explicitly review any additional finding.

Python AST, shell syntax, new JSON files, source/public provenance hashes and new Markdown links are checked. Historical raw JSON captures retain their previously documented format exceptions; their bytes are not rewritten to make a parser pass. This publication validation is not a product or runtime acceptance suite.

## Manifest scope

`INTEGRATION_MANIFEST.json` hashes the complete staged publication tree except itself and `INTEGRATION_CHECKS.json`; those two control files are protected by the publication commit. Earlier archive/publication manifests and receipts remain historical records for their stated commits. The root README and handoff now point to the consolidated decision, so earlier manifest claims are not presented as current-tree byte equality.

The full-refactor decision remains **NOT READY TO START THE FULL OPENSHELL REFACTOR**. Start with the merged research index before continuing work on missing capabilities.
