#!/usr/bin/env python3
#
# Copyright (C) 2008, 2011, 2017, 2019 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""
Extracts closed issues from a NAV milestone on GitHub to produce a list of
fixed issues for a release changelog entry.
"""
from __future__ import print_function, unicode_literals

import re
import sys
import textwrap
import operator
from argparse import ArgumentParser

from github import Github  # pip install PyGithub
from git import Repo  # pip install GitPython

COMMIT_LOG_ISSUE_PATTERN = re.compile(
    r"\b(merge.*|close|closes|closed|fix|fixes|fixed|resolve|resolves|resolved) "
    r"#(?P<issueno>[0-9]+)",
    re.IGNORECASE,
)


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("version")
    parser.add_argument("--token", "-t", type=str, help="GitHub API token to use")
    parser.add_argument(
        "--no-markdown",
        "-m",
        action="store_true",
        help="Output in legacy format rather than markdown",
    )
    parser.add_argument(
        "--gitlog",
        action="store_true",
        help="Get issue list from git log comments rather than a milestone. Uses git "
        "log output for -r <version>..HEAD",
    )
    args = parser.parse_args()

    if args.token:
        hub = Github(args.token)
    else:
        hub = Github()

    repo = hub.get_user('Uninett').get_repo('nav')
    if args.gitlog:
        issues = get_issues_from_gitlog(repo, args.version)
    else:
        issues = get_issues_from_milestone(repo, args.version)

    formatter = format_issue if args.no_markdown else format_issue_markdown
    for issue in sorted(issues, key=operator.attrgetter('number')):
        print(formatter(issue))


def get_issues_from_milestone(github_repo, version):
    milestones = [
        m for m in github_repo.get_milestones(state='all') if m.title == version
    ]
    if milestones:
        mstone = milestones[0]
    else:
        print("Couldn't find milestone for {}".format(version), file=sys.stderr)
        sys.exit(1)

    return github_repo.get_issues(state='closed', milestone=mstone)


def get_issues_from_gitlog(github_repo, version):
    issue_numbers = set()
    local_repo = Repo('.', search_parent_directories=True)
    for commit in local_repo.iter_commits(rev=f"{version}..HEAD"):
        for match in COMMIT_LOG_ISSUE_PATTERN.finditer(commit.message):
            issue_numbers.add(int(match.group('issueno')))

    queue = list(issue_numbers)
    while queue:
        number = queue.pop()
        issue = github_repo.get_issue(number)
        yield issue
        if issue.pull_request and issue.body:
            for match in COMMIT_LOG_ISSUE_PATTERN.finditer(issue.body):
                linked_issue_no = int(match.group('issueno'))
                if linked_issue_no not in issue_numbers:
                    issue_numbers.add(linked_issue_no)
                    queue.append(linked_issue_no)


def format_issue(issue):
    lead_in = "  * #{:<4} (".format(issue.number)
    indent = " " * len(lead_in)
    line = "{}{})".format(lead_in, issue.title)

    return '\n'.join(textwrap.wrap(line, width=72, subsequent_indent=indent))


def format_issue_markdown(issue):
    line = "- {title} ([#{number:<4}]({url}))"
    return line.format(number=issue.number, title=issue.title, url=issue.html_url)


if __name__ == '__main__':
    main()
