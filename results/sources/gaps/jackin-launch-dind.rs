# Extract: crates/services/jackin-runtime-launch-dind/src/launch_dind.rs

Source: `jackin-project/jackin` @ `41bad147b5ba9db09be99b07248531ce1bd867be`.

Lines 55–80 define labels for role-owned resources, including `LABEL_MANAGED` and `jackin.role=<container_name>`. Lines 88–105 expose `run_dind_sidecar_headless`, retaining the resulting `ContainerHandle` in `dind_handle_slot`. Lines 143–154 construct the owned network and Dind sidecar. Lines 193 onward apply `LABEL_KIND_DIND`; lines 223 onward retain the handle for lifecycle coordination.

This proves Jackin's current Docker backend owns and labels its DinD companion as part of the Jackin instance. It does not make OpenShell the required owner of an external daemon.
