#!/usr/bin/env python3
"""Check that new test method names follow the given/when/then/it_should convention.

Scans git diff for newly added test methods and warns if they lack
convention keywords (given, when, then, should).

Usage:
    # Check staged changes (pre-commit)
    python checks/check_test_names.py

    # Check branch diff against master
    python checks/check_test_names.py --base master

    # Check specific files
    python checks/check_test_names.py --files tests/test_foo.py tests/test_bar.py

    # Read unified diff from stdin
    git diff HEAD --unified=0 -- tests/test_foo.py | \
        python checks/check_test_names.py --stdin
"""

import argparse
import re
import subprocess
import sys

KEYWORDS = {"given", "when", "then"}
PHRASE_KEYWORDS = {"it_should"}
TEST_DEF_RE = re.compile(r"^\+\s*def (test_\w+)\(")
TEST_FILE_RE = re.compile(r"^tests/.*\.py$")

# Matches: +++ b/tests/some/path.py
DIFF_FILE_RE = re.compile(r"^\+\+\+ b/(.+)$")


def get_new_test_names_from_diff(diff: str) -> list[tuple[str, str]]:
    """Extract (filename, test_name) pairs from added lines in a diff."""
    results = []
    current_file = None

    for line in diff.splitlines():
        file_match = DIFF_FILE_RE.match(line)
        if file_match:
            path = file_match.group(1)
            current_file = path if TEST_FILE_RE.match(path) else None
            continue

        if current_file is None:
            continue

        test_match = TEST_DEF_RE.match(line)
        if test_match:
            results.append((current_file, test_match.group(1)))

    return results


def check_name(name: str) -> bool:
    """Return True if the test name contains at least one convention keyword."""
    lower = name.lower()
    parts = set(lower.split("_"))
    if parts & KEYWORDS:
        return True
    return any(phrase in lower for phrase in PHRASE_KEYWORDS)


def get_diff_staged() -> str:
    result = subprocess.run(
        ["git", "diff", "--cached", "--unified=0"],
        capture_output=True,
        text=True,
    )
    return result.stdout


def get_diff_base(base: str) -> str:
    merge_base = subprocess.run(
        ["git", "merge-base", base, "HEAD"],
        capture_output=True,
        text=True,
    )
    base_ref = merge_base.stdout.strip()
    if not base_ref:
        print(f"Could not find merge base with {base}", file=sys.stderr)
        sys.exit(2)

    result = subprocess.run(
        ["git", "diff", base_ref, "HEAD", "--unified=0"],
        capture_output=True,
        text=True,
    )
    return result.stdout


def get_diff_files(files: list[str]) -> str:
    """Read files and pretend all test defs are new (for checking specific files)."""
    lines = []
    for path in files:
        if not TEST_FILE_RE.match(path):
            continue
        lines.append(f"+++ b/{path}")
        try:
            with open(path) as f:
                for line in f:
                    stripped = line.rstrip()
                    if re.match(r"\s*def test_\w+\(", stripped):
                        lines.append(f"+{stripped}")
        except FileNotFoundError:
            print(f"File not found: {path}", file=sys.stderr)
    return "\n".join(lines)


def format_plain(violations, total):
    lines = [
        f"{len(violations)} of {total} new test name(s) missing"
        " convention keywords (given/when/then/it_should):\n"
    ]
    for filepath, name in violations:
        lines.append(f"  {filepath}: {name}")
    lines.append(
        "\nConsider rephrasing with given/when/then/it_should, e.g.:"
        "\n  test_when_no_incidents_then_returns_empty_list"
        "\n  test_it_should_create_incident_with_set_description"
        "\n  test_given_expired_token_when_refreshing_then_raises_error"
    )
    return "\n".join(lines)


def format_markdown(violations, total):
    lines = [
        "> [!WARNING]",
        f"> **{len(violations)}** of **{total}** new test names are missing"
        " convention keywords (`given`/`when`/`then`/`it_should`)",
        "",
        "| File | Test name |",
        "|------|-----------|",
    ]
    for filepath, name in violations:
        lines.append(f"| `{filepath}` | `{name}` |")
    lines.extend(
        [
            "",
            "<details>",
            "<summary>Why am I seeing this?</summary>",
            "",
            "Test names should follow a loose **given/when/then** pattern with"
            " keywords like `given`, `when`, `then`, or `it_should`."
            " This is a suggestion, not a blocker."
            " The check runs on new test methods added in this PR.",
            "",
            "Examples:",
            "- `test_when_no_incidents_then_returns_empty_list`",
            "- `test_it_should_create_incident_with_set_description`",
            "- `test_given_expired_token_when_refreshing_then_raises_error`",
            "</details>",
        ]
    )
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stdin",
        action="store_true",
        help="Read unified diff from stdin instead of running git.",
    )
    parser.add_argument(
        "--base",
        help="Base branch to diff against (e.g. master)."
        " If omitted, checks staged changes.",
    )
    parser.add_argument(
        "--files",
        nargs="+",
        help="Check all test names in specific files (ignores git diff).",
    )
    parser.add_argument(
        "--format",
        choices=["plain", "markdown"],
        default="plain",
        dest="output_format",
        help="Output format (default: plain).",
    )
    args = parser.parse_args()

    if args.stdin:
        diff = sys.stdin.read()
    elif args.files:
        diff = get_diff_files(args.files)
    elif args.base:
        diff = get_diff_base(args.base)
    else:
        diff = get_diff_staged()

    new_tests = get_new_test_names_from_diff(diff)

    if not new_tests:
        return

    violations = [(f, name) for f, name in new_tests if not check_name(name)]

    if not violations:
        print(f"All {len(new_tests)} new test name(s) follow the naming convention.")
        return

    formatter = format_markdown if args.output_format == "markdown" else format_plain
    print(formatter(violations, len(new_tests)))
    sys.exit(1)


if __name__ == "__main__":
    main()
