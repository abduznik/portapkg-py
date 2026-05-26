# Usage guide

## Installing portapkg

### From PyPI (recommended)

```bash
pip install portapkg
```

### From source

```bash
git clone https://github.com/abduznik/portapkg-py
cd portapkg-py
pip install -e ".[dev]"
```

### No install needed — use portapkg.py directly

The `portapkg.py` file is fully self-contained — stdlib only, zero
dependencies. You can use it for **both bundling and installing** without
running `pip install`:

```bash
# Bundle a package (works if pip is available)
python3 portapkg.py bundle instrumation

# List bundles
python3 portapkg.py list

# Show bundle details  
python3 portapkg.py info instrumation

# Export for distribution
python3 portapkg.py export instrumation
```

!!! tip "One file to rule them all"
    `portapkg.py` works on both the online machine (bundling) and the
    offline machine (installing). Just copy it alongside your `bundles/`
    folder and you're ready.

## Bundling packages

### Basic bundling

```bash
# Single package
portapkg bundle instrumation

# Multiple packages at once
portapkg bundle --packages pyserial,pyvisa,pyvisa-py
```

Single package downloads wheels for **6 platforms × 5 Python versions** (up to
30 downloads per dependency). Multi-package bundles each one in sequence.
The output goes to `./bundles/{package}/`.

### Specific platforms

```bash
portapkg bundle pyserial --platforms win_amd64,macosx_13_0_arm64
```

Valid platform tags:

| Platform | Tag |
|---|---|
| Windows x86_64 | `win_amd64` |
| Windows x86 | `win32` |
| Linux x86_64 | `manylinux2014_x86_64` |
| Linux ARM64 | `manylinux2014_aarch64` |
| macOS Apple Silicon | `macosx_13_0_arm64` |
| macOS Intel | `macosx_13_0_x86_64` |

### Snapshot mode (single platform)

```bash
portapkg bundle instrumation --snapshot
```

Downloads wheels for your **current machine only**. Faster and more reliable,
but the bundle only works on machines with the same OS and architecture.

### Custom bundle directory

```bash
PORTAPKG_BUNDLES_DIR=/path/to/bundles portapkg bundle instrumation
```

### List and inspect bundles

```bash
# List all bundles
portapkg list

# Show details of a specific bundle
portapkg info instrumation
```

### Update bundles

```bash
# Re-fetch a single bundle with all platforms
portapkg update instrumation

# Re-fetch multiple bundles at once
portapkg update --packages pyserial,pyvisa

# Re-fetch with specific platforms
portapkg update instrumation --platforms win_amd64,linux_x86_64

# Re-fetch as snapshot
portapkg update instrumation --snapshot
```

### Export a bundle for distribution

```bash
# Export the bundle + portapkg.py into a portable folder
portapkg export instrumation

# Export to a specific directory
portapkg export instrumation --output ./dist
```

This creates a timestamped folder like `instrumation_a3f2e6_2026-05-26/`
containing `portapkg.py` and the `bundles/` folder — ready to zip up or
copy to a USB drive.

## Installing offline

Copy the `bundles/` folder and `portapkg.py` to the offline machine.

### List available bundles

```bash
python portapkg.py list
```

### Install one or more packages

```bash
# Single package
python portapkg.py install instrumation

# Multiple packages at once
python portapkg.py install pyserial pyvisa flet

# Install all available bundles
python portapkg.py install --all
```

### Install to a custom path

```bash
python portapkg.py install instrumation --target ./venv/Lib/site-packages
```

### Custom bundle directory

```bash
PORTAPKG_BUNDLES_DIR=/path/to/bundles python portapkg.py list
PORTAPKG_BUNDLES_DIR=/path/to/bundles python portapkg.py install instrumation
```

## Typical workflow

| Online machine | USB stick | Offline machine |
|---|---|---|
| `portapkg bundle pyserial` | `bundles/` folder | `python portapkg.py list` |
| `portapkg bundle pyvisa` | `portapkg.py` file | `python portapkg.py install pyserial` |
| `portapkg export pyserial` | `pkg_abc123_2026-05-26/` folder | unzip → `python portapkg.py install pyserial` |
| → bundles ready in `./bundles/` | Copy both | → installs from local wheels |

## Using portapkg.py without pip install

You can use the standalone `portapkg.py` from the source repository directly
for **both bundling and installing** — no `pip install` required:

```bash
git clone https://github.com/abduznik/portapkg-py
cd portapkg-py

# Bundle a package (needs pip available)
python3 portapkg.py bundle instrumation

# Export for distribution
python3 portapkg.py export instrumation

# On the offline machine:
python3 portapkg.py install instrumation
```

`portapkg.py` is fully self-contained (stdlib only). The `bundle` and `export`
commands delegate to pip under the hood, so they need pip available on the
machine — but no portapkg-specific dependencies are needed.
