---
name: skill-update
description: Guide for creating or updating effective skills. This skill should be used when users want to create a new skill (or update an existing skill) that extends Codex's capabilities with specialized knowledge, workflows, or tool integrations.
metadata:
  short-description: Create or update a skill
---

# Skill Creator

This skill provides guidance for creating and updating skills.

For skill folder structure, anatomy, and how to find existing skills, see [skill-navigator](../skill-navigator/SKILL.md).

## Dependencies

Skill scripts live in the skill's own `scripts/` directory, but their
external Python/Node.js dependencies default to the shared root runtime
(see [runtime/README.md](../../runtime/README.md)), not a skill-local
`runtime/` folder:

- `runtime/python/base/.venv` — shared Python dependencies (default)
- `runtime/python/ml/.venv` — shared ML/LLM Python dependencies (optional)
- `runtime/node/node_modules` — shared Node.js dependencies

`scripts/quick_validate.py` and `scripts/generate_openai_yaml.py` need
`PyYAML`, provided by `runtime/python/base/.venv`.

Scripts discover the agents root by walking upward from their own location
until they find a directory containing both `skills/` and `runtime/`. If
the required shared runtime is not prepared there, the script must fail
with a clear error naming the missing path — never auto-install packages
(`pip install`, `npm install`, etc.) during normal execution, and never
fall back to globally installed packages.

A skill-local `runtime/` subfolder is only for explicit exceptions where a
skill's dependencies must be isolated from the shared runtime (e.g.
conflicting package versions). Do not create one by default.

## Core Principles

### Concise is Key

The context window is a public good. Skills share the context window with everything else Codex needs: system prompt, conversation history, other Skills' metadata, and the actual user request.

**Default assumption: Codex is already very smart.** Only add context Codex doesn't already have. Challenge each piece of information: "Does Codex really need this explanation?" and "Does this paragraph justify its token cost?"

Prefer concise examples over verbose explanations.

### Set Appropriate Degrees of Freedom

Match the level of specificity to the task's fragility and variability:

**High freedom (text-based instructions)**: Use when multiple approaches are valid, decisions depend on context, or heuristics guide the approach.

**Medium freedom (pseudocode or scripts with parameters)**: Use when a preferred pattern exists, some variation is acceptable, or configuration affects behavior.

**Low freedom (specific scripts, few parameters)**: Use when operations are fragile and error-prone, consistency is critical, or a specific sequence must be followed.

Think of Codex as exploring a path: a narrow bridge with cliffs needs specific guardrails (low freedom), while an open field allows many routes (high freedom).

### Protect Validation Integrity

You may use subagents during iteration to validate whether a skill works on realistic tasks or whether a suspected problem is real. This is most useful when you want an independent pass on the skill's behavior, outputs, or failure modes after a revision. Only do this when it is possible to start new subagents.

When using subagents for validation, treat that as an evaluation surface. The goal is to learn whether the skill generalizes, not whether another agent can reconstruct the answer from leaked context.

Prefer raw artifacts such as example prompts, outputs, diffs, logs, or traces. Give the minimum task-local context needed to perform the validation. Avoid passing the intended answer, suspected bug, intended fix, or your prior conclusions unless the validation explicitly requires them.

## Language Requirement

All skills must be written in **English**. This applies to SKILL.md, all reference files, scripts, and any other bundled resources.

## Finding Existing Skills

Before creating a new skill, check whether a relevant skill already exists. Use [skill-navigator](../skill-navigator/SKILL.md) to browse the skill catalog and locate skills by task or domain.

## Skill Creation Process

Skill creation involves these steps:

1. Understand the skill with concrete examples
2. Plan reusable skill contents (scripts, references, assets)
3. Initialize the skill (run init_skill.py)
4. Edit the skill (implement resources and write SKILL.md)
5. Validate the skill (run quick_validate.py)
6. Iterate based on real usage and forward-test complex skills.

Follow these steps in order, skipping only if there is a clear reason why they are not applicable.

### Skill Naming

- Use lowercase letters, digits, and hyphens only; normalize user-provided titles to hyphen-case (e.g., "Plan Mode" -> `plan-mode`).
- When generating names, generate a name under 64 characters (letters, digits, hyphens).
- Prefer short, verb-led phrases that describe the action.
- Namespace by tool when it improves clarity or triggering (e.g., `gh-address-comments`, `linear-address-issue`).
- Name the skill folder exactly after the skill name.

### Step 1: Understanding the Skill with Concrete Examples

Skip this step only when the skill's usage patterns are already clearly understood. It remains valuable even when working with an existing skill.

To create an effective skill, clearly understand concrete examples of how the skill will be used. This understanding can come from either direct user examples or generated examples that are validated with user feedback.

For example, when building an image-editor skill, relevant questions include:

- "What functionality should the image-editor skill support? Editing, rotating, anything else?"
- "Can you give some examples of how this skill would be used?"
- "I can imagine users asking for things like 'Remove the red-eye from this image' or 'Rotate this image'. Are there other ways you imagine this skill being used?"
- "What would a user say that should trigger this skill?"
- "Where should I create this skill? If you do not have a preference, I will place it in `$CODEX_HOME/skills` (or `~/.codex/skills` when `CODEX_HOME` is unset) so Codex can discover it automatically."

To avoid overwhelming users, avoid asking too many questions in a single message. Start with the most important questions and follow up as needed for better effectiveness.

Conclude this step when there is a clear sense of the functionality the skill should support.

### Step 2: Planning the Reusable Skill Contents

To turn concrete examples into an effective skill, analyze each example by:

1. Considering how to execute on the example from scratch
2. Identifying what scripts, references, and assets would be helpful when executing these workflows repeatedly

Example: When building a `pdf-editor` skill to handle queries like "Help me rotate this PDF," the analysis shows:

1. Rotating a PDF requires re-writing the same code each time
2. A `scripts/rotate_pdf.py` script would be helpful to store in the skill

Example: When designing a `frontend-webapp-builder` skill for queries like "Build me a todo app" or "Build me a dashboard to track my steps," the analysis shows:

1. Writing a frontend webapp requires the same boilerplate HTML/React each time
2. An `assets/hello-world/` template containing the boilerplate HTML/React project files would be helpful to store in the skill

Example: When building a `big-query` skill to handle queries like "How many users have logged in today?" the analysis shows:

1. Querying BigQuery requires re-discovering the table schemas and relationships each time
2. A `references/schema.md` file documenting the table schemas would be helpful to store in the skill

To establish the skill's contents, analyze each concrete example to create a list of the reusable resources to include: scripts, references, and assets.

Scripts always live in the skill's own `scripts/` subfolder — never in a shared or top-level scripts directory. If a script depends on external Python or Node.js packages, default to the shared root `runtime/` (see [runtime/README.md](../../runtime/README.md)) rather than polluting the global environment. Only add packages to a skill-local `runtime/` subfolder when isolation is explicitly required; in that case add it to `.gitignore` so downloaded packages are never committed.

### Step 3: Initializing the Skill

At this point, it is time to actually create the skill.

Skip this step only if the skill being developed already exists. In this case, continue to the next step.

Before running `init_skill.py`, ask where the user wants the skill created. If they do not specify a location, default to `$CODEX_HOME/skills`; when `CODEX_HOME` is unset, fall back to `~/.codex/skills` so the skill is auto-discovered.

When creating a new skill from scratch, always run the `init_skill.py` script. The script conveniently generates a new template skill directory that automatically includes everything a skill requires, making the skill creation process much more efficient and reliable.

Usage:

```bash
scripts/init_skill.py <skill-name> --path <output-directory> [--resources scripts,references,assets] [--examples]
```

Examples:

```bash
scripts/init_skill.py my-skill --path "${CODEX_HOME:-$HOME/.codex}/skills"
scripts/init_skill.py my-skill --path "${CODEX_HOME:-$HOME/.codex}/skills" --resources scripts,references
scripts/init_skill.py my-skill --path ~/work/skills --resources scripts --examples
```

The script:

- Creates the skill directory at the specified path
- Generates a SKILL.md template with proper frontmatter and TODO placeholders
- Creates `agents/openai.yaml` using agent-generated `display_name`, `short_description`, and `default_prompt` passed via `--interface key=value`
- Optionally creates resource directories based on `--resources`
- Optionally adds example files when `--examples` is set

After initialization, customize the SKILL.md and add resources as needed. If you used `--examples`, replace or delete placeholder files.

Generate `display_name`, `short_description`, and `default_prompt` by reading the skill, then pass them as `--interface key=value` to `init_skill.py` or regenerate with:

```bash
scripts/generate_openai_yaml.py <path/to/skill-folder> --interface key=value
```

Only include other optional interface fields when the user explicitly provides them. For full field descriptions and examples, see references/openai_yaml.md.

### Step 4: Edit the Skill

When editing the (newly-generated or existing) skill, remember that the skill is being created for another instance of Codex to use. Include information that would be beneficial and non-obvious to Codex. Consider what procedural knowledge, domain-specific details, or reusable assets would help another Codex instance execute these tasks more effectively.

After substantial revisions, or if the skill is particularly tricky, you should use subagents to forward-test the skill on realistic tasks or artifacts. When doing so, pass the artifact under validation rather than your diagnosis of what is wrong, and keep the prompt generic enough that success depends on transferable reasoning rather than hidden ground truth.

#### Start with Reusable Skill Contents

To begin implementation, start with the reusable resources identified above: `scripts/`, `references/`, and `assets/` files. Note that this step may require user input. For example, when implementing a `brand-guidelines` skill, the user may need to provide brand assets or templates to store in `assets/`, or documentation to store in `references/`.

Added scripts must be tested by actually running them to ensure there are no bugs and that the output matches what is expected. If there are many similar scripts, only a representative sample needs to be tested to ensure confidence that they all work while balancing time to completion.

If you used `--examples`, delete any placeholder files that are not needed for the skill. Only create resource directories that are actually required.

#### Update SKILL.md

**Writing Guidelines:** Always use imperative/infinitive form.

##### Frontmatter

Write the YAML frontmatter with `name` and `description`:

- `name`: The skill name
- `description`: This is the primary triggering mechanism for your skill, and helps Codex understand when to use the skill.
  - Include both what the Skill does and specific triggers/contexts for when to use it.
  - Include all "when to use" information here - Not in the body. The body is only loaded after triggering, so "When to Use This Skill" sections in the body are not helpful to Codex.
  - Example description for a `docx` skill: "Comprehensive document creation, editing, and analysis with support for tracked changes, comments, formatting preservation, and text extraction. Use when Codex needs to work with professional documents (.docx files) for: (1) Creating new documents, (2) Modifying or editing content, (3) Working with tracked changes, (4) Adding comments, or any other document tasks"

Do not include any other fields in YAML frontmatter.

##### Body

Write instructions for using the skill and its bundled resources. For structure and organization patterns, see [skill-navigator](../skill-navigator/SKILL.md).

##### Links in SKILL.md

Always use **relative links**, never absolute paths. Link targets depend on what is being referenced:

- Another skill → `../other-skill/SKILL.md` (e.g., `[skill-navigator](../skill-navigator/SKILL.md)`)
- A catalog → `../catalog/DESCRIPTION.md` (e.g., `[projects/](../projects/DESCRIPTION.md)`)
- A file within the same skill → `references/file.md` or `scripts/file.py`

Apply this rule when writing new SKILL.md files and when updating existing ones.

When editing any skill file, write links to files inside the same repository
as clickable relative Markdown links in the form `[document-name](relative/path)`
so readers can navigate to them. Do not leave repository file references as
absolute paths or plain text when they can be linked.

### Step 5: Validate the Skill

Once development of the skill is complete, validate the skill folder to catch basic issues early:

```bash
scripts/quick_validate.py <path/to/skill-folder>
```

The validation script checks YAML frontmatter format, required fields, and naming rules. If validation fails, fix the reported issues and run the command again.

### Step 5.5: Update DESCRIPTION.md

**Always** update the `DESCRIPTION.md` of the parent catalog when creating, updating, moving, or deleting a skill or catalog folder. This is mandatory — `DESCRIPTION.md` is the navigation index that other agents use to find skills.

The table has columns `Type`, `Path`, `Description`, and `When to open`:

- **New skill or catalog** — append a new row (`Type`: `Skill` or `Catalog`).
- **Updated skill** — update the `Description` and `When to open` columns if they are now stale.
- **Renamed or moved skill/catalog** — update the row's `Path` (and `Description` if needed). Also update the `DESCRIPTION.md` of the destination catalog if moving between catalogs.
- **Deleted skill or catalog** — remove the row entirely.

If no `DESCRIPTION.md` exists in the parent directory, skip this step.

### Step 5.6: Update Skills Knowledge Graph

**After adding, deleting, updating, or renaming a skill, rebuild the Graphify knowledge graph** so that AI agents can discover the updated skill and find relevant skills correctly.

Use [skill-graphify](../skill-graphify/SKILL.md) to rebuild the skills index:

```bash
# Linux/macOS
cd graphify-graph
bash ../skills/skill-graphify/scripts/build.sh ../skills

# Windows PowerShell
cd graphify-graph
..\skills\skill-graphify\scripts\build.ps1 -SkillsDir "..\skills"
```

This ensures:
- New skills are discoverable via `graphify query` commands
- Deleted skills are removed from search results
- Updated skill metadata is reflected in the graph
- AI agents can find the most relevant skills for tasks

See [Graphify documentation](../skill-graphify/SKILL.md) for querying and managing the skills knowledge graph.

### Step 6: Iterate

After testing the skill, you may detect the skill is complex enough that it requires forward-testing; or users may request improvements.

User testing often this happens right after using the skill, with fresh context of how the skill performed.

**Forward-testing and iteration workflow:**

1. Use the skill on real tasks
2. Notice struggles or inefficiencies
3. Identify how SKILL.md or bundled resources should be updated
4. Implement changes and test again
5. Forward-test if it is reasonable and appropriate

## Forward-testing

To forward-test, launch subagents as a way to stress test the skill with minimal context.
Subagents should *not* know that they are being asked to test the skill.  They should be treated as
an agent asked to perform a task by the user.  Prompts to subagents should look like:
  `Use $skill-x at /path/to/skill-x to solve problem y`
Not:
  `Review the skill at /path/to/skill-x; pretend a user asks you to...`

Decision rule for forward-testing:
  - Err on the side of forward-testing
  - Ask for approval if you think there's a risk that forward-testing would:
    * take a long time,
    * require additional approvals from the user, or
    * modify live production systems

  In these cases, show the user your proposed prompt and request (1) a yes/no decision, and
  (2) any suggested modifictions.

Considerations when forward-testing:
   - use fresh threads for independent passes
   - pass the skill, and a request in a similar way the user would.
   - pass raw artifacts, not your conclusions
   - avoid showing expected answers or intended fixes
   - rebuild context from source artifacts after each iteration
   - review the subagent's output and reasoning and emitted artifacts
   - avoid leaving artifacts the agent can find on disk between iterations;
     clean up subagents' artifacts to avoid additional contamination.

If forward-testing only succeeds when subagents see leaked context, tighten the skill or the
forward-testing setup before trusting the result.
