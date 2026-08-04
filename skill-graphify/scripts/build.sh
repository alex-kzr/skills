#!/usr/bin/env bash
set -euo pipefail

if [ "${1:-}" = "" ]; then
  echo "Usage: bash skills/skill-graphify/scripts/build.sh <absolute-or-relative-skills-folder>"
  echo "Example: bash skills/skill-graphify/scripts/build.sh .agents/skills"
  exit 1
fi

SKILLS_DIR="$1"

if [ ! -d "$SKILLS_DIR" ]; then
  echo "Skills folder does not exist: $SKILLS_DIR"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GRAPH_WORKSPACE="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$GRAPH_WORKSPACE"

echo "Building Graphify knowledge graph for skills folder only..."
echo "Skills folder: $SKILLS_DIR"
echo "Graph workspace: $GRAPH_WORKSPACE"

if graphify --help | grep -q "update"; then
  graphify update "$SKILLS_DIR"
else
  graphify "$SKILLS_DIR"
fi

echo "Skills graph build completed."
echo "Expected outputs:"
echo "- $GRAPH_WORKSPACE/graphify-out/graph.html"
echo "- $GRAPH_WORKSPACE/graphify-out/GRAPH_REPORT.md"
echo "- $GRAPH_WORKSPACE/graphify-out/graph.json"
