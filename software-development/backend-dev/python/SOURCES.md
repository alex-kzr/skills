# Sources and selection record

Imported: 2026-08-25. Licenses are preserved in [licenses/](licenses/).

## wshobson/agents

Source repository: https://github.com/wshobson/agents  
Source commit: `d82998e7df393c671ede2387a8435075f0b633f5`  
License: MIT

| Skill | Source path | Local modifications | Notes |
|---|---|---|---|
| async-python-patterns | plugins/python-development/skills/async-python-patterns | None | ADD |
| python-anti-patterns | plugins/python-development/skills/python-anti-patterns | None | ADD |
| python-background-jobs | plugins/python-development/skills/python-background-jobs | None | ADD |
| python-code-style | plugins/python-development/skills/python-code-style | None | ADD |
| python-configuration | plugins/python-development/skills/python-configuration | None | ADD |
| python-design-patterns | plugins/python-development/skills/python-design-patterns | None | ADD |
| python-error-handling | plugins/python-development/skills/python-error-handling | None | ADD |
| python-observability | plugins/python-development/skills/python-observability | None | ADD |
| python-packaging | plugins/python-development/skills/python-packaging | Replaced unguarded `rm -rf` example | ADD |
| python-performance-optimization | plugins/python-development/skills/python-performance-optimization | None | ADD |
| python-project-structure | plugins/python-development/skills/python-project-structure | None | ADD |
| python-resilience | plugins/python-development/skills/python-resilience | None | ADD |
| python-resource-management | plugins/python-development/skills/python-resource-management | None | ADD |
| python-testing-patterns | plugins/python-development/skills/python-testing-patterns | None | ADD |
| python-type-safety | plugins/python-development/skills/python-type-safety | None | ADD |
| uv-package-manager | plugins/python-development/skills/uv-package-manager | Removed remote-pipe installers | ADD; security repair |
| fastapi-templates | plugins/api-scaffolding/skills/fastapi-templates | None | ADD |

## Jeffallan/claude-skills

Source repository: https://github.com/Jeffallan/claude-skills  
Source commit: `882ef55e377dbf9a4dbe496bb41ac6ccd0e555cf`  
License: MIT

| Skill | Source path | Local modifications | Notes |
|---|---|---|---|
| python-pro | skills/python-pro | Kept only required frontmatter and narrowed activation to general implementation. | ADD |
| django-expert | skills/django-expert | Kept only required frontmatter. | ADD; distinct framework coverage |
| fastapi-expert | skills/fastapi-expert | Not imported. | SKIP_DUPLICATE: overlaps required `fastapi-templates`. |
| secure-code-guardian | skills/secure-code-guardian | Not imported. | SKIP_OUT_OF_SCOPE: generic cross-language security; `py-security` is Python-specific. |

## l-mb/python-refactoring-skills

Source repository: https://github.com/l-mb/python-refactoring-skills  
Source commit: `b08357109fe81821decc100c8ea73ea2e3add08b`  
License: MIT

| Skill | Source path | Local modifications | Notes |
|---|---|---|---|
| py-security | skills/py-security | Normalized frontmatter; removed `.claude` permissions and direct hook edits. | ADD |
| py-refactor | skills/py-refactor | Not imported. | SKIP_DUPLICATE: orchestrates focused catalog skills and expects siblings not vendored here. |
| py-code-health, py-complexity, py-test-quality, py-quality-setup | skills/* | Not imported. | SKIP_DUPLICATE: overlap code-style, anti-pattern, testing, and type-safety skills. |
| py-git-hooks | skills/py-git-hooks | Not imported. | SKIP_OUT_OF_SCOPE: generic Git workflow and includes bypass guidance. |
| py-modernize | skills/py-modernize | Not imported. | SKIP_LOW_QUALITY: embeds unsafe remote installer and prescriptive runtime assumptions. |

## zaripych/skills-python-refactor

Skill: python-refactor  
Source repository: https://github.com/zaripych/skills-python-refactor  
Source path: repository root  
Source commit: `f9f88d89427d70c6269fd7ec35517b90c3df878a`  
License: no repository license file or explicit reuse grant found  
Imported: no  
Local modifications: none  
Notes: REJECTED_LICENSE. The AST-aware Rope workflow is relevant, but copying is not permitted without an explicit license. No replacement is claimed.

## Registry review

`skills.sh` was reviewed as a discovery registry only. No registry entry was copied without checking a repository source and license. No additional candidate exceeded the selected focused coverage.
