# Public snapshot provenance

This directory contains a sanitized publication of the frozen independent audit. It complements the later execution follow-up already published at `a94bb70`; it does not replace that follow-up's successful Rust, PTY, role and admitted-storage primitives with older NOT TESTED entries. Read the [merged research index](../../RESEARCH_INDEX.md).

`SOURCE_ARTIFACT_MANIFEST.json` describes original source bytes. `PUBLICATION_PROVENANCE.json` maps each included source file to its public SHA-256 and transformations. `ARTIFACT_MANIFEST.json` hashes public bytes. Source validation receipts describe the original pinned source checkouts; they are not evidence that excluded clones exist in this publication.

Personal paths/hostnames and authority-token references were normalized. Sandbox IDs, generations, request IDs, image identities, failures and limitations were retained. Source clones, runtime state, credentials, keys, binaries and interpreter caches are not included. Recreate pinned sources with `experiments/metadata/fetch-sources.py`; inspect all reproduction scripts and replace public path placeholders before running. Generate fresh isolated names/namespaces/ports/PKI. Do not execute historical Docker-probe or cleanup/restoration scripts blindly.

The local source remains unchanged. Publication adds a scope banner to README, which is recorded as a publication transformation. This snapshot's NOT READY decision remains consistent with the consolidated verdict.
