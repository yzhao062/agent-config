# agent-config local rules

Hand-authored, cross-agent, never touched by bootstrap. Everything here is specific to working inside `agent-config`; the shared rules live in `AGENTS.md`, which is byte-identical to the `anywhere-agents` copy.

- The user is a computer scientist and professor working in machine learning and AI. Common tasks include research papers, funding proposals, scientific writing, and administrative writing.
- Preferred Python interpreter: the Miniforge `py312` environment (`%USERPROFILE%\miniforge3\envs\py312\python.exe` on Windows, `$HOME/miniforge3/envs/py312/bin/python` on macOS/Linux). Prefer `mamba` for install and create operations; fall back to `conda` only for commands mamba lacks.
- PyCharm: the `py312` conda environment is the default interpreter for new projects (File > New Projects Setup > Settings for New Projects > Python Interpreter). Existing clones point at it unless they need a project-specific venv.
- Fresh clone or new machine: read `ONBOARDING.md` at the repo root. It indexes `anywhere-agents.md` (the two-repo relationship), `../anywhere-agents/RELEASING.md` (release runbook), and `../anywhere-agents/CHANGELOG.md` (current version).
