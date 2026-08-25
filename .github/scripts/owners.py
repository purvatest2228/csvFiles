"""Shared loader and validator for .github/owners.toml."""

import pathlib
import tomllib

CONFIG_PATH = pathlib.Path(".github/owners.toml")
CODEOWNERS_PATH = pathlib.Path(".github/CODEOWNERS")

VALID_PERMISSIONS = ["pull", "triage", "push", "maintain", "admin"]

# Anything below "push" cannot act as a code owner — GitHub drops the entry.
OWNER_MIN_PERMISSION = "push"


def load(path=CONFIG_PATH):
    with path.open("rb") as handle:
        config = tomllib.load(handle)
    config.setdefault("people", [])
    config.setdefault("rules", [])
    validate(config)
    return config


def validate(config):
    """Raise on config that would silently misbehave once pushed."""
    errors = []
    handles = {}

    for person in config["people"]:
        handle = person.get("handle")
        if not handle:
            errors.append("A [[people]] entry is missing 'handle'")
            continue
        if handle in handles:
            errors.append(f"Duplicate person: {handle}")
        permission = person.get("permission")
        if permission not in VALID_PERMISSIONS:
            errors.append(
                f"{handle}: permission {permission!r} is not one of {VALID_PERMISSIONS}"
            )
        handles[handle] = permission

    minimum = VALID_PERMISSIONS.index(OWNER_MIN_PERMISSION)
    for rule in config["rules"]:
        if not rule.get("pattern"):
            errors.append("A [[rules]] entry is missing 'pattern'")
        if not rule.get("owners"):
            errors.append(f"Rule {rule.get('pattern')!r} has no owners")
        for owner in rule.get("owners") or []:
            if owner not in handles:
                errors.append(
                    f"Rule {rule.get('pattern')!r} names {owner}, "
                    "who has no [[people]] entry"
                )
            elif VALID_PERMISSIONS.index(handles[owner]) < minimum:
                errors.append(
                    f"{owner} owns {rule.get('pattern')!r} but only has "
                    f"{handles[owner]!r} access — GitHub ignores code owners "
                    f"below {OWNER_MIN_PERMISSION!r}"
                )

    if not any(person.get("protected") for person in config["people"]):
        errors.append(
            "At least one person must be marked protected = true, "
            "otherwise a bad edit could revoke everyone's access"
        )

    if errors:
        raise SystemExit(
            "owners.toml is invalid:\n" + "\n".join(f"  {e}" for e in errors)
        )
