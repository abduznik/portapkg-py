# Real-world example

This walkthrough shows a complete workflow: a developer needs to install
Python instrumentation packages (`pyvisa`, `pyserial`, `pyvisa-py`) and a
GUI app (`flet`) on an **air-gapped Windows machine** in a lab environment.

## Scenario

- **Online machine**: macOS (Apple Silicon) — has internet
- **Offline machine**: Windows 10 (x86_64) — no internet, no PyPI access
- **Goal**: Get `pyvisa`, `pyserial`, `pyvisa-py`, and `flet` onto the
  Windows machine with all dependencies

## Step 1 — Bundle on the online machine

```bash
# Install portapkg (one-time)
pip install portapkg

# Bundle all 4 packages at once
portapkg bundle --packages pyserial,pyvisa,pyvisa-py,flet
```

This downloads wheels for **6 platforms × 5 Python versions** per dependency.
Output in `./bundles/`:

```
bundles/
├── pyserial/          (1 dep,   1 wheel)
├── pyvisa/            (2 deps,  2 wheels)
├── pyvisa-py/         (3 deps,  3 wheels)
└── flet/              (11 deps, 16 wheels)
```

!!! tip "Multi-platform means one bundle serves all machines"
    Even though we bundled on macOS, the downloaded wheels include
    `win_amd64` variants — so the same bundle folder works on Windows.

## Step 2 — Export to a portable folder

```bash
portapkg export --name lab-pc --packages pyserial,pyvisa,pyvisa-py,flet
```

Creates:

```
lab-pc_a3f2e6_2026-05-26/
├── portapkg.py
└── bundles/
    ├── pyserial/
    ├── pyvisa/
    ├── pyvisa-py/
    └── flet/
```

Now zip the folder and copy it to a USB drive.

## Step 3 — Transfer via USB

```bash
# On the online machine — zip it up
zip -r lab-pc_a3f2e6_2026-05-26.zip lab-pc_a3f2e6_2026-05-26/

# Copy to USB drive, walk over to the Windows machine
```

## Step 4 — Install on the offline Windows machine

```powershell
# Copy the zip onto the Windows machine and unzip
# Open PowerShell or Command Prompt in the extracted folder

cd lab-pc_a3f2e6_2026-05-26

# List what's available
python portapkg.py list

# Output:
#   pyserial   v3.5   (2026-05-26)
#   pyvisa     v1.16.2 (2026-05-26)
#   pyvisa-py  v0.8.1 (2026-05-26)
#   flet       v0.85.2 (2026-05-26)

# Install everything
python portapkg.py install pyserial
python portapkg.py install pyvisa
python portapkg.py install pyvisa-py
python portapkg.py install flet
```

!!! tip "No internet needed"
    Each `install` command runs `pip install --no-index --find-links <wheels>`
    — pip installs from the local `.whl` files. Zero network traffic.

## Alternative: Install into a virtual environment

```powershell
# Create and activate a venv
python -m venv .venv
.venv\Scripts\activate

# Install from the local bundles
python portapkg.py install pyvisa
python portapkg.py install flet
```

## Another scenario: Shipping a single-file tool

You have a Python script `scan.py` that depends on `pyserial` and `pyvisa`.
You want to hand it to a colleague who has no internet.

```bash
# On your machine:
portapkg bundle --packages pyserial,pyvisa
portapkg export --name scan-tool --packages pyserial,pyvisa

# Now the folder scan-tool_abc123_2026-05-26/ has everything.
# Drop your script in there:

cp scan.py scan-tool_abc123_2026-05-26/
```

Hand them the folder on a USB stick:

```bash
cd scan-tool_abc123_2026-05-26
python portapkg.py install pyserial
python portapkg.py install pyvisa
python scan.py
```

## What to watch out for

| Issue | How to handle |
|---|---|
| Package has native extensions | Bundle on a machine with the **same OS architecture** as the target, or use `--snapshot` |
| Very large bundles (100+ MB) | Use `--platforms win_amd64` to target only Windows, skipping macOS/Linux wheels |
| Offline machine has old Python | Check the bundled Python versions — default covers 3.9–3.13 |
| `pip` not on the offline machine | Run `python -m ensurepip --upgrade` first |
| Need conda-compatible install | Activate the conda environment first, then use `portapkg.py install` — pip installs into the active env |

## Summary

```
Online machine                        USB stick                  Offline machine
───────────────                      ──────────                  ───────────────
pip install portapkg                                              
portapkg bundle --packages ...       bundles/                    python portapkg.py list
portapkg export --name lab-pc ...    lab-pc_a3f2e6_2026-05-26/   python portapkg.py install pyvisa
zip -r lab-pc.zip lab-pc_*/          lab-pc.zip → USB            python scan.py
```
