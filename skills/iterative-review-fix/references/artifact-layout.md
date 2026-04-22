# Artifact Layout

Use one persistent workspace per review-fix run.

Default root inside the current work root:

```text
.codex-artifacts/iterative-review-fix/sessions/<timestamp>-<task-slug>/
```

Directory layout:

```text
manifest.json
session-state.json
event-log.jsonl
reviews/
  iteration-1.json
  iteration-2.json
  iteration-3.json
```

## What each file is for

- `manifest.json` keeps immutable metadata about the run:
  - schema version;
  - created at;
  - workspace root;
  - run dir;
  - requested entry mode;
  - base branch;
  - artifact paths.

- `session-state.json` is the mutable SSOT:
  - input task and raw findings;
  - scope, constraints, and project context;
  - current status;
  - analysis and strategy;
  - confirmed business decisions;
  - open questions;
  - changed surface;
  - verification summary;
  - final outcome.

- `event-log.jsonl` is append-only history:
  - run created;
  - entry mode resolved;
  - user answer received;
  - review pass persisted;
  - fix batch started or finished;
  - final status recorded.

- `reviews/iteration-N.json` stores one full review pass:
  - review basis;
  - findings in scope;
  - fixes applied;
  - verification;
  - subagent prompt summary;
  - raw subagent response;
  - normalized findings, risks, questions, next batch;
  - user answers related to this pass;
  - exit decision.

## Design intent

This layout solves two operational problems:

1. The agent has one clear mutable source of truth instead of many partially overlapping Markdown files.
2. Automation can validate completeness and order of the workflow without heuristics.

## Required checkpoint

The same `reviews/iteration-N.json` is filled in two ownership phases:

1. The subagent records reviewer trace first:
  - raw response;
  - normalized review summary;
  - reviewer metadata.
2. The caller records orchestration state after `wait_agent`:
  - fixes applied;
  - verification;
  - user answers;
  - exit decision;
  - finalization.

After `wait_agent` returns, the caller must ensure that `reviews/iteration-N.json` already contains reviewer trace, and then finalize the same file before any new code edits or extra verification.

If this checkpoint is missing, the run is incomplete even when the UI already shows the subagent response.

## Suggested JSON shapes

### `manifest.json`

```json
{
  "schema_version": 3,
  "created_at": "2026-04-17T22:40:57+03:00",
  "workspace_root": "/abs/path",
  "run_dir": "/abs/path/.codex-artifacts/iterative-review-fix/sessions/20260417-224057-task",
  "entry_mode_requested": "findings-fix-cycle",
  "base_branch": null,
  "paths": {
    "session_state": "/abs/path/.../session-state.json",
    "event_log": "/abs/path/.../event-log.jsonl",
    "reviews_dir": "/abs/path/.../reviews"
  }
}
```

### `session-state.json`

```json
{
  "schema_version": 3,
  "metadata": {},
  "input": {},
  "analysis": {},
  "working_state": {},
  "confirmed_business_decisions": [],
  "open_questions": [],
  "final_result": {}
}
```

### `reviews/iteration-N.json`

```json
{
  "schema_version": 3,
  "iteration": 1,
  "mode": "re-review-after-fixes",
  "basis": {},
  "in_scope": [],
  "fixes_applied": [],
  "verification": {
    "inspections": [],
    "quality_checks": [],
    "tests": []
  },
  "subagent": {
    "reviewer_skill": "final-gate-review",
    "prompt_summary": "",
    "raw_response": ""
  },
  "normalized_review": {
    "overall_summary": "",
    "remaining_issues": [],
    "regression_risks": [],
    "questions_for_user": [],
    "next_fix_batch": [],
    "what_was_checked": []
  },
  "user_answers": [],
  "exit_decision": {
    "decision": "continue",
    "reason": ""
  }
}
```

### `event-log.jsonl`

One JSON object per line:

```json
{"timestamp":"2026-04-17T22:40:57+03:00","type":"run-created","details":{"entry_mode":"findings-fix-cycle"}}
{"timestamp":"2026-04-17T22:48:58+03:00","type":"review-pass-persisted","details":{"iteration":1,"decision":"continue"}}
```

## Usage rules

- Keep `event-log.jsonl` append-only.
- Replace `session-state.json` when the current state changes.
- Replace `reviews/iteration-N.json` while the pass is in progress, then freeze it once the pass exit decision is recorded.
- Do not spread one review pass across multiple files.
- Let the subagent persist reviewer trace through `scripts/persist_review_subagent_handoff.py`.
- Let the caller finalize the same pass through `scripts/persist_review_pass.py`.
- If subagent handoff is missing, let the caller reconstruct the pass through `scripts/persist_review_pass.py` with `--raw-response-file`.
