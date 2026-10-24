# Extract: crates/services/jackin-runtime-docker-profile/README.md

Source: `jackin-project/jackin` @ `41bad147b5ba9db09be99b07248531ce1bd867be`.

> Docker security profile resolution and flag emission.

This crate owns resolution (`resolve_profile`, `resolve_effective_grants`, `ProfileSource`) and Docker flag generation (`capability_flags`, `resource_flags`, `readonly_root_flags`, tmpfs paths, labels).

Runtime-level Docker security configuration is thus Jackin-owned; it is separable from the lower-level execution substrate.
