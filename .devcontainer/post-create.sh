#!/usr/bin/env bash
set -euo pipefail

echo "==> Installing uv..."
curl -LsSf https://astral.sh/uv/install.sh | sh

# Make uv visible immediately and in future shells.
export PATH="$HOME/.local/bin:$PATH"
if ! grep -q 'HOME/.local/bin' "$HOME/.bashrc"; then
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
fi

echo "==> Installing Python 3.11..."
uv python install 3.11

echo "==> Syncing project dependencies (if pyproject.toml exists)..."
if [ -f pyproject.toml ]; then
  uv sync --all-extras
fi

echo "==> Installing pre-commit hooks (if config exists)..."
if [ -f .pre-commit-config.yaml ]; then
  uv run pre-commit install || echo "(skipped — will install on next commit)"
fi

echo "==> Setup complete."
