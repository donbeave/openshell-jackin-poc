FROM jfr24-architect-grok:93a46c2
USER root
RUN if ! getent group sandbox >/dev/null; then \
      if getent group 1000 >/dev/null; then \
        groupmod -n sandbox "$(getent group 1000 | cut -d: -f1)"; \
      else \
        groupadd --gid 1000 sandbox; \
      fi; \
    fi \
    && usermod --gid sandbox agent \
    && chgrp -R sandbox /home/agent /jackin/default-home \
    && chmod -R g+rwX /home/agent /jackin/default-home
USER agent:sandbox
