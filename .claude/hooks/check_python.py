#!/usr/bin/env python3
"""
PostToolUse hook (Edit/Write/MultiEdit): enforce CONTRIBUTING.md checks on
every Python file the agent changes inside workspace/.

TheAlgorithms/Python's CONTRIBUTING.md requires that submissions pass
`ruff check`, recommends `ruff format`, and requires doctests that pass under
`python3 -m doctest`. This hook runs all three on the edited file right after
each edit. On failure it exits with code 2, which makes Claude Code show the
report to Claude so it fixes the problem before moving on.
"""

import json
import os
import shutil
import subprocess
import sys


def ruff_command() -> list[str] | None:
    if shutil.which("ruff"):
        return ["ruff"]
    if shutil.which("uvx"):
        return ["uvx", "ruff"]
    return None


def find_repo_root(path: str) -> str:
    directory = os.path.dirname(path)
    while directory != os.path.dirname(directory):
        if os.path.isdir(os.path.join(directory, ".git")):
            return directory
        directory = os.path.dirname(directory)
    return os.path.dirname(path)


def run(command: list[str], cwd: str) -> tuple[bool, str]:
    env = dict(os.environ, PYTHONPATH=cwd)
    try:
        result = subprocess.run(
            command, cwd=cwd, capture_output=True, text=True, timeout=150, env=env
        )
    except subprocess.TimeoutExpired:
        return False, f"timed out: {' '.join(command)}"
    return result.returncode == 0, (result.stdout + result.stderr).strip()


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    file_path = payload.get("tool_input", {}).get("file_path", "")
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", payload.get("cwd", ""))
    workspace = os.path.join(project_dir, "workspace")
    file_path = os.path.abspath(file_path) if file_path else ""

    # Only check Python files inside the cloned fork, not the harness itself.
    if not file_path.endswith(".py") or not file_path.startswith(workspace + os.sep):
        sys.exit(0)

    repo_root = find_repo_root(file_path)
    failures: list[str] = []

    ruff = ruff_command()
    if ruff is None:
        failures.append("ruff not found: install it (pip install ruff) or install uv.")
    else:
        ok, output = run([*ruff, "check", file_path], repo_root)
        if not ok:
            failures.append(f"`ruff check` failed (required by CONTRIBUTING.md):\n{output}")
        ok, output = run([*ruff, "format", "--check", "--diff", file_path], repo_root)
        if not ok:
            failures.append(
                f"`ruff format --check` failed; run `ruff format {file_path}`:\n{output}"
            )

    ok, output = run([sys.executable, "-m", "doctest", file_path], repo_root)
    if not ok:
        failures.append(f"`python3 -m doctest` failed:\n{output[-4000:]}")

    if failures:
        print(f"check_python hook found problems in {file_path}:\n", file=sys.stderr)
        print("\n\n".join(failures), file=sys.stderr)
        sys.exit(2)

    print(f"check_python: ruff check, ruff format and doctests passed for {file_path}")
    sys.exit(0)


if __name__ == "__main__":
    main()
