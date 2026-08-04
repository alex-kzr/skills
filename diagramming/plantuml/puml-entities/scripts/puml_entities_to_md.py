#!/usr/bin/env python3
"""Extract entities/classes/enums from PlantUML (.puml) and render Markdown.

Supported patterns:
- class <name> { ... }
- entity "<name>" as <alias> { ... }
- enum <name> { ... }

Field line examples:
- * PK id: int
- * FK contract_id: int
- alias: TEXT
- * format: TEXT [frame, redirect]

Comments:
- A line starting with "'" directly above a field/value is used as description.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass, field
from pathlib import Path
import sys


@dataclass
class FieldDef:
    name: str
    typ: str
    required: bool = False
    keys: list[str] = field(default_factory=list)  # PK/FK
    description: str = ""
    extras: str = ""


@dataclass
class EntityDef:
    name: str
    kind: str  # class/entity
    description: str = ""
    fields: list[FieldDef] = field(default_factory=list)


@dataclass
class EnumDef:
    name: str
    description: str = ""
    values: list[tuple[str, str]] = field(default_factory=list)  # (value, description)


_RE_CLASS_START = re.compile(r"^\s*class\s+([A-Za-z0-9_]+)\s*\{\s*$")
_RE_ENTITY_START_BARE = re.compile(r"^\s*entity\s+([A-Za-z0-9_]+)\s*(?:#\S+)?\s*\{\s*$")
_RE_ENTITY_START = re.compile(r'^\s*entity\s+"([^"]+)"\s+as\s+([A-Za-z0-9_]+)\s*(?:#\S+)?\s*\{\s*$')
_RE_ENUM_START = re.compile(r"^\s*enum\s+([A-Za-z0-9_]+)\s*\{\s*$")
_RE_BLOCK_END = re.compile(r"^\s*\}\s*$")

_RE_REL = re.compile(
    r'^\s*([A-Za-z0-9_]+)\s*(?:"([^"]+)")?\s*(-->|<--|--)\s*(?:"([^"]+)")?\s*([A-Za-z0-9_]+)\s*$'
)


def _sanitize_type_for_md(typ: str) -> str:
    # Avoid round brackets in attribute type descriptions like "uuid (v4)".
    # Keep round brackets that are part of the type itself, e.g. "decimal(18,2)".
    return re.sub(r"\s\(([^()]*)\)", r" [\1]", typ)


def _parse_field(line: str, pending_comment: str) -> FieldDef | None:
    s = line.strip()
    if not s or s.startswith("'"):
        return None

    required = False
    if s.startswith("*"):
        required = True
        s = s[1:].strip()

    keys: list[str] = []
    for k in ("PK", "FK"):
        if s.startswith(k + " "):
            keys.append(k)
            s = s[len(k) :].strip()

    if ":" not in s:
        return None

    left, right = s.split(":", 1)
    name = left.strip()
    typ = right.strip()

    extras = ""
    m = re.search(r"\[(.+?)\]\s*$", typ)
    if m:
        extras = m.group(1).strip()

    return FieldDef(
        name=name,
        typ=typ,
        required=required,
        keys=keys,
        description=pending_comment.strip(),
        extras=extras,
    )


def parse_puml(text: str) -> tuple[list[EntityDef], list[EnumDef], list[str]]:
    lines = text.splitlines()
    entities: list[EntityDef] = []
    enums: list[EnumDef] = []
    rels: set[str] = set()

    pending_decl_comment = ""
    i = 0
    while i < len(lines):
        ln = lines[i]
        stripped = ln.strip()

        if stripped.startswith("'"):
            pending_decl_comment = stripped.lstrip("'").strip()
            i += 1
            continue

        # relations outside blocks
        m_rel = _RE_REL.match(ln)
        if m_rel:
            left = m_rel.group(1)
            left_card = m_rel.group(2) or ""
            conn = m_rel.group(3)
            right_card = m_rel.group(4) or ""
            right = m_rel.group(5)

            left_part = f"`{left}`" + (f" ({left_card})" if left_card else "")
            right_part = f"`{right}`" + (f" ({right_card})" if right_card else "")
            rels.add(f"{left_part} {conn} {right_part}")

        m = _RE_CLASS_START.match(ln)
        if m:
            name = m.group(1)
            desc = pending_decl_comment
            pending_decl_comment = ""
            i += 1
            pending = ""
            fields: list[FieldDef] = []
            while i < len(lines) and not _RE_BLOCK_END.match(lines[i]):
                cur = lines[i].rstrip()
                if cur.strip().startswith("'"):
                    pending = cur.strip().lstrip("'").strip()
                else:
                    f = _parse_field(cur, pending)
                    if f:
                        fields.append(f)
                    pending = ""
                i += 1
            entities.append(EntityDef(name=name, kind="class", description=desc, fields=fields))
            i += 1
            continue

        m = _RE_ENTITY_START_BARE.match(ln)
        if m:
            name = m.group(1)
            desc = pending_decl_comment
            pending_decl_comment = ""
            i += 1
            pending = ""
            fields = []
            while i < len(lines) and not _RE_BLOCK_END.match(lines[i]):
                cur = lines[i].rstrip()
                if cur.strip().startswith("'"):
                    pending = cur.strip().lstrip("'").strip()
                else:
                    f = _parse_field(cur, pending)
                    if f:
                        fields.append(f)
                    pending = ""
                i += 1
            entities.append(EntityDef(name=name, kind="entity", description=desc, fields=fields))
            i += 1
            continue

        m = _RE_ENTITY_START.match(ln)
        if m:
            name = m.group(1)
            desc = pending_decl_comment
            pending_decl_comment = ""
            i += 1
            pending = ""
            fields = []
            while i < len(lines) and not _RE_BLOCK_END.match(lines[i]):
                cur = lines[i].rstrip()
                if cur.strip().startswith("'"):
                    pending = cur.strip().lstrip("'").strip()
                else:
                    f = _parse_field(cur, pending)
                    if f:
                        fields.append(f)
                    pending = ""
                i += 1
            entities.append(EntityDef(name=name, kind="entity", description=desc, fields=fields))
            i += 1
            continue

        m = _RE_ENUM_START.match(ln)
        if m:
            name = m.group(1)
            desc = pending_decl_comment
            pending_decl_comment = ""
            i += 1
            pending = ""
            values: list[tuple[str, str]] = []
            while i < len(lines) and not _RE_BLOCK_END.match(lines[i]):
                cur = lines[i].strip()
                if not cur:
                    i += 1
                    continue
                if cur.startswith("'"):
                    pending = cur.lstrip("'").strip()
                else:
                    # value line
                    values.append((cur, pending))
                    pending = ""
                i += 1
            enums.append(EnumDef(name=name, description=desc, values=values))
            i += 1
            continue

        i += 1

    return entities, enums, sorted(rels)


def _md_escape(s: str) -> str:
    return s.replace("|", "\\|")


def render_markdown(entities: list[EntityDef], enums: list[EnumDef], rels: list[str]) -> str:
    parts: list[str] = []

    for e in entities:
        parts.append(f"### `{e.name}`\n")
        if e.description:
            parts.append(f"{e.description}\n\n")
        parts.append("| Column | Req | Type | Keys | Description |\n")
        parts.append("|--------|:---:|------|------|-------------|\n")
        for f in e.fields:
            req = "+" if f.required else "-"
            keys = ", ".join(f.keys) if f.keys else ""
            desc = _md_escape(f.description)
            typ = _sanitize_type_for_md(f.typ)
            parts.append(f"| `{f.name}` | {req} | `{_md_escape(typ)}` | {keys} | {desc} |\n")
        parts.append("\n")

    if enums:
        parts.append("### Enums\n")
        for en in enums:
            parts.append(f"- `{en.name}`:\n")
            if en.description:
                parts.append(f"  - {en.description}\n")
            for v, d in en.values:
                if d:
                    parts.append(f"  - `{v}` — {d}\n")
                else:
                    parts.append(f"  - `{v}`\n")
        parts.append("\n")

    if rels:
        parts.append("### Relations\n")
        for r in rels:
            parts.append(f"- {r}\n")
        parts.append("\n")

    return "".join(parts).strip() + "\n"


def main() -> int:
    # Ensure Russian comments render correctly in PowerShell terminals.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True, help="Path to .puml")
    ap.add_argument("--out", dest="out", default=None, help="Optional output .md")
    args = ap.parse_args()

    p = Path(args.inp)
    text = p.read_text(encoding="utf-8", errors="replace")
    entities, enums, rels = parse_puml(text)
    md = render_markdown(entities, enums, rels)

    if args.out:
        # Use UTF-8 with BOM for better compatibility with Windows tools.
        Path(args.out).write_text(md, encoding="utf-8-sig")
    else:
        print(md, end="")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
