# 6. Getting to know a large codebase such as AlphaFold

You do not read a large repository front to back, and neither should the agent. You find the
few front doors, follow one real run from start to finish, and write down what you saw. The
`map-codebase` skill does this; the steps below are what it does and why.

You do not need to install or run AlphaFold to understand it. Running it needs a GPU and
several hundred gigabytes of sequence databases. Reading it needs a copy of the files.

## Step by step

**1. Get a local copy, outside this repository.**

```bash
mkdir -p ~/Documents/main/reading
git clone --depth 1 https://github.com/google-deepmind/alphafold ~/Documents/main/reading/alphafold
```

`--depth 1` fetches the latest snapshot without the history, which is quicker. Drop it if you
want `git log` to explain why things changed.

**2. Start a read-only session in it.**

```bash
cd ~/Documents/main/reading/alphafold
claude --permission-mode plan
```

Plan mode reads and answers and changes nothing.

**3. Ask from the outside in.** One question at a time, in this order:

1. "What does this project do, what does it need to run, and what are its entry points? Read
   the README and the build files first."
2. "Give me the top-level folders with one line each and roughly how much code is in each."
3. "Trace one prediction from the command line to the output file. List every file it passes
   through, with line references."
4. "Which ten files matter most, and which folders can I ignore?"
5. "Define the domain words this code uses: MSA, template, Evoformer, pLDDT, relaxation."

**4. Go deep on one piece.** Pick the part you care about and ask for it to be explained
against its tests: "Explain `alphafold/model/folding.py` using its tests as examples of how
it is called."

**5. Keep the map.** Ask for the result to be written to `notes/alphafold/MAP.md` in this
repository. A map you can reopen beats an explanation that scrolled away.

## What you will find in AlphaFold

The layout below was read from the repository. The path of a run is the usual account of it;
have the agent confirm each hop with a line reference before you rely on it.

```text
run_alphafold.py        the front door: reads flags, runs the stages below in order
alphafold/
  data/                 turning a sequence into model inputs
    pipeline.py           single-chain feature pipeline (pipeline_multimer.py for complexes)
    tools/                wrappers around external search programs
    parsers.py, mmcif_parsing.py, templates.py, msa_pairing.py, feature_processing.py
  model/                the neural network
    model.py              loads parameters and runs a prediction
    modules.py            the network itself (modules_multimer.py for complexes)
    folding.py            the structure module: from representations to 3D coordinates
    config.py             every model setting in one place
    features.py, all_atom.py, geometry/, tf/
  common/               shared definitions
    residue_constants.py  the chemistry tables
    protein.py            the protein data structure, reading and writing PDB files
    confidence.py         confidence scores computed from the model's outputs
  relax/                physics-based clean-up of the predicted structure
    relax.py, amber_minimize.py, cleanup.py
  notebooks/            helpers for the Colab notebook
docker/, scripts/       how to build the container and download the databases
```

One run, in one line: `run_alphafold.py` → `data/pipeline.py` builds features from sequence
searches and templates → `model/model.py` runs the network defined in `model/modules.py` and
`model/folding.py` → `common/confidence.py` scores it → `relax/relax.py` tidies the geometry
→ `common/protein.py` writes the PDB file.

## Habits that carry over to any repository

- **Local copy first.** An agent searching files on disk is far more reliable than one
  reading web pages.
- **Entry points before folders.** `run_*.py`, `main.py`, `[project.scripts]`,
  `if __name__ == "__main__"`.
- **Config files are a table of contents.** `model/config.py` here names every component the
  model has.
- **Tests are usage examples** with small inputs.
- **Ask for `path:line` references** and open a few yourself. An agent can describe a
  plausible design that is not the one in the code; a line reference is quick to check.
- **Broad search in a subagent, deep reading in the main session.** "Find everywhere
  templates are used" produces a lot of noise; a subagent returns only the answer.
- **Clear the session between areas.** A session full of the data pipeline is a poor place to
  start learning the model.

## From reading to building

To reuse an idea from a codebase you studied, do not paste the code across. Write a task
(`plan-task`) that names the file and lines you are borrowing from, what must behave the
same, and a test that shows it does. Check the licence first: AlphaFold's code is Apache 2.0,
and its model parameters have their own terms.
