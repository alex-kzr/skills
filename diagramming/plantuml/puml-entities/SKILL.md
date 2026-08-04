---
name: puml-entities
description: Document entities/tables/enums  PlantUML (.puml). Extract diagrams into human-readable Markdown. Render svg from puml.
---

# PlantUML Entities → Markdown

## Goal
- Create or update `.puml` with entities/classes/enums
- (Optional) Extract into a Markdown snippet for documentation
- (Optional) Generate svg diagram

## Inputs
- Path to `.puml`.
- (Optional) Output `.md` path.

## Puml diagram rules
1) Entity blocks:
- `entity <name> { ... }`
- `entity “<name>” as <alias> { ... }`
- Legacy/compatibility: `class <name> { ... }` (prefer `entity` for new diagrams)
2) Field lines inside blocks:
- Leading `*` means “required”.
- Prefix tokens `PK` and `FK` are placed **before** the field name: `* PK id : bigserial`, `FK order_id : int8`. Never use suffix `<<PK>>`/`<<FK>>` notation.
- Type is parsed from `<field>: <type>`.
3) Comments (convention):
- Comment of entity/enum: a line starting with `'` immediately before the declaration line.
- Comment of attribute/enum value: a line starting with `'` immediately before the attribute/value line.
4) Enums:
- `enum <name> { ... }` values are extracted (with `'` comments as descriptions).
5) Relations:
- Relations are extracted from lines containing `-->`, `<--`, `--` (including multiplicities like `”1” -- “0..*”`).
- **Never** use `table::attribute` syntax in relation lines — it breaks PlantUML's relation rendering. Use plain table aliases only: `payment }o--o| person_snapshot`.
- **Do not add labels to relation lines.** Labels render on top of entities and obstruct the diagram. Write relations without any `: “...”` suffix: `order }o--o{ payment`.
- **Never duplicate a relation line between the same two entities.** If multiple FK columns in one table reference the same target table, use a single relation line.
6) Entities use `entity` blocks.
7) Enumerators use `enum` blocks.
8) Comment of entity/enum goes on the line **before** the declaration.
9) Comment of attribute goes on the line **before** the attribute.
10) Required attributes **must always** be marked by `*` before the attribute — no exceptions. Determine required/not-null from the DB schema (NULL = NO) or entity definition. Example: `* id: int`.
11) Attribute type goes after `:` (e.g. `report_preparation_day: int`). Use square brackets for type parameters (e.g. `varchar[255]`, `numeric[10,2]`) — never parentheses, as PlantUML treats `type(...)` as a method signature. For enum-like string fields, list allowed values inline after a second `:` using `|` without spaces: `type : varchar[255] : [routing|cascading]`. Never wrap values to a new line with `\n`.
17) **No `..label..` separators** inside entity blocks unless the user explicitly requests them. Do not add visual section dividers like `..снапшоты персон..` or bare `..` on your own initiative.
12) Always add relations with multiplicity where it matters (e.g. `company \”1\” -- \”0..*\” contract`).
13) In enums, “attributes” are enum values.
14) **No `--` separator** inside entity blocks. Do not use `--` to separate the PK field from the rest of the attributes.
15) Place relations after entity declarations to avoid PlantUML auto-creating placeholders (and name conflicts).
16) **Цвет атрибута и обязательность**: если атрибут помечается цветом (новый/изменённый), то признак обязательности `*` ставится **до** тега `<b><color:...>`, а PK/FK — после. Формат: `*<b><color:darkgreen> FK account_id : int8`. Это нужно, потому что PlantUML применяет стиль ко всей оставшейся строке, и если `*` поставить после тега — он тоже окрасится и читается неверно.

## Generate Markdown from `.puml`

```powershell
python .agents/skills/puml-entities/scripts/puml_entities_to_md.py --in <path-to.puml> --out <path-to.md>
```

### Output Format (Markdown)
- `### \`entity_name\``
- Table: `Column / Req / Type / Keys / Description`
- Enums rendered as bullet lists
- Relations rendered as bullet list

## Render `.puml` to `.svg
Render `.puml` to `.svg` next to the diagram:

```powershell
python .agents/skills/aw-cr-spec-updater-from-file/scripts/render_puml_svg.py --in <path-to.puml> --out <path-to.svg>
```

Note: the renderer strips a leading PlantUML processing-instruction line like `<?plantuml 1.2026.2?>` from the generated SVG.