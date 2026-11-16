#!/usr/bin/env bash
# Fork TheAlgorithms/Python to your account and clone the fork into workspace/Python.
# Upstream is added as a fetch-only remote (its push URL is DISABLED).
set -euo pipefail

UPSTREAM_REPO="TheAlgorithms/Python"
ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../../../.." && pwd)}"
DEST="$ROOT/workspace/Python"

gh auth status >/dev/null 2>&1 || { echo "gh is not logged in. Run: gh auth login" >&2; exit 1; }
GH_USER="$(gh api user --jq .login)"
FORK_REPO="${FORK_REPO:-$GH_USER/Python}"

case "$FORK_REPO" in
  TheAlgorithms/*|thealgorithms/*) echo "FORK_REPO must be your fork, not upstream." >&2; exit 1 ;;
esac

echo "==> Forking $UPSTREAM_REPO to $GH_USER (skipped if it already exists)"
gh repo fork "$UPSTREAM_REPO" --clone=false --default-branch-only || true

mkdir -p "$ROOT/workspace"
if [ ! -d "$DEST/.git" ]; then
  echo "==> Cloning $FORK_REPO into $DEST"
  git clone "https://github.com/$FORK_REPO.git" "$DEST"
fi

cd "$DEST"
git remote get-url upstream >/dev/null 2>&1 \
  || git remote add upstream "https://github.com/$UPSTREAM_REPO.git"
git remote set-url --push upstream DISABLED

echo "==> Syncing master with upstream"
git fetch upstream master
git checkout master
git merge --ff-only upstream/master
git push origin master

echo
git remote -v
echo "==> Fork ready at $DEST (origin = $FORK_REPO, upstream = fetch-only)"
