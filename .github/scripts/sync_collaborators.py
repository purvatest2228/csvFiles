#!/usr/bin/env python3
"""Apply .github/owners.toml to the repository's actual collaborator list.

    python3 .github/scripts/sync_collaborators.py           # dry run, prints a plan
    python3 .github/scripts/sync_collaborators.py --apply   # performs the changes

Environment:
    GITHUB_TOKEN       token with admin rights on the repo (a fine-grained PAT
                       with the "Administration: read and write" permission)
    GITHUB_REPOSITORY  "owner/name"

People listed in owners.toml are added or have their permission corrected.
Anyone holding *direct* access who is not listed is removed, unless they are
the repository owner or marked protected. Organization- or team-granted
access is left alone; this only touches direct collaborators.
"""

import json
import os
import sys
import urllib.error
import urllib.request

import owners

API = "https://api.github.com"

# GitHub reports role_name; owners.toml uses the API's permission vocabulary.
ROLE_TO_PERMISSION = {
    "read": "pull",
    "triage": "triage",
    "write": "push",
    "maintain": "maintain",
    "admin": "admin",
}


def request(method, path, token, payload=None):
    req = urllib.request.Request(
        f"{API}{path}",
        method=method,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
            "User-Agent": "owners-sync",
        },
    )
    with urllib.request.urlopen(req) as response:
        body = response.read()
        return json.loads(body) if body else None


def current_collaborators(repo, token):
    """Direct collaborators only, as {handle_lower: permission}."""
    result = {}
    page = 1
    while True:
        batch = request(
            "GET",
            f"/repos/{repo}/collaborators?affiliation=direct&per_page=100&page={page}",
            token,
        )
        if not batch:
            break
        for user in batch:
            role = user.get("role_name", "")
            result[user["login"].lower()] = ROLE_TO_PERMISSION.get(role, role)
        page += 1
    return result


def pending_invitations(repo, token):
    invites = request("GET", f"/repos/{repo}/invitations?per_page=100", token) or []
    return {
        invite["invitee"]["login"].lower(): invite["id"]
        for invite in invites
        if invite.get("invitee")
    }


def build_plan(config, repo, existing, invited):
    repo_owner = repo.split("/")[0].lower()
    wanted = {p["handle"].lower(): p for p in config["people"]}
    plan = []

    for handle, person in wanted.items():
        if handle == repo_owner:
            continue  # the owner's access is inherent, not a collaborator grant
        want = person["permission"]
        have = existing.get(handle)
        if have is None and handle in invited:
            plan.append(("pending", handle, want, "invitation already sent"))
        elif have is None:
            plan.append(("invite", handle, want, "not a collaborator yet"))
        elif have != want:
            plan.append(("update", handle, want, f"currently {have}"))
        else:
            plan.append(("ok", handle, want, "already correct"))

    protected = {p["handle"].lower() for p in config["people"] if p.get("protected")}
    for handle in sorted(existing):
        if handle in wanted or handle == repo_owner or handle in protected:
            continue
        plan.append(("remove", handle, existing[handle], "not listed in owners.toml"))

    for handle, invite_id in sorted(invited.items()):
        if handle not in wanted:
            plan.append(("revoke-invite", handle, str(invite_id), "not listed"))

    return plan


def apply_plan(plan, repo, token):
    for action, handle, detail, _ in plan:
        if action in ("invite", "update"):
            request(
                "PUT",
                f"/repos/{repo}/collaborators/{handle}",
                token,
                {"permission": detail},
            )
            print(f"  {action}: {handle} -> {detail}")
        elif action == "remove":
            request("DELETE", f"/repos/{repo}/collaborators/{handle}", token)
            print(f"  removed: {handle}")
        elif action == "revoke-invite":
            request("DELETE", f"/repos/{repo}/invitations/{detail}", token)
            print(f"  revoked invitation: {handle}")


def main():
    apply = "--apply" in sys.argv
    repo = os.environ.get("GITHUB_REPOSITORY")
    token = os.environ.get("GITHUB_TOKEN")

    if not repo or not token:
        raise SystemExit("GITHUB_REPOSITORY and GITHUB_TOKEN must both be set")

    config = owners.load()

    try:
        existing = current_collaborators(repo, token)
        invited = pending_invitations(repo, token)
    except urllib.error.HTTPError as error:
        raise SystemExit(
            f"GitHub API returned {error.code} listing collaborators. "
            "The token needs admin (Administration: read and write) on this repo."
        )

    plan = build_plan(config, repo, existing, invited)

    print(f"Plan for {repo}:\n")
    for action, handle, detail, reason in plan:
        print(f"  {action:<14} {handle:<24} {detail:<10} ({reason})")

    changes = [step for step in plan if step[0] not in ("ok", "pending")]
    if not changes:
        print("\nNothing to do.")
        return

    if not apply:
        print(f"\n{len(changes)} change(s) pending. Re-run with --apply to perform them.")
        return

    print("\nApplying:")
    apply_plan(changes, repo, token)
    print("\nDone.")


if __name__ == "__main__":
    main()
