FROM rust:1.99.1-bookworm@sha256:48b7f435b8fc6378ce43b44f15e3a47fd8919b2825f835c39bd4bd3da50af5b8
RUN cargo install cargo-nextest --locked --version 0.9.140
WORKDIR /workspace/rust-project
CMD ["cargo", "nextest", "run"]
