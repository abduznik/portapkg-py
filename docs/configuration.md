# Configuration

## Environment variables

### `PORTAPKG_BUNDLES_DIR`

Overrides the default bundle storage directory.

**Default:** `./bundles/` (relative to the current working directory)

**Example:**

```bash
export PORTAPKG_BUNDLES_DIR=/data/portapkg/bundles
portapkg bundle instrumation
# stores in /data/portapkg/bundles/instrumation/
```

Both the CLI (`portapkg`) and the standalone script (`portapkg.py`) respect
this environment variable.

## Default platforms and Python versions

When no `--platforms` flag is given, the bundler uses all 6 platforms:

| Platform | Tag |
|---|---|
| Windows x86_64 | `win_amd64` |
| Windows x86 | `win32` |
| Linux x86_64 | `manylinux2014_x86_64` |
| Linux ARM64 | `manylinux2014_aarch64` |
| macOS Apple Silicon | `macosx_13_0_arm64` |
| macOS Intel | `macosx_13_0_x86_64` |

And all 5 Python versions: **3.9, 3.10, 3.11, 3.12, 3.13**

## Bundle structure

A typical bundle looks like this:

```
bundles/
└── instrumation/
    ├── manifest.json
    └── wheels/
        ├── instrumation-0.3.0-py3-none-any.whl
        ├── pyserial-3.5-py2.py3-none-any.whl
        └── ...
```

### `manifest.json`

Contains metadata about the bundle:

```json
{
  "name": "instrumation",
  "version": "0.3.0",
  "date_bundled": "2026-05-26T12:00:00",
  "source_platform": "macosx_13_0_arm64",
  "source_python": "314",
  "dependencies": [
    {"name": "instrumation", "version": "0.3.0"},
    {"name": "pyserial", "version": "3.5"}
  ]
}
```
