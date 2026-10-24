#!/bin/sh
set -eu
: "${OJP_VALUE:?OJP_VALUE is required}"
printf '%s\n' "$OJP_VALUE" >> /workspace/hook.log
exec "$@"
