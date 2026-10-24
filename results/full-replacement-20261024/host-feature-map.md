# Complete command and retained host feature map

Pinned Jackin `41bad147b5ba9db09be99b07248531ce1bd867be`. All command variants in `crates/apps/jackin/src/cli.rs:89-154` are inventoried below. This is source mapping, not runtime execution or a host-feature PASS. Paths below are relative to `crates/apps/jackin/src/` except explicitly named service/core crates. Detailed source reports expand dependencies.

| Implemented surface | Source | Retained responsibility and runtime dependency | Matrix IDs |
|---|---|---|---|
| load/hardline/eject/exile/purge | app/load_cmd.rs; services/jackin-runtime/src/runtime/{launch,attach,cleanup} | OpenShell control, immutable resource identity, sessions and durable storage | R07–R16,R25–R29 |
| prewarm/prune | cli/prewarm.rs; app/prune_cmd.rs | Image builder/cache identities; optional engine adoption/ownership; safe cache deletion | R03,R26,R30 |
| console | cli/dispatch.rs:12-59; console modules | Host terminal/UI retained; runtime session/control/event transport required | R08–R10,R28,R33 |
| role validate/migrate/scaffold | cli/role.rs; role command dispatch | Retained host file validation and trust; installed role image/hook execution separately proved | R01,R03,R04 |
| workspace | app/workspace_cmd.rs; workspace modules | Host saved configuration/authorization retained; runtime files/Git semantics required | R12–R15 |
| account | app/account_cmd.rs; services/jackin-instance-agents | Host account selection/authorization retained; credential staging/auth/resume required | R05,R06,R11 |
| config | app/config_cmd.rs; core/jackin-config | Host config/trust/mount grants retained; effective runtime policy enforcement required | R01,R12,R23,R24 |
| daemon | app/daemon_cmd.rs | Retained host broker/service; runtime control/session and secret resolution dependencies | R11,R16,R30,R33 |
| doctor | cli/doctor.rs | Host prerequisite diagnostics retained; target bootstrap failures and control qualification required | R16,R32 |
| diagnostics | cli/diagnostics.rs | Host OTLP validation retained; workload observability transport separately required | R10,R33 |
| status | cli/status.rs | Host inventory/rendering retained; authenticated target status, unavailable target vs deletion distinction | R16,R28,R29,R32,R33 |
| workflow | app/workflow_cmd.rs; app/workflow_export.rs | Host repair planning/export retained; actual runtime mutation must satisfy identity/recovery/export | R10,R25–R29 |
| usage | cli/usage.rs; daemon usage modules | Broker cached usage/monitor state retained; deterministic workload usage/event relay; no billing correctness claim | R10,R33 |
| help/default dispatch | cli.rs:55-154; cli/dispatch.rs | Host-only help and terminal selection, no OpenShell implementation requirement | RETAINED HOST LOGIC |

Roles, hooks, plugins and skills are actual role inputs, not features OpenShell must select. OpenShell must execute their installed tools, filesystem access, networking, process identities and credential routes. Cached usage display is implemented host behavior; inactive account-authority and signed credential-transcript foundations are listed separately in control-source.md. Existing incomplete agents/Apple finalize are not OpenShell regressions. Newly requested VM/remote/Kubernetes support remains acceptance scope.
