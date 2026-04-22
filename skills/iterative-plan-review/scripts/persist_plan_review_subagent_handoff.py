#!/usr/bin/env python3
"""Persist the subagent-owned part of one iterative-plan-review pass."""

from __future__ import annotations

import argparse
from pathlib import Path

from persist_plan_review_pass import (
    SCHEMA_VERSION,
    append_jsonl,
    load_paths,
    normalize_review_summary,
    now_iso,
    read_json,
    read_raw_response,
    write_json,
)


def persist_subagent_handoff(
    *,
    run_dir: Path,
    iteration: int,
    reviewer_role: str,
    reviewer_model: str | None,
    prompt_summary: str,
    raw_response: str,
) -> Path:
    paths = load_paths(run_dir=run_dir, iteration=iteration)
    review_payload = read_json(paths.review_file)
    timestamp = now_iso()

    review_payload["schema_version"] = SCHEMA_VERSION
    review_payload["iteration"] = iteration
    review_payload["stage"] = "subagent_handoff_recorded"
    review_payload["subagent"] = {
        "reviewer_role": reviewer_role,
        "reviewer_model": reviewer_model,
        "prompt_summary": prompt_summary.strip(),
        "raw_response": raw_response,
    }
    review_payload["normalized_review"] = normalize_review_summary(raw_response)
    review_payload["persisted_at"] = timestamp

    write_json(paths.review_file, review_payload)
    append_jsonl(
        paths.event_log,
        {
            "timestamp": timestamp,
            "type": "subagent-review-handoff-recorded",
            "details": {
                "iteration": iteration,
                "reviewer_role": reviewer_role,
                "reviewer_model": reviewer_model,
            },
        },
    )
    return paths.review_file


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, help="Path to one plan-review run directory.")
    parser.add_argument("--iteration", required=True, type=int, help="Review iteration number.")
    parser.add_argument("--reviewer-role", default="plan-critic", help="Subagent reviewer role.")
    parser.add_argument("--reviewer-model", help="Subagent reviewer model.")
    parser.add_argument("--prompt-summary", default="", help="Compact summary of what the subagent reviewed.")
    parser.add_argument("--raw-response-file", help="Optional file containing the raw subagent response.")
    args = parser.parse_args()

    raw_response = read_raw_response(
        Path(args.raw_response_file).expanduser().resolve() if args.raw_response_file else None
    )
    review_file = persist_subagent_handoff(
        run_dir=Path(args.run_dir).expanduser().resolve(),
        iteration=args.iteration,
        reviewer_role=args.reviewer_role,
        reviewer_model=args.reviewer_model,
        prompt_summary=args.prompt_summary,
        raw_response=raw_response,
    )
    print(str(review_file))


if __name__ == "__main__":
    main()
