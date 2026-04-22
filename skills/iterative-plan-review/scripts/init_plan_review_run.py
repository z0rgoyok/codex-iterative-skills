#!/usr/bin/env python3
"""Create a compact JSON-first artifact workspace for iterative plan review runs."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


DEFAULT_ARTIFACT_ROOT = ".codex-artifacts/iterative-plan-review"
SCHEMA_VERSION = 3


@dataclass(frozen=True)
class RunLayout:
    """Describe the directory layout for one plan review run."""

    run_dir: Path
    reviews_dir: Path
    manifest_path: Path
    session_state_path: Path
    event_log_path: Path


def slugify(value: str) -> str:
    """Convert free-form text into a stable filesystem slug."""

    normalized = value.strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    normalized = normalized.strip("-")
    if normalized:
        return normalized

    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()[:8]
    return f"plan-review-{digest}"


def build_layout(workspace_root: Path, task_slug: str, created_at: datetime) -> RunLayout:
    """Build the paths for a single run directory."""

    run_name = f"{created_at:%Y%m%d-%H%M%S}-{task_slug}"
    run_dir = workspace_root / DEFAULT_ARTIFACT_ROOT / "sessions" / run_name
    reviews_dir = run_dir / "reviews"
    return RunLayout(
        run_dir=run_dir,
        reviews_dir=reviews_dir,
        manifest_path=run_dir / "manifest.json",
        session_state_path=run_dir / "session-state.json",
        event_log_path=run_dir / "event-log.jsonl",
    )


def write_text(path: Path, content: str) -> None:
    """Write UTF-8 text to disk, creating parent directories as needed."""

    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as stream:
        stream.write(content)
        temp_path = Path(stream.name)
    temp_path.replace(path)


def write_json(path: Path, payload: object) -> None:
    """Persist a JSON document with stable formatting."""

    write_text(path, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def append_jsonl(path: Path, payload: object) -> None:
    """Append one JSON object to a JSONL log."""

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(payload, ensure_ascii=False) + "\n")


def build_session_state(
    task: str,
    created_at: datetime,
    workspace_root: Path,
    run_dir: Path,
) -> dict[str, object]:
    """Build the initial mutable session state."""

    timestamp = created_at.isoformat(timespec="seconds")
    return {
        "schema_version": SCHEMA_VERSION,
        "metadata": {
            "created_at": timestamp,
            "workspace_root": str(workspace_root),
            "run_dir": str(run_dir),
            "current_phase": "initialized",
            "last_updated_at": timestamp,
        },
        "input": {
            "task": task.strip(),
            "confirmed_context": [],
            "confirmed_constraints": [],
            "project_context": [],
            "assumptions": [],
        },
        "plan_analysis": {
            "goal": "",
            "expected_outcome": "",
            "dependencies": [],
            "risks": [],
            "verification_points": [],
        },
        "working_state": {
            "current_status": [
                "Run initialized.",
                "Plan v1 not recorded yet.",
                "First review pass not started.",
            ],
            "current_plan_markdown": "",
            "plan_versions": {
                "v1": "",
                "current_label": "uninitialized",
            },
            "latest_review_pass": None,
        },
        "confirmed_business_decisions": [],
        "open_questions": [],
        "final_result": {
            "status": "in_progress",
            "final_plan_markdown": "",
            "final_summary": "",
            "open_questions": [],
        },
    }


def build_iteration_payload(iteration: int) -> dict[str, object]:
    """Build the initial JSON skeleton for one review pass."""

    return {
        "schema_version": SCHEMA_VERSION,
        "iteration": iteration,
        "stage": "initialized",
        "basis": {
            "task_summary": "",
            "confirmed_context": [],
            "confirmed_constraints": [],
            "confirmed_business_decisions": [],
            "open_questions_at_start": [],
        },
        "plan_before": "",
        "subagent": {
            "reviewer_role": "plan-critic",
            "reviewer_model": None,
            "prompt_summary": "",
            "raw_response": "",
        },
        "normalized_review": {
            "overall_summary": "",
            "critical_gaps": [],
            "improvement_suggestions": [],
            "questions_for_user": [],
            "revised_plan_markdown": "",
            "plan_quality_signals": [],
        },
        "user_answers": [],
        "plan_after": "",
        "change_summary": [],
        "exit_decision": {
            "decision": "pending",
            "reason": "",
        },
        "persisted_at": None,
    }


def create_initial_files(
    layout: RunLayout,
    task: str,
    created_at: datetime,
    workspace_root: Path,
) -> None:
    """Create the baseline artifact files for a new run."""

    layout.reviews_dir.mkdir(parents=True, exist_ok=True)

    session_state = build_session_state(
        task=task,
        created_at=created_at,
        workspace_root=workspace_root,
        run_dir=layout.run_dir,
    )
    write_json(layout.session_state_path, session_state)

    for iteration in range(1, 4):
        write_json(layout.reviews_dir / f"iteration-{iteration}.json", build_iteration_payload(iteration))

    append_jsonl(
        layout.event_log_path,
        {
            "timestamp": created_at.isoformat(timespec="seconds"),
            "type": "run-created",
            "details": {
                "task": task.strip(),
                "schema_version": SCHEMA_VERSION,
            },
        },
    )


def write_manifest(
    layout: RunLayout,
    task: str,
    created_at: datetime,
    workspace_root: Path,
) -> None:
    """Persist machine-readable metadata for the run."""

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "created_at": created_at.isoformat(timespec="seconds"),
        "workspace_root": str(workspace_root),
        "run_dir": str(layout.run_dir),
        "task": task.strip(),
        "paths": {
            "session_state": str(layout.session_state_path),
            "event_log": str(layout.event_log_path),
            "reviews_dir": str(layout.reviews_dir),
            "reviews": {
                f"iteration_{iteration}": str(layout.reviews_dir / f"iteration-{iteration}.json")
                for iteration in range(1, 4)
            },
        },
    }
    write_json(layout.manifest_path, manifest)


def main() -> None:
    """Parse arguments and create a new run workspace."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-root", required=True, help="Root directory for project-local artifacts.")
    parser.add_argument("--task", required=True, help="Raw task text from the user.")
    parser.add_argument("--slug", help="Optional filesystem slug for the run directory.")
    args = parser.parse_args()

    workspace_root = Path(args.workspace_root).expanduser().resolve()
    created_at = datetime.now().astimezone()
    task_slug = slugify(args.slug or args.task)
    layout = build_layout(workspace_root=workspace_root, task_slug=task_slug, created_at=created_at)

    create_initial_files(
        layout=layout,
        task=args.task,
        created_at=created_at,
        workspace_root=workspace_root,
    )
    write_manifest(
        layout=layout,
        task=args.task,
        created_at=created_at,
        workspace_root=workspace_root,
    )

    print(layout.run_dir)


if __name__ == "__main__":
    main()
