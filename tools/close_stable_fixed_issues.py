#!/usr/bin/env python3
#
# Copyright (C) 2026 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with
# NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""
Close GitHub issues that were fixed by PRs merged to a stable branch.

GitHub auto-closes issues only when a "Fixes #N" PR is merged to the default
branch. PRs merged to stable branches (e.g. 5.17.x) leave their linked issues
open. This tool walks recently merged stable-branch PRs, finds the issues they
claim to fix (via formal "Development" links and via "Fixes/Closes/Resolves
#N" keywords in the PR body), and closes the still-open ones — interactively
by default, with a dry-run option.

Requires the `gh` CLI to be installed and authenticated.
"""

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from datetime import date, timedelta

DEFAULT_SINCE_DAYS = 30
DEFAULT_BRANCH_PATTERN = r"^\d+\.\d+\.x$"
DEFAULT_LIMIT = 200
DEFAULT_TEMPLATE = "Closed by {pr_numbers}, merged to {base_branches}."

# Match only verbs that GitHub itself treats as closing keywords. Bare "#N"
# references are intentionally excluded — the PR must purport to close the
# issue.
CLOSING_KEYWORD_PATTERN = re.compile(
    r"\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#(?P<issueno>\d+)\b",
    re.IGNORECASE,
)


def main():
    args = parse_args()
    repo = args.repo or detect_repo()
    cutoff = (date.today() - timedelta(days=args.since)).isoformat()
    branch_re = re.compile(args.branch_pattern)

    prs = fetch_merged_prs(repo, cutoff, args.limit)
    stable_prs = [pr for pr in prs if branch_re.match(pr["baseRefName"] or "")]

    issue_to_prs = collect_issue_links(stable_prs)
    if not issue_to_prs:
        print(f"No stable-branch PRs in the last {args.since} days link to any issue.")
        return 0

    open_issues = filter_open_issues(repo, sorted(issue_to_prs))
    if not open_issues:
        print("No still-open issues found among the linked ones.")
        return 0

    print(
        f"Found {len(open_issues)} open issue(s) linked from stable-branch "
        f"PRs merged since {cutoff}."
    )
    process_issues(repo, open_issues, issue_to_prs, args)
    return 0


def parse_args():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--since",
        type=int,
        default=DEFAULT_SINCE_DAYS,
        help="Look at PRs merged within the last N days (default: %(default)s)",
    )
    parser.add_argument(
        "--branch-pattern",
        default=DEFAULT_BRANCH_PATTERN,
        help="Regex matching stable branch names (default: %(default)s)",
    )
    parser.add_argument(
        "--repo",
        help="OWNER/REPO (default: detected from current gh context)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would happen without modifying any issue",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip per-issue confirmation; close every match",
    )
    parser.add_argument(
        "--comment-template",
        help=(
            "Override the closing-comment template. Available placeholders: "
            "{pr_number}, {pr_numbers}, {base_branch}, {base_branches}, "
            "{pr_url}, {pr_urls}. If unset, a sensible default is used."
        ),
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
        help="Maximum PRs to fetch (default: %(default)s)",
    )
    return parser.parse_args()


def detect_repo():
    out = run_gh(["repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"])
    return out.strip()


def fetch_merged_prs(repo, cutoff, limit):
    fields = "number,title,baseRefName,mergedAt,body,closingIssuesReferences,url"
    out = run_gh(
        [
            "pr",
            "list",
            "--repo",
            repo,
            "--state",
            "merged",
            "--search",
            f"merged:>={cutoff}",
            "--json",
            fields,
            "--limit",
            str(limit),
        ]
    )
    return json.loads(out)


def collect_issue_links(prs):
    """Return {issue_number: [pr_dict, ...]} for the given PRs."""
    issue_to_prs = defaultdict(list)
    for pr in prs:
        issue_numbers = set()
        for ref in pr.get("closingIssuesReferences") or []:
            number = ref.get("number")
            if number:
                issue_numbers.add(number)
        for match in CLOSING_KEYWORD_PATTERN.finditer(pr.get("body") or ""):
            issue_numbers.add(int(match.group("issueno")))
        for number in issue_numbers:
            issue_to_prs[number].append(pr)
    return issue_to_prs


def filter_open_issues(repo, issue_numbers):
    """Return list of {number, title, url} dicts for issues currently open."""
    open_issues = []
    for number in issue_numbers:
        try:
            out = run_gh(
                [
                    "issue",
                    "view",
                    str(number),
                    "--repo",
                    repo,
                    "--json",
                    "number,state,title,url",
                ]
            )
        except subprocess.CalledProcessError as err:
            # Most likely the number refers to a PR rather than an issue
            # (they share GitHub's numbering space), or the issue has been
            # transferred to another repo.
            print(
                f"  (skipping #{number}: {err.stderr.strip() or 'not found'})",
                file=sys.stderr,
            )
            continue
        data = json.loads(out)
        if data.get("state") == "OPEN":
            open_issues.append(data)
    return open_issues


def process_issues(repo, open_issues, issue_to_prs, args):
    yes_to_all = args.yes
    for issue in open_issues:
        prs = issue_to_prs[issue["number"]]
        print()
        print(f"Issue  #{issue['number']}: {issue['title']}")
        print(f"  {issue['url']}")
        print("Fixed by:")
        for pr in prs:
            print(
                f"  #{pr['number']} -> {pr['baseRefName']} "
                f"(merged {pr['mergedAt'][:10]}) {pr['url']}"
            )

        comment = render_comment(prs, args.comment_template)
        print(f"Comment: {comment}")

        if args.dry_run:
            print("  [dry-run] would close.")
            continue

        if yes_to_all:
            choice = "y"
        else:
            choice = prompt("Close this issue? [y/N/a/q] ")

        if choice == "q":
            print("Aborted.")
            return
        if choice == "a":
            yes_to_all = True
            choice = "y"
        if choice != "y":
            print("  skipped.")
            continue

        close_issue(repo, issue["number"], comment)
        print(f"  closed #{issue['number']}.")


def render_comment(prs, template_override):
    template = template_override or DEFAULT_TEMPLATE
    return template.format(
        pr_number=prs[0]["number"],
        base_branch=prs[0]["baseRefName"],
        pr_url=prs[0]["url"],
        pr_numbers=", ".join(f"#{pr['number']}" for pr in prs),
        base_branches=", ".join(f"`{pr['baseRefName']}`" for pr in prs),
        pr_urls=", ".join(pr["url"] for pr in prs),
    )


def close_issue(repo, number, comment):
    run_gh(
        [
            "issue",
            "close",
            str(number),
            "--repo",
            repo,
            "--comment",
            comment,
        ]
    )


def prompt(message):
    try:
        answer = input(message).strip().lower()
    except EOFError:
        return "n"
    return answer or "n"


def run_gh(args):
    result = subprocess.run(["gh", *args], capture_output=True, text=True, check=True)
    return result.stdout


if __name__ == "__main__":
    try:
        sys.exit(main())
    except subprocess.CalledProcessError as err:
        sys.stderr.write(err.stderr or str(err))
        sys.exit(err.returncode or 1)
    except KeyboardInterrupt:
        sys.stderr.write("\nInterrupted.\n")
        sys.exit(130)
