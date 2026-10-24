# Extract: `crates/apps/jackin-capsule/src/firewall.rs`

Source: `jackin-project/jackin` @ `41bad147b5ba9db09be99b07248531ce1bd867be`.

Lines 43–49 load `JACKIN_ALLOWED_HOSTS` and require `iptables`, `ip6tables`, and `ipset`. Lines 52–56 install IPv4/IPv6 rules. Lines 63–97 install DNS and allowlist rules. Lines 164–177 set OUTPUT default to DROP while admitting loopback and established traffic. Dispatcher `crates/apps/jackin-capsule/src/client_dispatch.rs` routes `firewall-apply` to this function. Runtime profile code invokes it via a root container exec only when `NetworkGrant::Allowlist` (see `jackin-docker-profile-readme.md` and `jackin-network-egress-policy.mdx`). This is actual role-container enforcement. It does not impose the policy inside external DinD children.
