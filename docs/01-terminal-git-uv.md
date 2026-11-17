# 1. Terminal, Git and uv basics

You can ask an agent to run any of these for you. Knowing what they do lets you read what the
agent is doing and step in when it goes wrong.

## Terminal

The terminal always has a *current folder*. Commands act on it unless told otherwise.

| Command | What it does |
|---|---|
| `pwd` | Print the current folder |
| `ls -la` | List files here, including hidden ones (names starting with `.`) |
| `cd path/to/folder` | Move into a folder. `cd ..` goes up one, `cd ~` goes home |
| `mkdir -p a/b` | Create a folder, and any missing parents |
| `cat file` | Print a file. `less file` pages through it (`q` quits) |
| `grep -rn "text" src/` | Find text in files under `src/` |
| `open .` | Open the current folder in Finder (macOS) |
| `which uv` | Show where a program is installed |
| `Ctrl+C` | Stop the running command |

Inside Claude Code, start a line with `!` to run a command yourself, for example `! git status`.
The output lands in the conversation so Claude can see it.

## Git

Git records snapshots of a folder so you can see what changed and go back. GitHub is a website
that stores a copy of those snapshots online. They are separate: this folder is already a Git
repository and works without GitHub.

| Word | Meaning |
|---|---|
| repository (repo) | A folder Git is tracking. The history lives in the hidden `.git` folder |
| commit | One saved snapshot, with a message saying why |
| staging (`git add`) | Choosing which changes go into the next commit |
| branch | A named line of commits. `main` is the default one |
| remote | An online copy, usually on GitHub, usually named `origin` |
| push / pull | Send your commits to the remote / fetch commits from it |
| worktree | A second folder checked out from the same repository on its own branch, so two agents can work without touching each other's files |

The everyday commands:

```bash
git status                 # what has changed since the last commit
git diff                   # the changes themselves, line by line
git add -A                 # stage everything
git commit -m "Add screening stage to lab run"   # save a snapshot
git log --oneline -10      # the last ten commits
git switch -c try-idea     # create a branch and move to it
git switch main            # go back to main
git push                   # send commits to GitHub (once a remote exists)
```

Undoing things, from safest to most dangerous:

```bash
git restore path/to/file   # throw away uncommitted changes to one file
git revert <commit>        # add a new commit that undoes an old one (safe, keeps history)
git reset --hard <commit>  # delete commits and changes. This repository denies it to agents
```

The habit that matters most: **commit small and often.** A commit is the undo button for
everything an agent does. Claude Code's own `/rewind` only covers edits made with its file
tools, not changes made by shell commands.

To put this project on GitHub (optional, and private by default):

```bash
gh repo create agent-system --private --source . --push
```

## uv

uv installs Python, manages the packages a project depends on, and runs commands inside the
project's own environment. It has nothing to do with agents; it just makes Python projects
repeatable.

| File or folder | What it is |
|---|---|
| `pyproject.toml` | The project's description: name, dependencies, tool settings |
| `uv.lock` | The exact versions that were resolved. Commit it |
| `.python-version` | Which Python version to use |
| `.venv/` | The installed environment. Never commit it; `uv sync` rebuilds it |

```bash
uv sync                # make .venv match pyproject.toml and uv.lock
uv run pytest -q       # run a command inside the environment
uv run lab status      # same, for this project's own command
uv add numpy           # add a dependency (updates pyproject.toml and uv.lock)
uv add --dev pytest    # add a tool only needed for development
uv remove numpy        # remove one
uv init --lib          # start a new packaged project with a src/ folder
```

Use `uv add`, never `pip install`. `pip install` changes the environment without recording
it, so the project stops being reproducible.

## How a Python project is laid out

```text
my-project/
  pyproject.toml       the project description
  uv.lock
  README.md
  src/my_project/      the code you import (this is called the "src layout")
  tests/               tests, named test_*.py
```

`[project.scripts]` in `pyproject.toml` is what turns a function into a command. Here,
`lab = "labkit.cli:main"` is why `uv run lab` works.
