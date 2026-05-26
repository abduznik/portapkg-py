# Frequently Asked Questions

## What is portapkg for?

Portapkg helps you install Python packages on machines that **don't have
internet access** (air-gapped, classified, or strictly controlled
environments). You bundle the packages on an online machine, transfer them
via USB drive, then install offline.

## How is this different from `pip download`?

`pip download <package>` downloads wheels for your current platform only.
Portapkg downloads for **6 platforms × 5 Python versions** at once, so a
single bundle works on Windows, Linux, macOS, x86, and ARM.

Portapkg also gives you:

- A standalone `portapkg.py` installer (stdlib only, no dependencies)
- An `export` command that packages everything into one portable folder
- A `manifest.json` with metadata about the bundle

## Do I need to install portapkg on the offline machine?

**No.** The standalone `portapkg.py` file has zero dependencies — it only
uses the Python standard library and subprocess calls to pip. Copy it
alongside the `bundles/` folder and you're ready to install.

## Can I bundle for only one platform?

Yes. Use `--snapshot` to bundle for your current machine only, or
`--platforms win_amd64` to target a single specific platform.

## What if a wheel doesn't exist for my platform?

The bundler falls back to a **source distribution** (sdist). However, the
sdist may require a C compiler (`gcc`, `clang`, or MSVC) to build on the
target machine. If possible, prefer binary wheels by bundling on a machine
with the same architecture as the target.

## Can I install to a virtual environment?

Yes. Use the `--target` flag:

```bash
python portapkg.py install pyserial --target ./venv/Lib/site-packages
```

Or activate the virtual environment first and install normally — pip will
install into the active environment.

## Does portapkg work with conda?

No. Portapkg uses pip under the hood, so it only works with PyPI packages.
For conda environments, you can still use `portapkg.py` after activating
the conda environment — pip will install into the current environment.

## What Python versions are supported?

- **Bundling**: Python 3.9+
- **Installing**: Python 3.9+ (any machine with pip)
- **Bundled wheel coverage**: Python 3.9 through 3.13 (all 5 versions)

## Are the bundles compressed or encrypted?

No. Bundles are plain folders with standard `.whl` files inside. You can
inspect them, modify them, or add additional wheels manually. Zip the folder
to compress for transfer.

## What about packages with native extensions?

Packages like `numpy`, `pandas`, or `cryptography` have compiled native code
and publish **platform-specific wheels** (e.g., `numpy-1.26.0-cp312-cp312-win_amd64.whl`).
The bundler downloads the correct wheel for each platform automatically.

## Can I bundle packages that aren't on PyPI?

No. The bundler uses pip to resolve and download from PyPI. For private
packages, you'd need to add them manually to the `wheels/` directory and
update the `manifest.json`.

## How do I update a bundle?

```bash
portapkg update pyserial
```

This re-fetches all wheels for the bundle with the same options as `bundle`.
If the package has a newer version on PyPI, it'll be downloaded.

## Can I bundle multiple packages together in one folder?

Yes, use the `--name` flag with `export`:

```bash
portapkg bundle --packages pyserial,pyvisa
portapkg export --name mydev --packages pyserial,pyvisa
```

This creates a folder `mydev_abc123_2026-05-26/` with both bundles and
the standalone installer.
