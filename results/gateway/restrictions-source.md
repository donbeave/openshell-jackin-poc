# Released source analysis: live connections and executable rebuilds

Source version: OpenShell v0.1.5, commit `bdb956f2cd65a635f1294fccf1d138d263bf650f`. This is source inspection only; the associated runtime failures are recorded separately by the policy and native test experiments.

## Live connections during network-policy reload

The enforcement owner is the sandbox's `openshell-supervisor-network` process, not the Docker gateway. Its OPA engine (`crates/openshell-supervisor-network/src/opa.rs`) atomically replaces the policy engine and advances one process-wide generation on every successful reload. `PolicyGenerationGuard` stores the captured generation and a receiver for changes. Its `wait_until_stale()` comment explicitly says relay boundaries use this to close idle or raw streams when a new generation, including fail-closed quarantine, is published.

The relay owner is `crates/openshell-supervisor-network/src/proxy/relay.rs`: HTTP and raw relay setup pin the current generation; relay loops select on `generation_guard.wait_until_stale()` and emit a stale-policy close. `proxy.rs` handles stale relay setup by ending the connection. Thus a valid policy update that does not affect a particular established flow still increments the global generation and closes that flow. The experiment's Docker stream truncation and Redis EOF match this behavior; the no-change control remaining open is also consistent.

Smallest upstream capability: generation changes need to preserve established flows whose authorization is unchanged, while promptly closing or revalidating flows affected by a changed or revoked rule. A scope-aware authorization lease (or equivalent comparison of each flow's endpoint, protocol, identity, and matched rule against the new policy) is required. Simply suppressing the stale-generation close would weaken revocation and fail-closed guarantees. No such change was attempted; this would need targeted tests for allowed unrelated changes, changed rules, explicit revocation, and races at policy activation.

Released source links:

- [`opa.rs` generation and reload](https://github.com/NVIDIA/OpenShell/blob/bdb956f2cd65a635f1294fccf1d138d263bf650f/crates/openshell-supervisor-network/src/opa.rs)
- [`proxy/relay.rs` generation-pinned relays](https://github.com/NVIDIA/OpenShell/blob/bdb956f2cd65a635f1294fccf1d138d263bf650f/crates/openshell-supervisor-network/src/proxy/relay.rs)
- [`proxy.rs` stream handling](https://github.com/NVIDIA/OpenShell/blob/bdb956f2cd65a635f1294fccf1d138d263bf650f/crates/openshell-supervisor-network/src/proxy.rs)

## Rebuilding a network-authorized executable at the same path

The integrity owner is `crates/openshell-supervisor-network/src/identity.rs`, specifically `BinaryIdentityCache::verify_or_cache_with_paths`. The cache is keyed by executable path. On a cache hit, a filesystem fingerprint (size, mtime, ctime, and Unix device/inode) avoids rehashing. When the fingerprint changes, the file is hashed again and compared with the first SHA-256 pinned for that path. A changed digest returns `Binary integrity violation: <path> executable changed`. Supplied executable identity chains are also pinned by path and digest. This is fail-closed trust-on-first-use behavior, not an accidental cache miss.

The experiments found that rebuilding to the same path changes the hash and causes an identity denial; building to a distinct executable path passes. The native failure remains recorded. Smallest upstream capability: a narrowly scoped, authenticated way to rotate the pinned digest after an intentional build, with explicit approval of the new digest and auditability, while preserving automatic denial for unapproved changes. Alternatives include a lifecycle operation that deliberately starts a fresh identity cache after verifying policy and runtime state. Merely clearing the cache on any file change would remove the current tamper protection. No source patch was attempted.

Released source links:

- [`identity.rs` cache, fingerprint, and digest comparison](https://github.com/NVIDIA/OpenShell/blob/bdb956f2cd65a635f1294fccf1d138d263bf650f/crates/openshell-supervisor-network/src/identity.rs)
- [`sandbox-policy.rego` binary matching and TOFU boundary](https://github.com/NVIDIA/OpenShell/blob/bdb956f2cd65a635f1294fccf1d138d263bf650f/crates/openshell-supervisor-network/data/sandbox-policy.rego)

## Namespace-isolated gateway durability check

The diagnostic sandbox `ojp-20261024-gwl` (ID `57bac7d3-5c2b-46ff-a7e8-2fbce16d6422`) was created under the unique released Docker `sandbox_label="ojp-20261024"`, with an approved named volume mounted at `/workspace/ojp-project`. At 22:39:23 UTC—about 10 minutes 59 seconds after creation—it remained Phase `Ready`; both sandbox and supervisor containers were running, and the workload was not OOM-killed. See [`gateway-unique-label-after-5m.json`](../engine/gateway-unique-label-after-5m.json). This revalidates that the current test-gateway namespace avoids the earlier default-namespace reconciliation collision for a mounted sandbox. It does not test daemon ownership or cleanup behavior.
