# Project Profile Contract

Detailed contract for [feature-pipeline-project-setup](../SKILL.md): input and
report shapes, generated file schemas, path rules, the exact Graphify output
set, and the error contract. `SKILL.md` stays lean; this file holds the
specifics.

## Table of Contents

- [Terms and anchors](#terms-and-anchors)
- [Path rules](#path-rules)
- [Input shape](#input-shape)
- [Confirmation and fail-closed rules](#confirmation-and-fail-closed-rules)
- [Generated layout](#generated-layout)
- [Schema: pipeline.profile.json](#schema-pipelineprofilejson)
- [Schema: integrations.json](#schema-integrationsjson)
- [Schema: checks.json](#schema-checksjson)
- [Graphify workspace and the five required outputs](#graphify-workspace-and-the-five-required-outputs)
- [Ignore rule and tracked/generated split](#ignore-rule-and-trackedgenerated-split)
- [Setup report shape](#setup-report-shape)
- [Error contract](#error-contract)
- [Out of scope](#out-of-scope)

## Terms and anchors

| Term | Meaning |
|---|---|
| `project_root` | The target repository this skill configures. All generated paths are relative to it. |
| `agents_root` | The shared agents repository checkout. `--project-skill` resolves against this, never against `project_root`. |
| `core_root` | The portable `feature-pipeline-skill/` checkout that provides the pipeline mechanism. Read-only for this skill. |
| `anchor-relative` | A path expressed relative to one named anchor (default `project_root`), never absolute and never containing `~` or `..`. |

The three anchors are always supplied explicitly by the caller. This skill does
not infer them from the current working directory.

## Path rules

- Every path written into configuration or the report is **POSIX-style**
  (`/` separators) even when generation runs on Windows.
- Every path is **anchor-relative**. No absolute path, no `~`, no `..`, no
  drive letter.
- Paths under `project_root` that this skill may create are limited to
  `tools/**` and the root `.gitignore`.
- `wrapper_dir` in `integrations.json` is an anchor-relative path to the
  approved Graphify wrapper scripts inside the project (normally under
  `tools/graphify/config/`).
- Generated Graphify artifacts are only ever under
  `tools/graphify/graphify-out/`.

## Input shape

The skill consumes one machine-readable object. All keys are required; there is
no implicit default.

```json
{
  "anchors": {
    "project_root": "<abs or caller-relative path to target repo>",
    "agents_root": "<path to shared agents repo>",
    "core_root": "<path to feature-pipeline-skill checkout>"
  },
  "task_routing": [
    { "task_type": "<name>", "working_root": "<anchor-relative dir>" }
  ],
  "technology_stacks": [
    {
      "stack": "<name>",
      "checks": [
        { "name": "<check id>", "argv": ["<exe>", "<arg>", "..."], "cwd": "<anchor-relative dir>" }
      ]
    }
  ],
  "run_state_path": "<anchor-relative path>",
  "roles": [
    { "role": "<name>", "min_grants": ["<grant>", "..."] }
  ],
  "graphify": {
    "enabled": true,
    "wrapper_source": "<path to approved wrapper scripts>",
    "wrapper_destination": "tools/graphify/config/<dir>"
  }
}
```

Rules:

- `task_routing` maps each supported task type to exactly one working root.
- `technology_stacks[].checks[].argv` is a real argv list — no shell string,
  no `|`, `&&`, `;`, `>`, or `<`. Each check carries its own `cwd`.
- `run_state_path` is a single anchor-relative path.
- `roles[].min_grants` lists the minimum grants for that role, nothing more.
- When `graphify.enabled` is `false`, `wrapper_source` and
  `wrapper_destination` are omitted and no `tools/graphify/` tree is created.

## Confirmation and fail-closed rules

- Any value that was **discovered** (not passed explicitly) must be presented
  to the user and explicitly confirmed before a single file is written.
- A missing, empty, or unconfirmed required value is a hard stop. Do not
  substitute a similar command, infer a path, or fall back to a default.
- The skill never guesses a quality/check command and never replaces an absent
  check with a lookalike.

## Generated layout

```text
<project_root>/
  .gitignore                       # adds exactly one line (see below)
  tools/
    feature-pipeline/
      config/
        pipeline.profile.json      # tracked
        integrations.json          # tracked
        checks.json                # tracked, only if checks are split out
      run_pipeline.py              # tracked, optional thin launcher
      README.md                    # tracked
    graphify/                      # only when graphify.enabled
      .graphifyignore              # tracked
      config/                      # tracked: project settings + approved wrapper
      graphify-out/                # generated, never tracked
        graph.json
        GRAPH_REPORT.md
        manifest.json
        .graphify_labels.json
        .graphify_root
```

Nothing is written outside `tools/**` and the root `.gitignore`.

## Schema: pipeline.profile.json

```json
{
  "schema_version": 1,
  "project": "<project name>",
  "anchors": {
    "agents_root": "<anchor-relative>",
    "core_root": "<anchor-relative>"
  },
  "task_routing": [
    { "task_type": "<name>", "working_root": "<anchor-relative dir>" }
  ],
  "run_state_path": "<anchor-relative path>",
  "roles": [
    { "role": "<name>", "min_grants": ["<grant>"] }
  ]
}
```

- `task_routing` mirrors the confirmed input, one entry per supported task
  type.
- `roles` carries only the minimum grants confirmed for each role.
- Checks live here inline under an optional `checks` array **or** are split
  into `checks.json`; never both.

## Schema: integrations.json

```json
{
  "schema_version": 1,
  "graphify": {
    "stage": "graphify",
    "executor": "runner:graphify",
    "workspace": "tools/graphify",
    "wrapper_dir": "<anchor-relative path to approved wrapper scripts>",
    "expected_outputs": [
      "tools/graphify/graphify-out/graph.json",
      "tools/graphify/graphify-out/GRAPH_REPORT.md",
      "tools/graphify/graphify-out/manifest.json",
      "tools/graphify/graphify-out/.graphify_labels.json",
      "tools/graphify/graphify-out/.graphify_root"
    ],
    "diff_policy": "tracked-empty",
    "forbidden": [
      "graphify claude install",
      "graphify codex install",
      "graphify antigravity install"
    ]
  }
}
```

- `workspace` is always `tools/graphify`. The wrapper must pass this workspace
  explicitly if the installed Graphify version defaults to a `graphify/`
  directory.
- `expected_outputs` is exactly the five paths above, in this order.
- `diff_policy` is `tracked-empty`: configuration is tracked, generated output
  must not appear in a tracked diff.
- `forbidden` is the installer denylist; these subcommands must be rejected
  before execution.
- When Graphify is disabled, the `graphify` key is omitted entirely.

## Schema: checks.json

Only generated when checks are split out of `pipeline.profile.json`.

```json
{
  "schema_version": 1,
  "checks": [
    {
      "stack": "<name>",
      "name": "<check id>",
      "argv": ["<exe>", "<arg>", "..."],
      "cwd": "<anchor-relative dir>"
    }
  ]
}
```

- `argv` is shell-free. Each check has an explicit `cwd`.
- Every check comes from a confirmed repository-defined command; no invented
  or approximated commands.

## Graphify workspace and the five required outputs

The complete required output set for a Graphify build is exactly:

| Path | Required |
|---|---|
| `tools/graphify/graphify-out/graph.json` | yes |
| `tools/graphify/graphify-out/GRAPH_REPORT.md` | yes |
| `tools/graphify/graphify-out/manifest.json` | yes |
| `tools/graphify/graphify-out/.graphify_labels.json` | yes |
| `tools/graphify/graphify-out/.graphify_root` | yes |
| `tools/graphify/graphify-out/graph.html` | no — may be produced, absence is not an error |

Tracked workspace files (`.graphifyignore`, `config/`) make indexing rules and
wrapper invocation explicit and reproducible. The build must be runnable
without an installer subcommand.

## Ignore rule and tracked/generated split

- The root `.gitignore` gains exactly one line:
  `/tools/graphify/graphify-out/`.
- Do **not** ignore all of `tools/graphify/` — that would hide the tracked
  configuration and make builds unreproducible.
- `tools/feature-pipeline/config/**` and `tools/graphify/{.graphifyignore,config}`
  are tracked.
- `tools/graphify/graphify-out/**` is generated and must never be staged.

## Setup report shape

The report records what actually ran, not what was intended.

```json
{
  "confirmed_inputs": { "...": "the exact confirmed input object" },
  "written_files": ["tools/feature-pipeline/config/pipeline.profile.json", "..."],
  "gitignore_line_added": "/tools/graphify/graphify-out/",
  "commands": [
    { "argv": ["<exe>", "<arg>"], "cwd": "<anchor-relative>", "exit_code": 0, "summary": "<short result>" }
  ],
  "graphify_enabled": true,
  "notes": ["<anything the operator must know, e.g. a skipped optional launcher>"]
}
```

- `commands` lists each command with its own `cwd` and `exit_code`.
- No command in the report may be a commit, push, installer subcommand, or a
  dependency installation.

## Error contract

| Condition | Behavior |
|---|---|
| A required input key is missing or empty | Stop before writing; report the missing key. |
| A discovered value is not confirmed | Stop before writing; report the unconfirmed value. |
| A check command is not a known repository-defined command | Stop; do not substitute. |
| A path is absolute, contains `~` or `..`, or uses `\` separators | Stop; report the offending path. |
| `graphify.enabled` is true but `wrapper_source` is missing | Stop; report the missing wrapper source. |
| Target write path resolves outside `tools/**` or the root `.gitignore` | Stop; refuse the write. |
| Shared agents repository or the managed Python runtime is unavailable | Stop; report the blocking condition. |

Every stop is fail-closed: no partial project configuration is left behind
beyond files already written in the same run, which the report lists.

## Out of scope

- Any edit to `feature-pipeline-skill/pipeline_core/**`.
- Graphify installer subcommands and dependency installation.
- `git commit`, `git push`, and staging generated output.
- Relocating `--project-skill` under `tools/`.
- Implementing or invoking pipeline stages 10–16.
