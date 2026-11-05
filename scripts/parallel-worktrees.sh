#!/usr/bin/env bash
# Create or remove isolated Git worktrees for parallel agent sessions.
#
#   scripts/parallel-worktrees.sh create export-csv due-date
#   scripts/parallel-worktrees.sh list
#   scripts/parallel-worktrees.sh remove export-csv
#
# Worktrees live in ../<repo>.worktrees/<name> by default and use branch
# parallel/<name> based on BASE_REF (default HEAD). Override the parent
# directory with WORKTREE_ROOT.
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "error: not inside a git repository" >&2
  exit 1
}
repo_name="$(basename "$repo_root")"
root="${WORKTREE_ROOT:-$(dirname "$repo_root")/$repo_name.worktrees}"
base="${BASE_REF:-HEAD}"

usage() {
  cat <<'TXT'
Usage:
  scripts/parallel-worktrees.sh create <name> [<name> ...]
  scripts/parallel-worktrees.sh list
  scripts/parallel-worktrees.sh remove <name> [<name> ...]

Environment:
  WORKTREE_ROOT  parent directory (default: ../<repo>.worktrees)
  BASE_REF       base revision (default: HEAD)
TXT
}

valid_name() {
  [[ "$1" =~ ^[A-Za-z0-9._-]+$ ]]
}

create() {
  [[ $# -gt 0 ]] || { usage; exit 2; }
  mkdir -p "$root"
  local name path branch
  for name in "$@"; do
    valid_name "$name" || { echo "error: invalid name '$name'" >&2; exit 2; }
    path="$root/$name"
    branch="parallel/$name"
    if [[ -e "$path" ]]; then
      echo "skip: $path already exists" >&2
      continue
    fi
    if git show-ref --verify --quiet "refs/heads/$branch"; then
      git worktree add "$path" "$branch"
    else
      git worktree add -b "$branch" "$path" "$base"
    fi
    echo "created $path (branch: $branch)"
    echo "  open: code \"$path\""
  done
}

list() {
  git worktree list
}

remove() {
  [[ $# -gt 0 ]] || { usage; exit 2; }
  local name path
  for name in "$@"; do
    valid_name "$name" || { echo "error: invalid name '$name'" >&2; exit 2; }
    path="$root/$name"
    if [[ ! -d "$path" ]]; then
      echo "skip: $path not found" >&2
      continue
    fi
    # Refuse to discard uncommitted work: commit inside the worktree first.
    git worktree remove "$path"
    echo "removed $path (branch parallel/$name kept)"
  done
}

command="${1:-create}"
[[ $# -gt 0 ]] && shift

case "$command" in
  create) create "$@" ;;
  list) list ;;
  remove) remove "$@" ;;
  -h|--help|help) usage ;;
  *)
    echo "error: unknown command '$command'" >&2
    usage
    exit 2
    ;;
esac
