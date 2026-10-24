# Extract: `crates/services/jackin-runtime-docker-profile/src/docker_profile/exec.rs`

Source: `jackin-project/jackin` @ `41bad147b5ba9db09be99b07248531ce1bd867be`.

Lines 24–30:

```rust
pub fn firewall_post_run_argv<'a>(
    grants: &EffectiveGrants,
    container_ref: &'a str,
) -> Option<[&'a str; 6]> {
    (grants.network == NetworkGrant::Allowlist)
        .then(|| capsule_root_exec_argv(container_ref, "firewall-apply"))
}
```

This active function creates the firewall command only for allowlist network mode, targeting the role container reference.
