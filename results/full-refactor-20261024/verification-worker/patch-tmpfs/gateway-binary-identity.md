# Patched gateway binary identity

- Pinned source base: `bdb956f2cd65a635f1294fccf1d138d263bf650f`.
- Experimental patch commit: `68cfa648538a497acd4af2cf48424eda9834ba0f`.
- Patch SHA256: `ff61fbd50e03e44d518dca339221cae9012f4eee4d8b24161ec320dfc4176a00`.
- The patched gateway build used for the P10–P14 runtime tests exited 0, but its binary was later removed from the shared mbx target cache before its SHA256 was recorded. The hash of the historical executable that the running gateway loaded is therefore **NOT CAPTURED**.
- A subsequent `mise exec -- cargo build -p openshell-gateway -q` from the same committed source exited 0. Its rebuilt-only binary SHA256 is `5bb214fdbc41e9035bdd523a0b8686c376b1e00594a8c95f948d1f01d982d1b8` (`gateway-binary-rebuilt.sha256`). This is a reproduction build identity and is not substituted for the historical runtime binary identity.

The narrow patch result remains supported by the independent focused test log (150 passed, 2 ignored), gateway build exit records, and P10–P14 execution through the patched gateway. The worker contract remains FAIL.
