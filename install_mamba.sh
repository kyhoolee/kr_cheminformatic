#!/usr/bin/env bash
# Install micromamba to ~/.local/bin and initialize bash shell hook.
set -euo pipefail

PLATFORM="$(uname -s)"
ARCH="$(uname -m)"

case "$PLATFORM" in
  Linux)  TARGET="linux-64" ;;
  Darwin) TARGET="osx-64" ;;
  *) echo "Unsupported platform: $PLATFORM" >&2; exit 1 ;;
esac

if [[ "$PLATFORM" == "Darwin" && "$ARCH" == "arm64" ]]; then
  TARGET="osx-arm64"
fi

INSTALL_DIR="$HOME/.local/bin"
mkdir -p "$INSTALL_DIR"
echo "Downloading micromamba ($TARGET) to $INSTALL_DIR ..."
curl -Ls "https://micro.mamba.pm/api/micromamba/${TARGET}/latest" \
  | tar -xj -C "$INSTALL_DIR" --strip-components=1 bin/micromamba

export PATH="$INSTALL_DIR:$PATH"
echo "PATH updated: $PATH"

echo "Initializing shell hook..."
micromamba shell init -s bash -p "$HOME/.micromamba"

echo "Reloading shell to activate micromamba hook..."
exec "$SHELL"
