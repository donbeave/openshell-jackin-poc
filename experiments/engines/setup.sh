#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
IMAGE='docker:29.8.2-dind@sha256:1e08cdb63405ca788aea94ef35b792d1e299607c667d33d7bcbcae1fd2611ced'

for name in ojp-20261024-engine-a ojp-20261024-engine-b; do
    if docker inspect "$name" >/dev/null 2>&1; then
        echo "fixture already exists: $name; inspect before reuse" >&2
        exit 1
    fi
done

issue() {
    name=$1
    dir="$ROOT/private/$name"
    if [ -s "$dir/ca.pem" ] && [ -s "$dir/server/cert.pem" ] && [ -s "$dir/client/cert.pem" ]; then
        openssl verify -CAfile "$dir/ca.pem" "$dir/server/cert.pem" "$dir/client/cert.pem"
        return
    fi
    mkdir -p "$dir/server" "$dir/client"
    chmod 700 "$dir" "$dir/server" "$dir/client"
    openssl ecparam -name prime256v1 -genkey -noout -out "$dir/ca.key"
    openssl req -x509 -new -key "$dir/ca.key" -sha256 -days 7 -subj "/CN=ojp-$name-ca" -out "$dir/ca.pem"
    openssl ecparam -name prime256v1 -genkey -noout -out "$dir/server/key.pem"
    openssl req -new -key "$dir/server/key.pem" -subj "/CN=host.docker.internal" -out "$dir/server.csr"
    cat > "$dir/server.ext" <<EOF
subjectAltName=DNS:host.docker.internal,DNS:localhost,IP:127.0.0.1
extendedKeyUsage=serverAuth
keyUsage=digitalSignature,keyEncipherment
EOF
    openssl x509 -req -in "$dir/server.csr" -CA "$dir/ca.pem" -CAkey "$dir/ca.key" -CAcreateserial -days 7 -sha256 -extfile "$dir/server.ext" -out "$dir/server/cert.pem"
    cp "$dir/ca.pem" "$dir/server/ca.pem"
    openssl ecparam -name prime256v1 -genkey -noout -out "$dir/client/key.pem"
    openssl req -new -key "$dir/client/key.pem" -subj "/CN=ojp-$name-client" -out "$dir/client.csr"
    cat > "$dir/client.ext" <<EOF
extendedKeyUsage=clientAuth
keyUsage=digitalSignature,keyEncipherment
EOF
    openssl x509 -req -in "$dir/client.csr" -CA "$dir/ca.pem" -CAkey "$dir/ca.key" -CAcreateserial -days 7 -sha256 -extfile "$dir/client.ext" -out "$dir/client/cert.pem"
    cp "$dir/ca.pem" "$dir/client/ca.pem"
    chmod 600 "$dir/ca.key" "$dir/server/key.pem" "$dir/client/key.pem"
    rm "$dir"/*.csr "$dir"/*.ext "$dir"/*.srl
    openssl verify -CAfile "$dir/ca.pem" "$dir/server/cert.pem" "$dir/client/cert.pem"
}

issue engine-a
issue engine-b

for item in 'engine-a 18776 15432 18080-18084 18080 18084' 'engine-b 18777 15433 18085-18089 18085 18089'; do
    set -- $item
    name=$1
    port=$2
    service_port=$3
    auto_ports=$4
    auto_start=$5
    auto_end=$6
    container="ojp-20261024-$name"
    volume="ojp-20261024-$name-project"
    docker volume create --label openshell.ai/sandbox-attachable=true --label openshell.ai/sandbox-attachable-workspace=default "$volume" >/dev/null
    docker run -d --name "$container" --hostname "$name" --privileged \
        --cpus=2 --memory=4g \
        --label ojp.test-id=ojp-20261024 --label ojp.owner=experiments/engines/setup.sh \
        --publish "$port:2376" \
        --publish "$service_port:$service_port" \
        --publish "$auto_ports:$auto_ports" \
        --sysctl "net.ipv4.ip_local_port_range=$auto_start $auto_end" \
        --mount "type=bind,src=$ROOT/private/$name,dst=/certs,readonly" \
        --mount "type=volume,src=$volume,dst=/sandbox/ojp-project" \
        --env DOCKER_TLS_CERTDIR=/certs \
        "$IMAGE" >/dev/null
done

for item in 'engine-a 18776 15432 18080-18084' 'engine-b 18777 15433 18085-18089'; do
    set -- $item
    name=$1
    port=$2
    service_port=$3
    auto_ports=$4
    attempt=0
    until docker --host "tcp://127.0.0.1:$port" --tlsverify \
        --tlscacert "$ROOT/private/$name/client/ca.pem" \
        --tlscert "$ROOT/private/$name/client/cert.pem" \
        --tlskey "$ROOT/private/$name/client/key.pem" info >/dev/null 2>&1; do
        attempt=$((attempt + 1))
        [ "$attempt" -lt 60 ] || { echo "readiness timeout: $name" >&2; exit 1; }
        sleep 2
    done
done

echo "engine-a=tcp://host.docker.internal:18776; service=15432; auto=18080-18084"
echo "engine-b=tcp://host.docker.internal:18777; service=15433; auto=18085-18089"
docker inspect ojp-20261024-engine-a ojp-20261024-engine-b --format '{{.Name}} {{.Image}} {{.Id}} {{json .HostConfig.PortBindings}} {{json .Mounts}}'
