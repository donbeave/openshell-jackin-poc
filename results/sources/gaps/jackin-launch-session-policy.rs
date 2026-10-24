# Extract: `crates/services/jackin-runtime/src/runtime/launch/launch_runtime/session.rs`

Source: `jackin-project/jackin` @ `41bad147b5ba9db09be99b07248531ce1bd867be`.

Lines 12–18 define `apply_post_run_policy`. Lines 29–39 append `firewall_apply` for the selected profile; lines 48–69 run it via Docker exec and fail closed by removing the role container if installation fails. `launch_runtime.rs` calls this function immediately after starting the role container and before starting the usage relay/agent session. This confirms Jackin installs allowlist egress before the agent starts; it is not merely a roadmap statement.
