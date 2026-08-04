#!/usr/bin/env python3
"""
Validate the skills catalog: link targets, catalog completeness,
SKILL.md frontmatter, and duplicate skill names.
"""

import os
import re
import sys
from pathlib import Path


def _find_agents_root(start: Path) -> Path:
    current = start.resolve()
    for parent in [current, *current.parents]:
        if (parent / "skills").exists() and (parent / "runtime").exists():
            return parent
    raise RuntimeError("Cannot find agents root with both skills/ and runtime/")


def _add_runtime_site_packages() -> None:
    agents_root = _find_agents_root(Path(__file__))
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
    sys.path.insert(0, str(site_packages))


_add_runtime_site_packages()

import yaml

LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def _is_local_link(target: str) -> bool:
    if not target or target.startswith("#"):
        return False
    return not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target)


def check_description_links(description_path: Path, errors: list) -> None:
    content = description_path.read_text(encoding="utf-8")
    for match in LINK_RE.finditer(content):
        target = match.group(1).strip()
        if not _is_local_link(target):
            continue
        target = target.split("#", 1)[0]
        resolved = (description_path.parent / target).resolve()
        if not resolved.exists():
            errors.append(f"{description_path}: broken link -> {target}")


def check_catalog_completeness(description_path: Path, errors: list) -> None:
    catalog_dir = description_path.parent
    content = description_path.read_text(encoding="utf-8")

    for child in sorted(catalog_dir.iterdir()):
        if not child.is_dir():
            continue

        child_skill = child / "SKILL.md"
        child_desc = child / "DESCRIPTION.md"

        if child_skill.exists():
            expected = f"{child.name}/SKILL.md"
            if expected not in content:
                errors.append(
                    f"{description_path}: skill folder '{child.name}/' with SKILL.md "
                    "is not listed"
                )
        elif child_desc.exists():
            expected = f"{child.name}/DESCRIPTION.md"
            if expected not in content:
                errors.append(
                    f"{description_path}: catalog folder '{child.name}/' with "
                    "DESCRIPTION.md is not listed"
                )


def check_skill_frontmatter(skill_md_path: Path, errors: list, names: dict) -> None:
    content = skill_md_path.read_text(encoding="utf-8")
    if not content.startswith("---"):
        errors.append(f"{skill_md_path}: no YAML frontmatter found")
        return

    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        errors.append(f"{skill_md_path}: invalid frontmatter format")
        return

    try:
        frontmatter = yaml.safe_load(match.group(1))
    except yaml.YAMLError as e:
        errors.append(f"{skill_md_path}: invalid YAML in frontmatter: {e}")
        return

    if not isinstance(frontmatter, dict):
        errors.append(f"{skill_md_path}: frontmatter must be a YAML dictionary")
        return

    if "name" not in frontmatter:
        errors.append(f"{skill_md_path}: missing 'name' in frontmatter")
    if "description" not in frontmatter:
        errors.append(f"{skill_md_path}: missing 'description' in frontmatter")

    name = frontmatter.get("name")
    if isinstance(name, str) and name.strip():
        names.setdefault(name.strip(), []).append(skill_md_path)


def validate_catalog(skills_root: Path) -> list:
    errors = []
    names: dict = {}

    for description_path in sorted(skills_root.rglob("DESCRIPTION.md")):
        check_description_links(description_path, errors)
        check_catalog_completeness(description_path, errors)

    for skill_md_path in sorted(skills_root.rglob("SKILL.md")):
        check_skill_frontmatter(skill_md_path, errors, names)

    for name, paths in sorted(names.items()):
        if len(paths) > 1:
            locations = ", ".join(str(p) for p in paths)
            errors.append(f"Duplicate skill name '{name}': {locations}")

    return errors


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("skills")
    if not target.exists():
        print(f"Path not found: {target}")
        sys.exit(1)

    found_errors = validate_catalog(target)

    if not found_errors:
        print("Catalog is valid!")
        sys.exit(0)

    print(f"Found {len(found_errors)} issue(s):")
    for err in found_errors:
        print(f"  - {err}")
    sys.exit(1)
