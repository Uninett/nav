#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "jinja2",
#     "mistletoe",
# ]
# ///
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
Generate release announcement artifacts from CHANGELOG.md.

Produces three outputs:
1. GitHub release notes (markdown)
2. Hugo blog post (markdown with frontmatter)
3. Email announcement (plain text)
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
import textwrap
import tomllib
import webbrowser
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import jinja2
import mistletoe
from mistletoe.block_token import Heading
from mistletoe.markdown_renderer import MarkdownRenderer


# -----------------------------------------------------------------------------
# Data structures
# -----------------------------------------------------------------------------


@dataclass
class ChangelogEntry:
    """Represents a single version entry from the changelog."""

    version: str
    date: str
    sections: dict[str, str] = field(default_factory=dict)


# -----------------------------------------------------------------------------
# Main entry point
# -----------------------------------------------------------------------------


def main() -> int:
    """Main entry point."""
    parser = create_argument_parser()
    args = parser.parse_args()

    config = load_config(args.config)
    if config is None:
        return 1

    entry = parse_changelog(args.changelog, args.version)
    if entry is None:
        return 1

    # If no output flags specified, generate all
    generate_all = not (args.github or args.blog or args.email)
    do_github = args.github or generate_all
    do_blog = args.blog or generate_all
    do_email = args.email or generate_all

    print(f"Generating announcements for NAV {entry.version} ({entry.date})")

    github_md = generate_github_release(entry) if do_github else None

    # Blog is always generated if email is needed (email derives from blog)
    blog_md = (
        generate_blog_post(entry, config, args.security)
        if do_blog or do_email
        else None
    )

    email_subject, email_body = (
        generate_email(entry, config, blog_md, args.security)
        if do_email
        else (None, None)
    )

    # Only include blog in output if explicitly requested
    # (not just for email derivation)
    blog_output = blog_md if do_blog else None

    if args.dry_run:
        print_outputs(github_md, blog_output, email_subject, email_body)
    else:
        write_outputs(
            args.output_dir, entry, github_md, blog_output, email_subject, email_body
        )

    if args.enact:
        enact_announcements(
            entry, config, github_md, blog_output, email_subject, email_body
        )

    return 0


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "version",
        nargs="?",
        help="Version to extract (default: latest in changelog)",
    )
    parser.add_argument(
        "--security",
        action="store_true",
        help="Mark as security release (affects email subject)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("."),
        help="Write files to DIR (default: current directory)",
    )
    parser.add_argument(
        "--changelog",
        type=Path,
        default=Path("CHANGELOG.md"),
        help="Path to CHANGELOG.md (default: ./CHANGELOG.md)",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).parent / "announcement.toml",
        help="Path to config file",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print to stdout only, don't write files",
    )
    parser.add_argument(
        "--github",
        action="store_true",
        help="Generate GitHub release notes",
    )
    parser.add_argument(
        "--blog",
        action="store_true",
        help="Generate Hugo blog post",
    )
    parser.add_argument(
        "--email",
        action="store_true",
        help="Generate email announcement",
    )
    parser.add_argument(
        "--enact",
        action="store_true",
        help="Enact announcements (copy blog, create GitHub draft, open email)",
    )
    return parser


# -----------------------------------------------------------------------------
# Configuration and input parsing
# -----------------------------------------------------------------------------


def load_config(config_path: Path) -> dict | None:
    """Load configuration from TOML file."""
    if not config_path.exists():
        print(f"Error: Config file not found: {config_path}", file=sys.stderr)
        return None
    return tomllib.loads(config_path.read_text())


def parse_changelog(
    changelog_path: Path, target_version: str | None = None
) -> ChangelogEntry | None:
    """Parse CHANGELOG.md and extract the specified version entry.

    Args:
        changelog_path: Path to CHANGELOG.md
        target_version: Version to extract, or None for the latest

    Returns:
        ChangelogEntry with parsed data, or None on error
    """
    if not changelog_path.exists():
        print(f"Error: Changelog not found: {changelog_path}", file=sys.stderr)
        return None

    try:
        return extract_changelog_entry(changelog_path, target_version)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return None


def extract_changelog_entry(
    changelog_path: Path, target_version: str | None
) -> ChangelogEntry:
    """Extract a version entry from the changelog.

    Raises:
        ValueError: If version not found or changelog has no entries
    """
    content = changelog_path.read_text()

    with MarkdownRenderer() as renderer:
        doc = mistletoe.Document(content)
        entries = find_version_entries(doc, renderer)

        if not entries:
            raise ValueError("No version entries found in changelog")

        target_idx = find_target_version_index(entries, target_version)
        return build_changelog_entry(doc, renderer, entries, target_idx)


def find_version_entries(doc, renderer) -> list[tuple[int, str, str]]:
    """Find all version headings in the document.

    Returns:
        List of (index, version, date) tuples
    """
    version_pattern = re.compile(r"\[(\d+\.\d+\.\d+)\]\s*-\s*(\d{4}-\d{2}-\d{2})")
    entries: list[tuple[int, str, str]] = []

    for i, child in enumerate(doc.children):
        if isinstance(child, Heading) and child.level == 2:
            heading_text = renderer.render(child).strip().lstrip("#").strip()
            match = version_pattern.search(heading_text)
            if match:
                entries.append((i, match.group(1), match.group(2)))

    return entries


def find_target_version_index(
    entries: list[tuple[int, str, str]], target_version: str | None
) -> int:
    """Find the index of the target version in entries.

    Raises:
        ValueError: If specified version not found
    """
    if target_version is None:
        return 0  # Latest version

    for idx, (_, version, _) in enumerate(entries):
        if version == target_version:
            return idx

    raise ValueError(f"Version {target_version} not found in changelog")


def build_changelog_entry(
    doc, renderer, entries: list[tuple[int, str, str]], target_idx: int
) -> ChangelogEntry:
    """Build a ChangelogEntry from the document at the given index."""
    start_idx, version, date = entries[target_idx]

    if target_idx + 1 < len(entries):
        end_idx = entries[target_idx + 1][0]
    else:
        end_idx = len(doc.children)

    entry = ChangelogEntry(version=version, date=date)
    current_section: str | None = None
    section_content: list[str] = []

    for child in doc.children[start_idx + 1 : end_idx]:
        if isinstance(child, Heading) and child.level == 3:
            if current_section and section_content:
                content = "\n".join(section_content).strip()
                entry.sections[current_section] = normalize_list_items(content)
            current_section = renderer.render(child).strip().lstrip("#").strip()
            section_content = []
        elif current_section is not None:
            rendered = renderer.render(child).strip()
            if rendered:
                section_content.append(rendered)

    if current_section and section_content:
        content = "\n".join(section_content).strip()
        entry.sections[current_section] = normalize_list_items(content)

    return entry


def normalize_list_items(text: str) -> str:
    """Join continuation lines in markdown list items.

    GitHub-flavored markdown preserves newlines, so multi-line list items
    need to be collapsed to single lines for proper display.
    """
    lines = text.split("\n")
    result: list[str] = []
    current_item: list[str] = []

    for line in lines:
        if line.startswith("- "):
            # Start of new list item - flush previous
            if current_item:
                result.append("- " + " ".join(current_item))
            current_item = [line[2:]]  # Remove "- " prefix
        elif current_item and line.startswith("  "):
            # Continuation of list item (indented)
            current_item.append(line.strip())
        else:
            # Not a list item
            if current_item:
                result.append("- " + " ".join(current_item))
                current_item = []
            result.append(line)

    # Flush any remaining item
    if current_item:
        result.append("- " + " ".join(current_item))

    return "\n".join(result)


# -----------------------------------------------------------------------------
# Output generators
# -----------------------------------------------------------------------------


def create_jinja_env() -> jinja2.Environment:
    """Create Jinja environment with custom filters."""
    template_dir = Path(__file__).parent / "templates"
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(template_dir),
        keep_trailing_newline=True,
        trim_blocks=True,
    )
    env.filters["ordinal"] = ordinal
    env.filters["join_and"] = lambda items: ", ".join(items[:-1]) + " and " + items[-1]
    return env


def ordinal(n: int) -> str:
    """Return ordinal string for a number (first, second, 3rd, etc.).

    Uses words for 1-2 and numeric ordinals thereafter.
    """
    if n == 1:
        return "first"
    elif n == 2:
        return "second"
    elif 11 <= n % 100 <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def generate_github_release(entry: ChangelogEntry) -> str:
    """Generate GitHub release notes from changelog entry."""
    lines: list[str] = []

    for section, content in entry.sections.items():
        lines.append(f"## {section}\n")
        lines.append(content)
        lines.append("")

    return "\n".join(lines).strip()


def generate_blog_post(
    entry: ChangelogEntry,
    config: dict,
    is_security: bool = False,
) -> str:
    """Generate Hugo blog post from changelog entry using Jinja template."""
    major, minor, patch = parse_version(entry.version)

    env = create_jinja_env()
    template = env.get_template("announcement.md.j2")

    now = datetime.now(timezone.utc).astimezone()
    date_str = now.strftime("%Y-%m-%dT%H:%M:%S%z")
    date_str = date_str[:-2] + ":" + date_str[-2:]

    return template.render(
        version=entry.version,
        date=date_str,
        major=major,
        minor=minor,
        patch=patch,
        series=f"{major}.{minor}",
        is_security=is_security,
        sections=entry.sections,
        urls=config["urls"],
        debian_releases=config["debian"]["releases"],
    )


def generate_email(
    entry: ChangelogEntry,
    config: dict,
    blog_md: str,
    is_security: bool = False,
) -> tuple[str, str]:
    """Generate email announcement by converting blog markdown to plain text.

    The blog post is treated as the canonical version. Email is derived by:
    - Stripping YAML frontmatter
    - Converting markdown links to numbered references
    - Converting issue links [#1234](url) to just #1234
    - Stripping other markdown formatting

    Returns:
        Tuple of (subject, body)
    """
    subject = generate_email_subject(config, entry.version, is_security)

    # Strip YAML frontmatter
    body = strip_frontmatter(blog_md)

    # Convert markdown to plain text with numbered references
    body, urls = markdown_to_plaintext(body)

    # Add links section if there are any URLs
    if urls:
        body = body.rstrip() + "\n\n\n## Links\n\n"
        for i, url in enumerate(urls, 1):
            body += f"[{i}] {url}\n"

    return subject, wrap_email_body(body)


def generate_email_subject(config: dict, version: str, is_security: bool) -> str:
    """Generate email subject line."""
    template_key = "security_subject_template" if is_security else "subject_template"
    return config["email"][template_key].format(version=version)


def wrap_email_body(body: str) -> str:
    """Word wrap email body at 72 characters."""
    wrapped_lines: list[str] = []
    for line in body.split("\n"):
        if line.startswith("##") or line.startswith("[") or len(line) <= 72:
            wrapped_lines.append(line)
        elif line.startswith("- "):
            # Wrap list items with hanging indent
            wrapped = textwrap.wrap(
                line, width=72, initial_indent="", subsequent_indent="  "
            )
            wrapped_lines.extend(wrapped)
        else:
            wrapped_lines.extend(textwrap.wrap(line, width=72))
    return "\n".join(wrapped_lines)


def strip_frontmatter(text: str) -> str:
    """Strip YAML frontmatter from markdown text.

    Frontmatter is delimited by --- at the start and end.
    """
    if not text.startswith("---"):
        return text

    # Find the closing ---
    end_idx = text.find("---", 3)
    if end_idx == -1:
        return text

    # Skip past the closing --- and any following newlines
    return text[end_idx + 3 :].lstrip("\n")


def markdown_to_plaintext(text: str) -> tuple[str, list[str]]:
    """Convert markdown to plain text with numbered link references.

    Returns:
        Tuple of (converted_text, list_of_urls)
    """
    urls: list[str] = []

    # Convert issue references: ([#1234](url)) -> (#1234)
    text = re.sub(r"\(\[#(\d+)\]\([^)]+\)\)", r"(#\1)", text)

    # Also handle bare issue links: [#1234](url) -> #1234
    text = re.sub(r"\[#(\d+)\]\([^)]+\)", r"#\1", text)

    def collect_link(match: re.Match) -> str:
        """Collect URL and return text with reference number."""
        link_text = match.group(1)
        url = match.group(2)
        urls.append(url)
        return f"{link_text} [{len(urls)}]"

    # Convert other links: [text](url) -> text [N]
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", collect_link, text)

    # Convert backticks to nothing
    text = re.sub(r"`([^`]+)`", r"\1", text)

    return text, urls


# -----------------------------------------------------------------------------
# Output writers
# -----------------------------------------------------------------------------


def print_outputs(
    github_md: str | None,
    blog_md: str | None,
    email_subject: str | None,
    email_body: str | None,
) -> None:
    """Print selected outputs to stdout (dry-run mode)."""
    if github_md is not None:
        print("\n" + "=" * 60)
        print("GITHUB RELEASE NOTES")
        print("=" * 60)
        print(github_md)

    if blog_md is not None:
        print("\n" + "=" * 60)
        print("BLOG POST")
        print("=" * 60)
        print(blog_md)

    if email_body is not None:
        print("\n" + "=" * 60)
        print(f"EMAIL (Subject: {email_subject})")
        print("=" * 60)
        print(email_body)


def write_outputs(
    output_dir: Path,
    entry: ChangelogEntry,
    github_md: str | None,
    blog_md: str | None,
    email_subject: str | None,
    email_body: str | None,
) -> None:
    """Write selected outputs to files."""
    output_dir.mkdir(parents=True, exist_ok=True)

    if github_md is not None:
        github_file = output_dir / f"nav-{entry.version}-github.md"
        github_file.write_text(github_md)
        print(f"  Wrote: {github_file}")

    if blog_md is not None:
        blog_version = entry.version.replace(".", "-")
        blog_file = output_dir / f"nav-{blog_version}-released.md"
        blog_file.write_text(blog_md)
        print(f"  Wrote: {blog_file}")

    if email_body is not None:
        email_file = output_dir / f"nav-{entry.version}-email.txt"
        email_file.write_text(email_body)
        print(f"  Wrote: {email_file}")
        print(f"  Email subject: {email_subject}")


# -----------------------------------------------------------------------------
# Enactment functions
# -----------------------------------------------------------------------------


def enact_announcements(
    entry: ChangelogEntry,
    config: dict,
    github_md: str | None,
    blog_md: str | None,
    email_subject: str | None,
    email_body: str | None,
) -> None:
    """Enact the announcements (copy blog, create GitHub draft, open email)."""
    print("\nEnacting announcements...")

    if blog_md is not None:
        enact_blog(entry, config, blog_md)

    if github_md is not None:
        enact_github(entry, github_md)

    if email_body is not None:
        enact_email(config, email_subject, email_body)


def enact_blog(entry: ChangelogEntry, config: dict, blog_md: str) -> None:
    """Copy blog post to landing page repository and stage it."""
    blog_config = config.get("blog", {})
    landing_page_path = blog_config.get("landing_page_blog_path")

    if not landing_page_path:
        print("  Blog: Skipped (no landing_page_blog_path configured)")
        return

    dest_dir = Path(landing_page_path).expanduser()
    if not dest_dir.exists():
        print(f"  Blog: Error - directory not found: {dest_dir}")
        return

    blog_version = entry.version.replace(".", "-")
    dest_file = dest_dir / f"nav-{blog_version}-released.md"

    dest_file.write_text(blog_md)
    print(f"  Blog: Wrote {dest_file}")

    # Add to git and show status
    repo_dir = dest_dir.parent.parent  # Go up from content/blog to repo root
    subprocess.run(["git", "add", str(dest_file)], cwd=repo_dir)
    print("  Blog: Added to git staging area")
    print()
    result = subprocess.run(
        ["git", "status", "--short"], cwd=repo_dir, capture_output=True, text=True
    )
    print(f"  Git status in {repo_dir}:")
    for line in result.stdout.strip().split("\n"):
        print(f"    {line}")


def enact_github(entry: ChangelogEntry, github_md: str) -> None:
    """Create GitHub draft release and open in browser."""
    tag = entry.version
    title = f"NAV {entry.version}"

    # Write release notes to temp file for gh CLI
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False
    ) as notes_file:
        notes_file.write(github_md)
        notes_path = notes_file.name

    try:
        # Create draft release using gh CLI
        result = subprocess.run(
            [
                "gh",
                "release",
                "create",
                tag,
                "--draft",
                "--title",
                title,
                "--notes-file",
                notes_path,
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print(f"  GitHub: Error creating release: {result.stderr}")
            return

        # Extract URL from output (gh outputs the release URL)
        release_url = result.stdout.strip()
        if release_url:
            print(f"  GitHub: Created draft release at {release_url}")
            # Open edit page in browser
            edit_url = release_url.replace("/releases/tag/", "/releases/edit/")
            webbrowser.open(edit_url)
            print(f"  GitHub: Opened {edit_url} in browser")
        else:
            print("  GitHub: Draft release created (no URL returned)")

    finally:
        Path(notes_path).unlink()


def enact_email(config: dict, subject: str, body: str) -> None:
    """Open email client with announcement ready to send."""
    email_config = config.get("email", {})
    compose_command = email_config.get("compose_command")
    to_addresses = email_config.get("to", [])

    if not compose_command:
        print("  Email: Skipped (no compose_command configured)")
        return

    # Write subject and body to temp files
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False
    ) as subject_file:
        subject_file.write(subject)
        subject_path = subject_file.name

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False
    ) as body_file:
        body_file.write(body)
        body_path = body_file.name

    try:
        # Substitute placeholders in command
        to_str = ", ".join(to_addresses) if to_addresses else ""
        cmd = compose_command.format(
            subject=subject,
            subject_file=subject_path,
            body_file=body_path,
            to=to_str,
        )

        print("  Email: Running compose command...")
        subprocess.run(cmd, shell=True)
        print("  Email: Compose command executed")

    finally:
        Path(subject_path).unlink()
        Path(body_path).unlink()


# -----------------------------------------------------------------------------
# Utility functions
# -----------------------------------------------------------------------------


def parse_version(version: str) -> tuple[int, int, int]:
    """Parse version string into (major, minor, patch) tuple."""
    parts = version.split(".")
    return int(parts[0]), int(parts[1]), int(parts[2])


# -----------------------------------------------------------------------------
# Script entry point
# -----------------------------------------------------------------------------


if __name__ == "__main__":
    sys.exit(main())
