#!/usr/bin/env python3
"""Render .github/CODEOWNERS from .github/owners.toml.

Run after editing the config:

    python3 .github/scripts/generate_codeowners.py

Pass --check to verify the committed CODEOWNERS is up to date without
writing (used by the "CODEOWNERS in sync" CI job).
"""

import sys

import owners

BANNER = """\
# Generated from .github/owners.toml. Do not edit by hand;
# edit the config and run .github/scripts/generate_codeowners.py
#
# The last matching pattern wins.
"""

COLUMN = 24


def render(config):
    lines = [BANNER]
    for rule in config["rules"]:
        if rule.get("comment"):
            lines.append(f"# {rule['comment']}")
        handles = " ".join(f"@{owner}" for owner in rule["owners"])
        lines.append(f"{rule['pattern']:<{COLUMN}}{handles}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main():
    config = owners.load()
    rendered = render(config)
    path = owners.CODEOWNERS_PATH

    if "--check" in sys.argv:
        current = path.read_text() if path.exists() else ""
        if current != rendered:
            print(
                f"{path} is out of date with {owners.CONFIG_PATH}.\n"
                "Run: python3 .github/scripts/generate_codeowners.py",
                file=sys.stderr,
            )
            sys.exit(1)
        print(f"{path} is in sync.")
        return

    path.write_text(rendered)
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
