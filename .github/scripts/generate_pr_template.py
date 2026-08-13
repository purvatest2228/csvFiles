#!/usr/bin/env python3
"""Render .github/pull_request_template.md from .github/pr-rules.toml.

Run after editing the config:

    python3 .github/scripts/generate_pr_template.py

Pass --check to verify the committed template is up to date without writing
(used by the "Template in sync" CI job).
"""

import sys

import pr_rules

BANNER = (
    "<!-- Generated from .github/pr-rules.toml. Do not edit by hand;\n"
    "     edit the config and run .github/scripts/generate_pr_template.py -->\n"
)


def render(config):
    parts = [BANNER]

    for section in config["sections"]:
        parts.append(f"## {section['title']}\n")
        if section.get("hint"):
            parts.append(f"<!-- {section['hint']} -->\n")
        if section.get("must_match"):
            for rule in section["must_match"]:
                parts.append(f"<!-- Required: {rule['message']} -->\n")
        if section.get("body"):
            parts.append(section["body"].rstrip() + "\n")
        parts.append("")

    if config["checklist"]:
        parts.append("## Checklist\n")
        for item in config["checklist"]:
            parts.append(f"- [ ] {item}")
        parts.append("")

    return "\n".join(parts).rstrip() + "\n"


def main():
    config = pr_rules.load()
    rendered = render(config)
    path = pr_rules.TEMPLATE_PATH

    if "--check" in sys.argv:
        current = path.read_text() if path.exists() else ""
        if current != rendered:
            print(
                f"{path} is out of date with {pr_rules.CONFIG_PATH}.\n"
                "Run: python3 .github/scripts/generate_pr_template.py",
                file=sys.stderr,
            )
            sys.exit(1)
        print(f"{path} is in sync.")
        return

    path.write_text(rendered)
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
