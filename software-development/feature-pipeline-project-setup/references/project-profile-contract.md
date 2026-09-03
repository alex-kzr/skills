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
- [Schema: root .graphifyignore](#schema-root-graphifyignore)
- [Graphify workspace, scan root, and the five required outputs](#graphify-workspace-scan-root-and-the-five-required-outputs)
- [Ignore rules and tracked/generated split](#ignore-rules-and-trackedgenerated-split)
- [Setup report shape](#setup-report-shape)
- [Error contract](#error-contract)
- [Validator findings](#validator-findings)
- [Smoke harness](#smoke-harness)
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
  `tools/**`, the root `.gitignore`, and the root `.graphifyignore`.
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
    "wrapper_destination": "tools/graphify/config/<dir>",
    "index_excludes": ["<anchor-relative path>", "..."]
  }
}
```

Rules:

- `task_routing` maps each supported task type to exactly one working root.
- `technology_stacks[].checks[].argv` is a real argv list — no shell string,
  no `|`, `&&`, `;`, `>`, or `<`. Each check carries its own `cwd`.
- `run_state_path` is a single anchor-relative path.
- `roles[].min_grants` lists the minimum grants for that role, nothing more.
- When `graphify.enabled` is `true`, `index_excludes` is **required** (it may be
  an empty list). Each entry is an anchor-relative path below the repository
  root — never `.` itself — and becomes an anchored `/pattern` line in the root
  `.graphifyignore`. Duplicates and trailing slashes are normalised away.
- When `graphify.enabled` is `false`, `wrapper_source`, `wrapper_destination`,
  and `index_excludes` are omitted and no `tools/graphify/` tree and no root
  `.graphifyignore` are created.

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
  .graphifyignore                  # tracked, only when graphify.enabled — root scan-ignore rules
  tools/
    feature-pipeline/
      config/
        pipeline.profile.json      # tracked
        integrations.json          # tracked
        checks.json                # tracked, only if checks are split out
      run_pipeline.py              # tracked, optional thin launcher
      README.md                    # tracked
    graphify/                      # only when graphify.enabled — config/output home
      config/                      # tracked: graphify.project.json + approved wrapper
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
  into `checks.json`; never both. `scripts/setup_project.py` always chooses the
  split form when at least one check is declared, so a generated
  `pipeline.profile.json` never carries an inline `checks` array.
- `project` is the basename of the resolved `--project-root`.

## Schema: integrations.json

```json
{
  "schema_version": 1,
  "graphify": {
    "stage": "graphify",
    "executor": "runner:graphify",
    "workspace": "tools/graphify",
    "scan_root": ".",
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

- `workspace` is always `tools/graphify` — the Graphify **config/output home**
  (tracked `config/`, generated `graphify-out/`). It is **not** the scan root.
- `scan_root` is always `.` — Graphify indexes the whole repository from its
  root. The approved wrapper runs `graphify update .` with `GRAPHIFY_OUT` pinned
  to `tools/graphify/graphify-out` so output still lands under the workspace.
  Passing `tools/graphify` as the `graphify update` argument would index only
  that directory — that is the defect this field guards against.
- `expected_outputs` is exactly the five paths above, in this order.
- `diff_policy` is `tracked-empty`: configuration is tracked, generated output
  must not appear in a tracked diff.
- `forbidden` is the installer denylist; these subcommands must be rejected
  before execution.
- When Graphify is disabled, the `graphify` key is omitted entirely.

## Schema: root .graphifyignore

Written only when `graphify.enabled` is `true`. Skill-owned generated config —
overwritten on every regeneration, never merged. It lives at the **repository
root** because that is Graphify's scan root. Layout:

```text
# Generated by feature-pipeline-project-setup. Do not hand-edit; regenerate.
# ... explanatory header ...

# Generated Graphify output (also covered by .gitignore).
/tools/graphify/graphify-out/

# Project-declared exclusions.        <- only when index_excludes is non-empty
/<index_excludes[0]>
/<index_excludes[1]>
```

The `/tools/graphify/graphify-out/` line is always present. Graphify also
honours the root `.gitignore` and its own built-in cache/venv skips, so
`index_excludes` only needs the *extra* project-specific paths.

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

## Graphify workspace, scan root, and the five required outputs

`tools/graphify/` is the config/output **home**; the **scan root is the
repository root** (`scan_root: "."`). The complete required output set for a
Graphify build is exactly:

| Path | Required |
|---|---|
| `tools/graphify/graphify-out/graph.json` | yes |
| `tools/graphify/graphify-out/GRAPH_REPORT.md` | yes |
| `tools/graphify/graphify-out/manifest.json` | yes |
| `tools/graphify/graphify-out/.graphify_labels.json` | yes |
| `tools/graphify/graphify-out/.graphify_root` | yes |
| `tools/graphify/graphify-out/graph.html` | no — may be produced, absence is not an error |

Tracked files (the root `.graphifyignore`, `tools/graphify/config/`) make
indexing rules and wrapper invocation explicit and reproducible. The build must
be runnable without an installer subcommand. `scripts/setup_project.py` writes
`tools/graphify/config/graphify.project.json` (project settings: `workspace`,
`scan_root`, `out_dir`, `required_outputs`, `diff_policy`), copies the approved
wrapper source verbatim under `graphify.wrapper_destination`, and writes the root
`.graphifyignore` (always excludes `/tools/graphify/graphify-out/`, then any
`graphify.index_excludes`). The approved wrapper runs `graphify update .` with
`GRAPHIFY_OUT` pinned to `tools/graphify/graphify-out`. The optional thin
`tools/feature-pipeline/run_pipeline.py` launcher is not generated — its absence
is recorded in the setup report `notes`.

## Ignore rules and tracked/generated split

- The root `.gitignore` gains exactly one line:
  `/tools/graphify/graphify-out/`.
- The root `.graphifyignore` is a tracked, skill-owned file (see its schema
  above). It must never be `.gitignore`d.
- Do **not** ignore all of `tools/graphify/` — that would hide the tracked
  configuration and make builds unreproducible.
- `tools/feature-pipeline/config/**`, `tools/graphify/config/**`, and the root
  `.graphifyignore` are tracked.
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
| `graphify.enabled` is true but `index_excludes` is missing, or an entry is `.` / absolute / escaping | Stop; report the offending value. |
| Target write path resolves outside `tools/**`, the root `.gitignore`, or the root `.graphifyignore` | Stop; refuse the write. |
| Shared agents repository or the managed Python runtime is unavailable | Stop; report the blocking condition. |

Every stop is fail-closed: no partial project configuration is left behind
beyond files already written in the same run, which the report lists.

## Validator findings

`scripts/validate_project_setup.py` reads a generated setup and reports every
contract violation as a `{ "code": ..., "detail": ... }` finding. It never
mutates the target tree (`run_validation` snapshots before and after and raises
if anything changed) and never runs the Graphify wrapper. Exit status: `0` when
`findings` is empty, `1` when any finding is present, `2` for a bad invocation
(a missing `--project-root` / `--agents-root` / `--core-root`, a project root
that is not a directory or not inside a Git work tree, or a missing `git`).

The codes are stable identifiers; tests pin one code per single injected defect.

| Code | Raised when |
|---|---|
| `E_STRUCTURE` | A required file is absent: `pipeline.profile.json`, `integrations.json`, `tools/feature-pipeline/README.md`, or (Graphify) the root `.graphifyignore` / `tools/graphify/config/graphify.project.json`. |
| `E_JSON_SYNTAX` | A generated JSON file does not parse. |
| `E_SCHEMA` | Wrong `schema_version`, a missing/mistyped key, or an inline `checks` array in `pipeline.profile.json`. |
| `E_TASK_TYPE` | A `task_routing[].task_type` is not one of the approved task types. |
| `E_ROLE_GRANTS` | `roles` is empty, a role has no name, or a role's `min_grants` is not a non-empty list of grant names. |
| `E_PATH_BACKSLASH` | A configured path uses `\` separators. |
| `E_PATH_ABSOLUTE` | A configured path is absolute, drive-qualified, or starts with `/` or `~`. |
| `E_PATH_ESCAPE` | A configured path contains a `..` segment. |
| `E_ARGV_TYPE` | A `checks.json` `argv` is not a non-empty list of non-empty strings. |
| `E_ARGV_SHELL` | A `checks.json` `argv` token contains a shell operator (`|`, `&&`, `;`, `>`, `<`, `` ` ``, `$(`). |
| `E_RUN_STATE_PLACEMENT` | `run_state_path` names the repo root / `tools`, or sits inside `tools/graphify/graphify-out/` or inside the portable core. |
| `E_ANCHOR_MISMATCH` | `pipeline.profile.json` `anchors.agents_root` / `anchors.core_root` does not match the anchor passed on the command line. |
| `E_GRAPHIFY_WORKSPACE` | `integrations.json` `graphify.workspace` is not `tools/graphify` (the config/output home). |
| `E_GRAPHIFY_SCAN_ROOT` | `integrations.json` `graphify.scan_root` is not `.` (Graphify must index the whole repository). |
| `E_GRAPHIFYIGNORE_OUTPUT_RULE` | The root `.graphifyignore` exists but does not contain the `/tools/graphify/graphify-out/` line. |
| `E_GRAPHIFY_WRAPPER_MISSING` | `graphify.wrapper_dir` is outside `tools/graphify/`, or the directory does not exist or holds no files. |
| `E_GRAPHIFY_OUTPUTS` | `graphify.expected_outputs` is not exactly the five required outputs in the required order (extra entries, including `graph.html`, or a missing entry). |
| `E_GRAPHIFY_DIFF_POLICY` | `graphify.diff_policy` is not `tracked-empty`. |
| `E_GRAPHIFY_FORBIDDEN` | `graphify.forbidden` is not exactly the three-command installer denylist. |
| `E_GITIGNORE_MISSING_RULE` | The root `.gitignore` does not contain the exact line `/tools/graphify/graphify-out/`. |
| `E_GITIGNORE_BROAD_RULE` | The root `.gitignore` contains a rule that ignores all of `tools/graphify/` (e.g. `/tools/graphify/`, `tools/graphify/**`). |
| `E_GIT_TRACKED_OUTPUT` | `git ls-files` reports a tracked file under `tools/graphify/graphify-out/`. |
| `E_GIT_CONFIG_IGNORED` | `git check-ignore --no-index` reports that a tracked configuration/wrapper file, or the root `.graphifyignore`, would be ignored. Suppressed for `tools/graphify/**` when `E_GITIGNORE_BROAD_RULE` already covers it. |

`graph.html` is never required and its presence under `tools/graphify/graphify-out/`
(untracked) is not a finding.

## Smoke harness

`scripts/smoke_project_setup.py --self-test --core-root <checkout> [--agents-root <checkout>]`
proves setup output can drive the portable core's safe planning path. It is not
a Graphify build.

Flow, entirely inside one `TemporaryDirectory`:

1. Seed a minimal fixture project — its own Git work tree, a stub
   `feature-pipeline-skill/pipeline_core/` tree, an approved wrapper source —
   with every write beneath the temporary directory.
2. Apply `setup_project.run_setup` (Graphify enabled), then run
   `validate_project_setup.run_validation` read-only; any finding fails the smoke.
3. Translate the generated `pipeline.profile.json` + `checks.json` into a
   portable-core profile (`version`, `name`, `logical_paths`, `role_grants`, one
   `implement` stage, and a `registry` whose `task_types` / `roots` / `checks` /
   `storage` are the generated task routing, working roots, check `argv`, and
   run-state path) plus a one-task-per-routed-type plan.
4. Run the explicitly located core CLI exactly twice: `run_pipeline.py --help`
   and `run_pipeline.py --project-root … --agents-root … --core-root … --profile
   core.profile.json --plan core.plan.json --mode plan-only --dry-run`.

Exit contract checked: `--help` → `0`; a non-blocked `plan-only --dry-run` → `10`
(`EXIT_GATE_PENDING`, a delivery gate pending). Any other code fails the smoke.

Safety:

- `--core-root` and the optional `--agents-root` are always explicit; neither is
  inferred from the working directory or a home directory.
- Every subprocess argv is a shell-free list vetted before launch. An argv
  containing a Graphify installer (`graphify … install`), `commit`, `push`, or
  `tag` raises before any process starts.
- The Graphify wrapper and `graphify` itself are never executed.
- Every path outside the temporary directory the run can reach (the core
  checkout, an external agents root) is hashed before and after; any change
  fails the smoke.

`--self-test` runs the whole flow twice from independent temporary directories
and compares the redacted, timing-free reports (host paths → `<tmp>` /
`<core_root>` / `<agents_root>` / `<home>`, the core's throwaway
`pipeline-dry-run-*` directory name normalized). Exit: `0` when the two reports
are byte-identical and the exit / Graphify / outside-tmp checks all held; `1` on
any smoke-contract failure; `2` when the core cannot be resolved from
`--core-root` or its `--help` does not expose `plan-only` and `--dry-run`
(the blocking condition).

## Out of scope

- Any edit to `feature-pipeline-skill/pipeline_core/**`.
- Graphify installer subcommands and dependency installation.
- `git commit`, `git push`, and staging generated output.
- Relocating `--project-skill` under `tools/`.
- Implementing or invoking pipeline stages 10–16.
