#!/usr/bin/env bash
set -euo pipefail

if [ "${1:-}" = "" ]; then
  echo "Usage: bash skills/skill-graphify/scripts/query.sh \"your question\""
  echo "Example: bash skills/skill-graphify/scripts/query.sh \"Which skills are relevant for Rust development?\""
  exit 1
fi

QUESTION="$1"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GRAPH_WORKSPACE="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$GRAPH_WORKSPACE"

if [ ! -f "graphify-out/graph.json" ]; then
  echo "Graph file not found: graphify-out/graph.json"
  echo "Build the graph first."
  exit 1
fi

graphify query "$QUESTION"
