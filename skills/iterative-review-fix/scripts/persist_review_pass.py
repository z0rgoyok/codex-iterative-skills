#!/usr/bin/env python3
"""Persist one iterative-review-fix review pass into JSON artifacts."""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
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
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as stream:
        stream.write(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
        temp_path = Path(stream.name)
    temp_path.replace(path)


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


def read_raw_response(raw_response_file: Path | None, existing_raw_response: str = "") -> str:
    if raw_response_file is not None:
        return read_text(raw_response_file).strip()

    if not sys.stdin.isatty():
        stdin_payload = sys.stdin.read().strip()
        if stdin_payload:
            return stdin_payload

    if existing_raw_response.strip():
        return existing_raw_response.strip()

    raise ValueError("raw response must be provided via --raw-response-file, stdin, or existing review JSON")


def extract_json_summary(raw_response: str) -> dict[str, Any] | None:
    pattern = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)
    for match in pattern.finditer(raw_response):
        candidate = match.group(1)
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict) and (
            "remaining_issues" in parsed
            or "questions_for_user" in parsed
            or "next_fix_batch" in parsed
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

    for line in raw_response.splitlines():
        stripped = line.strip()
        heading = normalize_heading(stripped)
        if heading in {
            "итог",
            "findings",
            "remaining issues",
            "regression risks",
            "открытые вопросы",
            "questions for user",
            "next fix batch",
            "что проверено",
        }:
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


def fallback_normalized_review(raw_response: str) -> dict[str, Any]:
    sections = split_sections(raw_response)
    return {
        "overall_summary": "\n".join(sections.get("итог", sections.get("summary", []))).strip(),
        "remaining_issues": lines_to_items(
            sections.get("findings", sections.get("remaining issues", [])),
            "summary",
        ),
        "regression_risks": lines_to_items(sections.get("regression risks", []), "summary"),
        "questions_for_user": lines_to_items(
            sections.get("открытые вопросы", sections.get("questions for user", [])),
            "question",
        ),
        "next_fix_batch": lines_to_items(sections.get("next fix batch", []), "step"),
        "what_was_checked": lines_to_items(sections.get("что проверено", []), "item"),
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


def normalize_review_summary(raw_response: str) -> dict[str, Any]:
    parsed = extract_json_summary(raw_response)
    if parsed is None:
        return fallback_normalized_review(raw_response)

    return {
        "overall_summary": parsed.get("overall_summary", ""),
        "remaining_issues": ensure_list_of_objects(parsed.get("remaining_issues", []), "summary"),
        "regression_risks": ensure_list_of_objects(parsed.get("regression_risks", []), "summary"),
        "questions_for_user": ensure_list_of_objects(parsed.get("questions_for_user", []), "question"),
        "next_fix_batch": ensure_list_of_objects(parsed.get("next_fix_batch", []), "step"),
        "what_was_checked": ensure_list_of_objects(parsed.get("what_was_checked", []), "item"),
    }


def normalize_verification(payload: Any) -> dict[str, list[dict[str, Any]]]:
    if not isinstance(payload, dict):
        return {"inspections": [], "quality_checks": [], "tests": []}
    return {
        "inspections": ensure_list_of_objects(payload.get("inspections", []), "item"),
        "quality_checks": ensure_list_of_objects(payload.get("quality_checks", []), "item"),
        "tests": ensure_list_of_objects(payload.get("tests", []), "item"),
    }


def maybe_finalize(session_state: dict[str, Any], checkpoint: dict[str, Any], normalized_review: dict[str, Any]) -> None:
    if not checkpoint.get("finalize", False):
        return

    override = checkpoint.get("final_result_override", {})
    final_result = session_state.setdefault("final_result", {})
    final_result["status"] = override.get("status", "completed")
    final_result["merge_ready"] = override.get(
        "merge_ready",
        not normalized_review.get("remaining_issues") and not normalized_review.get("questions_for_user"),
    )
    final_result["resolved_findings"] = ensure_list_of_objects(
        override.get("resolved_findings", []),
        "summary",
    )
    final_result["remaining_findings"] = ensure_list_of_objects(
        override.get("remaining_findings", normalized_review.get("remaining_issues", [])),
        "summary",
    )
    final_result["residual_risk"] = ensure_list_of_objects(
        override.get("residual_risk", normalized_review.get("regression_risks", [])),
        "summary",
    )
    final_result["verification_summary"] = normalize_verification(
        override.get("verification_summary", checkpoint.get("verification", {})),
    )


def persist_review_pass(paths: Paths, checkpoint: dict[str, Any], raw_response: str) -> None:
    manifest = read_json(paths.manifest)
    session_state = read_json(paths.session_state)
    review_payload = read_json(paths.review_file)
    existing_subagent = review_payload.get("subagent", {})

    normalized_review = normalize_review_summary(raw_response)
    verification = normalize_verification(checkpoint.get("verification", {}))
    timestamp = now_iso()

    review_payload.update(
        {
            "schema_version": SCHEMA_VERSION,
            "iteration": checkpoint["iteration"],
            "mode": checkpoint.get("mode"),
            "basis": checkpoint.get("basis", {}),
            "in_scope": ensure_list_of_objects(checkpoint.get("in_scope", []), "summary"),
            "fixes_applied": ensure_list_of_objects(checkpoint.get("fixes_applied", []), "summary"),
            "verification": verification,
            "subagent": {
                "reviewer_skill": checkpoint.get("subagent", {}).get(
                    "reviewer_skill",
                    existing_subagent.get("reviewer_skill"),
                ),
                "prompt_summary": checkpoint.get("subagent", {}).get(
                    "prompt_summary",
                    existing_subagent.get("prompt_summary", ""),
                ),
                "raw_response": raw_response,
            },
            "normalized_review": normalized_review,
            "user_answers": ensure_list_of_objects(checkpoint.get("user_answers", []), "answer"),
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

    working_state = session_state.setdefault("working_state", {})
    working_state["current_status"] = [
        f"Iteration {checkpoint['iteration']} persisted.",
        f"Exit decision: {review_payload['exit_decision'].get('decision', 'pending')}.",
    ]
    working_state["latest_verification_summary"] = verification
    working_state["latest_review_pass"] = {
        "iteration": checkpoint["iteration"],
        "mode": checkpoint.get("mode"),
        "decision": review_payload["exit_decision"].get("decision", "pending"),
        "remaining_issues_count": len(normalized_review.get("remaining_issues", [])),
        "questions_for_user_count": len(normalized_review.get("questions_for_user", [])),
    }

    session_state["open_questions"] = normalized_review.get("questions_for_user", [])
    maybe_finalize(session_state, checkpoint, normalized_review)
    write_json(paths.session_state, session_state)

    append_jsonl(
        paths.event_log,
        {
            "timestamp": timestamp,
            "type": "review-pass-persisted",
            "details": {
                "iteration": checkpoint["iteration"],
                "decision": review_payload["exit_decision"].get("decision", "pending"),
                "remaining_issues_count": len(normalized_review.get("remaining_issues", [])),
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
                    "merge_ready": session_state.get("final_result", {}).get("merge_ready", False),
                    "status": session_state.get("final_result", {}).get("status"),
                },
            },
        )


def load_existing_raw_response(review_file: Path) -> str:
    if not review_file.exists():
        return ""
    payload = read_json(review_file)
    return str(payload.get("subagent", {}).get("raw_response", "")).strip()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, help="Path to one review-fix run directory.")
    parser.add_argument("--checkpoint-file", required=True, help="JSON file with iteration checkpoint metadata.")
    parser.add_argument("--raw-response-file", help="Optional file containing the raw subagent response.")
    args = parser.parse_args()

    run_dir = Path(args.run_dir).expanduser().resolve()
    checkpoint = load_checkpoint(Path(args.checkpoint_file).expanduser().resolve())
    paths = load_paths(run_dir=run_dir, iteration=int(checkpoint["iteration"]))
    raw_response = read_raw_response(
        Path(args.raw_response_file).expanduser().resolve() if args.raw_response_file else None,
        existing_raw_response=load_existing_raw_response(paths.review_file),
    )

    persist_review_pass(paths=paths, checkpoint=checkpoint, raw_response=raw_response)
    print(str(paths.review_file))


if __name__ == "__main__":
    main()
