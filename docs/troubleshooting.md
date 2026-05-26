# Troubleshooting

## "No compatible wheel found"

This means the bundle doesn't contain a wheel that matches your current OS,
architecture, or Python version.

**Solutions:**

- Bundle with `--snapshot` on a machine with the same OS/Python as the target
- Bundle with all default platforms (don't use `--platforms` filter on a
  platform the target machine doesn't match)
- Check the target machine's Python version: `python --version` — make sure
  it's one of the Python versions you bundled for (default: 3.9–3.13)

## "No manifest in ..."

The bundle directory is missing a `manifest.json` file.

**Solutions:**

- Delete the incomplete bundle and re-bundle
- Make sure the bundle completed without errors (check for "Bundle saved" message)

## "pip is not available"

The standalone `portapkg.py` uses pip under the hood for installation,
but pip isn't installed on the target machine.

**Solutions:**

- Install pip: `python -m ensurepip --upgrade`
- On some minimal Linux distributions, install the `python3-pip` package via
  the system package manager

## Multi-platform download warnings

When bundling, you may see warnings like:

```
pyvisa==1.16.2: no wheel available for win_amd64/39
```

This means the package doesn't publish wheels for that specific
platform/Python combination. A source distribution (sdist) is used instead,
which requires a C compiler on the target machine.

**Solutions:**

- These warnings are usually safe to ignore — pip will fall back to the sdist
- If installation fails on the target machine, try bundling with `--snapshot`
  on a machine identical to the target

## Large bundle sizes

Bundles with many dependencies (like `auto-py-to-exe` or `flet`) can be
large — up to hundreds of megabytes when bundling for all 6 platforms.

**Solutions:**

- Use `--platforms` to target only the platforms you need
- Use `--snapshot` to bundle for just your current machine
- Only bundle the specific packages you actually need, and skip heavy
  dev dependencies

## "No bundles found" after copying

You copied the `bundles/` folder to the offline machine, but `list` shows
nothing.

**Solutions:**

- Make sure the `bundles/` folder is in the same directory as `portapkg.py`
- Or set `PORTAPKG_BUNDLES_DIR` to point to the correct location
- Verify the folder structure looks like:
  ```
  bundles/
  └── yourpackage/
      ├── manifest.json
      └── wheels/
  ```

## Permission errors on Linux/macOS

The `portapkg.py` file needs execute permission to run directly.

**Solutions:**

- Run with Python: `python3 portapkg.py install <package>`
- Or make it executable: `chmod +x portapkg.py`

## Installation fails on the target machine

The `pip install` step fails even though compatible wheels exist.

**Solutions:**

- Make sure pip is up to date: `python -m pip install --upgrade pip`
- Check for missing system dependencies (e.g., `libffi-dev` for `cffi`-based
  packages)
- Try installing with verbose output: `python -m pip install --no-index
  --find-links ./wheels <package> --verbose`
