## Support This Project

> **All projects made with passion** 💙

[![Sponsor me](https://img.shields.io/badge/❤️%20Sponsor-GitHub-red?style=for-the-badge)](https://github.com/sponsors/abduznik)  

# portapkg

[![PyPI](https://img.shields.io/pypi/v/portapkg?color=brightgreen)](https://pypi.org/project/portapkg/)
[![License](https://img.shields.io/pypi/l/portapkg)](LICENSE)
[![PyPI Downloads](https://static.pepy.tech/personalized-badge/portapkg?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads)](https://pepy.tech/projects/portapkg)
[![CI](https://img.shields.io/github/actions/workflow/status/abduznik/portapkg-py/.github/workflows/test.yml?branch=main&label=CI)](https://github.com/abduznik/portapkg-py/actions/workflows/test.yml)
[![Last commit](https://img.shields.io/github/last-commit/abduznik/portapkg-py)](https://github.com/abduznik/portapkg-py/commits/main)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

Portable, offline-friendly Python package bundler and installer.

Bundle a package + all its dependencies on an online machine, then install
on an air-gapped machine with nothing but Python and pip.

## Quick start

### Online machine — bundle a package

```bash
# Install portapkg
pip install portapkg

# Bundle a package for all 6 platforms + 5 Python versions
portapkg bundle instrumation

# Bundle for specific platforms only
portapkg bundle instrumation --platforms win_amd64,macosx_13_0_arm64

# Bundle for specific platforms and python versions (faster!)
portapkg bundle instrumation --platforms win_amd64 --python-versions 313

# Bundle a snapshot of the current environment (single platform, most reliable)
portapkg bundle instrumation --snapshot

# List all bundles
portapkg list

# Show bundle details
portapkg info instrumation

# Update / re-fetch a bundle
portapkg update instrumation
```

Output bundle structure:

```
bundles/
└── instrumation/
    ├── manifest.json
    └── wheels/
        ├── instrumation-0.3.0-py3-none-any.whl
        ├── pyserial-3.5-py2.py3-none-any.whl
        └── ...
```

### Offline machine — install from USB

Copy the `bundles/` folder and `portapkg.py` to a USB drive, then on the
offline machine:

```bash
# List available bundles
python portapkg.py list

# Install a bundled package (works without internet)
python portapkg.py install instrumation

# Install to a custom path
python portapkg.py install instrumation --target ./myenv/Lib/site-packages
```

The `portapkg.py` file is fully self-contained — stdlib only, no dependencies.

## How it works

1. **Dependency resolution**: `pip download <package>` resolves the full
   transitive dependency tree using pip's own resolver. For multi-platform
   bundles, the resolver also scans each wheel's METADATA for
   platform-conditional deps (e.g. `pefile; sys_platform == "win32"`) and
   recursively resolves any missing deps found.
2. **Multi-platform fetch**: For each dependency, wheels are downloaded
   across multiple platforms × Python versions using
   `pip download --platform --python-version --only-binary=:all:`.
3. **Layered fallback strategy**:
   - **Layer 1**: Exact binary wheel for the target platform/Python.
   - **Layer 2**: Platform-constrained source distribution.
   - **Layer 3**: Unconstrained source distribution — catches sdist-only
     packages like `Eel`.
   - **Layer 4**: Version bump — queries `pip index versions` for newer
     releases with binary wheel coverage (e.g. `msgpack` gaining cp313
     wheels in a later patch).
4. **Offline install**: `pip install --no-index --find-links <wheels_dir>`
   installs from local files only.

## Development

### Setup

```bash
# Clone the repo
git clone https://github.com/your-org/portapkg-py && cd portapkg-py

# Install in editable mode with dev dependencies
pip install -e ".[dev]"
```

### Running tests

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=portapkg --cov-report=term-missing

# Run a specific test file
pytest tests/test_platform.py

# Run a specific test
pytest tests/test_platform.py::TestParseWheelFilename

# Run linter
pip install ruff
ruff check portapkg/ tests/ portapkg.py
```

### Project structure

```
portapkg/
├── portapkg.py                ← standalone offline installer (stdlib only)
├── portapkg/
│   ├── cli.py                 ← entrypoint: bundle/list/info/update
│   ├── bundler/
│   │   ├── fetch.py           ← multi-platform wheel download
│   │   ├── resolver.py        ← dependency resolution (pip download)
│   │   └── manifest.py        ← manifest.json read/write
│   └── installer/
│       ├── install.py         ← offline install logic
│       └── platform.py        ← OS/arch/python detection
├── tests/                     ← pytest test suite
├── pyproject.toml             ← packaging & tool config
└── .github/workflows/         ← CI / release workflows
```

### CI / CD

- **CI** (`.github/workflows/test.yml`): runs on push/PR to `main` — tests
  across 3 OS × 5 Python versions, plus linting with ruff.
- **Release** (`.github/workflows/publish.yml`): manual `workflow_dispatch`
  — specify a version tag, and it builds wheels + sdist and creates a
  GitHub Release with the artifacts attached.

## Platform matrix

| Platform                  | Tag                          |
|---------------------------|------------------------------|
| Windows x86_64            | `win_amd64`                  |
| Windows x86               | `win32`                      |
| Linux x86_64              | `manylinux2014_x86_64`       |
| Linux ARM64               | `manylinux2014_aarch64`      |
| macOS Apple Silicon       | `macosx_13_0_arm64`          |
| macOS Intel               | `macosx_13_0_x86_64`         |

Python versions: 3.9, 3.10, 3.11, 3.12, 3.13

## Error handling

- **Missing binary wheel**: warns and falls back through layered strategy
  (source dist → unconstrained sdist → version bump)
- **Platform-conditional deps**: automatically resolved by scanning wheel
  METADATA for `Requires-Dist` lines with `sys_platform` / `platform_system`
  / `implementation_name` markers, evaluated with `packaging.markers`.
- **No compatible wheel** on offline machine: clear human-readable error
  with suggested fix (`--snapshot`)
- **Missing pip**: detected before any install attempt
- **Missing bundle**: tells you which directory to copy

## Configuration

### `PORTAPKG_BUNDLES_DIR`

By default, bundles are stored in `./bundles/` relative to the current working
directory. You can override this with the `PORTAPKG_BUNDLES_DIR` environment
variable:

```bash
export PORTAPKG_BUNDLES_DIR=/path/to/bundles
portapkg bundle instrumation   # stores in /path/to/bundles/instrumation/
```

Both the CLI (`portapkg`) and the standalone script (`portapkg.py`) respect
this environment variable.

## Requirements

- **Online machine**: Python 3.9+, pip (any version)
- **Offline machine**: Python 3.9+, pip (any version)
- **No third-party packages** are used by portapkg itself — stdlib only.
