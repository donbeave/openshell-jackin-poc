#!/bin/sh
set -eu
ROOT=/var/lib/jfr-20261024-linux
CERTS="$ROOT/certs"
IP=192.168.139.147
openssl ecparam -name prime256v1 -genkey -noout -out "$CERTS/server/private-ip.key"
openssl req -new -key "$CERTS/server/private-ip.key" -subj "/CN=$IP" -out "$CERTS/server/private-ip.csr"
printf '%s\n' "subjectAltName=DNS:localhost,IP:127.0.0.1,IP:$IP" 'extendedKeyUsage=serverAuth' 'keyUsage=digitalSignature,keyEncipherment' > "$CERTS/server/private-ip.ext"
openssl x509 -req -in "$CERTS/server/private-ip.csr" -CA "$CERTS/ca.crt" -CAkey "$CERTS/ca.key" -CAcreateserial -days 7 -sha256 -extfile "$CERTS/server/private-ip.ext" -out "$CERTS/server/private-ip.crt"
openssl verify -CAfile "$CERTS/ca.crt" "$CERTS/server/private-ip.crt"
rm -f "$CERTS/server/private-ip.csr" "$CERTS/server/private-ip.ext" "$CERTS/ca.srl"
chmod 600 "$CERTS/server/private-ip.key"
