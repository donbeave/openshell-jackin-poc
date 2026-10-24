#!/bin/sh
set -eu
BASE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

# Only stop the gateway that uses this experiment's exact config path.
if command -v lsof >/dev/null 2>&1; then
    LISTENER=$(lsof -t -iTCP:28620 -sTCP:LISTEN || true)
    if [ -n "$LISTENER" ]; then
        COMMAND=$(ps -p "$LISTENER" -o command= || true)
        case "$COMMAND" in
            *"$BASE/gatewayfresh/gateway.toml"*) kill "$LISTENER" ;;
            *)
                echo "Refusing to stop unrelated listener on 28620: $COMMAND" >&2
                exit 1
                ;;
        esac
    fi
fi

# Delete generated keys, gateway state, and local logs from this experiment only.
for GATEWAY in gateway gatewayfresh; do
    rm -rf \
        "$BASE/$GATEWAY/certs" \
        "$BASE/$GATEWAY/config" \
        "$BASE/$GATEWAY/state" \
        "$BASE/$GATEWAY/gateway.toml" \
        "$BASE/$GATEWAY/gateway.log" \
        "$BASE/$GATEWAY/gateway.pid"
done
