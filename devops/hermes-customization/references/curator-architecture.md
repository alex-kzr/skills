# Curator Architecture — Internals Reference

## Overview

The curator is a background skill maintenance system that periodically reviews
agent-created skills and manages their lifecycle: active → stale → archived.

Core modules:
- `agent/curator.py` — Orchestrator: scheduling, state, LLM review prompt
- `tools/skill_usage.py` — Provenance, lifecycle states, archive/restore

State files (under `~/.hermes/skills/`):
- `.usage.json` — Per-skill telemetry (use_count, view_count, state, pinned, created_by)
- `.curator_state` — Scheduler state (last_run_at, paused, run_count)
- `.bundled_manifest` — Lines of `name:hash` for bundled (shipped) skills
- `.curator_suppressed` — Built-in skills the curator pruned; re-seeder leaves them archived
- `.hub/lock.json` — Hub-installed skill registry

## Provenance: who is eligible for curation?

```
is_curation_eligible(name)
├── Protected built-in (PROTECTED_BUILTIN_SKILLS = {"plan"}) → NEVER
├── Hub-installed (in .hub/lock.json) → NEVER
├── Bundled (in .bundled_manifest)
│   └── prune_builtins config flag (default True) → only if enabled
└── Agent-created (created_by=="agent" in .usage.json) → YES
```

Key functions in `tools/skill_usage.py`:
- `list_agent_created_skill_names()` — Walks `rglob("SKILL.md")`, filters by provenance
- `is_curation_eligible(name)` — Name-based eligibility check
- `is_protected_builtin(name)` — Hardcoded exclusion set
- `_is_curator_managed_record(record)` — Checks `created_by == "agent" or agent_created == True`

## Lifecycle states

```
active → (stale_after_days of inactivity) → stale
stale  → (archive_after_days of inactivity) → archived
```

- Config: `curator.stale_after_days` (default 30), `curator.archive_after_days` (default 90)
- "Activity" = use, view, or patch event. Creation time is NOT activity (it's a fallback anchor).
- Pinned skills bypass ALL transitions.
- `apply_automatic_transitions()` in `agent/curator.py` does the walk.

## The archive path

`archive_skill(name)` in `tools/skill_usage.py`:
1. Check `is_curation_eligible(name)` — refuses hub/protected/non-prunable
2. Find skill dir via `_find_skill_dir(name)` — rglob for matching frontmatter `name:`
3. Move directory to `~/.hermes/skills/.archive/<skill_name>/`
4. If bundled: add to `.curator_suppressed` so updates don't restore it
5. Set state to `archived` in `.usage.json`

The LLM review pass (forked auxiliary agent) can also call `skill_manage(action="delete")`
which routes through `archive_skill()`.

## Config options (curator.* in config.yaml)

| Key | Default | Purpose |
|-----|---------|---------|
| `enabled` | true | Master toggle |
| `interval_hours` | 168 (7 days) | Time between curator runs |
| `min_idle_hours` | 2 | Min idle time before running |
| `stale_after_days` | 30 | Days inactive → stale |
| `archive_after_days` | 90 | Days inactive → archived |
| `prune_builtins` | true | Allow pruning bundled skills |
| `exclude_dirs` | (none) | Directory names whose descendants are exempt |
| `backup.enabled` | true | Tar.gz backup before each run |
| `backup.keep` | 5 | Number of backups to retain |

## exclude_dirs (added 2026-06-16)

Custom config option added to protect skills under specific directories (e.g. `projects/`).

Implementation in `tools/skill_usage.py`:
- `_curator_exclude_dirs()` reads `curator.exclude_dirs` (list of directory names)
- `list_agent_created_skill_names()` skips any `SKILL.md` path containing an excluded dir component
- `archive_skill()` checks `skill_dir.parts` against exclude_dirs and refuses archival

Config example:
```yaml
curator:
  exclude_dirs:
    - projects
```

This protects ALL skills under `../../../project-skills/` (both `projects/ag/` and `projects/aw/`)
without needing to pin each skill individually.

## How to test curator changes

```python
import sys, importlib
sys.path.insert(0, "/opt/hermes")
for mod_name in list(sys.modules.keys()):
    if "skill_usage" in mod_name or "hermes_cli.config" in mod_name:
        del sys.modules[mod_name]

from tools import skill_usage

# Check exclusion
print(skill_usage._curator_exclude_dirs())  # {'projects'}

# Check candidates don't include excluded skills
candidates = skill_usage.list_agent_created_skill_names()
project_leaked = [c for c in candidates if c.startswith("aw-") or c.startswith("ag-")]
assert not project_leaked, f"Leaked: {project_leaked}"

# Test archive refusal
ok, msg = skill_usage.archive_skill("some-project-skill")
assert not ok and "excluded directory" in msg
```

## Skill directory layouts

Hermes supports two layouts:
- **Flat**: `skills/<skill-name>/SKILL.md`
- **Nested (category)**: `skills/<category>/<skill-name>/SKILL.md`

The `projects/` directory uses a deeper nesting: `../../../project-skills/<project>/<skill>/SKILL.md`.
The `exclude_dirs` check matches any path component, so `"projects"` catches all depths.
