"""Shared-runtime dependency discovery for the google-workspace skill scripts.

Locates the `agents` root (the ancestor directory containing both `skills/`
and `runtime/`) and adds the shared Python base venv's site-packages to
`sys.path`, so scripts can `import googleapiclient`, `google_auth_oauthlib`,
etc. without a local install.
"""

import os
import sys
from pathlib import Path


def find_agents_root(start: Path) -> Path:
    current = start.resolve()
    for parent in [current, *current.parents]:
        if (parent / "skills").exists() and (parent / "runtime").exists():
            return parent
    raise RuntimeError("Cannot find agents root with both skills/ and runtime/")


def add_runtime_site_packages() -> None:
    agents_root = find_agents_root(Path(__file__))
    venv_dir = agents_root / "runtime" / "python" / "base" / ".venv"

    if os.name == "nt":
        site_packages = venv_dir / "Lib" / "site-packages"
    else:
        candidates = list((venv_dir / "lib").glob("python*/site-packages"))
        site_packages = candidates[0] if candidates else None

    if not site_packages or not site_packages.exists():
        raise RuntimeError(
            "Python runtime is not prepared. Expected site-packages at: "
            f"{site_packages}. Prepare agents/runtime/python/base/.venv first."
        )

    if str(site_packages) not in sys.path:
        sys.path.insert(0, str(site_packages))
