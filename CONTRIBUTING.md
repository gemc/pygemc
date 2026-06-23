# Contributing to pygemc

Contributions to `pygemc` are welcome. Useful contributions include Python API improvements, documentation, examples, tests, bug reports, packaging fixes, and reproducible geometry or analyzer problems.

Keep changes focused and reviewable. A small pull request with clear motivation is easier to review and safer to merge than a broad rewrite.

## Before You Start

Open an issue before working on large changes, public APIs, command-line behavior, file formats, packaging, or behavior that affects the parent GEMC build. Small typo fixes, narrow documentation edits, and obvious bug fixes can go directly to a pull request.

For security vulnerabilities, do not open a public issue. Follow [`SECURITY.md`](SECURITY.md).

## Development Setup

Fork `gemc/pygemc` on GitHub, then clone your fork:

```shell
git clone https://github.com/<your-username>/pygemc.git
cd pygemc
```

Create and activate a virtual environment:

```shell
python3 -m venv ~/venv/pygemc
source ~/venv/pygemc/bin/activate
pip install -e ".[dev]"
```

## Test

Run the standalone Python tests:

```shell
pytest
```

Useful focused test commands:

```shell
pytest tests/test_cli.py
pytest tests/test_geometry.py
pytest -v
pytest -k "sqlite"
```

The standalone tests do not require Geant4 or a compiled `gemc` executable. If a change affects how `pygemc` is integrated into the main GEMC source build, also run the relevant Meson tests in `gemc/src`.

## Contribution Guidelines

- Match the style of the surrounding Python code.
- Prefer clear, local fixes over broad refactors.
- Add or update tests for behavior changes.
- Update README files, examples, and website documentation when user-facing behavior changes.
- Keep generated files, caches, virtual environments, and local IDE files out of commits.
- Do not mix unrelated cleanup with feature or bug-fix work.
- For geometry or PyVista visualization changes, include screenshots or links to generated scenes when that helps review.

## Commit Messages

Use short, imperative commit summaries:

```text
Fix sqlite material export
```

When the reasoning is not obvious, add a body explaining what changed and why. If the pull request closes an issue, include `Closes #123` in the pull request description.

## Pull Requests

Open a pull request from your fork to `gemc/pygemc`.

Before requesting review, check that:

- The title and description explain the change.
- Related issues are linked.
- Relevant tests or examples were run and listed.
- Documentation and examples were updated if needed.
- The pull request is focused on one topic.

Reviews may ask for changes to improve correctness, maintainability, performance, documentation, or test coverage.

## Communication

- General questions: open an issue.
- Security vulnerabilities: email **ungaro@jlab.org** instead of opening a public issue.
- Conduct concerns: email **ungaro@jlab.org** and see [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).

## Licensing and Citation

By contributing, you agree that your contributions are licensed under the Apache License, Version 2.0. See
[`LICENSE`](LICENSE).

If you use GEMC or `pygemc` in scientific work, cite:

> M. Ungaro, "Geant4 Monte-Carlo (GEMC) A database-driven simulation program," EPJ Web of Conferences 295, 05005 (2024). https://doi.org/10.1051/epjconf/202429505005
