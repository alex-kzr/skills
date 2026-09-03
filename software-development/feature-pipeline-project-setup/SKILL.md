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
   **source** location, its **destination** inside `tools/graphify/`, and any
   **`index_excludes`** — extra repository-relative paths (on top of `.gitignore`
   and Graphify's built-in cache skips) to keep out of the index.

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
  Graphify is enabled: `config/graphify.project.json` (project-local settings)
  and the approved wrapper. `tools/graphify/` is the Graphify **config/output
  home**, not the scan root.
- **Graphify indexing rules** — a tracked repository-root `.graphifyignore`
  (skill-owned, overwritten on regeneration). Graphify indexes the whole
  repository *from the root*, so its ignore file must live at the root. It
  always excludes `/tools/graphify/graphify-out/` and then any project-declared
  `index_excludes`. The root `.gitignore` and Graphify's built-in cache/venv
  skips are also honoured.
- **Generated Graphify artifacts** — only ever under
  `tools/graphify/graphify-out/`, and never tracked. The wrapper pins
  `GRAPHIFY_OUT` to that directory so output lands there even though the scan
  root is the repository root.
- **Ignore rule** — add exactly `/tools/graphify/graphify-out/` to the root
  `.gitignore`. Do not ignore the rest of `tools/graphify/`, and never ignore
  the tracked root `.graphifyignore`.
- **Setup report** — the actual commands run and their results.

The required Graphify output set is exactly five files under
`tools/graphify/graphify-out/`: `graph.json`, `GRAPH_REPORT.md`,
`manifest.json`, `.graphify_labels.json`, `.graphify_root`. `graph.html` may be
produced but its absence is not an error. See the reference for the exact
`integrations.json` `graphify` block, including `workspace` (config/output
home), `scan_root` (`.` — the repository root), `wrapper_dir`,
`diff_policy: tracked-empty`, and the installer denylist. The approved wrapper
must run `graphify update .` (repository root as the scan root) with
`GRAPHIFY_OUT` pinned to `tools/graphify/graphify-out`; passing
`tools/graphify` as the `graphify update` argument would index only that
directory.

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
4. Write the project-local configuration, Graphify config/output home, and the
   ignore rules listed above — nothing outside `tools/`, the root `.gitignore`,
   and the root `.graphifyignore`.
5. Produce the setup report with the exact commands and their results.

## Generator

`scripts/setup_project.py` performs steps 3–5 deterministically and
fail-closed. It validates the entire input before the first write, renders every
file in memory, then writes only under `tools/**`, the root `.gitignore`
(merged), and the root `.graphifyignore` (overwritten):

```
python scripts/setup_project.py --input <input.json> \
    --project-root <target repo> --report <repo-relative report path> --confirm
```

Without `--confirm` it refuses to write. Any contract violation (unknown key,
absolute/escaping path, `\` separator, shell-form `argv`, unapproved task type,
unresolved Graphify wrapper, target outside `tools/**`) stops the run before any
file is created. Check commands are always split into `config/checks.json` when
present, so `pipeline.profile.json` never also carries an inline `checks` array.
`scripts/test_project_setup.py` holds the fixture-based tests for both the
generator and the validator (run them with the shared runtime's
`python -m unittest`).

## Validator

`scripts/validate_project_setup.py` is a **read-only, fail-closed** check that a
generated setup conforms to both the portable profile schema and the
project-local Graphify policy. It only reads files and runs read-only Git
plumbing (`git rev-parse`, `git ls-files`, `git check-ignore`); it never
repairs, normalizes, or creates anything, never runs the wrapper, and never
requires `graph.html`. A failure is *evidence of a generator defect*, not
something to patch in project output.

```
python scripts/validate_project_setup.py --project-root <target repo> \
    --agents-root <agents checkout> --core-root <feature-pipeline-skill>
python scripts/validate_project_setup.py --self-test
```

It validates directory structure, JSON syntax and schema, known task types,
anchor-relative non-escaping paths, shell-free check `argv`, role/grant shape,
run-state placement, and — when Graphify is enabled — `workspace: tools/graphify`
and `scan_root: .`, an existing non-empty wrapper directory, exactly the five
required `expected_outputs` in order, `diff_policy: tracked-empty`, the complete
installer denylist, a tracked repository-root `.graphifyignore` that contains the
`/tools/graphify/graphify-out/` rule, the narrow `/tools/graphify/graphify-out/`
`.gitignore` rule (rejecting any rule that hides all of `tools/graphify/`), no
Git-tracked file under `tools/graphify/graphify-out/`, and that tracked
configuration, wrappers, and the root `.graphifyignore` are not Git-ignored. It prints a JSON report and exits `0` when valid, `1` on any
finding, `2` on a bad invocation (missing anchor, not a Git work tree). `--self-test`
builds its fixture only in a temporary directory and proves both the passing and
failing paths leave the tree byte-identical. Stable finding codes are listed in
[references/project-profile-contract.md](references/project-profile-contract.md).

## Smoke harness

`scripts/smoke_project_setup.py` proves the generated setup can drive the
portable core's **safe planning path** end to end, without a live project and
without any delivery side effect. In one fresh temporary directory it builds a
complete minimal fixture (its own Git work tree, a stub core tree, an approved
wrapper source), applies `setup_project.py`, runs `validate_project_setup.py`
read-only over the result, derives a portable-core `profile.json` + `plan.json`
**from the generated `pipeline.profile.json` / `checks.json`** (task types,
working roots, check `argv`, role grants, run-state location — all straight from
setup output), then invokes the explicitly located core CLI exactly twice:
`--help` (exit `0`) and one `--mode plan-only --dry-run` scenario (exit `10`, a
delivery gate pending).

```
python scripts/smoke_project_setup.py --self-test \
    --core-root <feature-pipeline checkout> [--agents-root <agents checkout>]
```

Both roots are explicit and never inferred from a home directory. Every
subprocess argv is a shell-free list checked *before* launch; an argv carrying a
Graphify installer, `commit`, or `push` raises before any process starts, and
the harness never runs the Graphify wrapper or Graphify itself. It snapshots
every path outside the temporary directory it can reach (the core checkout, and
an external `--agents-root`) and fails if a byte changes. `--self-test` runs the
whole flow twice from independent temporary directories and exits `0` only when
the redacted, timing-free reports are byte-identical, the exit contract held,
Graphify was not executed, and nothing outside the temp dir moved; `1` on any
smoke-contract failure; `2` when the core cannot be resolved or does not expose
`plan-only --dry-run`. `scripts/test_project_setup.py` holds its tests
(argv guard, generated-input translation, successful smoke, core non-zero exit,
out-of-fixture mutation detection, nondeterministic-report detection).
