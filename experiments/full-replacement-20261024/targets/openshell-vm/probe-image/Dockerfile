FROM nvcr.io/nvidia/base/ubuntu@sha256:7e0f726d635d440d28a7f18e6498d3bdb76c7038bd4c90a090c21eb7c9f40686
LABEL jfr.experiment="jfr-20261024-vm" jfr.role="vm-target-probe"
RUN mkdir -p /workspace && chown 1000:1000 /workspace
COPY --chown=1000:1000 input.txt /workspace/role-marker
WORKDIR /workspace
