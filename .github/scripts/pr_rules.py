"""Shared loader for .github/pr-rules.toml.

Both the template generator and the description validator read the config
through here, so the two can never drift apart on defaults.

TOML is parsed with the stdlib tomllib (Python 3.11+), so these scripts have
no third-party dependencies and run the same locally and in CI.
"""

import fnmatch
import pathlib
import tomllib

CONFIG_PATH = pathlib.Path(".github/pr-rules.toml")
TEMPLATE_PATH = pathlib.Path(".github/pull_request_template.md")

DEFAULTS = {
    "template_intro": "",
    "min_section_chars": 10,
    "min_description_words": 0,
    "require_images": 0,
    "allowed_image_hosts": [],
    "require_all_checkboxes_ticked": True,
    "sections": [],
    "checklist": [],
    "banned_phrases": [],
}


def load(path=CONFIG_PATH):
    config = dict(DEFAULTS)
    with path.open("rb") as handle:
        config.update(tomllib.load(handle))
    return config


def is_required(section, changed_paths):
    """A section is required outright, or only when matching paths changed."""
    if section.get("required"):
        return True
    globs = section.get("required_when_paths") or []
    return any(matches(path, globs) for path in changed_paths)


def matches(path, globs):
    name = pathlib.PurePosixPath(path).name
    return any(fnmatch.fnmatch(path, g) or fnmatch.fnmatch(name, g) for g in globs)
