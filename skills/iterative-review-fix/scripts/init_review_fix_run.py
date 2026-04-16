#!/usr/bin/env python3
"""Create a persistent artifact workspace for iterative review-fix runs."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


DEFAULT_ARTIFACT_ROOT = ".codex-artifacts/iterative-review-fix"


@dataclass(frozen=True)
class RunLayout:
    """Describe the directory layout for one review-fix run."""

    run_dir: Path
    input_dir: Path
    analysis_dir: Path
    working_dir: Path
    history_dir: Path
    reviews_dir: Path
    final_dir: Path


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
    return RunLayout(
        run_dir=run_dir,
        input_dir=run_dir / "00-input",
        analysis_dir=run_dir / "01-analysis",
        working_dir=run_dir / "02-working",
        history_dir=run_dir / "03-history",
        reviews_dir=run_dir / "04-reviews",
        final_dir=run_dir / "05-final",
    )


def write_text(path: Path, content: str) -> None:
    """Write UTF-8 text to disk, creating parent directories as needed."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def create_initial_files(layout: RunLayout, task: str, created_at: datetime) -> None:
    """Create the baseline artifact files for a new run."""

    for directory in (
        layout.input_dir,
        layout.analysis_dir,
        layout.working_dir,
        layout.history_dir,
        layout.reviews_dir,
        layout.final_dir,
    ):
        directory.mkdir(parents=True, exist_ok=True)

    write_text(layout.input_dir / "task.md", f"# Task\n\n{task.strip()}\n")
    write_text(layout.input_dir / "review-findings.md", "# Review Findings\n\n- Paste raw review findings here.\n")
    write_text(layout.input_dir / "scope-and-constraints.md", "# Scope and Constraints\n\n- Record confirmed boundaries here.\n")
    write_text(layout.input_dir / "project-context.md", "# Project Context\n\n- Record relevant local rules and code context here.\n")

    write_text(layout.analysis_dir / "findings-analysis.md", "# Findings Analysis\n\n- Record which findings are confirmed and why.\n")
    write_text(layout.analysis_dir / "fix-strategy.md", "# Fix Strategy\n\n- Describe the intended fix sequence and risk order.\n")
    write_text(layout.analysis_dir / "questions-for-user.md", "# Questions for User\n\n- Record business questions that block confident fixes.\n")

    write_text(layout.working_dir / "implementation-plan.md", "# Implementation Plan\n\n- Track the current fix batch here.\n")
    write_text(layout.working_dir / "current-status.md", "# Current Status\n\n- Keep the latest working status here.\n")
    write_text(layout.working_dir / "changed-surface.md", "# Changed Surface\n\n- Record files, modules, and behaviors touched by fixes.\n")

    write_text(
        layout.history_dir / "conversation-log.md",
        (
            "# Conversation Log\n\n"
            f"- {created_at.isoformat(timespec='seconds')}: Run created.\n"
            "- Append user questions, agent questions, and user answers chronologically.\n"
        ),
    )
    write_text(layout.history_dir / "decision-log.md", "# Decision Log\n\n- Record only decisions confirmed by the user.\n")
    write_text(layout.history_dir / "change-log.md", "# Change Log\n\n- Record why each fix iteration changed the solution.\n")

    for iteration in range(1, 4):
        iteration_dir = layout.reviews_dir / f"iteration-{iteration}"
        iteration_dir.mkdir(parents=True, exist_ok=True)
        write_text(
            iteration_dir / "README.md",
            (
                f"# Iteration {iteration}\n\n"
                "- Store the fix scope, code changes, verification, subagent review, "
                "questions for the user, answers received, and exit decision for this pass.\n"
            ),
        )
        write_text(iteration_dir / "findings-in-scope.md", f"# Findings In Scope {iteration}\n\n")
        write_text(iteration_dir / "fixes-applied.md", f"# Fixes Applied {iteration}\n\n")
        write_text(iteration_dir / "verification.md", f"# Verification {iteration}\n\n")
        write_text(iteration_dir / "subagent-review-prompt.md", f"# Subagent Review Prompt {iteration}\n\n")
        write_text(iteration_dir / "subagent-review.md", f"# Subagent Review {iteration}\n\n")
        write_text(iteration_dir / "questions-for-user.md", f"# Questions for User {iteration}\n\n")
        write_text(iteration_dir / "user-answers.md", f"# User Answers {iteration}\n\n")
        write_text(iteration_dir / "exit-decision.md", f"# Exit Decision {iteration}\n\n")

    write_text(layout.final_dir / "resolved-findings.md", "# Resolved Findings\n\n- List findings closed by the final solution.\n")
    write_text(layout.final_dir / "remaining-findings.md", "# Remaining Findings\n\n- List unresolved or deferred findings.\n")
    write_text(layout.final_dir / "final-summary.md", "# Final Summary\n\n- Explain what changed and why it is enough.\n")
    write_text(layout.final_dir / "verification-summary.md", "# Verification Summary\n\n- Summarize quality checks and remaining risk.\n")


def write_manifest(layout: RunLayout, task: str, created_at: datetime, workspace_root: Path) -> None:
    """Persist machine-readable metadata for the run."""

    manifest = {
        "created_at": created_at.isoformat(timespec="seconds"),
        "workspace_root": str(workspace_root),
        "run_dir": str(layout.run_dir),
        "task": task.strip(),
        "paths": {
            "input": str(layout.input_dir),
            "analysis": str(layout.analysis_dir),
            "working": str(layout.working_dir),
            "history": str(layout.history_dir),
            "reviews": str(layout.reviews_dir),
            "final": str(layout.final_dir),
        },
    }
    write_text(layout.run_dir / "manifest.json", json.dumps(manifest, indent=2, ensure_ascii=True) + "\n")


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

    create_initial_files(layout=layout, task=args.task, created_at=created_at)
    write_manifest(layout=layout, task=args.task, created_at=created_at, workspace_root=workspace_root)

    print(layout.run_dir)


if __name__ == "__main__":
    main()
