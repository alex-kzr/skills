---
name: pipeline-runtime-fallback
description: Use when a coding-runtime fallback is needed mid-pipeline.
---

# Pipeline Runtime Fallback

## Procedure

1. Read the terminal runner result and durable run record before retrying. Distinguish an executor defect from a verifier launch failure, quota limit, or adapter capability rejection.
2. Preserve the original run unchanged. Never resume a pinned-adapter pipeline run with another adapter and never edit its board, task file, or `.pipeline` state to make it look complete.
3. If the user explicitly authorizes a different runtime, use a **fresh direct session** in the same task branch and only inside the task's Allowed scope. Include the prior runner evidence and the unresolved acceptance finding in its prompt.
4. Run the task's declared checks after the direct change. Request a separate read-only review in the fallback runtime when practical; use it to find and repair acceptance gaps iteratively.
5. Report the fallback as direct/self-validation evidence. Leave runner-owned verification pending until a compatible independent runner verification can complete.

## Guardrails

- Do not weaken a strict capability boundary merely to make the fallback adapter launch; preserve a fail-closed `unsupported` result as evidence.
- Do not call direct checks or a fallback review `PASS/PASS`; that verdict belongs only to the pipeline's two independent verifier roles.
- Keep runner-owned lifecycle projections distinct from executor changes when reviewing scope: runner-updated board/task status is not executor scope creep.
- Use the user-requested fallback model and effort explicitly rather than relying on the CLI default.
