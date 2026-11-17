# 7. What commutate teaches, and what not to copy yet

[commutate](https://github.com/lucastiger/commutate) is one person building a physics product
(a layout tool for power electronics modules, called ModuleForge inside the repository) with
a team of agents. Its orchestrator, `mfos`, is about 3,000 lines of Python. It took its
author real effort to get right, and most of it exists to solve problems you do not have yet.
What is worth taking now is the thinking, which is cheap.

## How it works, in one paragraph

A small ordinary program loops over files in the repository. When a task is ready it starts a
fresh headless Claude Code session in one of six roles (planner, builder, scientist, critic,
scout, scribe), hands it a written packet, and waits. When the session ends, the program, not
the agent, runs the task's "definition of done" commands and decides whether the work counts.
Experiments run with no language model involved, and a separate evaluator turns result files
into PASS, FAIL, INCONCLUSIVE or INVALID. The owner approves goals, standards of evidence,
money, and anything that touches the outside world.

## The ideas, and where they are in this repository

| commutate's principle | Why it matters | Here |
|---|---|---|
| Agents propose, code disposes | An agent's report of success is not evidence | `lab run` and the check command decide; `lab review` gathers its own evidence |
| The repository is the database | State in files survives crashes, shows up in diffs, and any tool can read it | `project/`, `experiments/registry.jsonl`, `project/ledger.jsonl` |
| Fresh context by default | A long session anchors on its own earlier reasoning | One task file per task; the `handoff` skill; reviewers start cold |
| One agent unless independence or parallelism pays | More agents cost more and coordinate badly | Note 3's ladder; a single reviewer is the only standing second agent |
| Separation of powers | The thing being judged must not control the judge | Runners do not score themselves; agents may not edit `lab.toml`, bounds or caps |
| Sealed data | Tuning against the final test makes the final test meaningless | `data/holdout/` is unreadable by rule |
| Cost-bounded by construction | An unattended loop needs a ceiling that is not a suggestion | Caps on runs, compute, agent calls and dollars; exit code 3 |
| Boring technology | Files, Git and subprocesses can be debugged by reading them | `labkit` has no dependencies outside Python itself |
| Decisions are written down | In three months nobody remembers why | `project/decisions/` |

Its Claude Code configuration was also the model for this one: the same three-way split of
allow, ask and deny rules, a session-start hook that prints status, a stop hook that will not
let a session finish while its checks fail, and the same four reviewer verdicts.

## What was left out, and what would justify adding it

| In commutate | Add it here when |
|---|---|
| **Six agent roles**, each with its own model and tool list | One role's instructions keep getting in another's way, for example the builder keeps redesigning experiments |
| **An autonomous loop** that picks up tasks without you | You have at least ten well-specified tasks waiting, and the last ten you supervised passed review without rework |
| **Task packets**: a generated brief that is the agent's whole world | Task files stop being enough, because agents wander into unrelated parts of the repository |
| **A guard hook** that checks every edit against the role's allowed folders | An agent edits something it should not have, and a line in `AGENTS.md` did not stop it |
| **Blinded review checkouts**, with task history physically removed | You see a reviewer agreeing because it read the author's notes |
| **Pre-registered objectives** with pass and kill criteria fixed in advance | You are testing a hypothesis whose answer you care about, and are tempted to move the goalposts |
| **An inbox** of questions waiting for the owner | Agents run while you are away and block on decisions |
| **Review depth by risk** (none, one reviewer, two specialists) | Reviews cost enough that reviewing everything equally is wasteful |
| **Rented cloud machines** for heavy experiments | A single experiment no longer fits on your computer |
| **Checks on GitHub** (CI) that rerun the tests on every push | The repository is on GitHub and more than one session pushes to it |

Each of these is a response to a failure its author saw. Wait until you see the same failure.
You will then know exactly what the fix has to do, which is the hard part of building it.

## Two places this repository deliberately differs

- **Pushing.** commutate forbids agents from pushing, merging or using `gh` at all; a program
  does the integration. Here agents may commit and push, and only the destructive commands
  are refused, because you asked for work to be pushed after each major change and there is
  no orchestrator to do it instead.
- **Agent memory.** commutate turns Claude Code's automatic memory off and keeps knowledge
  only in reviewed files. Here it stays on, with the rule that anything both agents need goes
  into `AGENTS.md`, since Codex cannot see Claude's memory.

## Worth reading in the original

- `docs/ARCHITECTURE.md`, sections 1 to 3: the design and the reasons for rejecting agent
  teams, the Agent SDK and outside frameworks as the core.
- `.mfos/policy.toml`: every limit in one file.
- `.claude/agents/critic.md` and `builder.md`: how to write a role.
- `project/decisions/`: twenty-three decisions that show the method being used on real
  science, including the ones that record a result as void.

Use the recipe in note 6 on it.
