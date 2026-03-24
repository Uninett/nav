#!/bin/bash
# PostToolUse hook: check test naming conventions after Edit/Write on test files.
# Gives Claude feedback (exit 2) so it can fix the names before committing.

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# Only check test files under tests/
if [[ ! "$FILE_PATH" =~ ^.*/tests/.*\.py$ ]] && [[ ! "$FILE_PATH" =~ ^tests/.*\.py$ ]]; then
  exit 0
fi

# Find the project root (where checks/ lives)
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null)}"
CHECKER="$PROJECT_DIR/checks/check_test_names.py"

if [[ ! -f "$CHECKER" ]]; then
  exit 0
fi

# Make file_path relative to project root for the checker
REL_PATH="${FILE_PATH#"$PROJECT_DIR"/}"

output=$(python3 "$CHECKER" --files "$REL_PATH" 2>&1)
exit_code=$?

if [[ $exit_code -ne 0 ]]; then
  echo "$output" >&2
  exit 2
fi
