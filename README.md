# TheAlgorithms Contributor Agent (CS440 Lab 6)

A Claude Code harness that fixes an open issue in
[TheAlgorithms/Python](https://github.com/TheAlgorithms/Python), following that
repo's `CONTRIBUTING.md` (and its `AGENTS.md`), and submits the fix as a pull
request **to my fork only**, never to the upstream project.

It uses two Claude Code features: **skills** and **hooks**.

Target issue: [#15753: `num_digits_fast()` returns incorrect digit count for
large integers](https://github.com/TheAlgorithms/Python/issues/15753)
(`maths/number_of_digits.py`; `num_digits_fast(10**16 - 1)` returns 17 instead of 16).

## Project structure

```
thealgorithms-agent/
├── CLAUDE.md                          # Always-loaded rules for the agent
├── .claude/
│   ├── settings.json                  # Registers the hooks
│   ├── hooks/
│   │   ├── block_upstream.py          # PreToolUse: blocks any write to TheAlgorithms/*
│   │   └── check_python.py            # PostToolUse: ruff + doctests on every edit
│   └── skills/
│       ├── fix-thealgorithms-issue/
│       │   └── SKILL.md               # Step-by-step workflow from CONTRIBUTING.md
│       └── fork-and-pr/
│           ├── SKILL.md               # How to fork, sync and open PRs on the fork
│           └── scripts/
│               ├── setup_fork.sh      # Fork + clone into workspace/Python
│               └── open_pr.sh         # Push branch + open PR on the fork
└── workspace/                         # (git-ignored) the cloned fork lives here
```

## Code features

### Skills
| Skill | Purpose |
|---|---|
| `fix-thealgorithms-issue` | Turns `CONTRIBUTING.md` / `AGENTS.md` into an ordered workflow: read the issue, read the rules, reproduce the bug, branch, make a minimal one-file fix, verify (doctests, `ruff check`, `ruff format`, `pre-commit`), commit, fill in the PR template with real output and `Fixes #N`. |
| `fork-and-pr` | Handles the fork process and PR submission with two scripts. `setup_fork.sh` forks and clones, and makes `upstream` fetch-only (push URL `DISABLED`). `open_pr.sh` refuses to run from `master`, when `origin` is upstream, or when no PR-template box is ticked, then opens the PR with an explicit `--repo <fork>`. |

### Hooks
| Hook | Event | What it does |
|---|---|---|
| `block_upstream.py` | `PreToolUse` on `Bash` | Blocks `git push` to any remote named `upstream` or pointing at TheAlgorithms, `gh pr create` without `--repo <fork>` (inside a fork, gh defaults to the upstream repo), and `gh` comment/create/merge/API writes on TheAlgorithms. Read-only commands such as `gh issue view` and `git fetch upstream` are allowed. |
| `check_python.py` | `PostToolUse` on `Edit\|Write\|MultiEdit` | After each edit to a `.py` file in `workspace/`, runs `ruff check`, `ruff format --check` and `python3 -m doctest`. On failure it exits with code 2, so Claude sees the errors and must fix them. |

## Prerequisites

- [Claude Code](https://docs.claude.com/en/docs/claude-code), logged in with a Claude plan (`/status` to check)
- `git`, `python3` (3.12+)
- GitHub CLI `gh`, logged in: `gh auth login`
- [`uv`](https://docs.astral.sh/uv/) (provides `uvx ruff` and `uvx pre-commit`), or `pip install ruff pre-commit`

## How to run

```bash
git clone <this repo> thealgorithms-agent
cd thealgorithms-agent

# 1. Fork TheAlgorithms/Python and clone the fork into workspace/Python
bash .claude/skills/fork-and-pr/scripts/setup_fork.sh

# 2. Start the agent
claude
```

Then give it the task:

```
Fix TheAlgorithms/Python issue #15753 and open the PR on my fork.
```

The agent loads the `fix-thealgorithms-issue` skill, reproduces the bug, fixes
`maths/number_of_digits.py`, and the hooks check every edit and command. It
then opens the PR on `<your-user>/Python` and prints the link.

## Testing the hooks by hand

```bash
export CLAUDE_PROJECT_DIR=$PWD
# Blocked (exit 2):
echo '{"tool_input":{"command":"gh pr create --repo TheAlgorithms/Python --title x"}}' \
  | python3 .claude/hooks/block_upstream.py; echo "exit=$?"
# Allowed (exit 0):
echo '{"tool_input":{"command":"gh issue view 15753 --repo TheAlgorithms/Python"}}' \
  | python3 .claude/hooks/block_upstream.py; echo "exit=$?"
```

## Notes on CONTRIBUTING.md / AGENTS.md compliance

- One algorithm file per PR; code and doctests are not changed in the same PR
  (AGENTS.md), so a regression doctest is offered as a separate follow-up PR.
- The PR body uses `.github/pull_request_template.md` with the applicable boxes
  ticked; the `algorithms-keeper` bot closes PRs with no ticked box.
- `Fixes #N` is written in the PR body as CONTRIBUTING.md asks. On a fork PR it
  refers to the fork, so nothing is posted to the upstream issue.
