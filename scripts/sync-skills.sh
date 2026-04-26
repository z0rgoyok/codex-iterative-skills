#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_SKILLS_DIR="$ROOT_DIR/skills"
CODEX_SKILLS_DIR="${CODEX_HOME:-$HOME/.codex}/skills"
CLAUDE_SKILLS_DIR="${CLAUDE_HOME:-$HOME/.claude}/skills"

DEFAULT_SKILLS=(
  "iterative-plan-review"
  "iterative-review-fix"
  "final-gate-review"
  "monorepo-skill-structure-creator"
  "agentic-monorepo-operator"
)

print_usage() {
  cat <<'EOF'
Usage:
  scripts/sync-skills.sh <direction> [target] [skill...]

Directions:
  install   Copy skills from repo to target home directory.
  pull      Copy skills from target home directory back to repo.
  diff      Show differences between repo and target home directory.

Targets:
  codex     Use ~/.codex/skills
  claude    Use ~/.claude/skills
  all       Use both targets

Examples:
  scripts/sync-skills.sh install codex
  scripts/sync-skills.sh install all iterative-plan-review iterative-review-fix
  scripts/sync-skills.sh pull claude claude-review-manager
  scripts/sync-skills.sh diff all
EOF
}

log() {
  printf '%s\n' "$*"
}

resolve_target_dir() {
  local target="$1"
  case "$target" in
    codex) printf '%s\n' "$CODEX_SKILLS_DIR" ;;
    claude) printf '%s\n' "$CLAUDE_SKILLS_DIR" ;;
    *)
      log "Unknown target: $target" >&2
      exit 1
      ;;
  esac
}

sync_one_skill() {
  local src_root="$1"
  local dst_root="$2"
  local skill_name="$3"

  mkdir -p "$dst_root"
  mkdir -p "$(dirname "$dst_root/$skill_name")"
  rsync -a --delete \
    --exclude '__pycache__/' \
    --exclude '*.pyc' \
    "$src_root/$skill_name/" \
    "$dst_root/$skill_name/"
}

diff_one_skill() {
  local src_root="$1"
  local dst_root="$2"
  local skill_name="$3"

  if [[ ! -d "$src_root/$skill_name" ]]; then
    log "Missing source skill: $src_root/$skill_name"
    return 1
  fi

  if [[ ! -d "$dst_root/$skill_name" ]]; then
    log "Missing target skill: $dst_root/$skill_name"
    return 1
  fi

  diff -rq \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    "$src_root/$skill_name" \
    "$dst_root/$skill_name"
}

main() {
  if [[ $# -lt 2 ]]; then
    print_usage
    exit 1
  fi

  local direction="$1"
  local target="$2"
  shift 2

  local skills=()
  if [[ $# -gt 0 ]]; then
    skills=("$@")
  else
    skills=("${DEFAULT_SKILLS[@]}")
  fi

  local targets=()
  if [[ "$target" == "all" ]]; then
    targets=("codex" "claude")
  else
    targets=("$target")
  fi

  local current_target target_dir skill_name
  for current_target in "${targets[@]}"; do
    target_dir="$(resolve_target_dir "$current_target")"
    log "== $current_target =="

    for skill_name in "${skills[@]}"; do
      case "$direction" in
        install)
          log "install $skill_name -> $target_dir"
          sync_one_skill "$REPO_SKILLS_DIR" "$target_dir" "$skill_name"
          ;;
        pull)
          log "pull $skill_name <- $target_dir"
          sync_one_skill "$target_dir" "$REPO_SKILLS_DIR" "$skill_name"
          ;;
        diff)
          log "diff $skill_name"
          diff_one_skill "$REPO_SKILLS_DIR" "$target_dir" "$skill_name" || true
          ;;
        *)
          log "Unknown direction: $direction" >&2
          print_usage
          exit 1
          ;;
      esac
    done
  done
}

main "$@"
