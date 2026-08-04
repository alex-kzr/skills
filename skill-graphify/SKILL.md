---
name: skill-graphify
description: Graphify Skills Knowledge Graph — build and query a knowledge graph of the skills library for intelligent skill discovery, domain classification, and metadata validation. Use when an agent needs to find relevant skills for a task, detect duplicates, or validate skill documentation completeness.
---

# Graphify Skills Knowledge Graph

## Overview

Graphify is a specialized skill for building and querying a dedicated knowledge graph of the skills library. It allows AI agents to intelligently search, analyze, and select relevant skills for a given task without indexing the full project monorepo.

## Purpose

- **Skills Search**: Find relevant skills for specific domains (Rust, Docker, PostgreSQL, payment systems, etc.)
- **Skills Analysis**: Identify duplicates, overlaps, and missing metadata
- **Domain Classification**: Group skills by domain and category
- **Metadata Validation**: Detect skills missing README or DESCRIPTION files
- **Agent Assistance**: Help agents select the right skill for a task

## Key Features

1. **Isolated Indexing**: Indexes only the skills folder, not the entire monorepo
2. **Domain-Specific Queries**: Answer questions about skill categories and relationships
3. **Metadata Analysis**: Validate and report on skill documentation completeness
4. **Fast Graph-Based Search**: Uses Graphify's knowledge graph for intelligent queries
5. **Cross-Platform Support**: Scripts for Linux/macOS (Bash) and Windows (PowerShell)

## Installation

### Prerequisites

- **uv** package manager: https://docs.astral.sh/uv/

### Linux/macOS

```bash
bash skills/skill-graphify/scripts/install.sh
```

### Windows PowerShell

```powershell
.\skills\skill-graphify\scripts\install.ps1
```

## Building the Graph

The graph indexes the skills folder and generates searchable knowledge graph files.

### Linux/macOS

```bash
bash skills/skill-graphify/scripts/build.sh ../../skills
```

### Windows PowerShell

```powershell
.\skills\skill-graphify\scripts\build.ps1 -SkillsDir "..\..\skills"
```

### Output Files

After building, the following files are generated in `graphify-graph/graphify-out/`:

- `graph.html` - Interactive HTML visualization of the skills graph
- `graph.json` - Machine-readable knowledge graph
- `GRAPH_REPORT.md` - Human-readable report with detected skills and categories

## Querying Skills

### Common Queries

```bash
# List all skills grouped by domain
graphify query "List all available skills grouped by domain"

# Find skills for specific technologies
graphify query "Which skills are relevant for Rust development?"
graphify query "Which skills are relevant for Docker and VPS administration?"
graphify query "Which skills are relevant for PostgreSQL database analysis?"

# Find overlapping or duplicate skills
graphify query "Find duplicated or overlapping skills"

# Validate metadata
graphify query "Which skills are missing README or DESCRIPTION metadata?"

# Agent-focused queries
graphify query "Which skills should an agent use for codebase analysis?"
graphify query "Which skills are relevant for payment system analysis?"
```

### Using Query Scripts

#### Linux/macOS

```bash
bash skills/skill-graphify/scripts/query.sh "Which skills are relevant for Rust development?"
```

#### Windows PowerShell

```powershell
.\skills\skill-graphify\scripts\query.ps1 -Question "Which skills are relevant for Rust development?"
```

## Agent Workflow

When an AI agent needs to select a skill for a task:

1. **Query the Graph**: Ask Graphify about relevant skills for the task
2. **Review Results**: Examine the skills identified by the graph
3. **Read Skill Files**: Only read the SKILL.md or README.md of selected skills
4. **Apply Skill**: Use the selected skill's logic and recommendations
5. **Report Findings**: If no relevant skill is found, report this limitation

## Metadata Requirements

Each skill should have:

- `SKILL.md` or `README.md` in the skill's directory
- Clear description of purpose and use cases
- Tags or categories (Rust, Docker, PostgreSQL, etc.)
- Examples of relevant queries

## Maintenance

### Rebuild the Graph When

- New skills are added to the skills folder
- Existing skills are removed or renamed
- Skill documentation (README.md or SKILL.md) is significantly updated
- New skill categories or domains are introduced

### Schedule

- **Frequency**: Rebuild after major skill library changes
- **Automation**: Can be integrated into CI/CD pipelines for periodic updates

## File Structure

```text
skills/skill-graphify/
├── SKILL.md (this file)
└── scripts/
    ├── install.sh (Linux/macOS installation)
    ├── install.ps1 (Windows PowerShell installation)
    ├── build.sh (Linux/macOS graph building)
    ├── build.ps1 (Windows PowerShell graph building)
    ├── query.sh (Linux/macOS querying)
    └── query.ps1 (Windows PowerShell querying)

graphify-graph/
├── README.md (usage guide)
├── .graphifyignore (exclusion rules)
└── graphify-out/
    ├── graph.html (interactive visualization)
    ├── graph.json (machine-readable graph)
    └── GRAPH_REPORT.md (analysis report)
```

## Limitations

- Requires Graphify CLI tool installed
- Requires `uv` package manager
- Graph must be rebuilt when skills change
- Queries depend on skill documentation quality
- Large skill libraries may take time to index

## Related Documentation

- Graphify Documentation: https://graphifyy.readthedocs.io/
- Skills Library: See individual skill SKILL.md or README.md files
- Knowledge Graphs: Generic guide to building and querying knowledge graphs

## Support

For issues or questions:

1. Check Graphify documentation
2. Verify skills folder path is correct
3. Ensure .graphifyignore is not excluding skill metadata files
4. Rebuild the graph with fresh data
5. Check GRAPH_REPORT.md for analysis details
