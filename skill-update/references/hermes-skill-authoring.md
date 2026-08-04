# Hermes Agent Skill Authoring Guide

Detailed reference for authoring in-repo SKILL.md files: frontmatter requirements, structure patterns, and verification.

## Required Frontmatter

```yaml
---
name: <skill-name>          # lowercase, hyphens/underscores, max 64 chars
description: <one-line>      # what the skill does, when to trigger
version: 1.0.0
---
```

## Size Limits

- SKILL.md body: <5k words (keep lean, move details to references/)
- References files: no hard limit, but include grep patterns if >10k words
- Total skill package: keep proportional to complexity

## Peer-Matched Structure

```
<skill-name>/
├── SKILL.md           # Required: metadata + procedural instructions
├── references/        # Optional: detailed knowledge banks
├── templates/         # Optional: starter files to copy
├── scripts/           # Optional: re-runnable automation
└── assets/            # Optional: images, icons
```

## Workflow

1. Create directory under appropriate category
2. Write SKILL.md with frontmatter + body
3. Add references/templates/scripts as needed
4. Run validation: `python scripts/quick_validate.py`
5. Test skill loading: `skill_view(name='<skill-name>')`

## Cross-Referencing Other Skills

In frontmatter:
```yaml
related_skills: [other-skill-1, other-skill-2]
```

In body text, link to other skills by name.

## Editing Existing In-Repo Skills

1. Read the current SKILL.md with `skill_view`
2. Use `skill_manage(action='patch')` for targeted edits
3. Use `skill_manage(action='edit')` for full rewrites
4. Run validation after edits

## Common Pitfalls

1. **Duplicating content** — information should live in either SKILL.md or references, not both
2. **Missing frontmatter** — name and description are required
3. **Over-sized SKILL.md** — move detailed content to references/
4. **Broken relative links** — always use paths relative to skill root
5. **Not validating** — always run quick_validate.py after changes

## Verification Checklist

- [ ] Frontmatter has name + description
- [ ] SKILL.md body is under 5k words
- [ ] All relative links resolve correctly
- [ ] No duplicate content between SKILL.md and references/
- [ ] Skill loads via skill_view() without errors
