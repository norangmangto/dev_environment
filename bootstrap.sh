#!/usr/bin/env bash
# Mandatory bootstrap: ensure Homebrew + uv exist, then hand off to the
# Python TUI (install.py) for everything else. Safe to re-run.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v brew >/dev/null 2>&1; then
  echo "==> Homebrew not found, installing..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  if [ -x /opt/homebrew/bin/brew ]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
  elif [ -x /usr/local/bin/brew ]; then
    eval "$(/usr/local/bin/brew shellenv)"
  fi
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "==> uv not found, installing via Homebrew..."
  brew install uv
fi

exec uv run "$SCRIPT_DIR/install.py"
