import json
import subprocess
from pathlib import Path

import pytest

from labkit import agents, registry, review, tasks
from labkit.config import BudgetError


def argv(engine, write):
    return agents.build_argv(
        engine, write=write, cwd=Path("/repo"), max_usd=2.0, out_file=Path("/tmp/out"), model=None
    )


def test_claude_is_read_only_unless_write_is_requested():
    read, write = argv("claude", False), argv("claude", True)

    # `--tools` is what removes Bash, Edit and Write from the session. `--allowedTools`
    # alone would only add to the project's allow rules, which include `uv run`.
    assert read[read.index("--tools") + 1] == "Read,Grep,Glob"
    assert read[read.index("--allowedTools") + 1] == "Read,Grep,Glob"
    assert read[read.index("--permission-mode") + 1] == "dontAsk"
    assert "--strict-mcp-config" in read
    assert {"Edit", "Write", "Bash"} <= set(write[write.index("--tools") + 1].split(","))
    shell = [r for r in write[write.index("--allowedTools") + 1].split(",") if "Bash" in r]
    assert "Bash(uv run lab run *)" in shell
    # No blanket `uv run`, and no `lab ask` or `lab review`, which would start paid calls.
    blanket = ("(uv run *)", "(uv run lab *)")
    assert not [r for r in shell if r.endswith(blanket) or "lab ask" in r or "lab review" in r]
    assert write[write.index("--permission-mode") + 1] == "acceptEdits"
    assert read[read.index("--max-budget-usd") + 1] == "2.0"


def test_codex_is_sandboxed_read_only_unless_write_is_requested():
    read, write = argv("codex", False), argv("codex", True)

    assert read[read.index("--sandbox") + 1] == "read-only"
    assert write[write.index("--sandbox") + 1] == "workspace-write"
    assert read[-1] == "-"  # the prompt arrives on standard input


def test_candidates_put_a_reviewer_other_than_the_author_first(monkeypatch):
    monkeypatch.setattr(agents, "available", lambda: {"claude": "/bin/claude", "codex": None})
    assert agents.candidates("codex", avoid="claude") == ["claude"]
    monkeypatch.setattr(agents, "available", lambda: {"claude": "/bin/claude", "codex": "/bin/c"})
    assert agents.candidates("codex", avoid="claude") == ["codex", "claude"]
    assert agents.candidates("claude", avoid="claude") == ["codex", "claude"]
    assert agents.candidates("claude") == ["claude", "codex"]


def test_review_falls_back_when_the_preferred_reviewer_cannot_run(project, monkeypatch):
    git(project.root, "init", "-q")
    (project.root / "new.py").write_text("x = 1\n")

    def run(argv, prompt, cwd, timeout):
        if argv[0] == "codex":
            return 1, "ERROR: model not supported", ""
        return 0, json.dumps({"result": "VERDICT: accept\n\nFINDINGS:\n- none"}), ""

    monkeypatch.setattr(agents, "_execute", run)
    monkeypatch.setattr(agents, "available", lambda: {"claude": "/bin/claude", "codex": "/bin/c"})

    verdict, saved = review.review(project, check=False)

    assert verdict == "accept"
    assert saved.name.endswith("-claude.md")
    assert "codex could not review: ERROR: model not supported" in saved.read_text()


def fake_claude(reply, cost=0.25):
    def run(argv, prompt, cwd, timeout):
        run.prompts.append(prompt)
        return 0, json.dumps({"result": reply, "total_cost_usd": cost, "is_error": False}), ""

    run.prompts = []
    return run


def test_ask_records_cost_in_the_ledger_and_enforces_the_daily_cap(project, monkeypatch):
    monkeypatch.setattr(agents, "_execute", fake_claude("hello"))
    project.data["budgets"]["agent_usd_per_day"] = 0.4

    first = agents.ask(project, "claude", "hi", purpose="test")
    agents.ask(project, "claude", "hi", purpose="test")

    assert first.text == "hello" and first.cost_usd == 0.25
    assert len(registry.read(project.path("ledger"))) == 2
    with pytest.raises(BudgetError, match="spend cap"):
        agents.ask(project, "claude", "hi", purpose="test")


def test_a_claude_call_that_reports_no_cost_counts_at_the_per_call_cap(project, monkeypatch):
    monkeypatch.setattr(agents, "_execute", lambda *a: (124, "", "timed out after 900s"))
    project.data["budgets"]["agent_usd_per_call"] = 2.0
    project.data["budgets"]["agent_usd_per_day"] = 3.0

    assert not agents.ask(project, "claude", "hi", purpose="test").ok  # counted as $2
    assert not agents.ask(project, "codex", "hi", purpose="test").ok  # Codex has no cost
    agents.ask(project, "claude", "hi", purpose="test")  # $2 < $3, still allowed
    with pytest.raises(BudgetError, match="spend cap"):
        agents.ask(project, "claude", "hi", purpose="test")


def test_an_interrupted_call_is_still_written_to_the_ledger(project, monkeypatch):
    def interrupted(*args):
        raise KeyboardInterrupt

    monkeypatch.setattr(agents, "_execute", interrupted)
    with pytest.raises(KeyboardInterrupt):
        agents.ask(project, "claude", "hi", purpose="test")

    (entry,) = registry.read(project.path("ledger"))
    assert entry["ok"] is False and entry["cost_usd"] is None


def test_parse_verdict():
    reply = "VERDICT: accept_with_caveats\n\nFINDINGS:\n- none"
    assert review.parse_verdict(reply) == "accept_with_caveats"
    assert review.parse_verdict("Looks fine to me!") == "cannot_assess"
    assert review.parse_verdict("verdict: Reject") == "reject"


def git(root, *args):
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)


def test_review_sends_requirements_diff_and_own_evidence(project, monkeypatch):
    root = project.root
    git(root, "init", "-q")
    git(root, "config", "user.email", "t@example.com")
    git(root, "config", "user.name", "t")
    (root / "calc.py").write_text("def add(a, b):\n    return a + b\n")
    git(root, "add", "-A")
    git(root, "commit", "-qm", "first")
    (root / "calc.py").write_text("def add(a, b):\n    return a - b\n")
    task_path = tasks.new(project, "Make add subtract")
    project.data["check"]["command"] = ["echo", "3 passed"]
    engine = fake_claude("VERDICT: reject\n\nFINDINGS:\n- [high] calc.py:2 - add subtracts")
    monkeypatch.setattr(agents, "_execute", engine)

    verdict, saved = review.review(project, task_id="T0001", engine="claude")

    prompt = engine.prompts[0]
    assert verdict == "reject"
    assert "return a - b" in prompt
    assert "Make add subtract" in prompt
    assert "3 passed" in prompt
    assert task_path.name in prompt  # new, untracked files are listed for the reviewer
    assert "**reject**" in saved.read_text()


def committed_change(root):
    git(root, "init", "-q")
    git(root, "config", "user.email", "t@example.com")
    git(root, "config", "user.name", "t")
    (root / "notes.md").write_text("first\n")
    (root / "zebra.py").write_text("stripes = 1\n")
    git(root, "add", "-A")
    git(root, "commit", "-qm", "first")
    (root / "notes.md").write_text("second\n")
    (root / "zebra.py").write_text("stripes = 2\n")
    git(root, "add", "-A")
    git(root, "commit", "-qm", "second")


def test_a_second_review_still_sees_the_commit_not_its_own_bookkeeping(project, monkeypatch):
    committed_change(project.root)
    engine = fake_claude("VERDICT: accept\n\nFINDINGS:\n- none")
    monkeypatch.setattr(agents, "_execute", engine)

    for _ in range(2):  # the first review leaves a ledger entry and a saved review behind
        _, saved = review.review(project, engine="claude", check=False)

    assert "stripes = 2" in engine.prompts[1]
    assert "ledger.jsonl" not in engine.prompts[1]
    assert "Compared: the last commit" in saved.read_text()


def test_diff_puts_code_before_prose(project):
    committed_change(project.root)

    _, _, diff = review.collect_change(project.root, None)

    assert diff.index("zebra.py") < diff.index("notes.md")


def test_tasks_are_numbered_listed_and_updated(project):
    tasks.new(project, "First thing")
    second = tasks.new(project, "Second: thing!")
    tasks.set_status(project, "t0002", "doing")

    listed = [(t["id"], t["status"], t["title"]) for t in tasks.all_tasks(project)]
    assert second.name == "T0002-second-thing.md"
    assert listed == [("T0001", "todo", "First thing"), ("T0002", "doing", "Second: thing!")]
