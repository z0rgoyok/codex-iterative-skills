# Artifact Layout

Use one persistent workspace per plan-review run.

Default root inside the current work root:

```text
.codex-artifacts/iterative-plan-review/sessions/<timestamp>-<task-slug>/
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
  - artifact paths.

- `session-state.json` is the mutable SSOT:
  - input task, constraints, context, and assumptions;
  - current plan markdown;
  - plan goal, dependencies, risks, and verification points;
  - confirmed business decisions;
  - open questions;
  - final plan and summary.

- `event-log.jsonl` is append-only history:
  - run created;
  - review pass persisted;
  - user answers incorporated;
  - final status recorded.

- `reviews/iteration-N.json` stores one full review pass:
  - basis and plan-before snapshot;
  - prompt summary and raw subagent response;
  - normalized critical gaps, improvement suggestions, business questions, revised plan, quality signals;
  - user answers related to the pass;
  - plan-after snapshot;
  - change summary and exit decision.

## Design intent

This layout solves two operating problems:

1. The agent keeps one clear mutable source of truth instead of many loosely coordinated Markdown files.
2. Automation can validate that each review pass was actually persisted and whether business decisions were resolved.

## Required checkpoint

The same `reviews/iteration-N.json` is filled in two ownership phases:

1. The subagent records reviewer trace first:
  - raw response;
  - normalized review summary;
  - reviewer metadata.
2. The caller records orchestration state after `wait_agent`:
  - user answers;
  - plan_after;
  - change summary;
  - exit decision;
  - finalization.

After `wait_agent` returns, the caller must ensure that `reviews/iteration-N.json` already contains reviewer trace, and then finalize the same file before any new plan edits, extra questioning, or another review pass.

If this checkpoint is missing, the run is incomplete even when the UI already shows the subagent response.

The same `reviews/iteration-N.json` file may be updated while the pass is still in progress. The important rule is that one pass stays in one JSON document instead of being split across many files.

## Suggested JSON shapes

### `manifest.json`

```json
{
  "schema_version": 3,
  "created_at": "2026-04-18T13:00:00+03:00",
  "workspace_root": "/abs/path",
  "run_dir": "/abs/path/.codex-artifacts/iterative-plan-review/sessions/20260418-130000-task",
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
  "plan_analysis": {},
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
  "stage": "pass_completed",
  "basis": {
    "task_summary": "",
    "confirmed_context": [],
    "confirmed_constraints": [],
    "confirmed_business_decisions": [],
    "open_questions_at_start": []
  },
  "plan_before": "",
  "subagent": {
    "reviewer_role": "plan-critic",
    "reviewer_model": "gpt-5.4",
    "prompt_summary": "",
    "raw_response": ""
  },
  "normalized_review": {
    "overall_summary": "",
    "critical_gaps": [],
    "improvement_suggestions": [],
    "questions_for_user": [],
    "revised_plan_markdown": "",
    "plan_quality_signals": []
  },
  "user_answers": [],
  "plan_after": "",
  "change_summary": [],
  "exit_decision": {
    "decision": "continue",
    "reason": ""
  },
  "persisted_at": "2026-04-18T13:10:00+03:00"
}
```

### `event-log.jsonl`

One JSON object per line:

```json
{"timestamp":"2026-04-18T13:00:00+03:00","type":"run-created","details":{"schema_version":3}}
{"timestamp":"2026-04-18T13:10:00+03:00","type":"review-pass-persisted","details":{"iteration":1,"stage":"review_received","decision":"ask-user"}}
{"timestamp":"2026-04-18T13:18:00+03:00","type":"run-finalized","details":{"iteration":1,"status":"completed"}}
```

## Usage rules

- Keep `event-log.jsonl` append-only.
- Replace `session-state.json` when the current plan state changes.
- Replace `reviews/iteration-N.json` while the pass is in progress, then freeze it once the exit decision is recorded.
- Do not spread one review pass across multiple files.
- Let the subagent persist reviewer trace through `scripts/persist_plan_review_subagent_handoff.py`.
- Let the caller finalize the same pass through `scripts/persist_plan_review_pass.py`.
- If subagent handoff is missing, let the caller reconstruct the pass through `scripts/persist_plan_review_pass.py` with `--raw-response-file`.
