# Skill Manifest Design (Future)

This is a design proposal for a future machine-readable manifest at:

```text
skills/index.json
```

No generation tooling exists yet. Do not build it unless explicitly requested. This document exists so a future implementation has an agreed schema to start from.

## Why a manifest, in addition to DESCRIPTION.md

`DESCRIPTION.md` files are the primary navigation index and stay authoritative for humans and agents browsing top-down through the catalog tree — see [skill-navigator](../../skill-navigator/SKILL.md). They are prose tables meant to be read, not parsed.

`skills/index.json` would be a derived, flat, machine-readable index generated from the same source of truth (each skill's `SKILL.md` frontmatter and folder location), useful for:

- Programmatic tools (e.g. [skill-graphify](../../skill-graphify/SKILL.md), validation scripts, agent adapters) that need to query skills without walking the directory tree or parsing markdown tables.
- Cross-cutting queries that `DESCRIPTION.md` can't answer well, such as "which skills support agent X" or "which skills require network access."
- Fast lookup by name without knowing the catalog path.

The manifest complements `DESCRIPTION.md`; it does not replace it:

- `DESCRIPTION.md` remains the hand-maintained, human-readable navigation index and the source of truth for catalog structure.
- `skills/index.json` would be generated (not hand-edited) from `SKILL.md` frontmatter plus folder layout, the same way [skills/skill-update/scripts/validate_catalog.py](../scripts/validate_catalog.py) already reads that structure to check for drift.
- If the two disagree, `DESCRIPTION.md` and the actual `SKILL.md` files win; the manifest would be regenerated, never edited to force agreement.

## Proposed fields

Each entry in `skills/index.json` describes one skill:

| Field | Type | Description |
|---|---|---|
| `name` | string | Skill name, matching `SKILL.md` frontmatter `name`. Must be unique across the catalog. |
| `path` | string | Repo-relative path to the skill's `SKILL.md`, e.g. `skills/skill-update/SKILL.md`. |
| `catalog` | string | Repo-relative path to the parent `DESCRIPTION.md`, e.g. `skills/DESCRIPTION.md`. |
| `scope` | `"global"` \| `"project"` | Whether the skill lives under `skills/` directly or under `../../project-skills/`. |
| `project` | string \| null | Project code if `scope` is `"project"` (e.g. `"ag"`), else `null`. |
| `description` | string | Copied from `SKILL.md` frontmatter `description`. |
| `triggers` | string[] | Short trigger phrases or keywords extracted or curated from the description, for keyword-based lookup. |
| `agent_support` | string[] | Agents known to work with this skill (e.g. `["codex", "claude", "hermes"]`), based on [agents/](../../../agents/) profiles. |
| `requires_runtime` | string[] | Shared runtime paths this skill's scripts depend on (e.g. `["runtime/python/base"]`), or `[]` if the skill has no scripts. |
| `requires_network` | boolean | Whether the skill's normal operation requires network access (e.g. calling an external API). |
| `side_effects` | string[] | Categories of effects the skill can have (e.g. `["writes-files", "sends-messages", "modifies-git"]`), for agents deciding whether to run it autonomously. |
| `orchestration_role` | `"leaf"` \| `"orchestrator"` \| `"adapter"` | Whether the skill does task work directly (`leaf`), coordinates other skills/subagents (`orchestrator`), or bridges to a specific agent's API (`adapter`, e.g. the `autonomous-ai-agents/*` skills). |

## Example entry

```json
{
  "name": "skill-update",
  "path": "skills/skill-update/SKILL.md",
  "catalog": "skills/DESCRIPTION.md",
  "scope": "global",
  "project": null,
  "description": "Guide for creating or updating effective skills...",
  "triggers": ["create a skill", "update a skill", "new SKILL.md"],
  "agent_support": ["codex", "claude"],
  "requires_runtime": ["runtime/python/base"],
  "requires_network": false,
  "side_effects": ["writes-files"],
  "orchestration_role": "leaf"
}
```

## Generation approach (future work)

When this is implemented, prefer extending the existing catalog scan rather than writing a new parser:

1. Reuse the directory-walking and frontmatter-parsing logic already in [validate_catalog.py](../scripts/validate_catalog.py).
2. Fields directly available from `SKILL.md` frontmatter (`name`, `description`) and folder layout (`path`, `catalog`, `scope`, `project`) can be generated automatically.
3. Fields requiring judgment (`triggers`, `agent_support`, `requires_network`, `side_effects`, `orchestration_role`) likely need either curation in `SKILL.md` frontmatter (as new optional fields) or a one-time manual pass, then incremental maintenance.
4. Validate the generated manifest against `DESCRIPTION.md` contents (every skill listed in a `DESCRIPTION.md` should have a manifest entry, and vice versa) to catch drift between the two.

## Non-goals

- This manifest does not replace progressive disclosure — agents still read `SKILL.md` bodies on demand, not the manifest, for actual instructions.
- This manifest is not meant to be hand-edited; treat `skills/index.json` as a build artifact once implemented.
