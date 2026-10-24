# Extract: `crates/services/jackin-runtime-cleanup-eject-resources/src/eject_resources.rs`

Source: `jackin-project/jackin` @ `41bad147b5ba9db09be99b07248531ce1bd867be`.

Lines 11–43 implement explicit eject: validate role/DinD identities, remove role container, remove DinD container when recorded, remove cert volume and network, then remove socket directory. This function does not delete the per-instance durable state directory. Removing the DinD container is the Jackin operation that ends all its child workloads.
