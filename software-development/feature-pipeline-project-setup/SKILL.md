---
name: feature-pipeline-project-setup
description: "Generate a repository's project-local feature-pipeline and Graphify configuration without touching the portable pipeline core. Use when onboarding a new project to the feature pipeline, when a repository needs tracked tools/feature-pipeline and tools/graphify workspaces, a pipeline profile, an integration contract, or setup smoke checks, or when adopting project-local Graphify. Do not use to edit the portable core, run Graphify installers, install dependencies, or create commits."
---

# Feature Pipeline Project Setup

## Overview

This skill builds the **project-local** integration layer that the portable
feature-pipeline core (`feature-pipeline-skill/`) deliberately does not carry:
per-project task routing, technology checks, run-state location, agent grants,
and the Graphify workspace. The core stays portable; every project-specific
literal — paths, check commands, artifact names, roles — lives in the target
repository's own configuration.

**Boundary:** this skill only *writes project-local configuration into the
target repository*. It never edits `feature-pipeline-skill/pipeline_core/**`,
never runs Graphify installer subcommands, never installs language
dependencies, and never runs `git commit` or `git push`.

The exact schemas, path rules, the five required Graphify outputs, the
machine-readable input and report shapes, and the error contract are in
[references/project-profile-contract.md](references/project-profile-contract.md).
Read that file before generating anything.

## Inputs

Every input is either passed explicitly or discovered and then **confirmed by
the user before any file is written**. A missing or unconfirmed value fails
closed — never guess a quality command, substitute a similar one, or invent a
path.

Required:

1. **Anchors** — explicit `project_root`, `agents_root`, and `core_root`
   (the portable `feature-pipeline-skill/` checkout). All three are given, not
   inferred.
2. **Task routing** — the supported task types and the working root each one
   maps to.
3. **Technology stacks** — the stacks in play and, per stack, the exact
   repository-defined check commands as `argv` + `cwd` pairs (no shell string,
   no operators).
4. **Run state** — the path where the pipeline stores run state.
5. **Roles and grants** — the agent roles used and the minimum grants each
   role needs.
6. **Graphify** — whether Graphify is enabled and, if so, the approved wrapper
   **source** location and its **destination** inside the project workspace.

Present discovered values as a list and wait for explicit confirmation.
Treat unconfirmed or absent values as a hard stop, not a default.

## Outputs and ownership

When inputs are confirmed, generate only these, all POSIX-style and
anchor-relative:

- **Project pipeline configuration** — tracked, under `tools/feature-pipeline/`:
  `config/pipeline.profile.json`, `config/integrations.json`, optional
  `config/checks.json` when checks are split out, an optional thin
  `run_pipeline.py` launcher, and `README.md`.
- **Graphify policy and wrappers** — tracked, under `tools/graphify/` when
  Graphify is enabled: `.graphifyignore` and `config/` (project-local settings
  and the approved wrapper).
- **Generated Graphify artifacts** — only ever under
  `tools/graphify/graphify-out/`, and never tracked.
- **Ignore rule** — add exactly `/tools/graphify/graphify-out/` to the root
  `.gitignore`. Do not ignore the rest of `tools/graphify/`.
- **Setup report** — the actual commands run and their results.

The required Graphify output set is exactly five files under
`tools/graphify/graphify-out/`: `graph.json`, `GRAPH_REPORT.md`,
`manifest.json`, `.graphify_labels.json`, `.graphify_root`. `graph.html` may be
produced but its absence is not an error. See the reference for the exact
`integrations.json` `graphify` block, including `workspace`, `wrapper_dir`,
`diff_policy: tracked-empty`, and the installer denylist.

## Prohibited

- Editing or adding project identity, Graphify literals, output paths, or
  toolchain commands to `feature-pipeline-skill/pipeline_core/**`.
- Running Graphify installer subcommands
  (`graphify claude install`, `graphify codex install`,
  `graphify antigravity install`) — they can rewrite shared `AGENTS.md`,
  `CLAUDE.md`, and `.agents/`.
- Automatic language/dependency installation (`pip install`, `npm install`, …).
- Creating commits or pushes, or staging generated Graphify output.
- Moving `--project-skill` into `tools/`; it resolves against `--agents-root`.
- Treating Graphify as an implemented CLI stage — current `--mode execute`
  stops after stage 9; stages 10–16 are a separate follow-up.

## Workflow

1. Read [references/project-profile-contract.md](references/project-profile-contract.md).
2. Collect the six required inputs; discover what you can and present every
   value for explicit confirmation.
3. Stop if any value is missing or unconfirmed.
4. Write the project-local configuration, Graphify workspace, and ignore rule
   listed above — nothing outside `tools/` and the root `.gitignore`.
5. Produce the setup report with the exact commands and their results.
