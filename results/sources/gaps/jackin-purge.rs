# Extract: `crates/services/jackin-runtime/src/runtime/cleanup/purge.rs`

Source: `jackin-project/jackin` @ `41bad147b5ba9db09be99b07248531ce1bd867be`.

Lines 63–85 implement persisted-state deletion: reject preservation holds, require backend resources absent, clean isolated workspace mounts, remove the per-instance state directory, then remove its socket directory. This separates runtime teardown (`eject`/`exile`) from state deletion (`purge`).
