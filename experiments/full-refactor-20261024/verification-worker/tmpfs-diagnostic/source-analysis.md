# Tmpfs API path diagnosis

Source is the pinned OpenShell v0.1.5 commit `bdb956f2cd65a635f1294fccf1d138d263bf650f`, file `crates/openshell-driver-docker/src/lib.rs`.

- `docker_driver_mounts` and `docker_mount_from_config` at lines 3859–3912 translate `DockerDriverMountConfig::Tmpfs` into a structured Docker `MountTypeEnum::TMPFS` mount, with a `MountTmpfsOptions` value.
- `docker_tmpfs_option` at lines 4033–4051 converts a bare flag such as `nosuid` to a one-element option array and a key/value option such as `size=...` to two elements. The generated Bollard type documents `MountTmpfsOptions.options` as an array of arrays, with bare flags represented as one-element arrays.
- `build_sandbox_container` puts those user mounts into `HostConfig.mounts` at lines 5999–6011. It separately initializes the legacy `HostConfig.tmpfs` map for the supervisor CA runtime path at lines 6040–6046.

Execution isolates an API-path difference on the same OrbStack Docker engine and the same image:

1. OpenShell v0.1.5 structured `Mount` with `tmpfs_options` failed before sandbox readiness. Gateway log records Docker API 400, `invalid option: nosuid`.
2. The standalone Docker CLI create-only control accepted the exact same tmpfs options and sizes through `HostConfig.Tmpfs`. `docker inspect` reported:

   ```json
   {"/build":"rw,nosuid,size=268435456","/tmp":"rw,noexec,nosuid,size=67108864"}
   ```

   The exact container was never started. It was removed by ID; a subsequent inspect returned no such object.

**Conclusion (bounded):** the observed failure is specific to the released OpenShell structured tmpfs mount route on this tested engine. The engine's legacy `HostConfig.Tmpfs` path accepts the requested configuration. Runtime mount flags are not yet proven because the control was create-only and no OpenShell worker reached Ready.

**Small patch candidate (not implemented here):** leave mount validation intact; remove user tmpfs entries from the structured `Mount` vector; merge their targets and validated option strings into the existing `HostConfig.tmpfs` map while preserving the supervisor CA entry and rejecting duplicate targets. Keep named volumes on structured `Mount`. Then run the full worker policy unchanged, verify `noexec` by executing a harmless binary placed on the tmpfs and expecting `EACCES`, verify `nosuid` under a controlled setuid fixture without granting new capabilities, and run a malformed-option/forbidden-target negative test. If the negative `nosuid` result cannot be safely demonstrated under the existing no-new-privileges/cap-drop contract, do not claim it; keep that guarantee unresolved.
