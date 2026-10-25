#!/bin/sh
# Pin the research tool independently of the Go application's dependencies.
set -eu

GHIDRA_INSTALL_DIR=${GHIDRA_INSTALL_DIR:-"$HOME/.local/share/rea/ghidra_12.1.4_PUBLIC"}
export GHIDRA_INSTALL_DIR
if [ -z "${JAVA_HOME:-}" ] && [ -d /opt/homebrew/opt/openjdk@25 ]; then
    JAVA_HOME=/opt/homebrew/opt/openjdk@25
    export JAVA_HOME
fi

exec npx --yes rea-agents@6.8.0 "$@"
