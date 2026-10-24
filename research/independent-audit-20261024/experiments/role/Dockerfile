FROM jrr24-architect-role-base:7b72b38fe1d6
ARG CLAUDE_VERSION
ARG ROLE_REVISION=7b72b38fe1d66e35c0931899c53bf3719592bbcc
ARG ROLE_CONTENT_SHA
ARG JACKIN_CACHE_BUST=0
LABEL org.jackin.poc.role.revision=${ROLE_REVISION} \
      org.jackin.poc.role.content.sha=${ROLE_CONTENT_SHA} \
      org.jackin.poc.agent=claude \
      org.jackin.poc.agent.version=${CLAUDE_VERSION}
USER root
COPY ${CLAUDE_VERSION}/claude /jackin/agent-binaries/claude
COPY preflight.sh /jackin/runtime/hooks/preflight.sh
RUN chmod 0755 /jackin/agent-binaries/claude /jackin/runtime/hooks/preflight.sh
USER agent
ENV XDG_CACHE_HOME=/home/agent/.cache
ENV PATH=/home/agent/.local/bin:/home/agent/.local/share/mise/shims:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
RUN --mount=type=cache,id=jrr24-role-claude,target=/home/agent/.cache,uid=1000,gid=1000,sharing=locked \
    set -euxo pipefail && \
    : "${JACKIN_CACHE_BUST}" && \
    /jackin/agent-binaries/claude install && \
    claude --version
USER agent
RUN set -eu; \
    (claude plugin marketplace add anthropics/claude-plugins-official || true); \
    claude plugin marketplace add jackin-project/jackin-marketplace; \
    claude plugin marketplace add JuliusBrussee/caveman; \
    claude plugin install 'code-review@claude-plugins-official'; \
    claude plugin install 'code-simplifier@claude-plugins-official'; \
    claude plugin install 'feature-dev@claude-plugins-official'; \
    claude plugin install 'commit-commands@claude-plugins-official'; \
    claude plugin install 'github@claude-plugins-official'; \
    claude plugin install 'claude-md-management@claude-plugins-official'; \
    claude plugin install 'security-guidance@claude-plugins-official'; \
    claude plugin install 'pr-review-toolkit@claude-plugins-official'; \
    claude plugin install 'rust-analyzer-lsp@claude-plugins-official'; \
    claude plugin install 'jackin-dev@jackin-marketplace'; \
    claude plugin install 'caveman@caveman'; \
    rm -rf /home/agent/.claude/backups
USER agent
WORKDIR /workspace
