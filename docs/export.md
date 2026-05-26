# Exporting bundles

The `export` command packages one or more bundles together with the standalone
installer into a single portable folder — ready to copy to a USB drive and ship.

## Why export?

Instead of manually copying `portapkg.py` and the `bundles/` directory, `export`
creates a tidy, timestamped folder that includes everything the offline machine
needs:

```
mydev_a3f2e6_2026-05-26/
├── portapkg.py          ← standalone installer (stdlib only)
└── bundles/
    ├── pyserial/
    │   ├── manifest.json
    │   └── wheels/
    └── pyvisa/
        ├── manifest.json
        └── wheels/
```

## Usage

You must have already [bundled](usage.md#bundling-packages) the packages before
exporting them.

### Export a single package

```bash
portapkg export pyserial
# Creates: pyserial_abc123_2026-05-26/
```

### Export multiple packages under a custom name

```bash
portapkg export --name mydev --packages pyserial,pyvisa,pyvisa-py
# Creates: mydev_abc123_2026-05-26/
```

### Export multiple packages with auto-generated name

```bash
portapkg export --packages pyserial,pyvisa
# Creates: bundle_abc123_2026-05-26/
```

### Export to a specific directory

```bash
portapkg export --name mydev --packages pyserial,pyvisa --output ./dist
```

## How the folder is named

The export folder is named automatically as:

```
{name}_{short_id}_{today_date}
```

| Part | Description | Example |
|---|---|---|
| `name` | The export name (`--name`, package, or `"bundle"`) | `mydev` |
| `short_id` | A random 6-character hex string | `a3f2e6` |
| `today_date` | Today's date in ISO format | `2026-05-26` |

The name comes from (in order of priority):

1. `--name` flag (always used if provided)
2. Single package name (if exporting one package)
3. `"bundle"` (fallback for multi-package exports without `--name`)

## What's inside

| File / folder | Purpose |
|---|---|
| `portapkg.py` | The standalone offline installer — no dependencies, stdlib only |
| `bundles/{package}/` | Each package's bundle manifest and wheels |
| `bundles/{package}/manifest.json` | Metadata (version, deps, platform info) |
| `bundles/{package}/wheels/` | All downloaded wheel files |

## Using the exported folder on an offline machine

```bash
# Copy the entire folder to the offline machine, then:

cd mydev_abc123_2026-05-26/

# List available bundles
python portapkg.py list

# Install a package (no internet needed)
python portapkg.py install pyserial
python portapkg.py install pyvisa
```

## Using portapkg.py from source as an alternative

If you don't want to `pip install` portapkg on the online machine, you can
use the `portapkg.py` file directly from the source repository:

```bash
# Clone the repo
git clone https://github.com/abduznik/portapkg-py
cd portapkg-py

# Bundle and export without pip install
python3 portapkg.py bundle pyserial
python3 portapkg.py bundle pyvisa
python3 portapkg.py export --name mydev --packages pyserial,pyvisa
```

!!! tip "No install required"
    The `portapkg.py` script is fully self-contained. Use it for **bundling**
    (online), **exporting**, and **installing** (offline).

## Environment variables

- `PORTAPKG_BUNDLES_DIR` — override the bundle directory (default: `./bundles/`)
