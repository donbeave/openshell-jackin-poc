#!/bin/sh
set -eu
BASE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
GATEWAY_NAME=${GATEWAY_NAME:-jrr24-capsule-a-poc}
GATEWAY_PORT=${GATEWAY_PORT:-18818}
SANDBOX_LABEL=${SANDBOX_LABEL:-jrr24-capsule-a-poc}
CERTS="$BASE/certs"
mkdir -p "$CERTS/server" "$CERTS/client" "$CERTS/jwt" "$BASE/config" "$BASE/state/runtime" "$BASE/state/xdg"
chmod 700 "$CERTS" "$CERTS/server" "$CERTS/client" "$CERTS/jwt" "$BASE/state" "$BASE/state/runtime" "$BASE/state/xdg"
if [ ! -s "$CERTS/ca.key" ]; then
  openssl ecparam -name prime256v1 -genkey -noout -out "$CERTS/ca.key"
  openssl req -x509 -new -key "$CERTS/ca.key" -sha256 -days 3 -subj "/CN=$GATEWAY_NAME-ca" -out "$CERTS/ca.crt"
  openssl ecparam -name prime256v1 -genkey -noout -out "$CERTS/server/tls.key"
  openssl req -new -key "$CERTS/server/tls.key" -subj "/CN=localhost" -out "$CERTS/server/server.csr"
  printf 'subjectAltName=DNS:localhost,IP:127.0.0.1\nextendedKeyUsage=serverAuth\nkeyUsage=digitalSignature,keyEncipherment\n' > "$CERTS/server/server.ext"
  openssl x509 -req -in "$CERTS/server/server.csr" -CA "$CERTS/ca.crt" -CAkey "$CERTS/ca.key" -CAcreateserial -days 3 -sha256 -extfile "$CERTS/server/server.ext" -out "$CERTS/server/tls.crt"
  openssl ecparam -name prime256v1 -genkey -noout -out "$CERTS/client/tls.key"
  openssl req -new -key "$CERTS/client/tls.key" -subj "/CN=$GATEWAY_NAME-client" -out "$CERTS/client/client.csr"
  printf 'extendedKeyUsage=clientAuth\nkeyUsage=digitalSignature,keyEncipherment\n' > "$CERTS/client/client.ext"
  openssl x509 -req -in "$CERTS/client/client.csr" -CA "$CERTS/ca.crt" -CAkey "$CERTS/ca.key" -CAcreateserial -days 3 -sha256 -extfile "$CERTS/client/client.ext" -out "$CERTS/client/tls.crt"
  openssl genpkey -algorithm ED25519 -out "$CERTS/jwt/signing.pem"
  openssl pkey -in "$CERTS/jwt/signing.pem" -pubout -out "$CERTS/jwt/public.pem"
  openssl rand -hex 16 > "$CERTS/jwt/kid"
  rm "$CERTS/server/server.csr" "$CERTS/server/server.ext" "$CERTS/client/client.csr" "$CERTS/client/client.ext"
  rm -f "$CERTS/ca.srl"
  chmod 600 "$CERTS/ca.key" "$CERTS/server/tls.key" "$CERTS/client/tls.key" "$CERTS/jwt/signing.pem"
fi
cat > "$BASE/gateway.toml" <<EOF2
[openshell]
version = 2
[openshell.gateway]
name = "$GATEWAY_NAME"
bind_address = "127.0.0.1:$GATEWAY_PORT"
compute_driver = "docker"
guest_tls_ca = "$CERTS/ca.crt"
[openshell.drivers.docker]
allow_driver_config = false
sandbox_label = "$SANDBOX_LABEL"
[openshell.gateway.tls]
cert_path = "$CERTS/server/tls.crt"
key_path = "$CERTS/server/tls.key"
client_ca_path = "$CERTS/ca.crt"
[openshell.gateway.gateway_jwt]
signing_key_path = "$CERTS/jwt/signing.pem"
public_key_path = "$CERTS/jwt/public.pem"
kid_path = "$CERTS/jwt/kid"
gateway_id = "$GATEWAY_NAME"
EOF2
cat > "$BASE/run-gateway.sh" <<EOF2
#!/bin/sh
set -eu
BASE="$BASE"
export XDG_CONFIG_HOME="\$BASE/config"
export XDG_STATE_HOME="\$BASE/state/xdg"
export OPENSHELL_GATEWAY_CONFIG="\$BASE/gateway.toml"
exec /opt/homebrew/opt/openshell/bin/openshell-gateway --config "\$BASE/gateway.toml" --bind-address 127.0.0.1 --port $GATEWAY_PORT --tls-cert "\$BASE/certs/server/tls.crt" --tls-key "\$BASE/certs/server/tls.key" --tls-client-ca "\$BASE/certs/ca.crt" --enable-mtls-auth true --compute-driver docker
EOF2
cat > "$BASE/client.sh" <<EOF2
#!/bin/sh
set -eu
BASE="$BASE"
export XDG_CONFIG_HOME="\$BASE/config"
export XDG_STATE_HOME="\$BASE/state/xdg"
export OPENSHELL_LOCAL_TLS_DIR="\$BASE/certs"
exec /opt/homebrew/opt/openshell/bin/openshell --gateway $GATEWAY_NAME "\$@"
EOF2
chmod 700 "$BASE/run-gateway.sh" "$BASE/client.sh"
openssl verify -CAfile "$CERTS/ca.crt" "$CERTS/server/tls.crt" "$CERTS/client/tls.crt"
