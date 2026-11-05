Rules:

- Record all material implementation progress and completed phases in PROGRESS.md
- For substantial new work, define the scope and acceptance criteria before implementation
- commit and push to GitHub after every Phase Completed for code review
- Stop development for every Phase Completed for code review

Validation (before every commit that touches `shaders/` or `tools/`):

- `python tools/validate_wrappers.py`
- `python tools/validate_profiles.py`
- `python tools/validate_perf1.py`
- `python tools/validate_compile.py --baseline HEAD`. Add `--extended` when a change touches code paths that no profile enables (for example `BLOOMY_FOG`, `DOF`, `VANILLA_SUN` or histogram exposure). glslang is at `C:\Users\markj\.local\bin\glslang.exe`.
- `git diff --check`
- Record what was run and its result in PROGRESS.md. These are static and standalone-compile checks only: never claim in-game visuals or a speed-up without a test in the client.

DO NOT USE AGY DEVELOPER SKILL
