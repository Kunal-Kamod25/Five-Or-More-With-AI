# AGENTS.md — Working Agreement for This Repo

## Project Context
See `SPEC.md` for the current RL scope, `RULES.md` for the Five-or-More rules,
`PLAN.md` for current mission status, and `REPORT.md` for research notes.

## Environment
- Project: Five-or-More with AI
- Conda env name: `five-or-more-ai`
- Python 3.11, PyTorch (CPU by default; GPU optional — set up later)
- Always activate env before running anything:
  ```
  conda activate five-or-more-ai
  ```
- The environment is defined in `environment.yml`. If a dependency is added,
  update that file in the same change.

## Folder Structure (do not create new top-level folders without discussion)
```
Five-Or-More-With-AI/
├── AGENTS.md
├── SPEC.md
├── RULES.md
├── PLAN.md
├── REPORT.md
├── environment.yml
├── .gitignore
├── docs/
│   └── team_roles.md
├── game_engine/       <- Rust game logic and Bevy application
├── data/
│   ├── raw/           <- untouched downloaded datasets (gitignored)
│   └── processed/     <- cleaned/preprocessed data (gitignored)
├── notebooks/         <- exploration and prototyping
├── src/
│   ├── models/        <- neural network architectures
│   ├── training/       <- training loops, config, checkpoints
│   └── utils/         <- shared helper code
├── experiments/       <- logs, checkpoints, and run outputs (gitignored)
└── report/            <- report drafts, figures, final PDF/paper
```

## Code Conventions
- All game logic → `game_engine/`; keep core state transitions independent of Bevy where possible
- All model architecture code → `src/models/`
- Training loops and scripts → `src/training/`
- Environment wrappers and RL utilities → `src/utils/` or a clearly named RL module
- Shared helpers (board encoding, action masks, metrics, etc.) → `src/utils/`
- No large files committed to git: datasets, model weights, logs, or build output.
  These belong in `data/`, `experiments/` — all gitignored.
- Commit message format: `Mission N: <short description>`
- Tag each completed mission: `git tag vN.0-<mission-name>`

## Before Starting Any Work Session
1. Check `git status` and preserve unrelated user changes
2. Check `PLAN.md` for current mission status + open questions
3. Activate the project Python environment

## Before Ending Any Work Session
1. Update `PLAN.md` if mission status changed
2. Add any unresolved decisions to the "Open Questions" section of `PLAN.md`
   so the other person isn't blocked when they pick it up

## Changing Fixed Decisions
`SPEC.md` and `RULES.md` record the agreed project scope and game rules. Changes
must be called out in the response and recorded in `PLAN.md`.

## For AI Coding Assistants (Claude Code, Cursor, Copilot, etc.)
- Read `SPEC.md`, `RULES.md`, and `PLAN.md` before making changes.
- Do not install new dependencies without updating `environment.yml`.
- Follow the folder structure above exactly; do not invent new top-level folders.
- Do not commit files under `data/raw/`, `data/processed/`, or `experiments/`.
