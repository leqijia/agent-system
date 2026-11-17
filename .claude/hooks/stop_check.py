#!/usr/bin/env python3
"""Stop hook: when Python files have changed, lint and tests must pass before Claude finishes.

Exit code 2 tells Claude Code to keep working and shows it what was printed to stderr.
Standard library only, so it runs before the project environment exists.
"""

import json
import os
import subprocess
import sys

CHECKS = (
    ["uv", "run", "--quiet", "ruff", "check", "--quiet", "."],
    ["uv", "run", "--quiet", "pytest", "-q", "-x"],
)


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except ValueError:
        event = {}
    # Claude is already continuing because of this hook: do not block twice in a row.
    if event.get("stop_hook_active"):
        return 0

    root = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    status = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if not any(line.strip().endswith(".py") for line in status.stdout.splitlines()):
        return 0

    for command in CHECKS:
        result = subprocess.run(command, cwd=root, capture_output=True, text=True)
        if result.returncode != 0:
            tail = "\n".join((result.stdout + result.stderr).strip().splitlines()[-25:])
            print(
                f"`{' '.join(command)}` failed. Fix it before finishing, or tell the user "
                f"plainly why it cannot be fixed.\n{tail}",
                file=sys.stderr,
            )
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
