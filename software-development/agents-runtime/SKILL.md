---
name: agents-runtime
description: Manage and inspect the shared agents runtime on Windows PowerShell.
platforms: [windows]
---

# Shared Agents Runtime

The shared `.agents` repository owns this runtime. Its mutable state lives under `runtime/`; this skill owns its commands. Windows PowerShell is supported. Linux/macOS and `psmux` are future work.

Run `powershell -ExecutionPolicy Bypass -File scripts/runtime.ps1 doctor` from this skill directory.

`doctor`, `status`, and `export-diagnostics` are read-only. A feature pipeline may use only `doctor`. `bootstrap`, `sync`, and `clean-cache` are explicit maintenance commands for the shared-runtime owner.

- `doctor` checks Node 24 LTS, uv, and committed manifests/lockfiles.
- `bootstrap` and `sync` install from existing lockfiles without rewriting them.
- `status` prints detected versions and `export-diagnostics` emits redacted JSON.
- `clean-cache` removes only `runtime/cache` contents.

Python uses uv with Python 3.12. Node uses Node 24 LTS and the committed npm lockfile. Never substitute pip, venv, global packages, or an unpinned Node dependency.

Run tests with `powershell -ExecutionPolicy Bypass -File scripts/test_runtime.ps1`.
