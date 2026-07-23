# AGENTS.md — Working Agreement for This Repo

## Project Context
See `SPEC.md` for what we're building, `RULES.md` for the Gomoku ruleset,
`PLAN.md` for current mission status, `REPORT.md` for running research notes.

## Environment
- Conda env name: `gomoku-ai`
- Python 3.11, PyTorch (CPU by default; GPU optional — set up later)
- Always activate env before running anything:
  ```
  conda activate gomoku-ai
  ```
- Environment is defined in `environment.yml`. If you install a new package,
  update `environment.yml` in the same commit.

## Folder Structure (do not create new top-level folders without discussion)
```
gomoku-behavioral-cloning/
├── AGENTS.md
├── SPEC.md
├── RULES.md
├── PLAN.md
├── REPORT.md
├── environment.yml
├── .gitignore
├── docs/
│   └── team_roles.md
├── game_engine/       <- Gomoku game logic (board, moves, win detection)
├── data/
│   ├── raw/           <- untouched downloaded datasets (gitignored)
│   └── processed/     <- cleaned/preprocessed data (gitignored)
├── notebooks/         <- exploration, EDA, prototyping
├── src/
│   ├── models/        <- neural network architectures
│   ├── training/       <- training loops, config, checkpoints
│   └── utils/         <- shared helper code
├── experiments/       <- logs, saved checkpoints, run outputs (gitignored)
└── report/            <- report drafts, figures, final PDF/paper
```

## Code Conventions
- All game logic → `game_engine/`
- All model architecture code → `src/models/`
- Training loops/scripts → `src/training/`
- Shared helpers (board encoding, metrics, etc.) → `src/utils/`
- No large files committed to git: datasets, `.pth`/`.pt` model weights, logs.
  These belong in `data/`, `experiments/` — all gitignored.
- Commit message format: `Mission N: <short description>`
- Tag each completed mission: `git tag vN.0-<mission-name>`

## Before Starting Any Work Session
1. `git pull`
2. Check `PLAN.md` for current mission status + open questions
3. `conda activate gomoku-ai`

## Before Ending Any Work Session
1. Update `PLAN.md` if mission status changed
2. Commit and push — even incomplete work (use a branch + WIP commit if mid-task)
3. Add any unresolved decisions to the "Open Questions" section of `PLAN.md`
   so the other person isn't blocked when they pick it up

## Changing Fixed Decisions
`SPEC.md` and `RULES.md` contain decisions both teammates agreed on
(board size, ruleset, architecture choices, scope). Do not edit these silently.
If you want to change one:
1. Message/call the other person first
2. Agree on the change
3. Commit the edit with a message explaining *why* (not just *what*)

## For AI Coding Assistants (Claude Code, Cursor, Copilot, etc.)
- Read `SPEC.md`, `RULES.md`, and `PLAN.md` before making changes.
- Do not modify `RULES.md` or `SPEC.md` without explicitly flagging it in your
  response — these are team decisions, not code artifacts.
- Do not install new dependencies without updating `environment.yml`.
- Follow the folder structure above exactly; do not invent new top-level folders.
- Do not commit files under `data/raw/`, `data/processed/`, or `experiments/`.
