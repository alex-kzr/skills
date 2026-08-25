# Python Backend Agent Skills

## Purpose

This directory contains independently loadable Python backend Agent Skills. Each skill has a focused activation scope; use the most specific matching skill.

## Catalog

| Skill | Purpose | Source | Status | Local modifications |
|---|---|---|---|---|
| async-python-patterns | Asyncio and concurrent I/O. | wshobson/agents | Added | None |
| python-anti-patterns | Review checklist for Python smells. | wshobson/agents | Added | None |
| python-background-jobs | Queues, workers, and idempotent jobs. | wshobson/agents | Added | None |
| python-code-style | Python style, linting, and docs. | wshobson/agents | Added | None |
| python-configuration | Typed settings and secret separation. | wshobson/agents | Added | None |
| python-design-patterns | Maintainable Python design. | wshobson/agents | Added | None |
| python-error-handling | Validation and exception design. | wshobson/agents | Added | None |
| python-observability | Logging, metrics, and tracing. | wshobson/agents | Added | None |
| python-packaging | Packages and distributions. | wshobson/agents | Added | Safe cleanup wording |
| python-performance-optimization | Profiling and performance work. | wshobson/agents | Added | None |
| python-project-structure | Package layout and public APIs. | wshobson/agents | Added | None |
| python-resilience | Timeouts, retries, and backoff. | wshobson/agents | Added | None |
| python-resource-management | Sync and async cleanup patterns. | wshobson/agents | Added | None |
| python-testing-patterns | Pytest strategies and test design. | wshobson/agents | Added | None |
| python-type-safety | Type hints and strict checking. | wshobson/agents | Added | None |
| uv-package-manager | uv dependency and project workflows. | wshobson/agents | Added | Removed remote-pipe installers |
| fastapi-templates | Production FastAPI service patterns. | wshobson/agents | Added | None |
| python-pro | General Python implementation. | Jeffallan/claude-skills | Added | Normalized routing and frontmatter |
| django-expert | Django and DRF application work. | Jeffallan/claude-skills | Added | Normalized frontmatter |
| py-security | Python security analysis and remediation. | l-mb/python-refactoring-skills | Added | Normalized frontmatter and removed agent-specific hook setup |

## Selection guide

- General implementation: `python-pro`; async/concurrency: `async-python-patterns`.
- Tests: `python-testing-patterns`; typing: `python-type-safety`; dependencies: `python-packaging` or `uv-package-manager`.
- Architecture: `python-project-structure` or `python-design-patterns`; errors: `python-error-handling`; resilience: `python-resilience`.
- Resource cleanup: `python-resource-management`; jobs: `python-background-jobs`; performance: `python-performance-optimization`.
- Logging, metrics, tracing: `python-observability`; settings: `python-configuration`; quality: `python-code-style` or `python-anti-patterns`.
- Frameworks: `fastapi-templates` for FastAPI and `django-expert` for Django/DRF; security: `py-security`.

## Update procedure

1. Read `SOURCES.md`, fetch the recorded upstream commit, and compare the source skill directory with the local copy.
2. Preserve local safety and routing edits; apply upstream changes incrementally and re-check every relocated link.
3. Record the new commit, date, license, and local modifications in `SOURCES.md`.
4. Run the catalog validation command recorded in this repository's task report, then rebuild the skills Graphify index.
