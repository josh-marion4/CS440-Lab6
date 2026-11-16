#!/usr/bin/env bash
# Push the current branch of workspace/Python to your fork and open a PR
# against your fork's master branch. Never targets TheAlgorithms upstream.
# Usage: open_pr.sh "<PR title>" <path/to/pr_body.md>
set -euo pipefail

TITLE="${1:?Usage: open_pr.sh \"<PR title>\" <pr_body.md>}"
BODY_FILE="$(realpath "${2:?Usage: open_pr.sh \"<PR title>\" <pr_body.md>}")"
ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../../../.." && pwd)}"
cd "$ROOT/workspace/Python"

BRANCH="$(git branch --show-current)"
if [ "$BRANCH" = "master" ] || [ -z "$BRANCH" ]; then
  echo "Refusing to open a PR from master. Create a feature branch first." >&2
  exit 1
fi

ORIGIN_URL="$(git remote get-url --push origin)"
FORK_REPO="$(echo "$ORIGIN_URL" | sed -E 's#^(https://github\.com/|git@github\.com:)##; s#\.git$##')"
case "$FORK_REPO" in
  TheAlgorithms/*|thealgorithms/*)
    echo "origin points at upstream ($FORK_REPO). Refusing: lab rule is fork only." >&2
    exit 1 ;;
esac

grep -q '\* \[x\]' "$BODY_FILE" || {
  echo "PR body has no ticked box (* [x]); TheAlgorithms' bot would close it." >&2
  exit 1
}

echo "==> Pushing $BRANCH to $FORK_REPO"
git push -u origin "$BRANCH"

echo "==> Opening PR on $FORK_REPO ($BRANCH -> master)"
gh pr create --repo "$FORK_REPO" --base master --head "$BRANCH" \
  --title "$TITLE" --body-file "$BODY_FILE"
