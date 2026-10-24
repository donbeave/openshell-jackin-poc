# Integrated OpenShell replacement research

**NOT READY TO START THE FULL OPENSHELL REFACTOR**

All published research is in this repository. [READINESS_REPORT.md](READINESS_REPORT.md) is the consolidated current decision; [FULL_REFACTOR_HANDOFF.md](FULL_REFACTOR_HANDOFF.md) is the reading order. No Jackin product refactor was made. Docker is the image builder and an explicitly granted workload capability, never a legacy agent-execution fallback.

## Evidence groups

| Group | Entry point | Role in the decision |
|---|---|---|
| Original public baseline `2315e6a` | [Original capability matrix](CAPABILITY_MATRIX.md), [original decision](DECISION.md) | Historical released-0.1.5 primitives, failures, workarounds, cleanup and measurement limits |
| Published execution follow-up `a94bb70` | [Current report](READINESS_REPORT.md), [POC index](POC_RESULTS.md), [architecture](ARCHITECTURE_DECISIONS.md) | Broader real role, typed Rust, session, storage, identity-patch, strict-worker and target experiments |
| Independently reviewed audit snapshot | [Bundle](research/independent-audit-20261024/README.md), [source inventory](research/independent-audit-20261024/audits/SOURCE_INVENTORY.md), [raw results](research/independent-audit-20261024/POC_RESULTS.md) | Independent action/caller audit, root-policy failure, Claude recipe/version failures, CLI/group-timeout/identity negatives, inconclusive terminal replay and cleanup receipts |

The groups have different source/experiment breadth. Their shared current source pins are Jackin `6e266406b49da2ab3c55355f3b7d33d1643ee6cd`, Architect `7b72b38fe1d66e35c0931899c53bf3719592bbcc`, and released OpenShell `v0.1.5` / `bdb956f2cd65a635f1294fccf1d138d263bf650f`. The original group also references older Jackin revisions. Each group's compatibility analysis, actual image/platform, gateway policy and authentication records control reuse. Source inspection is not execution proof.

## Reconciliation of overlapping results

| Area | Combined interpretation |
|---|---|
| Source inventory | Both audits resolve production runtime effects and inactive foundations at the pinned source. Their 137 operation rows and 207 statement-level records overlap; counts are not additive. The independent audit also retains cross-cutting, operational/build and broad-match dispositions. |
| Capsule root | Independent policy rejection plus pinned source establish the existing root-started mechanism's incompatibility. The later follow-up executes the actual current-pin Linux binary and corroborates the root requirement. This is not a claim that every possible Capsule adaptation is impossible. |
| Rust control | The independent snapshot tests the installed Rust CLI and leaves a custom RPC route unproved. The later follow-up supplies typed SDK/caller-built verified Tonic-channel execution, including local/Linux-guest primitives. Those later proofs take precedence for their cases. Full identity/generation/retry/remote scope still needs qualification. |
| Persistent terminal | The independent reconnect attempts remained inconclusive for identical-process survival. The later canonical-main PTY/deterministic-process experiment demonstrates same-PID reconnect. Keep both outcomes; neither is the complete trusted session/account/desktop protocol. |
| Workspace | The independent worker bind fixture relaxed admission and cannot qualify the selected admitted-store design. Later approved bind-backed volumes prove selected live host/Git/retention primitives with admission preserved. They do not establish complete private-state materialization, VM confinement, remote synchronization or fleet recovery. |
| Real roles and versions | Independent Claude marketplace and exact-native-version failures remain failures. Later full Architect OpenCode/Amp/Kimi/Grok hook/version slices provide additional agent-specific evidence, not authenticated coding. Cache-agent mismatch and Codex fallback failure remain disclosed. Adapter/setup enumeration is not launch support; the consolidated contract distinguishes twelve adapters from six actual entrypoint cases. |
| Worker | Workload-side `killpg` and CLI timeout failures apply to the independent fixture. Later worker experiments and the separate tmpfs patch add useful mechanisms/limits, but strict confinement still fails the out-of-grant chmod test. Whole-sandbox removal does not automatically supply a trustworthy test exit result. No configuration is declared a complete worker pass. |
| Identity | Released name-based replacement races remain failures. The experimental Delete-only patch is narrow; it does not fix Stop/Start/Exec/session input, and is not released support. Preserve its exact patch pin and independent review. |
| Optional Docker | External engines prove their own connectivity and limits. Neither group demonstrates the required OpenShell-compatible managed companion ownership or policy/resource boundary. |
| Accounts, target matrix, combined run | Required real account/credential journeys, managed Docker, complete required-platform coverage and the critical combined fresh replay remain blocked or untested. No independent primitive success fills those gaps. |

## Patch and release boundaries

The tmpfs serialization patch `68cfa648538a497acd4af2cf48424eda9834ba0f` and Delete-only patch `95a1e7fe2bfc731ec21096dea0758fa7fc90a8db` have separate records. They were not tested as one combined architecture and must not be pooled with released behavior. Historical binary/digest attribution limitations remain in the [final decision review](results/full-refactor-20261024/final-decision-review.md). Current OpenShell main changes are source-only unless a specific executed case identifies them.

## Plans and remaining work

Use the consolidated [refactor plan](REFACTOR_PLAN.md), [responsibility map](RESPONSIBILITY_MAP.md), [workflow contract](USER_WORKFLOW_CONTRACT.md), [target matrix](TARGET_MATRIX.md) and [blockers](BLOCKERS.md). The independent [43-case release plan](research/independent-audit-20261024/REFACTOR_PLAN.md) adds corroborating acceptance requirements. These are future product gates, not passing results for an unwritten backend.

The consolidated design selects Candidate B as the full-scope direction. The independent snapshot leaves acceptance of that candidate unresolved because its critical authority/session proofs are absent. These statements are compatible: selecting a design direction does not establish research readiness. Managed companion ownership and other upstream dependencies remain explicit, unproved requirements.

## Publication and reproduction

[INTEGRATION_PUBLICATION.md](INTEGRATION_PUBLICATION.md) records how this merge was prepared. The independent bundle excludes source clones, compiled payloads, keys, credentials and runtime state; it includes pins, scripts, raw results and narrow-redaction provenance. Source-snapshot manifests describe original local evidence; newly generated publication manifests describe sanitized public bytes. Earlier archive/publication receipts remain historical records of their stated commits.

Do not execute historical cleanup/restoration scripts. Read the current ownership receipts and generate fresh isolated gateway names, namespaces, ports and certificates. Public path placeholders require adaptation before replay. No unrelated reset or cleanup is authorized by publishing these results.
