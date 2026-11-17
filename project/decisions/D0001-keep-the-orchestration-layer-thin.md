# D0001: Keep the orchestration layer thin

Date: 2026-11-16
Status: accepted

## Context

The model for this project is lucastiger/commutate, which runs a custom orchestrator (`mfos`,
about 3,000 lines) that calls Claude Code headlessly for six agent roles. It is tempting to
rebuild that. But Claude Code already provides subagents, worktrees, hooks, scheduling,
session recovery and usage reports, and the owner is new to these tools.

## Decision

`lab` owns only what Claude Code and Codex do not: experiment identity and caching, artifact
records, budgets, scoring by ordinary code, and review packets that cross engines. Sessions,
delegation, parallel work and memory stay with the agents' own features.

## Alternatives considered

- **A full role-based orchestrator like `mfos`.** Rejected for now: it pays off at hundreds of
  agent tasks, and it would have to be maintained before any research is done with it.
- **A workflow engine (Prefect) from day one.** Deferred until there is a pipeline that needs
  retries and scheduling across many steps. `lab run` is one step such an engine could call.
- **The Agent SDK as the core.** Deferred until driving `claude -p` as a subprocess becomes the
  problem being solved.
- **No custom code, only prompts.** Rejected: prompts are advice. Caps, caching and scoring
  have to be enforced by code to mean anything.

## Consequences

- Each new feature of `lab` must name what it does that the agents cannot already do.
- If a headless multi-step loop is ever needed, it is added as a small script on top of
  `lab ask`, with a task file as its input and a review as its exit.
- Revisit when a single project passes roughly 50 agent tasks or needs unattended runs
  overnight.
