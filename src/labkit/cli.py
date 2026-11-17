"""The `lab` command. Run `uv run lab --help`."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from labkit import agents, config, experiment, registry, review, status, tasks
from labkit.config import BudgetError, LabError

EXIT_FAILED, EXIT_USAGE, EXIT_BUDGET = 1, 2, 3


def cmd_status(cfg, args) -> int:
    print(status.report(cfg))
    return 0


def cmd_run(cfg, args) -> int:
    spec = experiment.load_spec(Path(args.spec).resolve())
    experiment.apply_overrides(spec, args.set or [], args.seed)
    record = experiment.run_spec(cfg, spec)
    if args.json:
        print(json.dumps(record, sort_keys=True))
    else:
        print(experiment.summarize(cfg, spec, record))
    return 0 if record["status"] == "ok" else EXIT_FAILED


def cmd_runs(cfg, args) -> int:
    records = registry.read(cfg.path("registry"))
    if args.spec_id:
        records = [r for r in records if r["spec"] == args.spec_id]
    for r in records[-args.n :]:
        metrics = ", ".join(f"{k}={v:.5g}" for k, v in sorted(r["metrics"].items()))
        changed = json.dumps(r["config"], sort_keys=True)
        print(
            f"{r['time'][:19]}  {r['run_id']}  {r['spec']}  {r['stage']:<6} {r['status']:<12}"
            f" {metrics}  {changed}"
        )
    if not records:
        print("no runs recorded yet")
    return 0


def cmd_show(cfg, args) -> int:
    matches = [r for r in registry.read(cfg.path("registry")) if r["run_id"] == args.run_id]
    if not matches:
        raise LabError(f"no run with id {args.run_id}")
    record = matches[-1]
    print(json.dumps(record, indent=2, sort_keys=True))
    print("\n--- last log lines ---")
    print(experiment.log_tail(cfg, record, lines=40))
    return 0


def cmd_task(cfg, args) -> int:
    if args.action == "new":
        path = tasks.new(cfg, args.title)
        print(f"created {path.relative_to(cfg.root)} - fill in Goal, Done when and Scope")
    elif args.action == "set":
        path = tasks.set_status(cfg, args.task_id, args.status)
        print(f"{path.name}: status is now {args.status}")
    else:
        for task in tasks.all_tasks(cfg):
            print(f"{task['id']}  {task['status']:<8} {task['title']}")
    return 0


def cmd_ask(cfg, args) -> int:
    prompt = sys.stdin.read() if args.prompt == "-" else args.prompt
    result = agents.ask(cfg, args.engine, prompt, purpose="ask", write=args.write, model=args.model)
    print(result.text)
    cost = f", ${result.cost_usd:.3f}" if result.cost_usd is not None else ""
    print(
        f"\n[{result.engine}: {'ok' if result.ok else 'FAILED'}, {result.seconds}s{cost}]",
        file=sys.stderr,
    )
    return 0 if result.ok else EXIT_FAILED


def cmd_review(cfg, args) -> int:
    verdict, saved = review.review(
        cfg, task_id=args.task, base=args.base, engine=args.engine, check=not args.no_check
    )
    print(saved.read_text())
    print(f"saved to {saved.relative_to(cfg.root)}")
    return 0 if verdict in ("accept", "accept_with_caveats") else EXIT_FAILED


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lab", description="Experiment identity, artifacts, budgets and independent review."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status", help="where the project stands").set_defaults(func=cmd_status)

    run = sub.add_parser("run", help="run one experiment from a spec file")
    run.add_argument("spec", help="path to a spec, e.g. experiments/specs/example-quadratic.toml")
    run.add_argument("--set", action="append", metavar="KEY=VALUE", help="override a config value")
    run.add_argument("--seed", type=int, help="override the seed")
    run.add_argument("--json", action="store_true", help="print the full record as JSON")
    run.set_defaults(func=cmd_run)

    runs = sub.add_parser("runs", help="list recorded runs")
    runs.add_argument("spec_id", nargs="?", help="only show runs of this spec id")
    runs.add_argument("-n", type=int, default=15, help="how many recent runs to show")
    runs.set_defaults(func=cmd_runs)

    show = sub.add_parser("show", help="show one run's record and the end of its log")
    show.add_argument("run_id")
    show.set_defaults(func=cmd_show)

    task = sub.add_parser("task", help="create and list task files")
    task_sub = task.add_subparsers(dest="action", required=True)
    task_new = task_sub.add_parser("new", help="create a task file from the template")
    task_new.add_argument("title")
    task_sub.add_parser("ls", help="list tasks")
    task_set = task_sub.add_parser("set", help="change a task's status")
    task_set.add_argument("task_id")
    task_set.add_argument("status", choices=tasks.STATUSES)
    task.set_defaults(func=cmd_task)

    ask = sub.add_parser("ask", help="send one bounded job to claude or codex, headlessly")
    ask.add_argument("engine", choices=agents.ENGINES)
    ask.add_argument("prompt", help="the prompt, or '-' to read it from standard input")
    ask.add_argument("--write", action="store_true", help="let the agent edit project files")
    ask.add_argument("--model", help="model name passed through to the engine")
    ask.set_defaults(func=cmd_ask)

    rev = sub.add_parser("review", help="independent review of the current change")
    rev.add_argument("--task", help="task id whose file states the requirements, e.g. T0001")
    rev.add_argument("--base", help="git ref to compare against, e.g. main")
    rev.add_argument("--engine", choices=agents.ENGINES, help="reviewer (default: not the author)")
    rev.add_argument("--no-check", action="store_true", help="skip running the check command")
    rev.set_defaults(func=cmd_review)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(config.load(), args)
    except BudgetError as exc:
        print(f"budget: {exc}", file=sys.stderr)
        return EXIT_BUDGET
    except LabError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_USAGE


if __name__ == "__main__":
    sys.exit(main())
