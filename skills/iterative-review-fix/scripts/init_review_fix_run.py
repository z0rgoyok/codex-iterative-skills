#!/usr/bin/env python3
"""Create a compact JSON-first artifact workspace for iterative review-fix runs."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


DEFAULT_ARTIFACT_ROOT = ".codex-artifacts/iterative-review-fix"
ENTRY_MODE_CHOICES = ("auto", "initial-diff-review", "findings-fix-cycle")
SCHEMA_VERSION = 3


@dataclass(frozen=True)
class RunLayout:
    """Describe the directory layout for one review-fix run."""

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
    return f"review-fix-{digest}"


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
    base_branch: str | None,
    entry_mode: str,
) -> dict[str, object]:
    """Build the initial mutable session state."""

    timestamp = created_at.isoformat(timespec="seconds")
    return {
        "schema_version": SCHEMA_VERSION,
        "metadata": {
            "created_at": timestamp,
            "workspace_root": str(workspace_root),
            "run_dir": str(run_dir),
            "entry_mode_requested": entry_mode,
            "base_branch": base_branch,
            "current_phase": "initialized",
            "last_updated_at": timestamp,
        },
        "input": {
            "task": task.strip(),
            "raw_findings": [],
            "scope_and_constraints": [],
            "project_context": [],
            "review_scope": {
                "worktree_status": "unknown",
                "first_review_basis": "unknown",
                "notes": [],
            },
        },
        "analysis": {
            "findings_analysis": [],
            "behavior_deltas": [],
            "fix_strategy": [],
        },
        "working_state": {
            "current_status": [
                "Run initialized.",
                "Review mode not resolved yet.",
            ],
            "implementation_plan": [],
            "changed_surface": [],
            "latest_verification_summary": {
                "inspections": [],
                "quality_checks": [],
                "tests": [],
            },
        },
        "confirmed_business_decisions": [],
        "open_questions": [],
        "final_result": {
            "status": "in_progress",
            "merge_ready": False,
            "resolved_findings": [],
            "remaining_findings": [],
            "residual_risk": [],
            "verification_summary": {
                "inspections": [],
                "quality_checks": [],
                "tests": [],
            },
        },
    }


def build_iteration_payload(iteration: int) -> dict[str, object]:
    """Build the initial JSON skeleton for one review pass."""

    return {
        "schema_version": SCHEMA_VERSION,
        "iteration": iteration,
        "mode": None,
        "basis": {
            "review_surface": None,
            "base_branch": None,
            "notes": [],
        },
        "in_scope": [],
        "fixes_applied": [],
        "verification": {
            "inspections": [],
            "quality_checks": [],
            "tests": [],
        },
        "subagent": {
            "reviewer_skill": None,
            "prompt_summary": "",
            "raw_response": "",
        },
        "normalized_review": {
            "remaining_issues": [],
            "regression_risks": [],
            "questions_for_user": [],
            "next_fix_batch": [],
        },
        "user_answers": [],
        "exit_decision": {
            "decision": "pending",
            "reason": "",
        },
    }


def create_initial_files(
    layout: RunLayout,
    task: str,
    created_at: datetime,
    workspace_root: Path,
    base_branch: str | None,
    entry_mode: str,
) -> None:
    """Create the baseline artifact files for a new run."""

    layout.reviews_dir.mkdir(parents=True, exist_ok=True)

    session_state = build_session_state(
        task=task,
        created_at=created_at,
        workspace_root=workspace_root,
        run_dir=layout.run_dir,
        base_branch=base_branch,
        entry_mode=entry_mode,
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
                "entry_mode_requested": entry_mode,
                "base_branch": base_branch,
            },
        },
    )


def write_manifest(
    layout: RunLayout,
    task: str,
    created_at: datetime,
    workspace_root: Path,
    base_branch: str | None,
    entry_mode: str,
) -> None:
    """Persist machine-readable metadata for the run."""

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "created_at": created_at.isoformat(timespec="seconds"),
        "workspace_root": str(workspace_root),
        "run_dir": str(layout.run_dir),
        "task": task.strip(),
        "entry_mode_requested": entry_mode,
        "base_branch": base_branch,
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
    parser.add_argument("--base-branch", help="Optional base branch for initial diff review mode.")
    parser.add_argument(
        "--entry-mode",
        choices=ENTRY_MODE_CHOICES,
        default="auto",
        help="How the run should enter the workflow.",
    )
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
        base_branch=args.base_branch,
        entry_mode=args.entry_mode,
    )
    write_manifest(
        layout=layout,
        task=args.task,
        created_at=created_at,
        workspace_root=workspace_root,
        base_branch=args.base_branch,
        entry_mode=args.entry_mode,
    )

    print(layout.run_dir)


if __name__ == "__main__":
    main()
