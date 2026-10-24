#!/bin/sh
set -eu
BASE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
CERTS="$BASE/certs"
mkdir -p "$CERTS/server" "$CERTS/client" "$CERTS/jwt" "$BASE/config" "$BASE/state/runtime"
chmod 700 "$CERTS" "$CERTS/server" "$CERTS/client" "$CERTS/jwt" "$BASE/state" "$BASE/state/runtime"

if [ ! -s "$CERTS/ca.key" ]; then
    openssl ecparam -name prime256v1 -genkey -noout -out "$CERTS/ca.key"
    openssl req -x509 -new -key "$CERTS/ca.key" -sha256 -days 7 -subj "/CN=ojp-20261024-vm-ca" -out "$CERTS/ca.crt"
    openssl ecparam -name prime256v1 -genkey -noout -out "$CERTS/server/tls.key"
    openssl req -new -key "$CERTS/server/tls.key" -subj "/CN=localhost" -out "$CERTS/server/server.csr"
    cat > "$CERTS/server/server.ext" <<EOF
subjectAltName=DNS:localhost,IP:127.0.0.1
extendedKeyUsage=serverAuth
keyUsage=digitalSignature,keyEncipherment
EOF
    openssl x509 -req -in "$CERTS/server/server.csr" -CA "$CERTS/ca.crt" -CAkey "$CERTS/ca.key" -CAcreateserial -days 7 -sha256 -extfile "$CERTS/server/server.ext" -out "$CERTS/server/tls.crt"
    openssl ecparam -name prime256v1 -genkey -noout -out "$CERTS/client/tls.key"
    openssl req -new -key "$CERTS/client/tls.key" -subj "/CN=ojp-20261024-vm-client" -out "$CERTS/client/client.csr"
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
name = "ojp-20261024-vm"
bind_address = "127.0.0.1:18771"
compute_driver = "vm"
guest_tls_ca = "$CERTS/ca.crt"

[openshell.drivers.vm]
driver_dir = "/opt/homebrew/opt/openshell/libexec"
state_dir = "$BASE/state/runtime"
grpc_endpoint = "https://127.0.0.1:18771"
default_image = "nvcr.io/nvidia/base/ubuntu:24.04"
bootstrap_image = "nvcr.io/nvidia/base/ubuntu:24.04"
vcpus = 2
mem_mib = 2048
overlay_disk_mib = 4096

[openshell.gateway.tls]
cert_path = "$CERTS/server/tls.crt"
key_path = "$CERTS/server/tls.key"
client_ca_path = "$CERTS/ca.crt"

[openshell.gateway.gateway_jwt]
signing_key_path = "$CERTS/jwt/signing.pem"
public_key_path = "$CERTS/jwt/public.pem"
kid_path = "$CERTS/jwt/kid"
gateway_id = "ojp-20261024-vm"
EOF

cat > "$BASE/run-gateway.sh" <<EOF
#!/bin/sh
set -eu
BASE="$BASE"
export XDG_CONFIG_HOME="\$BASE/config"
export XDG_STATE_HOME="\$BASE/state/xdg"
export OPENSHELL_GATEWAY_CONFIG="\$BASE/gateway.toml"
export PATH="/opt/homebrew/opt/e2fsprogs/sbin:\$PATH"
exec /opt/homebrew/opt/openshell/bin/openshell-gateway --config "\$BASE/gateway.toml" --bind-address 127.0.0.1 --port 18771 --tls-cert "\$BASE/certs/server/tls.crt" --tls-key "\$BASE/certs/server/tls.key" --tls-client-ca "\$BASE/certs/ca.crt" --enable-mtls-auth true --compute-driver vm
EOF

cat > "$BASE/client.sh" <<EOF
#!/bin/sh
set -eu
BASE="$BASE"
export XDG_CONFIG_HOME="\$BASE/config"
export XDG_STATE_HOME="\$BASE/state/xdg"
export OPENSHELL_LOCAL_TLS_DIR="\$BASE/certs"
exec /opt/homebrew/opt/openshell/bin/openshell --gateway ojp-20261024-vm "\$@"
EOF

chmod 700 "$BASE/run-gateway.sh" "$BASE/client.sh"
openssl verify -CAfile "$CERTS/ca.crt" "$CERTS/server/tls.crt" "$CERTS/client/tls.crt"
