---
name: fix-thealgorithms-issue
description: Fix an open issue in TheAlgorithms/Python by following that repo's CONTRIBUTING.md and AGENTS.md, then open the PR on the user's fork only. Use when asked to fix, solve or work on a TheAlgorithms/Python issue (e.g. "fix issue #15753").
---

# Fix a TheAlgorithms/Python issue

You are contributing a bug fix to TheAlgorithms/Python **through the user's fork**.
The fork is cloned at `workspace/Python`. Never push to, comment on, or open PRs
against `TheAlgorithms/*` — the `block_upstream` hook will stop you if you try.

Follow these steps in order. Do not skip the verification steps, and never
invent command output: run the command and use what it actually printed.

## 1. Make sure the fork is ready

- If `workspace/Python` does not exist, run the **fork-and-pr** skill's setup
  script first: `bash .claude/skills/fork-and-pr/scripts/setup_fork.sh`.
- Sync with upstream (read-only fetch is allowed):
  ```bash
  cd workspace/Python
  git checkout master
  git fetch upstream
  git merge --ff-only upstream/master
  ```

## 2. Read the issue

- Get it with `gh issue view <N> --repo TheAlgorithms/Python` (read-only), or use
  the issue text the user pasted.
- Note: the file path, the reproduction, expected vs. actual output, and any
  linked PRs or maintainer comments.

## 3. Read the rules — they override this skill

Read **all** of `workspace/Python/CONTRIBUTING.md` and `workspace/Python/AGENTS.md`
before writing code, and read `.github/pull_request_template.md`. The key rules
at the time this skill was written:

- One algorithm file per PR; keep the diff minimal and in the existing style.
- Do **not** change code and its doctests in the same PR. A bug-fix PR changes
  code only; a regression doctest goes in a separate, doctest-only PR.
- Type hints on every parameter and return value; descriptive snake_case names.
- Must pass `ruff check`; should be `ruff format`ted; doctests must pass under
  `python3 -m doctest -v <file>`.
- Do not edit `README.md` or `DIRECTORY.md`; do not add dependencies or new
  directories.
- PR description must use the PR template, have the applicable boxes ticked
  (`* [x]`) — the `algorithms-keeper` bot closes PRs with none ticked — and
  include `Fixes #<N>`.

If the current files say something different, follow the files.

## 4. Reproduce the bug first

From `workspace/Python`, run the issue's reproduction, e.g.:
```bash
python3 -c "from maths.number_of_digits import num_digits_fast; print(num_digits_fast(10**16 - 1))"
```
Record the actual output. **If the bug does not reproduce on current master,
stop and tell the user** — it may already be fixed.

## 5. Branch and fix

```bash
git checkout -b fix/issue-<N>
```
- Fix the root cause in the one affected file. Prefer exact/simple logic over
  clever logic (the repo is educational).
- Keep existing function names, signatures, type hints and docstrings unless
  the fix requires a change. Do not modify doctests in this PR.
- The `check_python` hook runs ruff and doctests after every edit. If it
  reports a problem, fix it before continuing.

## 6. Verify

Run each of these and keep the real output for the PR description:
```bash
python3 -c "<reproduction from step 4>"          # now prints the expected value
python3 -m doctest -v <path/to/file.py> | tail -3   # all existing doctests pass
uvx ruff check <path/to/file.py>
uvx ruff format --check <path/to/file.py>
uvx pre-commit run --files <path/to/file.py>       # full CI hook set
git diff --stat master                              # exactly one file changed
```
Also spot-check a few edge cases around the bug (e.g. powers of ten, 0,
negative numbers) with a quick `python3 -c` loop against a trusted reference.

## 7. Commit

```bash
git add <path/to/file.py>
git commit -m "Fix <short description of the bug> (#<N>)"
```

## 8. Write the PR description

Create `workspace/pr_body.md` from `.github/pull_request_template.md`:
- Under **Describe your change**: tick only *Fix a bug or typo in an existing
  algorithm?*
- Under **Checklist**: tick every item that is actually true for this change.
- Add a short explanation of the root cause and the fix, the before/after
  output from steps 4 and 6, and the line `Fixes #<N>`.

## 9. Open the PR on the fork

Use the **fork-and-pr** skill:
```bash
bash .claude/skills/fork-and-pr/scripts/open_pr.sh "Fix <short description> (#<N>)" workspace/pr_body.md
```
Report the PR URL to the user, plus a one-paragraph summary of the fix. Offer
a follow-up doctest-only PR (on the fork) that adds a regression doctest.
