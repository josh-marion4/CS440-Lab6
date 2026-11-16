#!/usr/bin/env python3
"""
PreToolUse hook (Bash): never let the agent contribute to the upstream project.

Lab rule: "Do not contribute to the upstream project." This hook inspects every
shell command Claude Code is about to run and blocks it (exit code 2) when it
would write to github.com/TheAlgorithms/*:

  * `git push` to a remote whose URL points at TheAlgorithms
  * `gh pr create` without `--repo <your-fork>` (on a fork, gh defaults to the
    upstream repo as the PR base, so an explicit fork target is required)
  * any other `gh` write action (pr/issue create, comment, edit, merge, review,
    `gh api` with a write method) that names TheAlgorithms

Read-only commands (git fetch/pull from upstream, `gh issue view`, etc.) and
`gh repo fork TheAlgorithms/Python` are allowed.

On exit code 2, Claude Code cancels the command and shows stderr to Claude.
"""

import json
import os
import re
import shlex
import subprocess
import sys

UPSTREAM_PATTERN = re.compile(r"thealgorithms/", re.IGNORECASE)
GH_WRITE_ACTIONS = {
    "create",
    "comment",
    "edit",
    "merge",
    "review",
    "close",
    "reopen",
    "delete",
    "ready",
    "lock",
    "transfer",
}
SEGMENT_SPLIT = re.compile(r"&&|\|\||;|\||\n")


def block(reason: str) -> None:
    print(f"BLOCKED by block_upstream hook: {reason}", file=sys.stderr)
    print(
        "Lab rule: work only on your fork. Push to `origin` (your fork) and open "
        "PRs with `gh pr create --repo <your-user>/<fork> --base master`, or use "
        "the fork-and-pr skill's open_pr.sh script.",
        file=sys.stderr,
    )
    sys.exit(2)


def tokenize(segment: str) -> list[str]:
    try:
        return shlex.split(segment)
    except ValueError:
        return segment.split()


def remote_url(repo_dir: str, remote: str) -> str:
    """
    Resolve a remote name to its fetch and push URLs; a URL is returned as is.
    Both are checked so a remote that fetches from upstream is never pushed to.
    """
    if "://" in remote or remote.startswith("git@"):
        return remote
    urls = []
    for extra in ([], ["--push"]):
        try:
            result = subprocess.run(
                ["git", "-C", repo_dir, "remote", "get-url", *extra, remote],
                capture_output=True,
                text=True,
                timeout=10,
            )
        except (OSError, subprocess.TimeoutExpired):
            continue
        urls.append(result.stdout.strip())
    return " ".join(urls)


def check_git(tokens: list[str], repo_dir: str) -> None:
    args = tokens[1:]
    # Handle `git -C <dir> ...`
    while len(args) >= 2 and args[0] == "-C":
        repo_dir = os.path.join(repo_dir, args[1])
        args = args[2:]
    if not args or args[0] != "push":
        return
    positional = [arg for arg in args[1:] if not arg.startswith("-")]
    remote = positional[0] if positional else "origin"
    url = remote_url(repo_dir, remote)
    # "upstream" is the conventional name for the original repo, so block it by
    # name too, even if the URL cannot be resolved from the current directory.
    if (
        remote == "upstream"
        or UPSTREAM_PATTERN.search(remote)
        or UPSTREAM_PATTERN.search(url)
    ):
        block(f"`git push` targets the upstream repository ({url or remote}).")


def check_gh(tokens: list[str]) -> None:
    args = tokens[1:]
    if len(args) < 2:
        return
    group, action = args[0], args[1]
    joined = " ".join(args)

    if group == "repo" and action == "fork":
        return  # forking upstream is exactly what we want

    if group == "pr" and action == "create":
        target = None
        for index, arg in enumerate(args):
            if arg in ("--repo", "-R") and index + 1 < len(args):
                target = args[index + 1]
            elif arg.startswith("--repo="):
                target = arg.split("=", 1)[1]
        if target is None:
            block(
                "`gh pr create` has no --repo flag; on a fork gh would target "
                "TheAlgorithms upstream by default."
            )
        if UPSTREAM_PATTERN.search(target + "/"):
            block(f"`gh pr create` targets upstream ({target}).")
        return

    if group in ("pr", "issue", "release", "label") and action in GH_WRITE_ACTIONS:
        has_repo_flag = any(
            arg in ("--repo", "-R") or arg.startswith("--repo=") for arg in args
        )
        # Without --repo, gh may resolve to upstream from inside a fork.
        if UPSTREAM_PATTERN.search(joined) or not has_repo_flag:
            block(
                f"`gh {group} {action}` would write to TheAlgorithms "
                "(or has no --repo pointing at your fork)."
            )

    if group == "api" and UPSTREAM_PATTERN.search(joined):
        write_method = re.search(
            r"(-X|--method)[ =]?(POST|PUT|PATCH|DELETE)", joined, re.IGNORECASE
        )
        has_fields = re.search(r"(^| )(-f|-F|--field|--raw-field|--input)( |=)", joined)
        if write_method or has_fields:
            block("`gh api` write request against TheAlgorithms.")


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)
    command = payload.get("tool_input", {}).get("command", "")
    repo_dir = payload.get("cwd") or os.getcwd()

    for segment in SEGMENT_SPLIT.split(command):
        tokens = tokenize(segment.strip())
        # Skip leading env assignments such as `GIT_TRACE=1 git push`.
        while tokens and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tokens[0]):
            tokens = tokens[1:]
        if not tokens:
            continue
        if tokens[0] == "cd" and len(tokens) > 1:
            repo_dir = os.path.join(repo_dir, os.path.expanduser(tokens[1]))
        elif tokens[0] == "git":
            check_git(tokens, repo_dir)
        elif tokens[0] == "gh":
            check_gh(tokens)
    sys.exit(0)


if __name__ == "__main__":
    main()
