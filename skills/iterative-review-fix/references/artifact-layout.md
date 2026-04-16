# Artifact Layout

Use one persistent workspace per review-fix run.

Default root inside the current work root:

```text
.codex-artifacts/iterative-review-fix/sessions/<timestamp>-<task-slug>/
```

Directory layout:

```text
00-input/
  task.md
  review-findings.md
  scope-and-constraints.md
  review-scope.md
  project-context.md
01-analysis/
  findings-analysis.md
  fix-strategy.md
  questions-for-user.md
02-working/
  implementation-plan.md
  current-status.md
  changed-surface.md
03-history/
  conversation-log.md
  decision-log.md
  change-log.md
04-reviews/
  iteration-1/
    review-basis.md
    findings-in-scope.md
    fixes-applied.md
    verification.md
    subagent-review-prompt.md
    subagent-review.md
    questions-for-user.md
    user-answers.md
    exit-decision.md
  iteration-2/
  iteration-3/
05-final/
  resolved-findings.md
  remaining-findings.md
  final-summary.md
  verification-summary.md
manifest.json
```

File intent:

- `task.md` keeps the original user request unchanged.
- `review-findings.md` keeps the raw review comments or findings.
- `scope-and-constraints.md` keeps confirmed limits, priorities, and exclusions.
- `review-scope.md` records the entry mode, base branch, worktree status, and why the first pass uses this review basis.
- `project-context.md` keeps local rules, architecture, and surrounding code context.
- `findings-analysis.md` records which findings are confirmed, partial, stale, or rejected.
- `fix-strategy.md` records the chosen order of fixes and the reasoning behind it.
- `questions-for-user.md` records only business decisions that need the user's answer.
- `implementation-plan.md` keeps the current fix batch and execution sequence.
- `current-status.md` is the SSOT for the latest state of the fix cycle.
- `changed-surface.md` records files, modules, and behaviors affected by the changes.
- `conversation-log.md` keeps the timeline of questions and answers.
- `decision-log.md` keeps only decisions explicitly confirmed by the user.
- `change-log.md` explains why the fix direction changed between iterations.
- `review-basis.md` records whether the pass is an initial diff review or a re-review after fixes.
- `findings-in-scope.md` records which findings were addressed in the current pass.
- `fixes-applied.md` records the actual changes introduced in the current pass.
- `verification.md` records inspections, quality checks, and tests for the current pass.
- `subagent-review-prompt.md` preserves what the reviewer actually saw.
- `subagent-review.md` preserves the reviewer comments from the subagent.
- `questions-for-user.md` and `user-answers.md` preserve the business clarification loop for each pass.
- `exit-decision.md` records why the cycle stops or continues after the pass.
- `resolved-findings.md` lists what is closed by the final state.
- `remaining-findings.md` lists unresolved or intentionally deferred issues.
- `final-summary.md` explains the business meaning of the result.
- `verification-summary.md` summarizes the final quality checks and residual risk.
- `manifest.json` gives machine-readable metadata for the run.

Usage rule:

- Keep history append-only.
- Replace `02-working/current-status.md` when the current state changes.
- Do not rewrite historical iteration files after a later pass changes the code or the interpretation of findings.
