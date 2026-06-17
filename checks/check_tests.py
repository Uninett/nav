#!/usr/bin/env python3
"""Check test code quality: naming conventions and discouraged function usage.

Scans git diff for newly added test code and warns if test methods:
  - lack convention keywords (given, when, then, it_should) in their name
  - use functions that are discouraged in tests

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

Adding new discouraged function rules:
    Append an entry to DISCOURAGED_RULES below. Each entry needs:
      re       - compiled regex matched against each added source line
      message  - short description of the violation
      hint     - what to use instead
      category - logical grouping shown in the report (e.g. "playwright")
"""

import argparse
import re
import subprocess
import sys

# ---------------------------------------------------------------------------
# Shared constants
# ---------------------------------------------------------------------------

TEST_FILE_RE = re.compile(r"^tests/.*\.py$")
DIFF_FILE_RE = re.compile(r"^\+\+\+ b/(.+)$")
HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)")

# ---------------------------------------------------------------------------
# Test naming check
# ---------------------------------------------------------------------------

KEYWORDS = {"given", "when", "then"}
PHRASE_KEYWORDS = {"it_should"}
TEST_DEF_RE = re.compile(r"^\+\s*def (test_\w+)\(")


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


# ---------------------------------------------------------------------------
# Discouraged function rules — extend this list to add new checks
# ---------------------------------------------------------------------------

DISCOURAGED_RULES = [
    {
        "re": re.compile(r"\.wait_for_timeout\s*\("),
        "message": "`wait_for_timeout()` is discouraged",
        "hint": (
            "Hard-coded timeouts make tests slow and flaky. "
            "Use expect(locator).to_be_visible(), locator.wait_for(), "
            "or page.wait_for_selector() instead."
        ),
        "category": "playwright",
    },
    {
        "re": re.compile(r"\.pause\s*\(\s*\)"),
        "message": "`page.pause()` must not be committed",
        "hint": (
            "This is a Playwright debugging helper that halts test execution. "
            "Remove it before merging."
        ),
        "category": "playwright",
    },
    {
        "re": re.compile(r"\btime\.sleep\s*\("),
        "message": "`time.sleep()` is discouraged in tests",
        "hint": (
            "Arbitrary sleeps make tests slow and unreliable. "
            "Use explicit Playwright waits instead."
        ),
        "category": "playwright",
    },
    {
        "re": re.compile(r"\basyncio\.sleep\s*\("),
        "message": "`asyncio.sleep()` is discouraged in tests",
        "hint": (
            "Arbitrary async sleeps make tests slow and unreliable. "
            "Use explicit Playwright waits instead."
        ),
        "category": "playwright",
    },
]


def get_discouraged_usages_from_diff(
    diff: str,
) -> list[tuple[str, int, str, str, str]]:
    """
    Return (filepath, lineno, text, message, hint)
    for each violation in added lines.
    """
    results = []
    current_file = None
    lineno = 0

    for line in diff.splitlines():
        file_match = DIFF_FILE_RE.match(line)
        if file_match:
            path = file_match.group(1)
            current_file = path if TEST_FILE_RE.match(path) else None
            lineno = 0
            continue

        hunk_match = HUNK_RE.match(line)
        if hunk_match:
            lineno = int(hunk_match.group(1)) - 1
            continue

        if current_file is None:
            continue

        if line.startswith("+") and not line.startswith("+++"):
            lineno += 1
            text = line[1:]
            for rule in DISCOURAGED_RULES:
                if rule["re"].search(text):
                    results.append(
                        (
                            current_file,
                            lineno,
                            text.rstrip(),
                            rule["message"],
                            rule["hint"],
                        )
                    )
        elif not line.startswith("-"):
            lineno += 1

    return results


# ---------------------------------------------------------------------------
# Diff acquisition
# ---------------------------------------------------------------------------


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
    """Read files and treat all lines as new (for checking specific files)."""
    lines = []
    for path in files:
        if not TEST_FILE_RE.match(path):
            continue
        lines.append(f"+++ b/{path}")
        lines.append("@@ -0,0 +1 @@")
        try:
            with open(path) as f:
                for line in f:
                    lines.append(f"+{line.rstrip()}")
        except FileNotFoundError:
            print(f"File not found: {path}", file=sys.stderr)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Formatters — naming check
# ---------------------------------------------------------------------------


def format_names_plain(violations, total):
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


def format_names_markdown(violations, total):
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


# ---------------------------------------------------------------------------
# Formatters — discouraged functions
# ---------------------------------------------------------------------------


def format_discouraged_plain(violations):
    lines = ["Discouraged function usage found:\n"]
    for filepath, lineno, text, message, hint in violations:
        lines.append(f"  {filepath}:{lineno}: {message}")
        lines.append(f"    {text.strip()}")
        lines.append(f"    Hint: {hint}\n")
    return "\n".join(lines)


def format_discouraged_markdown(violations):
    lines = [
        "> [!CAUTION]",
        f"> **{len(violations)}** discouraged function usage(s) found"
        f"please fix before merging",
        "",
        "| File | Line | Violation |",
        "|------|------|-----------|",
    ]
    for filepath, lineno, text, message, hint in violations:
        lines.append(f"| `{filepath}` | {lineno} | {message} |")
    lines += [
        "",
        "<details>",
        "<summary>Details</summary>",
        "",
    ]
    for filepath, lineno, text, message, hint in violations:
        lines.append(f"**`{filepath}:{lineno}`** — {message}")
        lines.append(f"```\n{text.strip()}\n```")
        lines.append(f"Hint: {hint}")
        lines.append("")
    lines.append("</details>")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


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

    failed = False

    # Naming check
    new_tests = get_new_test_names_from_diff(diff)
    if new_tests:
        name_violations = [(f, name) for f, name in new_tests if not check_name(name)]
        if name_violations:
            formatter = (
                format_names_markdown
                if args.output_format == "markdown"
                else format_names_plain
            )
            print(formatter(name_violations, len(new_tests)))
            failed = True
        else:
            print(
                f"All {len(new_tests)} new test name(s) follow the naming convention."
            )

    # Discouraged functions check
    discouraged = get_discouraged_usages_from_diff(diff)
    if discouraged:
        formatter = (
            format_discouraged_markdown
            if args.output_format == "markdown"
            else format_discouraged_plain
        )
        print(formatter(discouraged))
        failed = True

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
