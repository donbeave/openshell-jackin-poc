#!/bin/sh
set -eu
BASE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
CERTS="$BASE/certs"
[ ! -e "$CERTS/ca.key" ] && [ ! -e "$BASE/gateway.toml" ] || { echo "refusing to overwrite gateway-C state" >&2; exit 2; }
mkdir -p "$CERTS/server" "$CERTS/client" "$CERTS/jwt" "$BASE/config" "$BASE/state"
chmod 700 "$CERTS" "$CERTS/server" "$CERTS/client" "$CERTS/jwt" "$BASE/state"
openssl ecparam -name prime256v1 -genkey -noout -out "$CERTS/ca.key"
openssl req -x509 -new -key "$CERTS/ca.key" -sha256 -days 7 -subj '/CN=jfr-20261024-rctl-ca' -out "$CERTS/ca.crt"
openssl ecparam -name prime256v1 -genkey -noout -out "$CERTS/server/tls.key"
openssl req -new -key "$CERTS/server/tls.key" -subj '/CN=localhost' -out "$CERTS/server/server.csr"
printf 'subjectAltName=DNS:localhost,IP:127.0.0.1\nextendedKeyUsage=serverAuth\nkeyUsage=digitalSignature,keyEncipherment\n' > "$CERTS/server/server.ext"
openssl x509 -req -in "$CERTS/server/server.csr" -CA "$CERTS/ca.crt" -CAkey "$CERTS/ca.key" -CAcreateserial -days 7 -sha256 -extfile "$CERTS/server/server.ext" -out "$CERTS/server/tls.crt"
openssl ecparam -name prime256v1 -genkey -noout -out "$CERTS/client/tls.key"
openssl req -new -key "$CERTS/client/tls.key" -subj '/CN=jfr-20261024-rctl-client/OU=openshell-user' -out "$CERTS/client/client.csr"
printf 'extendedKeyUsage=clientAuth\nkeyUsage=digitalSignature,keyEncipherment\n' > "$CERTS/client/client.ext"
openssl x509 -req -in "$CERTS/client/client.csr" -CA "$CERTS/ca.crt" -CAkey "$CERTS/ca.key" -CAcreateserial -days 7 -sha256 -extfile "$CERTS/client/client.ext" -out "$CERTS/client/tls.crt"
openssl genpkey -algorithm ED25519 -out "$CERTS/jwt/signing.pem"
openssl pkey -in "$CERTS/jwt/signing.pem" -pubout -out "$CERTS/jwt/public.pem"
openssl rand -hex 16 > "$CERTS/jwt/kid"
chmod 600 "$CERTS/ca.key" "$CERTS/server/tls.key" "$CERTS/client/tls.key" "$CERTS/jwt/signing.pem"
cat > "$BASE/gateway.toml" <<EOF2
[openshell]
version = 2
[openshell.gateway]
compute_driver = "docker"
guest_tls_ca = "$CERTS/ca.crt"
[openshell.drivers.docker]
allow_driver_config = true
enable_bind_mounts = true
sandbox_label = "jfr-20261024-rctl"
[openshell.drivers.docker.resource_admission]
enabled = true
[openshell.gateway.gateway_jwt]
signing_key_path = "$CERTS/jwt/signing.pem"
public_key_path = "$CERTS/jwt/public.pem"
kid_path = "$CERTS/jwt/kid"
gateway_id = "jfr-20261024-rctl"
EOF2
rm "$CERTS/server/server.csr" "$CERTS/server/server.ext" "$CERTS/client/client.csr" "$CERTS/client/client.ext"
openssl verify -CAfile "$CERTS/ca.crt" "$CERTS/server/tls.crt" "$CERTS/client/tls.crt"
