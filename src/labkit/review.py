"""Independent review: a fresh agent sees the requirements, the diff and evidence that this
code produced itself. It never sees the author's account of the work.
"""

from __future__ import annotations

import re
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

from labkit import agents, tasks
from labkit.config import Config, LabError

MAX_DIFF_CHARS = 60_000
VERDICTS = ("accept", "accept_with_caveats", "reject", "cannot_assess")
EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
# Code comes first in the diff, so that the size limit cuts prose before it cuts code.
DIFF_ORDER = "*.py\n*.toml\n*.sh\n*.json\n*.yaml\n*.yml\n"

PROMPT = """You are an independent reviewer of a code change in this repository.
You did not write it, and you have deliberately not been shown the author's explanation.
Judge only what is below and what you can read in the repository. You may read files; do not
edit anything.

Look for, in this order:
1. The change not doing what the requirements ask.
2. Bugs: wrong results, unhandled cases, broken callers elsewhere in the repository.
3. Tests that were weakened, deleted, or that would pass even if the code were wrong.
4. Results or claims not supported by the evidence section.
Skip style and formatting.

Reply in exactly this shape:

VERDICT: <accept | accept_with_caveats | reject | cannot_assess>

FINDINGS:
- [high|medium|low] path/to/file:line - what is wrong, and the input or situation that shows it

If there are no findings, write "- none". Use cannot_assess when the requirements or the
evidence are too thin to judge, and say what is missing.

## Requirements

{requirements}

## Evidence (produced by the review tool, not by the author)

{evidence}

## Files changed

{files}

## Diff

```diff
{diff}
```
"""


def _git(root: Path, *args: str) -> str:
    out = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, timeout=60)
    if out.returncode != 0:
        raise LabError(f"git {' '.join(args)} failed: {out.stderr.strip()}")
    return out.stdout


def bookkeeping(cfg: Config) -> list[str]:
    """Files `lab review` and `lab ask` write themselves. Leaving them out keeps a review
    from mistaking its own traces for the change."""
    paths = (cfg.path("ledger"), cfg.path("reviews"))
    return [p.relative_to(cfg.root).as_posix() for p in paths if p.is_relative_to(cfg.root)]


def collect_change(
    root: Path, base: str | None, ignore: tuple[str, ...] | list[str] = ()
) -> tuple[str, str, str]:
    """Return (description of what is compared, changed files, diff)."""
    paths = ["--", ".", *(f":(exclude){path}" for path in ignore)]
    status = _git(root, "status", "--short", "--untracked-files=all", *paths)

    def exists(ref: str) -> bool:
        check = subprocess.run(
            ["git", "rev-parse", "--verify", "-q", ref], cwd=root, capture_output=True
        )
        return check.returncode == 0

    # Where a commit to compare against does not exist yet, git's empty tree stands in.
    if base:
        target, label = [base], f"working tree compared with {base}"
    elif not exists("HEAD"):
        target, label = [EMPTY_TREE], "all files (the repository has no commits yet)"
    elif status.strip():
        target, label = ["HEAD"], "uncommitted changes compared with the last commit"
    else:
        previous = "HEAD~1" if exists("HEAD~1") else EMPTY_TREE
        target, label = [previous, "HEAD"], "the last commit"
    with tempfile.NamedTemporaryFile("w", suffix=".order") as order:
        order.write(DIFF_ORDER)
        order.flush()
        diff = _git(root, "diff", f"-O{order.name}", *target, *paths)
    files = _git(root, "diff", "--stat", *target, *paths)
    if status.strip():
        files += "\nUncommitted or new files (read new files directly):\n" + status
    if len(diff) > MAX_DIFF_CHARS:
        diff = diff[:MAX_DIFF_CHARS] + "\n[diff truncated: read the changed files directly]"
    return label, files.strip(), diff.strip()


def run_check(cfg: Config) -> str:
    command = cfg.data["check"]["command"]
    try:
        out = subprocess.run(
            command,
            cwd=cfg.root,
            capture_output=True,
            text=True,
            timeout=cfg.data["check"]["timeout_s"],
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"`{' '.join(command)}` could not complete: {exc}"
    tail = "\n".join((out.stdout + out.stderr).strip().splitlines()[-30:])
    return f"`{' '.join(command)}` exited with code {out.returncode}. Last lines:\n{tail}"


def parse_verdict(text: str) -> str:
    match = re.search(r"^\s*VERDICT:\s*([a-z_]+)", text, re.M | re.I)
    verdict = match.group(1).lower() if match else "cannot_assess"
    return verdict if verdict in VERDICTS else "cannot_assess"


def review(
    cfg: Config,
    *,
    task_id: str | None = None,
    base: str | None = None,
    engine: str | None = None,
    check: bool = True,
) -> tuple[str, Path]:
    """Run a review, save it under project/reviews/, and return (verdict, saved file)."""
    label, files, diff = collect_change(cfg.root, base, bookkeeping(cfg))
    if not diff and not files:
        raise LabError("nothing to review: no changes found")

    if task_id:
        task = tasks.find(cfg, task_id)
        requirements = task["path"].read_text()
    else:
        requirements = (
            "No task file was given. Infer the intent from the change and say so in your "
            "findings if the intent is unclear."
        )
    evidence = run_check(cfg) if check else "No check was run."

    settings = cfg.data["engines"]
    # With no engine named, prefer one that did not write the change, and fall back to the
    # other if it cannot run. A named engine is used as asked, with no fallback.
    order = (
        [engine]
        if engine
        else agents.candidates(settings["reviewer"], avoid=settings["implementer"])
    )
    prompt = PROMPT.format(requirements=requirements, evidence=evidence, files=files, diff=diff)
    failures = []
    for engine in order:
        result = agents.ask(cfg, engine, prompt, purpose=f"review {task_id or 'adhoc'}")
        if result.ok:
            break
        failures.append(f"{engine} could not review: {result.text}")
    else:
        raise LabError("no reviewer succeeded:\n  " + "\n  ".join(failures))

    verdict = parse_verdict(result.text)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    folder = cfg.path("reviews")
    folder.mkdir(parents=True, exist_ok=True)
    saved = folder / f"{stamp}-{(task_id or 'adhoc').upper()}-{engine}.md"
    saved.write_text(
        f"# Review: {task_id or 'ad hoc'}\n\n"
        f"- Verdict: **{verdict}**\n"
        f"- Reviewer: {engine} (fresh headless session, read-only)\n"
        f"- Compared: {label}\n" + "".join(f"- Note: {failure}\n" for failure in failures) + "\n"
        f"## Evidence given to the reviewer\n\n{evidence}\n\n"
        f"## Reviewer's reply\n\n{result.text}\n"
    )
    return verdict, saved
