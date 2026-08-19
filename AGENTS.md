# AGENTS.md — Working Agreement for This Repo

## Project Context
See `SPEC.md` for what we're building, `RULES.md` for the Five-or-More ruleset,
`PLAN.md` for current mission status, `README.md` for project overview.

## Environment
- Conda env name: `five-or-more-ai`
- Python 3.11, PyTorch, Rust (Cargo)
- Always activate env before running anything:
  ```
  conda activate five-or-more-ai
  ```
- Environment is defined in `environment.yml` / `requirements.txt`.

## Folder Structure (do not create new top-level folders without discussion)
```
Five-Or-More-With-AI/
├── AGENTS.md
├── SPEC.md
├── RULES.md
├── PLAN.md
├── README.md
├── docs/
├── game_engine/       <- Five-or-More game logic (Rust / Python bindings)
├── src/
│   ├── models/        <- neural network architectures
│   ├── training/      <- training loops, config, checkpoints
│   └── env/           <- Python wrapper for the Rust environment
├── experiments/       <- logs, saved checkpoints, run outputs (gitignored)
└── report/            <- report drafts, figures
```

## Code Conventions
- All game logic → `game_engine/`
- All model architecture code → `src/models/`
- Training loops/scripts → `src/training/`
- Commit message format: `Mission N: <short description>` or standard descriptive commits.

## Before Starting Any Work Session
1. `git pull`
2. Check `PLAN.md` for current mission status + open questions
3. `conda activate five-or-more-ai`

## Before Ending Any Work Session
1. Update `PLAN.md` if mission status changed
2. Commit and push — even incomplete work (use a branch + WIP commit if mid-task)
3. Add any unresolved decisions to the "Open Questions" section of `PLAN.md`

## Changing Fixed Decisions
`SPEC.md` and `RULES.md` contain decisions both teammates agreed on. Do not edit these silently.
If you want to change one:
1. Message/call the other person first
2. Agree on the change
3. Commit the edit with a message explaining *why* (not just *what*)

## For AI Coding Assistants (Claude Code, Cursor, Copilot, Antigravity, etc.)
- Read `SPEC.md`, `RULES.md`, and `PLAN.md` before making changes.
- Do not modify `RULES.md` or `SPEC.md` without explicitly flagging it in your response.
- Follow the folder structure above exactly; do not invent new top-level folders.
