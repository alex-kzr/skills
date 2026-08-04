---
name: z-ai-model-selection
description: Select the right Z.AI GLM model for coding agents, OpenClaw workflows, multimodal tasks, office work, translation, OCR, image, audio, and video generation.
---

# Z.AI Model Selection Skill

Use this skill when an agent must choose a Z.AI model for a task.

## Core Rule

Always choose the cheapest and narrowest model that can complete the task reliably.

Do not use the strongest flagship model by default. Use it only when the task is complex, long-running, high-risk, or requires strong planning and execution consistency.

## Model Selection Table

| Task Type | Recommended Model | Why |
|---|---|---|
| Long-horizon coding task | `glm-5.1` | Best default for complex engineering work, long planning, iterative implementation, testing, fixing, and production-grade delivery. |
| Autonomous coding agent | `glm-5.1` | Use when the agent must plan, execute, inspect results, adjust strategy, and keep working across many steps. |
| Complex backend/frontend feature | `glm-5.1` | Strong choice when requirements are ambiguous, multi-step, or require cross-file changes. |
| Complex refactoring | `glm-5.1` | Better for preserving intent, dependencies, and consistency across a large codebase. |
| Deep debugging | `glm-5.1` | Use when the bug requires investigation, logs, tests, tool calls, or several repair attempts. |
| General high-quality assistant task | `glm-5.1` | Use for difficult multi-turn reasoning, planning, analysis, and high-quality written output. |
| Long documents, reports, office-style content | `glm-5.1` | Strong for organizing complex content, reports, teaching materials, PDFs, Word/Excel/PowerPoint-style outputs. |
| Creative writing with strong style control | `glm-5.1` | Use when consistency, tone, plot, character, or polished copywriting matters. |
| OpenClaw workflow | `glm-5-turbo` | Optimized for OpenClaw-style tasks, tool invocation, command following, scheduled/persistent tasks, and long-chain execution. |
| Skill-driven agent workflow | `glm-5-turbo` | Use when the agent relies heavily on tools/skills and must execute many procedural steps. |
| High-throughput tool workflow | `glm-5-turbo` | Good for business workflows where stable tool execution matters more than maximum reasoning quality. |
| Timed or persistent agent task | `glm-5-turbo` | Better fit when the task involves time-related instructions, scheduled triggers, or persistent execution. |
| Strong general coding but not the newest flagship | `glm-5` | Use when `glm-5.1` is unavailable or too expensive, but strong coding/agent performance is still required. |
| Agentic engineering on open-weight style workflows | `glm-5` | Good fallback for large coding and agent tasks when the latest model is not required. |
| Translation of formal/professional text | `glm-5` | Good for professional translation, terminology alignment, and structured language conversion. |
| Text data extraction from contracts, reports, announcements | `glm-5` | Good for extracting key fields and relationships into structured data. |
| Coding assistant with lower cost than GLM-5/5.1 | `glm-4.7` | Use for development support, prototype validation, UI generation, and complex demos when cost matters. |
| Frontend/UI generation without image input | `glm-4.7` | Good for web UI generation, visual aesthetics, layouts, and rapid prototyping from text requirements. |
| Frequent collaborative problem-solving | `glm-4.7` | Good for high-frequency dialogue, solution discussion, and development support. |
| Budget coding / office / translation fallback | `glm-4.6` | Use when you need a capable but older model for coding, smart office tasks, reasoning, search-based agents, or translation. |
| Minor-language or informal translation | `glm-4.6` | Suitable for French, Russian, Japanese, Korean, social media, e-commerce, and informal localized translation. |
| Image, screenshot, GUI, video, or file understanding | `glm-5v-turbo` | Use when the input includes images, screenshots, video, files, visual layouts, GUI elements, or charts. |
| Screenshot-to-frontend implementation | `glm-5v-turbo` | Use when generating frontend code from wireframes, mockups, design screenshots, or high-fidelity visual references. |
| Visual frontend debugging | `glm-5v-turbo` | Use when the bug is visible in a screenshot: layout shift, overlap, spacing, color mismatch, responsive issues. |
| GUI exploration or web visual automation | `glm-5v-turbo` | Use when an agent must understand webpage layout, GUI elements, charts, or visual navigation state. |
| OCR / document layout parsing | `glm-ocr` | Use for extracting text and layout from images or PDF documents. |
| Image generation | `glm-image` | Use for text-to-image generation. |
| Image generation, legacy/fallback | `cogview-4` | Use only when `glm-image` is unavailable or specifically required by the environment. |
| Audio transcription | `glm-asr-2512` | Use for speech-to-text and audio transcription. |
| Video generation | `cogvideox-3` / `vidu-q1` / `vidu-2` | Use for text-to-video or image-to-video generation, depending on the API/tool availability. |
| Slide or poster generation through Z.AI agent API | `slides_glm_agent` | Use the dedicated Slide/Poster Agent when the task is to create slides or posters, rather than manually asking a chat model. |
| Dedicated translation API workflow | Translation Agent API | Use when the task is translation with glossary, paraphrase translation, two-step translation, or three-pass translation strategy. |

## Default Decision Policy

1. If the task includes image, screenshot, video, visual UI, GUI, chart, or file understanding, use `glm-5v-turbo`.
2. Else if the task is OpenClaw-specific, skill-heavy, tool-heavy, persistent, or scheduled, use `glm-5-turbo`.
3. Else if the task is complex coding, long-horizon engineering, deep debugging, large refactoring, or autonomous agent work, use `glm-5.1`.
4. Else if the task is strong but ordinary coding and `glm-5.1` is not needed, use `glm-5` or `glm-4.7`.
5. Else if cost matters more than maximum quality, prefer `glm-4.7`, then `glm-4.6`.
6. Else if the task is OCR, audio, image, video, slide, or translation-agent workflow, use the dedicated model/API instead of a general chat model.

## Thinking Mode Guidance

Use thinking mode when the task requires:
- planning;
- reasoning;
- debugging;
- multi-step tool use;
- architecture decisions;
- structured analysis;
- long-context interpretation.

Disable or reduce thinking for:
- simple rewrites;
- short translations;
- formatting;
- trivial Q&A;
- deterministic extraction with a fixed schema.

## Agent Usage Notes

- For coding agents, prefer streaming responses.
- For JSON or integration tasks, request structured output explicitly.
- For long conversations or repeated context, use context caching when available.
- For tool-enabled agents, verify function calling support before relying on tool calls.
- For visual tasks, do not describe the screenshot manually to a text-only model unless `glm-5v-turbo` is unavailable.
- For OCR-heavy tasks, use `glm-ocr` first, then pass extracted text to a language model if reasoning is needed.
- For slides/posters or translation workflows, prefer the dedicated Z.AI agent APIs when available.

## Fallback Strategy

If the selected model is unavailable:

| Preferred Model | Fallback |
|---|---|
| `glm-5.1` | `glm-5`, then `glm-4.7` |
| `glm-5-turbo` | `glm-5.1`, then `glm-5` |
| `glm-5v-turbo` | `glm-4.6v`, then `glm-4.5v` |
| `glm-ocr` | `glm-5v-turbo` |
| `glm-image` | `cogview-4` |
| `glm-asr-2512` | Use another available ASR/transcription provider |
| `slides_glm_agent` | `glm-5.1` with explicit slide structure instructions |
| Translation Agent API | `glm-5`, then `glm-4.6` |

## Anti-Patterns

Do not:
- use `glm-5.1` for every trivial task;
- use a text-only model for screenshots or GUI understanding when `glm-5v-turbo` is available;
- use a general chat model for OCR when `glm-ocr` is available;
- use image/video generation models for analysis tasks;
- use older models for long-horizon autonomous coding unless cost or availability requires it;
- silently switch models without documenting the reason when the task is important.
