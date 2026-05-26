# Standalone script (`portapkg.py`)

The `portapkg.py` file is a **fully self-contained** offline installer that
uses only the Python standard library (plus `pip` via subprocess). It has
zero third-party dependencies.

## Why a standalone script?

- **No pip install needed** — just copy the file and run it
- **Works everywhere** — any machine with Python 3.9+ and pip
- **Single file** — easy to distribute, audit, or modify
- **Same bundle format** — compatible with bundles created by the full CLI

## Usage

```bash
# Copy portapkg.py alongside your bundles/ folder
# Then on the offline machine:

# List available bundles
python portapkg.py list

# Install a single package
python portapkg.py install instrumation

# Install multiple packages at once
python portapkg.py install pyserial pyvisa flet

# Install all available bundles
python portapkg.py install --all

# Install to a custom path
python portapkg.py install instrumation --target ./venv/Lib/site-packages
```

## How it works

1. Reads the bundle's `manifest.json` to understand the package structure
2. Scans the `wheels/` directory for wheels compatible with the current
   platform and Python version
3. Runs `pip install --no-index --find-links <wheels_dir> <package>`
   to install from local files only

## Platform detection

The script detects the current OS and CPU architecture to select
compatible wheels:

| Machine | Platform reported |
|---|---|
| Windows x86_64 | `win_amd64` |
| Windows x86 | `win32` |
| Linux x86_64 | `linux_x86_64` |
| Linux ARM64 | `linux_aarch64` |
| macOS Apple Silicon | `macosx_13_0_arm64` |
| macOS Intel | `macosx_13_0_x86_64` |

## Environment variables

- `PORTAPKG_BUNDLES_DIR` — override the bundle directory (default: `./bundles/`)
