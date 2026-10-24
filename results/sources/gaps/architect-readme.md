# Extract: `jackin-project/jackin-the-architect` README.md

Source: `jackin-project/jackin-the-architect` @ `7b72b38fe1d66e35c0931899c53bf3719592bbcc`.

> The Architect is the jackin agent role for developing jackin itself (role identifier `the-architect`). It provides the Rust development environment needed to build and test the jackin CLI.
>
> `jackin` validates this repo's Dockerfile, derives the final image itself, and mounts the cached repo checkout into `/workspace` when you run `jackin load the-architect`.

Lines 25–29 describe the Rust build tools and Cargo helper tools in the environment. `jackin-toolchain/mise.toml` pins `cargo-nextest` (`aqua:nextest-rs/nextest/cargo-nextest`) plus `cargo-audit`, `cargo-hack`, and related tools. This is direct evidence of the supported user workflow, not merely a theoretical way to execute a changed binary.
