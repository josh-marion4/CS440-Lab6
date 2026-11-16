---
name: fork-and-pr
description: Fork TheAlgorithms/Python to the user's GitHub account, clone the fork into workspace/Python, and open pull requests against the fork (never upstream). Use when setting up the fork, syncing it, or submitting a PR for a fix.
---

# Fork and PR (fork only, never upstream)

Two scripts handle the GitHub side. Both require the GitHub CLI (`gh`) to be
logged in (`gh auth status`). Run them from the harness root.

## Set up the fork

```bash
bash .claude/skills/fork-and-pr/scripts/setup_fork.sh
```

What it does:
1. Forks `TheAlgorithms/Python` to the logged-in account (no-op if the fork
   already exists). Set `FORK_REPO=<user>/<name>` if your fork has a
   different name.
2. Clones the fork into `workspace/Python` (`origin` = your fork).
3. Adds `upstream` = TheAlgorithms/Python for **fetching only** and sets its
   push URL to `DISABLED`, so `git push upstream` can never succeed.
4. Fast-forwards the fork's `master` to `upstream/master` and pushes it to
   `origin`.

## Open a PR on the fork

After committing on a feature branch in `workspace/Python`:
```bash
bash .claude/skills/fork-and-pr/scripts/open_pr.sh "<PR title>" workspace/pr_body.md
```

What it does:
1. Refuses to run on `master` or if `origin` points at TheAlgorithms.
2. Pushes the current branch to `origin` (your fork).
3. Runs `gh pr create --repo <your fork> --base master --head <branch>`.
   The explicit `--repo` matters: inside a fork, `gh pr create` otherwise
   defaults to the upstream repository.
4. Prints the PR URL.

## Rules

- Never pass `TheAlgorithms/...` to `--repo` for any write action.
- Never add a PR comment, issue comment, or cross-reference on upstream.
  Write `Fixes #<N>` (not `TheAlgorithms/Python#<N>`) in the PR body so the
  fork PR does not post a backlink on the upstream issue.
