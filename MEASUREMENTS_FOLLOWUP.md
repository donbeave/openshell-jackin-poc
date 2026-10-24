# Follow-up measurements and limits

These are component measurements, not a full-refactor benchmark. Each number has one sample unless stated otherwise. No tail percentiles or speedup claims are made. No shared cache was removed to manufacture cold conditions.

## Image construction on the same macOS ARM64 / OrbStack builder

Actual Jackin6e CLI, Architect7b-derived local pinned base, Linux6e Capsule, selected supported agent. Local role source018fb47 pins the published-base reference;93a46c2 adds a comment to the declared preflight. Complete input/image identities are in the per-agent JSON.

| Operation | Time | Cache condition / outcome |
|---|---:|---|
| OpenCode full derived image |77.774s| New derived tag; role/base/tool caches already present. PASS build; not a fully cold machine. |
| OpenCode unchanged prewarm |16.46s| Valid same-agent image reuse; no rebuild. |
| Declared role-source comment change |94.899s| Changed role/recipe/image digest; base/layers reused. |
| Amp intended build |78.725s| Owned mutable tag removed after immutable preservation because previous selected-agent reuse was wrong. This is a workaround condition, not a supported force flag. |
| Kimi intended build |108.355s| Same explicit missing-owned-tag condition; shared layers retained. |
| Grok intended build |119.05s| Same condition. |
| Claude failed full role build |72.05s| Installer ran; required marketplace setup failed. Not time to readiness. |
| Codex failed build |54.76s| Three404 installer attempts; not readiness. |
| Fresh wrong-agent cache confirmation |16.461s| Amp requested, Grok image reused. This is a FAIL, not a valid warm-agent result. |

Reported image sizes are logical Docker sizes, not additive unique disk consumption: role base6,133,969,953bytes; OpenCode13,981,089,043; Amp13,782,869,687; Kimi13,895,692,503; Grok13,808,679,580. Their layers overlap; do not sum them as experiment disk growth.

## Control, limits and idle sample

- One idle gateway-A sample before its sandbox workloads:0.4%CPU,134,496KiB RSS (about131.3MiB). `results/full-replacement-20261024/idle-resources.json` contains exact command/time. This is instantaneous consumption, not peak.
- Corrected Rust duplex:1,048,601stdout bytes (1MiB payload plus markers/input),500ms deliberate receiver pause, exact hash and split-NUL/EOF checks. This is a bounded correctness experiment, not throughput/tail-latency measurement.
- Small local sandbox limit:250m CPU/256MiB; bounded CPU workload increased throttling and512MiB allocation was OOM-killed. Configuration and enforcement observations are separate in workspace evidence.
- Worker:1CPU/512MiB/64PIDs and64MiB/256MiB tmpfs were configured and probed. The64PID cgroup includes OpenShell supervisor threads; only seven additional fixture children could start before EAGAIN in the recorded sample. It is not a64-usable-child budget.
- Worker OOM was enforced. One wrapper returned247 after childSIGKILL(-9); another observation returned74 and the sandbox lost readiness. This is not a predictable survival/exit contract. Unknown infrastructure outcome must remain explicit.
- Added Linux guest limits were2CPU/4GiB/32GiB from OrbStack/cgroup evidence. Its Docker API misleadingly reported host-scale18CPUs/~122GiB; that is not available guest allocation.
- Packaged VM configured2vCPU/2048MiB and reported2CPUs/2,036,904KiB MemTotal. No exhaustion enforcement or peak-consumption claim follows from guest sizing.

## Costs not established

Full cold/warm actual authenticated agent readiness, attach/reconnect latency distributions, daemon readiness timing, remote image transfer, peak supervisor/agent/account-domain costs, aggregate engine/children enforcement, simultaneous logical-instance startup, complete stop/cleanup timing and current-Jackin full-journey comparison remain NOT TESTED or BLOCKED. Component command completion is not application readiness. Model authentication is unavailable, and the complete candidate journey has not run.

Docker parent-engine memory already includes its children; any future per-child sample is attribution, not an additional term to add to parent consumption. Supervisor/agent shared cgroups also require avoiding double counting. Configured allocations are separate from measured consumption.

Disk audit samples under `results/full-refactor-20261024/disk-samples.jsonl` show ample space during concurrent work. Shared Docker build cache and unrelated workloads changed concurrently, so global growth is not an attributable per-instance cost. Scoped cleanup receipts describe only resources actually removed. Shared caches were preserved. A14MiB abandoned target remains after automatic deletion review rejected removal; it never blocked research.
