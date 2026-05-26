# Development

## Project structure

```
portapkg/
├── portapkg.py                ← standalone offline installer (stdlib only)
├── portapkg/
│   ├── __init__.py            ← version
│   ├── cli.py                 ← entrypoint: bundle/list/info/update
│   ├── bundler/
│   │   ├── fetch.py           ← multi-platform wheel download
│   │   ├── manifest.py        ← manifest.json read/write
│   │   └── resolver.py        ← dependency resolution
│   └── installer/
│       ├── install.py         ← offline install logic
│       └── platform.py        ← OS/arch/python detection
├── tests/                     ← pytest test suite
├── docs/                      ← documentation site (MkDocs)
├── pyproject.toml             ← packaging & tool config
└── .github/workflows/         ← CI / release / docs workflows
```

## Setup

```bash
git clone https://github.com/abduznik/portapkg-py
cd portapkg-py

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Install docs dependencies (optional)
pip install mkdocs mkdocs-material
```

## Running tests

```bash
# Run all tests
pytest

# With coverage
pytest --cov=portapkg --cov-report=term-missing

# Run a specific test file
pytest tests/test_platform.py

# Run a specific test
pytest tests/test_platform.py::TestParseWheelFilename
```

## Code style

This project uses [Ruff](https://docs.astral.sh/ruff/) for linting.

```bash
pip install ruff
ruff check portapkg/ tests/ portapkg.py
```

## Building documentation

```bash
# Preview locally
mkdocs serve

# Build static site
mkdocs build
```

The documentation is automatically deployed to GitHub Pages on push to `main`
via `.github/workflows/docs.yml`.

## Making a release

1. Bump the version in `portapkg/__init__.py` and `pyproject.toml`
2. Commit and tag: `git tag v0.x.x && git push --tags`
3. Trigger the [Publish workflow](https://github.com/abduznik/portapkg-py/actions/workflows/publish.yml)
   on GitHub, specifying the version tag

The workflow builds wheels + sdist, publishes to PyPI, and creates a
GitHub Release with the artifacts attached.

## Design principles

- **Stdlib only** — no third-party imports anywhere in the runtime code
- **Single-file fallback** — `portapkg.py` must work with nothing but Python
  and pip
- **Pip as engine** — all heavy lifting (download, resolve, install) delegates
  to pip; portapkg just orchestrates
- **Clear errors** — every failure mode has a human-readable message with a
  suggested fix
