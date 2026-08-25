#!/usr/bin/env python3
"""Fail the build unless the pull request description is actually filled in.

Rules come from .github/pr-rules.toml — the same file the template is
generated from, so what the template asks for and what CI enforces stay
identical.

Reads the PR body from the PR_BODY environment variable (never from argv, so
the untrusted description is not interpolated into a shell command) and the
list of changed paths from changed_files.txt.
"""

import os
import pathlib
import re
import sys

import pr_rules

HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
HEADING = re.compile(r"^\s{0,3}#{1,6}\s+(.*?)\s*#*\s*$", re.MULTILINE)
UNCHECKED = re.compile(r"^\s*[-*]\s*\[ \]\s*(.+)$", re.MULTILINE)
FENCED_CODE = re.compile(r"```.*?```", re.DOTALL)
MARKDOWN_IMAGE = re.compile(r"!\[[^\]]*\]\(\s*<?([^)\s>]+)")
HTML_IMAGE = re.compile(r"""<img[^>]+src=["']?([^"'>\s]+)""", re.IGNORECASE)
BARE_URL = re.compile(r"https?://\S+")
WORD = re.compile(r"[A-Za-z0-9][A-Za-z0-9'’/._-]*")


def split_sections(body):
    """Return {heading_text_lowercased: section_body} for every heading."""
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


def check_sections(config, sections, paths, errors):
    minimum = config["min_section_chars"]

    for section in config["sections"]:
        title = section["title"]
        found = sections.get(title.lower())

        if not pr_rules.is_required(section, paths):
            continue
        if found is None:
            errors.append(f'Missing section: "## {title}"')
            continue

        content = content_of(found)
        if len(content) < minimum:
            errors.append(
                f'Section "## {title}" is empty or too short '
                f"(needs at least {minimum} characters of real content)"
            )
            continue

        for rule in section.get("must_match") or []:
            if not re.search(rule["pattern"], content, re.MULTILINE):
                errors.append(f'Section "## {title}": {rule["message"]}')


def prose_words(body):
    """Words a reviewer actually reads: no markup, code, URLs or checkboxes."""
    text = HTML_COMMENT.sub("", body)
    text = FENCED_CODE.sub("", text)
    text = MARKDOWN_IMAGE.sub("", text)
    text = HTML_IMAGE.sub("", text)
    text = BARE_URL.sub("", text)
    kept = [
        line
        for line in text.splitlines()
        if not line.strip().startswith("- [") and not HEADING.match(line)
    ]
    return WORD.findall("\n".join(kept))


def find_images(body):
    text = HTML_COMMENT.sub("", body)
    return MARKDOWN_IMAGE.findall(text) + HTML_IMAGE.findall(text)


def check_length(config, body, errors):
    minimum = config["min_description_words"]
    if not minimum:
        return
    count = len(prose_words(body))
    if count < minimum:
        errors.append(
            f"Description is {count} words; at least {minimum} are required "
            "(headings, code blocks, image markup, URLs and checklist lines "
            "do not count)"
        )


def check_images(config, body, errors):
    required = config["require_images"]
    if not required:
        return

    images = find_images(body)
    if len(images) < required:
        errors.append(
            f"Description contains {len(images)} image(s); {required} required. "
            "Paste a screenshot of the successful build into the "
            '"Build evidence" section.'
        )
        return

    hosts = config["allowed_image_hosts"]
    if not hosts:
        return
    for url in images:
        if not any(host in url for host in hosts):
            errors.append(
                f"Image {url} is not hosted on GitHub. Paste the screenshot "
                "into the description so GitHub stores it, rather than "
                "linking an external image that can disappear."
            )


def check_banned(config, body, errors):
    stripped = HTML_COMMENT.sub("", body)
    for rule in config["banned_phrases"]:
        if re.search(rule["pattern"], stripped, re.MULTILINE):
            errors.append(rule["message"])


def check_checkboxes(config, body, errors):
    if not config["require_all_checkboxes_ticked"]:
        return
    unchecked = UNCHECKED.findall(HTML_COMMENT.sub("", body))
    if unchecked:
        errors.append(f"{len(unchecked)} unchecked checklist item(s):")
        errors.extend(f"    - {item.strip()}" for item in unchecked)


def main():
    config = pr_rules.load()
    body = os.environ.get("PR_BODY") or ""
    errors = []

    if not body.strip():
        report(["The PR description is empty. Fill in the template."])

    check_sections(config, split_sections(body), changed_paths(), errors)
    check_length(config, body, errors)
    check_images(config, body, errors)
    check_banned(config, body, errors)
    check_checkboxes(config, body, errors)
    report(errors)


def report(errors):
    if errors:
        print("PR description check failed:\n", file=sys.stderr)
        for error in errors:
            print(f"  {error}", file=sys.stderr)
        print(
            "\nRules live in .github/pr-rules.toml. Edit the pull request "
            "description to fix these, then this check re-runs automatically.",
            file=sys.stderr,
        )
        sys.exit(1)
    print("PR description check passed.")
    sys.exit(0)


if __name__ == "__main__":
    main()
