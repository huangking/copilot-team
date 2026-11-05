#!/usr/bin/env bash
# Install the Copilot parallel-agent kit into an existing Git repository.
#
#   ./install.sh /path/to/repo
#   ./install.sh /path/to/repo --dry-run
#   ./install.sh /path/to/repo --force
#
# Safe by default: existing files are never overwritten. AGENTS.md and
# docs/parallel-tasks.md are always preserved; an existing AGENTS.md gets a
# sibling AGENTS.copilot.md instead.
set -euo pipefail

KIT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET=""
DRY_RUN=0
FORCE=0

usage() {
  cat <<'TXT'
Usage: install.sh <target-repo> [--dry-run] [--force]

  <target-repo>   existing Git repository to install into
  --dry-run       print what would happen, write nothing
  --force         overwrite installed agents/skills/script (never AGENTS.md
                  or docs/parallel-tasks.md)

Installs:
  .github/agents/*.agent.md     PM / Dev / Test / DevOps / Review Lead / Reviewer
  .agents/skills/*              role playbooks (Copilot CLI + VS Code)
  scripts/parallel-worktrees.sh helper for isolated worktrees
  docs/parallel-tasks.md        parallel task list (only if missing)
  AGENTS.md                     contract (or AGENTS.copilot.md if one exists)
  .vscode/settings.json         merge missing Copilot chat settings
TXT
}

die() { echo "error: $*" >&2; exit 1; }

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    --force) FORCE=1 ;;
    -h|--help) usage; exit 0 ;;
    -*) echo "error: unknown option '$arg'" >&2; usage; exit 2 ;;
    *)
      [[ -z "$TARGET" ]] || die "only one target repository is supported"
      TARGET="$arg"
      ;;
  esac
done

[[ -n "$TARGET" ]] || { usage; exit 2; }
[[ -d "$TARGET" ]] || die "target is not a directory: $TARGET"
TARGET="$(cd "$TARGET" && pwd)"
git -C "$TARGET" rev-parse --show-toplevel >/dev/null 2>&1 \
  || die "target is not a Git repository: $TARGET"

if [ "$TARGET" = "$KIT" ]; then die "refusing to install into the kit itself"; fi

say() { echo "$*"; }
run() {
  if ((DRY_RUN)); then
    echo "[dry-run] $*"
  else
    "$@"
  fi
}

copy_file() {
  local src="$1" dst="$2" label="$3"
  if [[ -e "$dst" ]] && ((!FORCE)); then
    say "skip  $label (already exists)"
    return 0
  fi
  run mkdir -p "$(dirname "$dst")"
  run cp "$src" "$dst"
  say "write $label"
}

copy_tree() {
  local src="$1" dst="$2" label="$3"
  if [[ -e "$dst" ]] && ((!FORCE)); then
    say "skip  $label (already exists)"
    return 0
  fi
  run mkdir -p "$(dirname "$dst")"
  run cp -R "$src" "$dst"
  say "write $label"
}

merge_settings() {
  local file="$TARGET/.vscode/settings.json"
  if ((DRY_RUN)); then
    say "[dry-run] merge .vscode/settings.json"
    return 0
  fi
  mkdir -p "$TARGET/.vscode"
  python3 - "$file" <<'PY'
import json
import os
import sys

path = sys.argv[1]
data = {}
if os.path.exists(path):
    with open(path, encoding="utf-8") as handle:
        try:
            data = json.load(handle)
        except json.JSONDecodeError as exc:
            print(f"error: {path} is not valid JSON: {exc}", file=sys.stderr)
            raise SystemExit(3)
    if not isinstance(data, dict):
        print(f"error: {path} must contain a JSON object", file=sys.stderr)
        raise SystemExit(3)

wanted = {
    "chat.agent.enabled": True,
    "chat.useAgentsMdFile": True,
    "chat.agentFilesLocations": {".github/agents": True},
    "chat.instructionsFilesLocations": {".github/instructions": True},
    "chat.promptFilesLocations": {".github/prompts": True},
    "github.copilot.chat.cli.customAgents.enabled": True,
}

for key, value in wanted.items():
    if key not in data:
        data[key] = value
    elif isinstance(value, dict) and isinstance(data[key], dict):
        for subkey, subvalue in value.items():
            data[key].setdefault(subkey, subvalue)

with open(path, "w", encoding="utf-8") as handle:
    json.dump(data, handle, indent=2)
    handle.write("\n")
print(f"write .vscode/settings.json")
PY
}

say "target: $TARGET"
if ((DRY_RUN)); then say "mode: dry-run"; fi

# Agents
for src in "$KIT"/agents/*.agent.md; do
  copy_file "$src" "$TARGET/.github/agents/$(basename "$src")" ".github/agents/$(basename "$src")"
done

# Skills
for src in "$KIT"/skills/*/; do
  name="$(basename "$src")"
  copy_tree "$src" "$TARGET/.agents/skills/$name" ".agents/skills/$name"
done

# Worktree helper
copy_file "$KIT/scripts/parallel-worktrees.sh" "$TARGET/scripts/parallel-worktrees.sh" "scripts/parallel-worktrees.sh"
if ((!DRY_RUN)) && [[ -f "$TARGET/scripts/parallel-worktrees.sh" ]]; then
  chmod +x "$TARGET/scripts/parallel-worktrees.sh"
fi

# Task list (never overwrite: it is the user's work queue)
if [[ -f "$TARGET/docs/parallel-tasks.md" ]]; then
  say "skip  docs/parallel-tasks.md (already exists)"
else
  run mkdir -p "$TARGET/docs"
  run cp "$KIT/templates/parallel-tasks.template.md" "$TARGET/docs/parallel-tasks.md"
  say "write docs/parallel-tasks.md"
fi

# Contract: never overwrite an existing AGENTS.md
if [[ -f "$TARGET/AGENTS.md" ]]; then
  copy_file "$KIT/templates/AGENTS.template.md" "$TARGET/AGENTS.copilot.md" "AGENTS.copilot.md"
else
  copy_file "$KIT/templates/AGENTS.template.md" "$TARGET/AGENTS.md" "AGENTS.md"
fi

# VS Code settings merge
if ! merge_settings; then
  echo "warn: .vscode/settings.json was left untouched (fix the JSON and re-run)" >&2
fi

say ""
say "done. next:"
if [[ -f "$TARGET/AGENTS.copilot.md" ]]; then
  say "  1. merge AGENTS.copilot.md into AGENTS.md (roles, commands, write scopes)"
else
  say "  1. edit AGENTS.md: role table, real commands, write scopes"
fi
say "  2. fill $TARGET/docs/parallel-tasks.md with real, path-disjoint tasks"
say "  3. run: cd $TARGET && copilot"
say "     then: /fleet 按 docs/parallel-tasks.md 执行可并行的 todo 任务"
