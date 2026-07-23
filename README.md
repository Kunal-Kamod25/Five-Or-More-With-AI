# Human-Like Gomoku AI Using Behavioral Cloning and Player Modeling

A Master's research project: training a neural network (PyTorch) to imitate
human Gomoku gameplay via Behavioral Cloning, using public game datasets.

## Start Here
- `AGENTS.md` — how we work in this repo (setup, conventions, git workflow)
- `SPEC.md` — what we're building, precisely
- `RULES.md` — the Gomoku ruleset we're using
- `PLAN.md` — current mission status, open questions, decision log
- `REPORT.md` — running research notes → becomes the final report

## Quick Setup
```bash
conda env create -f environment.yml
conda activate gomoku-ai
python -c "import torch; print(torch.__version__)"
```

## Status
See `PLAN.md` for current mission.
