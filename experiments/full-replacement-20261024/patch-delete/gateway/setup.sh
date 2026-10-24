#!/bin/sh
set -eu
BASE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
CERTS="$BASE/certs"
mkdir -p "$CERTS/server" "$CERTS/client" "$CERTS/jwt" "$BASE/config" "$BASE/state/runtime"
chmod 700 "$CERTS" "$CERTS/server" "$CERTS/client" "$CERTS/jwt" "$BASE/state" "$BASE/state/runtime"

if [ ! -s "$CERTS/ca.key" ]; then
    openssl ecparam -name prime256v1 -genkey -noout -out "$CERTS/ca.key"
    openssl req -x509 -new -key "$CERTS/ca.key" -sha256 -days 7 -subj "/CN=jfr-20261024-pdel-ca" -out "$CERTS/ca.crt"
    openssl ecparam -name prime256v1 -genkey -noout -out "$CERTS/server/tls.key"
    openssl req -new -key "$CERTS/server/tls.key" -subj "/CN=localhost" -out "$CERTS/server/server.csr"
    cat > "$CERTS/server/server.ext" <<EOF
subjectAltName=DNS:localhost,IP:127.0.0.1
extendedKeyUsage=serverAuth
keyUsage=digitalSignature,keyEncipherment
EOF
    openssl x509 -req -in "$CERTS/server/server.csr" -CA "$CERTS/ca.crt" -CAkey "$CERTS/ca.key" -CAcreateserial -days 7 -sha256 -extfile "$CERTS/server/server.ext" -out "$CERTS/server/tls.crt"
    openssl ecparam -name prime256v1 -genkey -noout -out "$CERTS/client/tls.key"
    openssl req -new -key "$CERTS/client/tls.key" -subj "/CN=jfr-20261024-pdel-client/OU=openshell-user" -out "$CERTS/client/client.csr"
    cat > "$CERTS/client/client.ext" <<EOF
extendedKeyUsage=clientAuth
keyUsage=digitalSignature,keyEncipherment
EOF
    openssl x509 -req -in "$CERTS/client/client.csr" -CA "$CERTS/ca.crt" -CAkey "$CERTS/ca.key" -CAcreateserial -days 7 -sha256 -extfile "$CERTS/client/client.ext" -out "$CERTS/client/tls.crt"
    rm "$CERTS/server/server.csr" "$CERTS/server/server.ext" "$CERTS/client/client.csr" "$CERTS/client/client.ext"
    rm -f "$CERTS/ca.srl"
    chmod 600 "$CERTS/ca.key" "$CERTS/server/tls.key" "$CERTS/client/tls.key"
fi

if [ ! -s "$CERTS/jwt/signing.pem" ]; then
    openssl genpkey -algorithm ED25519 -out "$CERTS/jwt/signing.pem"
    openssl pkey -in "$CERTS/jwt/signing.pem" -pubout -out "$CERTS/jwt/public.pem"
    openssl rand -hex 16 > "$CERTS/jwt/kid"
    chmod 600 "$CERTS/jwt/signing.pem"
fi

cat > "$BASE/gateway.toml" <<EOF
[openshell]
version = 2
[openshell.gateway]
compute_driver = "docker"
guest_tls_ca = "$CERTS/ca.crt"
[openshell.drivers.docker]
allow_driver_config = true
sandbox_label = "jfr-20261024-pdel"
[openshell.gateway.gateway_jwt]
signing_key_path = "$CERTS/jwt/signing.pem"
public_key_path = "$CERTS/jwt/public.pem"
kid_path = "$CERTS/jwt/kid"
gateway_id = "jfr-20261024-pdel"
EOF
openssl verify -CAfile "$CERTS/ca.crt" "$CERTS/server/tls.crt" "$CERTS/client/tls.crt"
