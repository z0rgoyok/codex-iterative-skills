# Artifact Layout

Use one persistent workspace per planning run.

Default root inside the current work root:

```text
.codex-artifacts/iterative-plan-review/sessions/<timestamp>-<task-slug>/
```

Directory layout:

```text
00-input/
  task.md
  constraints.md
  project-context.md
01-working/
  plan-v1.md
  plan-current.md
02-history/
  conversation-log.md
  business-decisions.md
  change-log.md
03-reviews/
  iteration-1/
    plan-before.md
    subagent-prompt.md
    subagent-feedback.md
    questions-for-user.md
    user-answers.md
    plan-after.md
  iteration-2/
  iteration-3/
04-final/
  final-plan.md
  final-summary.md
  open-questions.md
manifest.json
```

File intent:

- `task.md` keeps the original user request unchanged.
- `constraints.md` keeps confirmed limitations and boundaries.
- `project-context.md` keeps local rules and relevant repository context.
- `plan-v1.md` keeps the first meaningful draft.
- `plan-current.md` is the SSOT for the latest working plan.
- `conversation-log.md` keeps the timeline of user and agent exchanges.
- `business-decisions.md` keeps only decisions confirmed by the user.
- `change-log.md` explains why the plan changed after each review pass.
- `subagent-prompt.md` preserves what the reviewer actually saw.
- `subagent-feedback.md` preserves the review comments from the subagent.
- `questions-for-user.md` keeps only business questions that require user choice.
- `user-answers.md` preserves the user's answers without reinterpretation.
- `plan-before.md` and `plan-after.md` preserve the delta around each pass.
- `final-plan.md` is the final delivery artifact.
- `final-summary.md` explains the business meaning of the final plan.
- `open-questions.md` keeps unresolved items that still affect execution.
- `manifest.json` gives machine-readable metadata for the run.

Usage rule:

- Keep history append-only.
- Replace `plan-current.md` when the plan changes.
- Do not rewrite historical iteration files after a later pass changes the plan.
