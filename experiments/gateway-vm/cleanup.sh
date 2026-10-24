#!/bin/sh
set -eu
BASE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
RESULTS="$BASE/../../results/gateway-vm"
STATE="$BASE/state/runtime"
SANDBOX_NAME=ojp-20261024-vm1

case "$BASE" in
    */openshell-jackin-poc/experiments/gateway-vm) ;;
    *) echo "refusing unexpected cleanup path: $BASE" >&2; exit 1 ;;
esac

mkdir -p "$RESULTS"
if [ -f "$BASE/gateway.toml" ]; then
    cp "$BASE/gateway.toml" "$RESULTS/gateway-config.toml"
fi
if [ -f "$BASE/gateway-vm.log" ]; then
    cp "$BASE/gateway-vm.log" "$RESULTS/gateway-startup.log"
fi

if [ -x "$BASE/client.sh" ] && [ -f "$BASE/config/openshell/active_gateway" ]; then
    "$BASE/client.sh" gateway info >/dev/null || {
        echo "VM gateway unavailable; retaining state for manual cleanup" >&2
        exit 1
    }
    "$BASE/client.sh" sandbox delete "$SANDBOX_NAME" >/dev/null 2>&1 || true
    deleted=false
    for attempt in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30; do
        if ! "$BASE/client.sh" sandbox get "$SANDBOX_NAME" >/dev/null 2>&1; then
            deleted=true
            break
        fi
        sleep 1
    done
    if [ "$deleted" != true ]; then
        echo "sandbox record still exists; retaining VM gateway and state" >&2
        exit 1
    fi
fi

# Delete removes the instance overlay and its private per-sandbox state. Wait
# for those processes and files before shutting down the gateway or removing
# its cache. A residual instance is a hard stop: preserve its state for review.
for attempt in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30; do
    instance_alive=false
    for pid in $(pgrep -f "$STATE/sandboxes/" 2>/dev/null || true); do
        [ "$pid" = "$$" ] && continue
        instance_alive=true
    done
    if [ -d "$STATE/sandboxes" ] && [ -n "$(find "$STATE/sandboxes" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null)" ]; then
        instance_alive=true
    fi
    [ "$instance_alive" = false ] && break
    sleep 1
done
if [ "$instance_alive" = true ]; then
    echo "VM instance processes or state remain; retaining gateway and runtime" >&2
    exit 1
fi

for pid in $(lsof -tiTCP:18771 -sTCP:LISTEN 2>/dev/null || true); do
    command=$(ps -p "$pid" -o command= 2>/dev/null || true)
    case "$command" in *"$BASE/gateway.toml"*) kill -TERM "$pid" 2>/dev/null || true ;; esac
done

for attempt in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30; do
    driver_alive=false
    for pid in $(pgrep -f "$STATE/run/compute-driver.sock" 2>/dev/null || true); do
        [ "$pid" = "$$" ] && continue
        driver_alive=true
    done
    gateway_alive=false
    for pid in $(lsof -tiTCP:18771 -sTCP:LISTEN 2>/dev/null || true); do
        command=$(ps -p "$pid" -o command= 2>/dev/null || true)
        case "$command" in *"$BASE/gateway.toml"*) gateway_alive=true ;; esac
    done
    [ "$driver_alive" = false ] && [ "$gateway_alive" = false ] && break
    sleep 1
done
if [ "$driver_alive" = true ] || [ "$gateway_alive" = true ]; then
    echo "VM gateway or driver remains; retaining runtime and credentials" >&2
    exit 1
fi

rm -rf "$BASE/state" "$BASE/config" "$BASE/certs"
printf 'Removed this experiment VM runtime, client config, and ephemeral certificates. Preserved gateway.toml and logs.\n'
