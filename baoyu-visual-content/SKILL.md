---
name: baoyu-visual-content
description: "Generate Chinese-language visual content: infographics (信息图, 21 layouts × 21 styles) and knowledge comics (知识漫画, educational/biography/tutorial)."
version: 1.0.0
metadata:
  hermes:
    tags: [infographic, comic, visual, Chinese, 信息图, 知识漫画, baoyu, visualization]
    absorbed_from: [baoyu-infographic, baoyu-comic]
---

# Baoyu Visual Content — Infographics & Knowledge Comics

Generate rich visual content in Chinese: data-driven infographics and educational knowledge comics.

---

## Section 1: Infographics (信息图)

Create structured infographics with 21 layouts × 21 styles. Turn data, comparisons, processes, or hierarchies into polished visual graphics.

### When to Use
- User wants an infographic (信息图/可视化)
- Data needs visual representation
- Comparisons, timelines, processes, or hierarchies need visualization

### Workflow

1. **Analyze content** — determine the data type and best layout
   - See `references/infographic/analysis-framework.md`
2. **Select layout** — 21 options (comparison, timeline, process, hierarchy, etc.)
   - See `references/infographic/layouts/`
3. **Select style** — 21 visual styles
   - See `references/infographic/styles/`
4. **Generate base prompt** — structured prompt for the image generator
   - See `references/infographic/base-prompt.md`
5. **Add structured content** — fill in the data
   - See `references/infographic/structured-content-template.md`

---

## Section 2: Knowledge Comics (知识漫画)

Create educational comics for biography, tutorial, or knowledge-sharing scenarios.

### When to Use
- User wants a knowledge comic (知识漫画)
- Educational/biography content needs visual storytelling
- Tutorial steps need comic-style illustration

### Workflow

1. **Analyze content** — determine story arc and key scenes
   - See `references/comic/analysis-framework.md`
2. **Select art style** — match the subject matter
   - See `references/comic/art-styles/`
3. **Build storyboard** — plan panels and dialogue
   - See `references/comic/storyboard-template.md`
4. **Create characters** — design recurring characters
   - See `references/comic/character-template.md`
5. **Select layout** — panel arrangement
   - See `references/comic/layouts/`
6. **Apply tones** — visual mood/atmosphere
   - See `references/comic/tones/`
7. **Generate** — use the base prompt and workflow
   - See `references/comic/base-prompt.md` and `references/comic/workflow.md`

### Additional Resources
- `references/comic/auto-selection.md` — automatic style/layout selection
- `references/comic/presets/` — pre-configured style presets
- `references/comic/partial-workflows.md` — partial generation workflows
- `references/comic/ohmsha-guide.md` — Ohmsha-style guide
