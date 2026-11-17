---
name: experiment-loop
description: Run a bounded experimental search with the lab tool, where the agent proposes configs or code changes and ordinary code runs and scores them. Use for tuning, ablations, benchmarks, or any "try variations and compare" work.
---

# Experiment loop

You propose. `lab` runs, scores and records. You never compute or report a metric yourself.

## Setting up a new experiment

1. Copy `experiments/specs/example-quadratic.toml` and read its comments.
2. Write a runner in `experiments/runners/` that reads `$LAB_CONFIG` (JSON with `config` and
   `seed`) and writes raw output into `$LAB_RUN_DIR`. Give it a fast mode that the `[screen]`
   overrides can switch on.
3. Write an evaluator in `experiments/evaluators/` that reads the raw output and writes
   `metrics.json` (a flat object of finite numbers) into `$LAB_RUN_DIR`.
4. List every file that affects the result under `code` and every data file under `inputs`.
   A file left out can change without the cache noticing.
5. Ask the user to set `max_runs`, `[bounds]` and `timeout_s`. Those are their decisions.

## Running the search

1. `uv run lab runs <spec id>` to see what has been tried. Do not repeat it.
2. Write down, in the task file's Log, what you will try next and what you expect to see.
   A prediction made before the run is worth more than an explanation made after.
3. Run one variation: `uv run lab run experiments/specs/<name>.toml --set key=value`.
4. Read the summary. For a failure, read the log it points to before changing anything.
5. Repeat. Change one thing at a time unless you are deliberately sweeping.

## What the outcomes mean

- `ok` - metrics recorded. `(cached)` means this exact run already existed.
- `screened_out` - the cheap first pass failed or was out of range; the full run was skipped.
- `failed`, `timeout`, `no_metrics` - the run is recorded with its log. Fix the cause.
- `error: invalid config` (exit 2) - a value is outside `[bounds]`. Nothing ran.
- `budget:` (exit 3) - a cap was reached. Stop and report what you learned and what you
  would try next. Do not edit the cap.

## Rules

- Never edit an evaluator, `[bounds]`, `[screen]` or `max_runs` to improve a number.
- Never read `data/holdout/`. A final holdout evaluation is run once, by the user's decision.
- Report results as run ids, so they can be checked: "run c83551a97dc5: loss 0.012".
- Long computations should save checkpoints into `$LAB_RUN_DIR`. A failed run that is run
  again gets the same directory and can resume.
