# Selected Architect role and agent evidence

## Frozen inputs

- Jackin source: `6e266406b49da2ab3c55355f3b7d33d1643ee6cd`, tree `11c7af3812dd9ba0be27f6ae33fc078fa40ff85c`.
- Architect source: `7b72b38fe1d66e35c0931899c53bf3719592bbcc`.
- OpenShell: v0.1.5, `bdb956f2cd65a635f1294fccf1d138d263bf650f`.
- Experiment role source commit: `018fb476eeff6ff2dd750962127470953311a511`, tree `260192eb11b1ff72b8ead74cfe0fbc4322bbb331`. It derives from the pinned role source, excludes an unrelated host-only environment file from the build context, and changes `published_image` to the pinned local base tag `jfr-20261024-architect-base:7b72b38`.
- Base image: `sha256:e7655072c6d511250b183e9511ca1f701e635766ec0d190a68bfe470745df63a`, `linux/arm64`.
- Test host: macOS 27.0.1, arm64; Docker context `orbstack`; endpoint `unix://<home>/.orbstack/run/docker.sock`.

## Build evidence

The 6e Jackin CLI build passed:

```text
mise exec -- cargo build --locked --release --target-dir <experiment>/jackin-target-cli -p jackin
exit 0; duration 203.471 s; jackin 0.6.4
sha256 307d6985e79662ed3edf4068c5013d28e742b56b430c6d2abc285583cbf8c7d0
```

The 6e Capsule has a native macOS build and a separate Linux ARM64 build. The native binary runs `jackin-capsule 0.6.4`; the Linux binary was run successfully inside OpenShell. Their hashes are `3765eef14d44a2b6ebf6e0234a535dfa5f600b316fc8c062f2b4d82d3007700d` (Mach-O arm64) and `60f50d7441a4caa64e92205444cc97868166a0714bac4c8b0a1fc334020de22d` (ELF aarch64).

The actual pinned Jackin 6e `prewarm --agent claude --image --role jfr24/architect --role-git <experiment>/architect-derived` ran for 72.05 seconds and exited 1. The actual Claude Code installer ran as a Docker image-build step and installed version `2.1.310`. The build then failed during the unmodified Architect manifest's Claude plugin marketplace setup:

```text
claude plugin marketplace add 'tailrocks/tailrocks-rust-skills'
Failed to add marketplace: Marketplace file not found at
/home/agent/.claude/plugins/marketplaces/tailrocks-tailrocks-rust-skills/.claude-plugin/marketplace.json
```

The role declares `tailrocks/tailrocks-rust-skills` as a Claude marketplace. That repository at `18467d1531760a017d42509ce461569a306895e` contains `.claude-plugin/plugin.json` and skill content but no `.claude-plugin/marketplace.json`. Jackin created no derived image tag. This is a real role/build-input failure, not an OpenShell failure, and it prevents testing the complete role and its preflight in a derived image.

The first prewarm reproduction used the native macOS Capsule override. It failed at plugin installation before producing an image, so that run provides no runtime evidence. A direct attempt to execute the Linux ELF from macOS returned `exec format error`, but Jackin's non-Linux `verify_version` path reads embedded identity/version markers rather than executing the override. The actual Codex rerun therefore uses the Linux ARM64 artifact that will be copied into the linux/arm64 image. The same correct-artifact Claude reproduction is saved separately under `architect-claude-image-6e-linux-capsule/`.

## Capsule isolation evidence

The actual 6e Capsule was built natively for Linux ARM64 inside OpenShell and then run in a minimal fixture image. Its isolation wrapper returned exit 1 with `Error: capsule isolation wrapper must start as root`. OpenShell v0.1.5 rejected both process-policy values `root` and `0` as `run_as_user`/`run_as_group` (`[1, 4294967294]` only). We did not weaken the policy or grant root. This blocks unchanged Capsule session startup under the tested released OpenShell policy.

The same actual source's macOS Capsule build returned exit 1 with `isolated agent sessions require a Linux Landlock boundary`.

## Actual OpenCode selected image

The pinned 6e Jackin CLI build passed on macOS arm64 using `mise exec -- cargo build --locked --release -p jackin`: exit 0, 203.471 seconds, version `jackin 0.6.4`, SHA-256 `307d6985e79662ed3edf4068c5013d28e742b56b430c6d2abc285583cbf8c7d0`.

Using the exact Architect role, local pinned base `jfr-20261024-architect-base:7b72b38`, Linux ARM64 Capsule built from 6e, and selected agent OpenCode, Jackin's real `prewarm --agent opencode --image` built:

- `jk_jfr24_architect:018fb47`, ID `sha256:d1c82a2c8d9b21dfcb1d2bb20dd5a23823a7747799f01d73c291f3a7140546a2`, `linux/arm64`, 13,981,089,043 bytes. Cold image-prewarm duration: 77.774 s.
- An unchanged warm prewarm reused that exact image in 16.46 s.
- Appending a behavior-neutral comment to the declared `hooks/preflight.sh` in the experiment-only role clone produced role commit `93a46c2ddfbd868e4208109f4ca23401ccd519e8`, new recipe hash `c48bffb87a3e624e...`, new tag `jk_jfr24_architect:93a46c2`, and image ID `sha256:f14f7f176039788cf487f2dc59e57ccf746a4dcf9219a356bf4cf7a7f7ad35ff` in 94.899 s.

The image recipe's fallback installer installed OpenCode `1.19.4`; image-build logs include its own `opencode --version` step. The host agent-binary prewarm failed to resolve the upstream OpenCode binary but did not prevent the Docker fallback image build. Full logs and metadata are under `results/full-refactor-20261024/agents/architect-opencode-image-6e*`.

The unmodified derived image still fails OpenShell provisioning because its `USER agent` has GID 0. OpenShell v0.1.5 rejected it with `IdentityResolutionFailed: workload identity must not contain UID or GID zero` (sandbox `jfr24-openc-01`, ID `8fe50c45-8a26-4038-b9ad-5bfe46927325`).

As a separately labeled configuration workaround, an experiment-only image changed the user's primary group to nonzero GID 1000 and its home/default-home group ownership; it added no capabilities and did not grant root. OpenShell then provisioned UID/GID 1000:1000 with supplementary group 1000, `CapEff=0`, `CapBnd=0`, and `NoNewPrivs=1`. With explicit PATH for the image-installed tools and `/jackin` configured read-only, OpenShell exec ran the actual Architect preflight hook (exit 0), `opencode --version` (`1.19.4`), and Linux Capsule `--version` (`0.6.4`). The hook wrote the expected local Headroom MCP record under `/sandbox/.config/opencode/opencode.json`. Default policy did not permit reading `/jackin`; adding only `/jackin` read-only fixed access. OpenShell also overrode the image's HOME and PATH, so the test explicitly used `HOME=/sandbox` (gateway default) and the image tool PATH. Workaround evidence and command logs are in `results/full-refactor-20261024/agents/opencode-gid-workaround/`.

A controlled preflight failure test set a harmless fake Context7 value, with OpenShell network denied. The image's `mise` reported that `ctx7` was not a valid shim; the actual hook exited 1, and the wrapper did not run the subsequent OpenCode version command. This checks the hook's failure behavior, but it does not prove the complete Capsule entrypoint path. OpenShell did not automatically run the image ENTRYPOINT; a command explicitly ran the hook. Capsule `runtime-setup` and full Jackin session launch remain blocked by the independent root/Landlock restriction.

The Claude selection still fails in the actual Architect manifest because `tailrocks/tailrocks-rust-skills` is not a Claude marketplace (its pinned repo has a plugin manifest but no marketplace manifest). Codex still fails because the released fallback URL `https://chatgpt.com/codex/install.sh` returned HTTP 404 three times. These failures are preserved; no role feature or plugin was removed. OpenCode authentication and a coding task remain NOT TESTED.

## Supported-agent image paths from the Architect role

The actual role's declared supported list is Claude, Codex, Amp, OpenCode, Kimi, and Grok. Each was selected through the pinned 6e `prewarm --agent <agent> --image` operation against the same local role source revision `93a46c2...` and pinned local published base. Distinct output images were retagged before subsequent builds could overwrite Jackin's shared mutable tag.

| Agent | Image construction / installation | OpenShell execution evidence | Result |
| --- | --- | --- | --- |
| Claude | Fallback installed Claude Code 2.1.310, then full role build failed while registering the invalid Tailrocks marketplace; no complete image | None for this full role image | FAIL; authenticated task BLOCKED (no approved credentials) |
| Codex | Fallback `https://chatgpt.com/codex/install.sh` returned HTTP 404 on all 3 attempts | None | FAIL; authenticated task BLOCKED (no approved credentials) |
| OpenCode | Fallback installed 1.19.4; full role image passed image construction | In GID/read-only-path workaround, actual preflight then `opencode --version` returned 1.19.4 | PASS for installation/version primitive under CONFIGURATION + WORKAROUND; authenticated task BLOCKED (no approved credentials) |
| Amp | Fallback installed `0.0.1792800065-ga5b55b` | In GID/read-only-path workaround, actual preflight then `amp --version` returned `0.0.1792800065-ga5b55b` | PASS for installation/version primitive under CONFIGURATION + WORKAROUND; authenticated task BLOCKED (no approved credentials) |
| Kimi | Fallback installed Kimi 2.3.1 | Image moves `.kimi-code` into `/jackin/default-home`; after explicitly seeding that image data into `/sandbox`, preflight and `kimi --version` passed | PASS for installation/version primitive under CONFIGURATION + WORKAROUND; authenticated task BLOCKED (no approved credentials) |
| Grok | Fallback installed Grok 1.0.70 | Image moves `.grok` into `/jackin/default-home`; after explicitly seeding that image data into `/sandbox`, preflight and `grok --version` passed | PASS for installation/version primitive under CONFIGURATION + WORKAROUND; authenticated task BLOCKED (no approved credentials) |

The historical first Amp reuse run's raw prewarm output was overwritten by a later forced build, so that observation alone is not used as evidence. A fresh isolated reproduction was run in `cache-agent-switch-confirm/`: before prewarm, mutable tag `jk_jfr24_architect:93a46c2` and immutable Grok tag `jfr24-architect-grok:93a46c2` both resolved to image ID `sha256:1d4bd013fbc63139a9f1b487845ba4519a625666042d4ca5a4836ca7ae72c64f`. The exact pinned Jackin 6e CLI command requested `prewarm --agent amp --image`, exited 0 in 16.461 seconds, and printed `amp reused jk_jfr24_architect:93a46c2`; both tags still resolved to that same Grok image afterward. That image was then supplied by immutable ID to OpenShell. The first too-long sandbox name was rejected before command execution; this attempt is retained as a failed reproduction detail. With a valid short sandbox name, OpenShell started the exact image using a nonzero UID/GID policy. A follow-up OpenShell command inspected the actual image paths and ran `/jackin/default-home/.grok/bin/grok --version`, which returned Grok 1.0.70, exit 0. No Amp executable existed at the expected `/home/agent/.local/bin/amp`, `/home/agent/.amp/bin/amp`, or `/jackin/default-home/.amp/bin/amp` locations; the exact reused image was therefore demonstrated to have Grok and lack selected Amp. This fresh result, not the overwritten historical run, supports the wrong-selected-agent reuse failure. After preserving the prior image under an immutable test tag and removing only the experiment-owned mutable Jackin tag, the actual `prewarm --agent amp --image` path installed Amp `0.0.1792800065-ga5b55b` into a distinct image, and OpenShell exec returned that version with exit 0. The tag removal is a WORKAROUND condition, not evidence of a supported force-rebuild flag. The lack of a force flag on released `prewarm` remains a gap. Fresh raw commands, output, status, image identities, and sandbox evidence are retained in `cache-agent-switch-confirm/`, `cache-agent-switch-confirm-retry/`, and `cache-agent-switch-confirm-paths/`.

For Kimi/Grok, the first OpenShell version attempts also show the generated image depends on Capsule `runtime-setup` seeding `/jackin/default-home` into the home. OpenShell did not run the image ENTRYPOINT. The successful test performed an explicit copy into `/sandbox`; a full rewrite must implement equivalent seed/retained-state behavior and prove it across recreation. These version commands do not establish model authentication or coding-task success.

The OpenCode seed was also copied into `/sandbox`; with `OPENCODE_CONFIG_CONTENT={"permission":"allow"}`, the explicit `opencode --model zai/glm-5.2 --version` command passed and returned 1.19.4. This confirms the role's model flag/config is accepted by the selected CLI without making a model request.

Jackin `prewarm` has no force-rebuild flag. The old `load --rebuild` command was not run because it would continue into the Docker runtime. A forced rebuild is therefore NOT TESTED through the supported prewarm path.

## Authentication status

No approved live-agent test credentials were available. No personal credentials were read or used. Authenticated coding tasks for the supported agents are **BLOCKED** by missing approved credentials; version commands are installation evidence only and do not pass this requirement.

## Session and retained-home boundaries

The full Jackin Capsule/session contract remains **BLOCKED** by the released OpenShell root-identity restriction and the macOS Landlock requirement. Canonical PTY command completion does not prove reconnect-to-the-same-agent-session, focus/control arbitration, or conversation resume. Private agent-home persistence across sandbox deletion and recreation is **NOT TESTED**. Kimi/Grok/OpenCode state was explicitly copied from `/jackin/default-home` into `/sandbox` for isolated version/configuration probes; those copies do not prove persistent-volume ownership, correct account separation, or retention after recreation.

## Raw files

- Jackin build: `results/full-refactor-20261024/agents/jackin-cli-6e/`.
- Prewarm: `results/full-refactor-20261024/agents/architect-claude-image-6e/`.
- Capsule builds and isolation: `results/full-refactor-20261024/agents/capsule-build-6e/`.
- Prewarm reproduction script: `experiments/full-refactor-20261024/agents/prewarm-architect-claude-6e.py`.
- Frozen-source rebuild procedure and its precise two-file role diff: `experiments/full-refactor-20261024/agents/role-reproduction/` (`rebuild-role-image.sh`, `architect-role-inputs.patch`, and hashes). The role patch changes only `published_image` and adds the behavior-neutral preflight comment. The script uses sparse checkout and a curated Docker context to exclude the host environment file; it requires a separately built Linux ARM64 Capsule artifact.
- Scoped sandbox cleanup manifest and receipt: `experiments/full-refactor-20261024/agents/owned-sandbox-cleanup-manifest.json` and `results/full-refactor-20261024/agents/owned-sandbox-cleanup/`. The exact 15 owned role/Capsule/session fixture sandboxes were deleted and verified absent.
- Owned image-tag cleanup receipt: `experiments/full-refactor-20261024/agents/owned-image-cleanup-manifest.json` and `results/full-refactor-20261024/agents/owned-image-cleanup/`. The 11 exact derived/test tags were removed after identity and no-container-reference checks. The shared Architect base tag and Docker caches were preserved. Capsule and CLI binaries remain in experiment-only results for hash-verified reproduction and are not included in public staging.
