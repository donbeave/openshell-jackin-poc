#!/bin/sh
set -eu
BASE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PRIV="$BASE/private/certs"
GATEWAY_CA="$BASE/../gateway-a/certs"
mkdir -p "$PRIV"
chmod 700 "$PRIV"
issue_client() {
  cn=$1
  ou=$2
  stem=$3
  openssl genpkey -algorithm EC -pkeyopt ec_paramgen_curve:P-256 -out "$PRIV/$stem.key" >/dev/null 2>&1
  openssl req -new -key "$PRIV/$stem.key" -subj "/CN=$cn/OU=$ou" -out "$PRIV/$stem.csr" >/dev/null 2>&1
  printf 'extendedKeyUsage=clientAuth\nkeyUsage=digitalSignature\n' > "$PRIV/$stem.ext"
  openssl x509 -req -in "$PRIV/$stem.csr" -CA "$GATEWAY_CA/ca.crt" -CAkey "$GATEWAY_CA/ca.key" -set_serial "0x$(printf '%s' "$stem" | od -An -tx1 | tr -d ' \n')" -days 2 -sha256 -extfile "$PRIV/$stem.ext" -out "$PRIV/$stem.crt" >/dev/null 2>&1
}
issue_client jfr-control-20261024 openshell-user control-client
issue_client jfr-invalid-20261024 invalid-user wrong-ou-client
openssl req -x509 -newkey ec -pkeyopt ec_paramgen_curve:P-256 -nodes -days 2 -subj /CN=jfr-wrong-ca-20261024 -keyout "$PRIV/untrusted-ca.key" -out "$PRIV/untrusted-ca.crt" >/dev/null 2>&1
openssl genpkey -algorithm EC -pkeyopt ec_paramgen_curve:P-256 -out "$PRIV/untrusted-client.key" >/dev/null 2>&1
openssl req -new -key "$PRIV/untrusted-client.key" -subj /CN=jfr-untrusted-client-20261024/OU=openshell-user -out "$PRIV/untrusted-client.csr" >/dev/null 2>&1
printf 'extendedKeyUsage=clientAuth\nkeyUsage=digitalSignature\n' > "$PRIV/untrusted-client.ext"
openssl x509 -req -in "$PRIV/untrusted-client.csr" -CA "$PRIV/untrusted-ca.crt" -CAkey "$PRIV/untrusted-ca.key" -set_serial 904241024 -days 2 -sha256 -extfile "$PRIV/untrusted-client.ext" -out "$PRIV/untrusted-client.crt" >/dev/null 2>&1
openssl verify -CAfile "$GATEWAY_CA/ca.crt" "$PRIV/control-client.crt" "$PRIV/wrong-ou-client.crt" >/dev/null
openssl verify -CAfile "$PRIV/untrusted-ca.crt" "$PRIV/untrusted-client.crt" >/dev/null
printf 'generated unique client identities; private keys retained under experiment-owned ignored directory\n'
