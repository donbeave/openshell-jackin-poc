# Extract: `crates/services/jackin-runtime-docker-profile/src/docker_profile/effective.rs`

Source: `jackin-project/jackin` @ `41bad147b5ba9db09be99b07248531ce1bd867be`.

Lines 26–79 define the actual profile defaults:

- `locked`: allowlist egress, no DinD (lines 28–41).
- `hardened`: allowlist egress, no DinD (lines 43–56).
- `standard`: open egress, no DinD (lines 58–71).
- `compat`: open egress, privileged DinD (lines 73–83).

`profile.rs` lines 32–46 resolves CLI override, workspace profile, config profile, then `DockerSecurityProfile::default()`. Thus the executable replacement gap is conditional for Jackin's constrained-egress + Docker-enabled development workflow; it is not a failure under the network-open, DinD-disabled compiled default.
