#!/usr/bin/env bash
# Runs once, the first time the codespace is created.
# Subsequent starts of the same codespace skip this.

set -euo pipefail

echo "==> Installing uv..."
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc

echo "==> Installing Python 3.11..."
uv python install 3.11

echo "==> Syncing project dependencies..."
if [ -f pyproject.toml ]; then
  uv sync --all-extras
fi

echo "==> Installing pre-commit hooks..."
if [ -f .pre-commit-config.yaml ]; then
  uv run pre-commit install
fi

echo "==> Setup complete."