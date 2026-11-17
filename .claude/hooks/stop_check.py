#!/usr/bin/env python3
"""Stop hook: when Python files have changed, run lint and tests before Claude finishes.

The first failure sends Claude back to work: exit code 2 makes Claude Code continue and
shows it what was printed to stderr. If the checks still fail when Claude stops again, the
hook lets it stop, so that a session cannot loop forever, and warns the user instead.
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
    second_attempt = bool(event.get("stop_hook_active"))

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
            if second_attempt:
                warning = f"`{' '.join(command)}` is still failing. The work is not finished."
                print(json.dumps({"systemMessage": warning}))
                return 0
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
