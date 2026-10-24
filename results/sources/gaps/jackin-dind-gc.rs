# Extract: `crates/services/jackin-runtime-cleanup-dind-gc/src/dind_gc.rs`

Source: `jackin-project/jackin` @ `41bad147b5ba9db09be99b07248531ce1bd867be`.

Lines 28–57 enumerate labeled DinD sidecars and classify one as orphaned when its role container is absent. Lines 60–149 sweep orphaned sidecars and then cert volumes/networks. It does not sweep an individual Testcontainers child while its Jackin role and DinD owner remain alive. This is eventual whole-sidecar orphan cleanup, not crash cleanup for an individual test client.
