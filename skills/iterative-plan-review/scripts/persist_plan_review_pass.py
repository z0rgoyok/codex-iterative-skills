#!/usr/bin/env python3
"""Persist one iterative-plan-review pass into JSON artifacts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 3


@dataclass(frozen=True)
class Paths:
    run_dir: Path
    manifest: Path
    session_state: Path
    event_log: Path
    review_file: Path


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(read_text(path))


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def append_jsonl(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(payload, ensure_ascii=False) + "\n")


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def load_paths(run_dir: Path, iteration: int) -> Paths:
    return Paths(
        run_dir=run_dir,
        manifest=run_dir / "manifest.json",
        session_state=run_dir / "session-state.json",
        event_log=run_dir / "event-log.jsonl",
        review_file=run_dir / "reviews" / f"iteration-{iteration}.json",
    )


def load_checkpoint(path: Path) -> dict[str, Any]:
    payload = read_json(path)
    if "iteration" not in payload:
        raise ValueError("checkpoint JSON must contain 'iteration'")
    return payload


def read_raw_response(raw_response_file: Path | None) -> str:
    if raw_response_file is not None:
        return read_text(raw_response_file).strip()

    if not sys.stdin.isatty():
        return sys.stdin.read().strip()

    raise ValueError("raw response must be provided via --raw-response-file or stdin")


def extract_json_summary(raw_response: str) -> dict[str, Any] | None:
    pattern = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)
    for match in pattern.finditer(raw_response):
        candidate = match.group(1)
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict) and (
            "critical_gaps" in parsed
            or "questions_for_user" in parsed
            or "revised_plan_markdown" in parsed
        ):
            return parsed
    return None


def normalize_heading(title: str) -> str:
    cleaned = title.strip().strip("*#").strip().lower()
    return cleaned.replace("ё", "е")


def split_sections(raw_response: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current = "summary"
    sections[current] = []

    known_headings = {
        "итог",
        "summary",
        "critical gaps",
        "критические пробелы",
        "critical issues",
        "improvement suggestions",
        "предложения по улучшению",
        "улучшения",
        "questions for user",
        "вопросы пользователю",
        "revised plan",
        "обновленный план",
        "обновлённый план",
        "пересобранный план",
        "plan quality signals",
        "сигналы качества плана",
    }

    for line in raw_response.splitlines():
        stripped = line.strip()
        heading = normalize_heading(stripped)
        if heading in known_headings:
            current = heading
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(line)

    return sections


def lines_to_items(lines: list[str], item_key: str) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    buffer: list[str] = []

    def flush() -> None:
        if not buffer:
            return
        text = "\n".join(part.rstrip() for part in buffer).strip()
        if text:
            items.append({item_key: text})
        buffer.clear()

    for line in lines:
        stripped = line.strip()
        if not stripped:
            flush()
            continue
        if stripped.startswith("- ") or stripped.startswith("* "):
            flush()
            buffer.append(stripped[2:].strip())
            continue
        if re.match(r"^\d+\.\s+", stripped):
            flush()
            buffer.append(re.sub(r"^\d+\.\s+", "", stripped))
            continue
        buffer.append(stripped)

    flush()
    return items


def lines_to_markdown(lines: list[str]) -> str:
    return "\n".join(line.rstrip() for line in lines).strip()


def fallback_normalized_review(raw_response: str) -> dict[str, Any]:
    sections = split_sections(raw_response)
    return {
        "overall_summary": "\n".join(sections.get("итог", sections.get("summary", []))).strip(),
        "critical_gaps": lines_to_items(
            sections.get("critical gaps", sections.get("критические пробелы", sections.get("critical issues", []))),
            "summary",
        ),
        "improvement_suggestions": lines_to_items(
            sections.get("improvement suggestions", sections.get("предложения по улучшению", sections.get("улучшения", []))),
            "summary",
        ),
        "questions_for_user": lines_to_items(
            sections.get("questions for user", sections.get("вопросы пользователю", [])),
            "question",
        ),
        "revised_plan_markdown": lines_to_markdown(
            sections.get(
                "revised plan",
                sections.get("обновленный план", sections.get("обновлённый план", sections.get("пересобранный план", []))),
            )
        ),
        "plan_quality_signals": lines_to_items(
            sections.get("plan quality signals", sections.get("сигналы качества плана", [])),
            "summary",
        ),
    }


def ensure_list_of_objects(values: Any, default_key: str) -> list[dict[str, Any]]:
    if not isinstance(values, list):
        return []

    result: list[dict[str, Any]] = []
    for value in values:
        if isinstance(value, dict):
            result.append(value)
        elif isinstance(value, str):
            result.append({default_key: value})
    return result


def normalize_markdown_text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        normalized_lines: list[str] = []
        for index, item in enumerate(value, start=1):
            if isinstance(item, str):
                normalized_lines.append(f"{index}. {item.strip()}")
            elif isinstance(item, dict):
                title = str(item.get("title") or item.get("step") or item.get("summary") or "").strip()
                if title:
                    normalized_lines.append(f"{index}. {title}")
        return "\n".join(normalized_lines).strip()
    return ""


def normalize_review_summary(raw_response: str) -> dict[str, Any]:
    parsed = extract_json_summary(raw_response)
    if parsed is None:
        return fallback_normalized_review(raw_response)

    return {
        "overall_summary": str(parsed.get("overall_summary", "")).strip(),
        "critical_gaps": ensure_list_of_objects(parsed.get("critical_gaps", []), "summary"),
        "improvement_suggestions": ensure_list_of_objects(parsed.get("improvement_suggestions", []), "summary"),
        "questions_for_user": ensure_list_of_objects(parsed.get("questions_for_user", []), "question"),
        "revised_plan_markdown": normalize_markdown_text(parsed.get("revised_plan_markdown", "")),
        "plan_quality_signals": ensure_list_of_objects(parsed.get("plan_quality_signals", []), "summary"),
    }


def maybe_finalize(session_state: dict[str, Any], checkpoint: dict[str, Any], normalized_review: dict[str, Any]) -> None:
    if not checkpoint.get("finalize", False):
        return

    override = checkpoint.get("final_result_override", {})
    final_result = session_state.setdefault("final_result", {})
    final_result["status"] = override.get("status", "completed")
    final_result["final_plan_markdown"] = override.get(
        "final_plan_markdown",
        checkpoint.get("plan_after", session_state.get("working_state", {}).get("current_plan_markdown", "")),
    )
    final_result["final_summary"] = override.get(
        "final_summary",
        normalized_review.get("overall_summary", ""),
    )
    final_result["open_questions"] = ensure_list_of_objects(
        override.get("open_questions", session_state.get("open_questions", [])),
        "question",
    )


def persist_review_pass(paths: Paths, checkpoint: dict[str, Any], raw_response: str) -> None:
    manifest = read_json(paths.manifest)
    session_state = read_json(paths.session_state)
    review_payload = read_json(paths.review_file)

    normalized_review = normalize_review_summary(raw_response)
    timestamp = now_iso()
    stage = checkpoint.get("stage", "pass_completed")
    plan_after = checkpoint.get("plan_after")
    if not isinstance(plan_after, str) or not plan_after.strip():
        plan_after = normalized_review.get("revised_plan_markdown", "")

    review_payload.update(
        {
            "schema_version": SCHEMA_VERSION,
            "iteration": checkpoint["iteration"],
            "stage": stage,
            "basis": {
                "task_summary": str(checkpoint.get("basis", {}).get("task_summary", "")).strip(),
                "confirmed_context": ensure_list_of_objects(
                    checkpoint.get("basis", {}).get("confirmed_context", []),
                    "summary",
                ),
                "confirmed_constraints": ensure_list_of_objects(
                    checkpoint.get("basis", {}).get("confirmed_constraints", []),
                    "summary",
                ),
                "confirmed_business_decisions": ensure_list_of_objects(
                    checkpoint.get("basis", {}).get("confirmed_business_decisions", []),
                    "decision",
                ),
                "open_questions_at_start": ensure_list_of_objects(
                    checkpoint.get("basis", {}).get("open_questions_at_start", []),
                    "question",
                ),
            },
            "plan_before": str(checkpoint.get("plan_before", "")).strip(),
            "subagent": {
                "reviewer_role": checkpoint.get("subagent", {}).get("reviewer_role", "plan-critic"),
                "reviewer_model": checkpoint.get("subagent", {}).get("reviewer_model"),
                "prompt_summary": str(checkpoint.get("subagent", {}).get("prompt_summary", "")).strip(),
                "raw_response": raw_response,
            },
            "normalized_review": normalized_review,
            "user_answers": ensure_list_of_objects(checkpoint.get("user_answers", []), "answer"),
            "plan_after": str(plan_after).strip(),
            "change_summary": ensure_list_of_objects(checkpoint.get("change_summary", []), "summary"),
            "exit_decision": checkpoint.get(
                "exit_decision",
                {"decision": "pending", "reason": ""},
            ),
            "persisted_at": timestamp,
        }
    )
    write_json(paths.review_file, review_payload)

    metadata = session_state.setdefault("metadata", {})
    metadata["current_phase"] = "review_pass_persisted"
    metadata["last_updated_at"] = timestamp
    metadata["schema_version"] = SCHEMA_VERSION

    if "input_updates" in checkpoint and isinstance(checkpoint["input_updates"], dict):
        input_state = session_state.setdefault("input", {})
        for field_name, default_key in (
            ("confirmed_context", "summary"),
            ("confirmed_constraints", "summary"),
            ("project_context", "summary"),
            ("assumptions", "summary"),
        ):
            if field_name in checkpoint["input_updates"]:
                input_state[field_name] = ensure_list_of_objects(checkpoint["input_updates"][field_name], default_key)

    if "plan_analysis_updates" in checkpoint and isinstance(checkpoint["plan_analysis_updates"], dict):
        plan_analysis = session_state.setdefault("plan_analysis", {})
        updates = checkpoint["plan_analysis_updates"]
        if "goal" in updates:
            plan_analysis["goal"] = str(updates["goal"]).strip()
        if "expected_outcome" in updates:
            plan_analysis["expected_outcome"] = str(updates["expected_outcome"]).strip()
        for field_name in ("dependencies", "risks", "verification_points"):
            if field_name in updates:
                plan_analysis[field_name] = ensure_list_of_objects(updates[field_name], "summary")

    if "confirmed_business_decisions" in checkpoint:
        session_state["confirmed_business_decisions"] = ensure_list_of_objects(
            checkpoint.get("confirmed_business_decisions", []),
            "decision",
        )

    open_questions_override = checkpoint.get("open_questions")
    if open_questions_override is not None:
        session_state["open_questions"] = ensure_list_of_objects(open_questions_override, "question")
    else:
        session_state["open_questions"] = normalized_review.get("questions_for_user", [])

    working_state = session_state.setdefault("working_state", {})
    current_plan_markdown = str(plan_after).strip() or str(working_state.get("current_plan_markdown", "")).strip()
    if current_plan_markdown:
        working_state["current_plan_markdown"] = current_plan_markdown

    current_label = checkpoint.get("current_plan_label")
    plan_versions = working_state.setdefault("plan_versions", {})
    if "plan_v1" in checkpoint:
        plan_versions["v1"] = str(checkpoint.get("plan_v1", "")).strip()
    if current_label:
        plan_versions["current_label"] = str(current_label).strip()
    elif current_plan_markdown and not plan_versions.get("current_label"):
        plan_versions["current_label"] = f"iteration-{checkpoint['iteration']}"

    working_state["current_status"] = [
        f"Iteration {checkpoint['iteration']} persisted.",
        f"Stage: {stage}.",
        f"Exit decision: {review_payload['exit_decision'].get('decision', 'pending')}.",
    ]
    working_state["latest_review_pass"] = {
        "iteration": checkpoint["iteration"],
        "stage": stage,
        "decision": review_payload["exit_decision"].get("decision", "pending"),
        "critical_gaps_count": len(normalized_review.get("critical_gaps", [])),
        "questions_for_user_count": len(normalized_review.get("questions_for_user", [])),
    }

    maybe_finalize(session_state, checkpoint, normalized_review)
    write_json(paths.session_state, session_state)

    append_jsonl(
        paths.event_log,
        {
            "timestamp": timestamp,
            "type": "review-pass-persisted",
            "details": {
                "iteration": checkpoint["iteration"],
                "stage": stage,
                "decision": review_payload["exit_decision"].get("decision", "pending"),
                "critical_gaps_count": len(normalized_review.get("critical_gaps", [])),
                "questions_for_user_count": len(normalized_review.get("questions_for_user", [])),
                "manifest_schema_version": manifest.get("schema_version"),
            },
        },
    )

    if checkpoint.get("finalize", False):
        append_jsonl(
            paths.event_log,
            {
                "timestamp": timestamp,
                "type": "run-finalized",
                "details": {
                    "iteration": checkpoint["iteration"],
                    "status": session_state.get("final_result", {}).get("status"),
                    "open_questions_count": len(session_state.get("final_result", {}).get("open_questions", [])),
                },
            },
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, help="Path to one plan-review run directory.")
    parser.add_argument("--checkpoint-file", required=True, help="JSON file with iteration checkpoint metadata.")
    parser.add_argument("--raw-response-file", help="Optional file containing the raw subagent response.")
    args = parser.parse_args()

    run_dir = Path(args.run_dir).expanduser().resolve()
    checkpoint = load_checkpoint(Path(args.checkpoint_file).expanduser().resolve())
    raw_response = read_raw_response(
        Path(args.raw_response_file).expanduser().resolve() if args.raw_response_file else None
    )
    paths = load_paths(run_dir=run_dir, iteration=int(checkpoint["iteration"]))

    persist_review_pass(paths=paths, checkpoint=checkpoint, raw_response=raw_response)
    print(str(paths.review_file))


if __name__ == "__main__":
    main()
