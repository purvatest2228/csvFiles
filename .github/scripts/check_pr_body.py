#!/usr/bin/env python3
"""Fail the build unless the pull request description is actually filled in.

Reads the PR body from the PR_BODY environment variable (never from argv, so
the untrusted description is not interpolated into a shell command) and the
list of changed paths from changed_files.txt.
"""

import os
import pathlib
import re
import sys

# Sections every PR must fill in.
REQUIRED_SECTIONS = ["What changed", "Why", "How to verify"]

# Only demanded when the PR actually touches data files.
CONDITIONAL_SECTIONS = [("Data impact", lambda paths: any(p.endswith(".csv") for p in paths))]

# A section needs at least this many real characters to count as filled.
MIN_SECTION_CHARS = 10

HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
HEADING = re.compile(r"^\s{0,3}#{1,6}\s+(.*?)\s*#*\s*$", re.MULTILINE)


def split_sections(body):
    """Return {heading_text: section_body} for every markdown heading."""
    sections = {}
    matches = list(HEADING.finditer(body))
    for i, match in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        sections[match.group(1).strip().lower()] = body[match.end():end]
    return sections


def content_of(section):
    """Section text with HTML comments and checklist lines stripped out."""
    text = HTML_COMMENT.sub("", section)
    kept = [line for line in text.splitlines() if not line.strip().startswith("- [")]
    return "\n".join(kept).strip()


def changed_paths():
    listing = pathlib.Path("changed_files.txt")
    if not listing.exists():
        return []
    return [line.strip() for line in listing.read_text().splitlines() if line.strip()]


def main():
    body = os.environ.get("PR_BODY") or ""
    errors = []

    if not body.strip():
        errors.append("The PR description is empty. Fill in the template.")
        report(errors)

    sections = split_sections(body)
    paths = changed_paths()

    expected = list(REQUIRED_SECTIONS)
    for name, applies in CONDITIONAL_SECTIONS:
        if applies(paths):
            expected.append(name)

    for name in expected:
        section = sections.get(name.lower())
        if section is None:
            errors.append(f'Missing section: "## {name}"')
        elif len(content_of(section)) < MIN_SECTION_CHARS:
            errors.append(
                f'Section "## {name}" is empty or too short '
                f"(needs at least {MIN_SECTION_CHARS} characters of real content)"
            )

    unchecked = re.findall(r"^\s*[-*]\s*\[ \]\s*(.+)$", body, re.MULTILINE)
    if unchecked:
        errors.append(f"{len(unchecked)} unchecked checklist item(s):")
        errors.extend(f"    - {item.strip()}" for item in unchecked)

    report(errors)


def report(errors):
    if errors:
        print("PR description check failed:\n", file=sys.stderr)
        for error in errors:
            print(f"  {error}", file=sys.stderr)
        print(
            "\nEdit the pull request description to fix these, "
            "then this check re-runs automatically.",
            file=sys.stderr,
        )
        sys.exit(1)
    print("PR description check passed.")
    sys.exit(0)


if __name__ == "__main__":
    main()


