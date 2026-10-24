#!/bin/sh
set -eu
BASE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PKI="$BASE/private/certs"
CA="$BASE/gateway-rctl/certs/ca.crt"
mkdir -p "$PKI"
chmod 700 "$BASE/private" "$PKI"
issue() {
  name=$1; subject=$2; serial=$3
  openssl genpkey -algorithm EC -pkeyopt ec_paramgen_curve:P-256 -out "$PKI/$name.key" >/dev/null 2>&1
  openssl req -new -key "$PKI/$name.key" -subj "$subject" -out "$PKI/$name.csr" >/dev/null 2>&1
  printf 'extendedKeyUsage=clientAuth\nkeyUsage=digitalSignature\n' > "$PKI/$name.ext"
  openssl x509 -req -in "$PKI/$name.csr" -CA "$CA" -CAkey "$BASE/gateway-rctl/certs/ca.key" -set_serial "$serial" -days 2 -sha256 -extfile "$PKI/$name.ext" -out "$PKI/$name.crt" >/dev/null 2>&1
  rm "$PKI/$name.csr" "$PKI/$name.ext"
}
issue wrong-ou-client '/CN=jfr-rctl-wrong-ou/OU=not-authorized' 440024
openssl req -x509 -newkey ec -pkeyopt ec_paramgen_curve:P-256 -nodes -days 2 -subj '/CN=jfr-rctl-untrusted-ca' -keyout "$PKI/wrong-ca.key" -out "$PKI/wrong-ca.crt" >/dev/null 2>&1
chmod 600 "$PKI"/*.key
openssl verify -CAfile "$CA" "$PKI/wrong-ou-client.crt"
openssl genpkey -algorithm EC -pkeyopt ec_paramgen_curve:P-256 -out "$PKI/untrusted-client.key" >/dev/null 2>&1
openssl req -new -key "$PKI/untrusted-client.key" -subj '/CN=jfr-rctl-untrusted-client/OU=openshell-user' -out "$PKI/untrusted-client.csr" >/dev/null 2>&1
printf 'extendedKeyUsage=clientAuth\nkeyUsage=digitalSignature\n' > "$PKI/untrusted-client.ext"
openssl x509 -req -in "$PKI/untrusted-client.csr" -CA "$PKI/wrong-ca.crt" -CAkey "$PKI/wrong-ca.key" -set_serial 440025 -days 2 -sha256 -extfile "$PKI/untrusted-client.ext" -out "$PKI/untrusted-client.crt" >/dev/null 2>&1
rm "$PKI/untrusted-client.csr" "$PKI/untrusted-client.ext"
chmod 600 "$PKI/untrusted-client.key"
openssl verify -CAfile "$PKI/wrong-ca.crt" "$PKI/untrusted-client.crt"
