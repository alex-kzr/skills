---
name: hermes-customization
description: "Patch Hermes Agent source code for features that config.yaml can't express. Covers locating source in the Docker deployment, safe patching patterns, testing changes, and curator internals."
version: 1.0.0
created_by: agent
---

# Hermes Source Customization

When `config.yaml` options and CLI commands are not enough, patch Hermes Agent's
Python source directly. This skill covers the Docker deployment on the VPS.

## When to use

- A Hermes feature needs behavior config.yaml doesn't expose (e.g. curator exclusion by directory)
- Need to understand Hermes internals to debug or extend a subsystem
- Adding a new config-driven option to an existing feature

## Source location

```
/opt/hermes/                    # Hermes source root (Docker container)
├── run_agent.py                # Core conversation loop (AIAgent)
├── model_tools.py              # Tool discovery and dispatch
├── toolsets.py                 # Toolset definitions
├── agent/                      # Prompt builder, curator, context, memory
│   ├── curator.py              # Curator orchestrator (background skill maintenance)
│   ├── skill_utils.py          # Skill metadata utilities
│   └── prompt_builder.py       # System prompt assembly
├── tools/                      # One file per tool
│   ├── skill_usage.py          # Skill usage telemetry + provenance (curator core)
│   ├── skills_sync.py          # Bundled skill syncing
│   └── registry.py             # Central tool registry
├── hermes_cli/                 # CLI subcommands, config
│   ├── config.py               # DEFAULT_CONFIG, load_config()
│   └── commands.py             # Slash command registry
├── gateway/                    # Messaging gateway
│   ├── run.py                  # Main gateway loop
│   └── platforms/              # Platform adapters
└── cron/                       # Job scheduler
```

## Config file location

```
/services/hermes/data/hermes/config.yaml   # Main config (mounted volume)
```

Read it with:
```python
from hermes_cli.config import load_config
cfg = load_config()
```

## Patching pattern

1. **Find the relevant module.** Use `search_files` or `grep` under `/opt/hermes/`.
2. **Read the full function/class** before editing — read with `read_file` using offset/limit for large files.
3. **Patch with the `patch` tool** (not sed/awk). Include surrounding context for uniqueness.
4. **Test immediately** with `execute_code` — import the module fresh:
   ```python
   import sys, importlib
   sys.path.insert(0, "/opt/hermes")
   # Clear cached modules
   for mod_name in list(sys.modules.keys()):
       if "target_module" in mod_name:
           del sys.modules[mod_name]
   from tools import target_module
   # Test the patched function
   ```
5. **Restart the container** to apply changes to the running process:
   ```
   docker restart hermes
   ```

## Adding a config-driven option

Pattern for adding a new `curator.*` (or other section) config key:

1. Add a `_read_new_option()` function in the relevant module (e.g. `tools/skill_usage.py`):
   ```python
   def _read_new_option() -> SomeType:
       try:
           from hermes_cli.config import load_config
           cfg = load_config()
           section = cfg.get("curator") if isinstance(cfg, dict) else None
           if isinstance(section, dict):
               val = section.get("new_key")
               # parse and return
       except Exception as e:
           logger.debug("Failed to read curator.new_key: %s", e)
       return default_value
   ```
2. Use the function in the logic that needs the gate.
3. Add the key to `config.yaml` under the appropriate section.

## Pitfalls

- **Changes need container restart.** Python caches modules at import time. `docker restart hermes` is required for the running process to pick up patched `.py` files.
- **Container recreation wipes patches.** If the container is destroyed and recreated (not just restarted), `/opt/hermes/` changes are lost unless the volume is preserved. Document patches in memory or a tracking file.
- **`hermes update` may overwrite patches.** The update process replaces the source tree. Re-apply patches after updates, or better: submit upstream PRs for features that should persist.
- **Lazy imports in modules.** Many modules use lazy `from hermes_cli.config import load_config` inside functions to avoid circular imports. Follow the same pattern when adding config reads.

## Reference files

- `references/curator-architecture.md` — Full curator internals: provenance tracking, lifecycle states, how skills are selected for archival, and how to extend the curator with new exclusion rules.
