FROM python@sha256:1b668429b3511ab407d8e00648891631b0b1a4d7e15e3ca70f38ab5b91ad4ab4
RUN printf 'jackin-test:x:1000:1000:Jackin test worker:/home/jackin-test:/bin/sh\n' >> /etc/passwd \
    && printf 'jackin-test:x:1000:\n' >> /etc/group \
    && mkdir -p /home/jackin-test /work/repo /jackin/checks /tmp /build \
    && chmod 0755 /home/jackin-test /work /work/repo /jackin /jackin/checks /tmp /build \
    && chown 1000:1000 /work/repo \
    && mkdir -p /etc/openshell
COPY patch-tmpfs/policy.yaml /etc/openshell/policy.yaml
USER 1000:1000
WORKDIR /work/repo
CMD ["/bin/sh", "-c", "sleep 3600"]
