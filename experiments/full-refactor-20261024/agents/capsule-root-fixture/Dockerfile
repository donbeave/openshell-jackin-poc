FROM jfr-20261024-architect-tools:1.99.1-1.27.0
USER root
RUN mkdir -p /jackin/run /jackin/runtime && chown -R agent:1000 /jackin
COPY --chown=agent:1000 --chmod=0755 jackin-capsule /jackin/runtime/jackin-capsule
COPY --chown=agent:1000 --chmod=0644 agent.toml /jackin/run/agent.toml
USER 1000:1000
