#!/usr/bin/env bash
set -euo pipefail

echo "Installing Graphify for skills knowledge graph..."

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required but was not found."
  echo "Install uv first: https://docs.astral.sh/uv/"
  exit 1
fi

uv tool install "graphifyy[pdf,office,openai]"

echo "Checking Graphify CLI..."
graphify --help

echo "Graphify installation completed."
