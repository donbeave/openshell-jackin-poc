#!/bin/sh
# Historical direct-Docker hook probe. Disabled by policy; use the isolated OpenShell gateway fixture.
echo "Disabled: this historical diagnostic used Docker to run a role workload and agent version command." >&2
echo "Use OpenShell sandbox execution for hook and version evidence." >&2
exit 2
