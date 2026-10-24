# Publication staging follow-up

This publication follows branch `research/full-openshell-refactor-20261024`, based on evidence baseline `2315e6a278231854b3139b1ca32402777ff3cd01`. Worker evidence, independent decision review, cleanup receipts and publication security review are included. The original baseline files are unchanged. See `PUBLICATION_FINAL_CHECK.json` for the final snapshot verification.

Research files were copied from the local evidence checkout using `scripts/refresh_publication_stage.py`. The script takes a source path, respects Git ignore rules, refuses to overwrite baseline files or later edits, sanitizes local paths and host/temp machine identifiers, and records provenance in `PUBLICATION_MANIFEST.json`. It preserves sandbox and request IDs.

The public staging excludes source checkouts and nested Git fixtures, compiled binaries and target directories, private gateway/client state, certificates and keys, environment files, VM disks, generated local state, and raw Gitleaks diagnostics. Three independently reviewed evidence files with credential-like expressions are included only when their source SHA-256 values match the reviewed versions recorded in the manifest. The upstream filename `config/fleet/velnor-host.env` is excluded by path before content access. The publication bundle contains the role rebuild procedure and focused role patch, but no checkout or Capsule/CLI binary. The refresh redacts UUID values only when they belong to a gateway-token-id or token-reference field; it preserves sandbox, request, generation, and TLS subject identifiers. Two recorded VM-specific temporary paths in the raw inventory output are normalized without rewriting other temporary paths.

One earlier internal source comparison transiently read bytes from that excluded host-only environment file while calculating a file-path comparison. It did not print or persist the contents or a per-file digest; no such material is included in this worktree. The limitation is recorded in the source provenance notes. The refresh script uses a filtered sparse checkout when reproducing the role so that path is absent before checkout.

## Cleanup warning

Do not execute the historical baseline `cleanup.sh`; it predates the scoped ownership receipts and can affect resources outside this follow-up. Use the current experiment-specific cleanup receipts and manifests in the results directories. The experiments’ owned gateways, sandboxes, volumes, and derived images have been checked and cleaned according to those receipts; shared base images and caches were retained.

## Publication checks

- The source evidence checkout remains at the pinned baseline and is not modified by publication staging.
- The publication commit adds files to the original baseline; it does not modify baseline files.
- `PUBLICATION_MANIFEST.json` records source paths, published SHA-256 hashes, exclusions, and redaction counts. It does not self-hash.
- Independent security review, file-format checks and final snapshot scan completed. The directory scanner retains five manually reviewed non-secret findings (exit 1), not a claimed zero-finding pass. See `PUBLICATION_FINAL_CHECK.json`.

The candidate-copy helper performs no commit or push. Publication is a separate authorized Git operation after review.

## Final inventory reconciliation

The candidate-copy helper conservatively skipped some previously generated files after they fell out of its prior manifest, leaving earlier copies present. The final check caught this before publication. Twelve independently reviewed source-evidence files were recopied using the final narrow redactor and added to the complete manifest. Three excluded empty Git-history diagnostic reports were moved outside the publication tree. Every newly published evidence file is now enumerated and hash-checked; publication scaffolding is identified separately. The helper creates a candidate, not a publication approval: repeat the complete manifest-versus-Git inventory check after every refresh. No baseline file was overwritten.
