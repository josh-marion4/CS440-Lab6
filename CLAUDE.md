# TheAlgorithms contributor agent

This repository is a Claude Code harness that fixes issues in
TheAlgorithms/Python and submits the fix as a pull request **to the user's
fork only**.

- The fork is cloned at `workspace/Python`. All code changes happen there.
- To fix an issue, use the `fix-thealgorithms-issue` skill.
- For forking, syncing, pushing and opening PRs, use the `fork-and-pr` skill.
- Never write to `TheAlgorithms/*` on GitHub (no pushes, PRs, comments or
  issues). The `block_upstream` hook enforces this.
- `workspace/Python/CONTRIBUTING.md` and `workspace/Python/AGENTS.md` are the
  authority on style and PR rules; follow them over anything else.
