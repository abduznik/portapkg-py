# Changelog

## v0.3.0 (2026-05-26)

### Improvements

- **Multi-package install**: `python portapkg.py install pkg1 pkg2 pkg3` —
  install multiple bundles in one command.
- **`--all` flag for install**: `python portapkg.py install --all` — install
  every available bundle in one go.
- **`testing_grounds/` folder**: Convenient sandbox directory for exports
  and offline testing, gitignored.

## v0.2.0 (2026-05-26)

### Bug fixes

- **BUNDLES_DIR resolution**: Now uses `os.getcwd()` + `PORTAPKG_BUNDLES_DIR`
  env var instead of working relative to `__file__`, so it works correctly
  regardless of how the tool is invoked.
- **macOS platform matching**: ARM64 (`arm64`) vs x86_64 (`x86_64`) are now
  properly distinguished — no longer matches both architectures.
- **Source dist fallback**: No longer uses `--no-deps` when falling back to
  source distributions. Keeps `--platform` and `--python-version` for
  correct fallback behavior.
- **Wheel deduplication**: `_wheel_exists()` now checks compatibility against
  the requested platform before skipping — a `win_amd64` wheel won't cause a
  `linux_x86_64` download to be skipped.
- **Wheel filename parsing**: Uses proper `{name}-{version}-{tags}` structure
  for all wheel parsing functions.

### Improvements

- **`--packages` flag**: Bundle or update multiple packages in one command
  with `portapkg bundle --packages pkg1,pkg2,pkg3`.
- **`export` command**: New `portapkg export` packages bundles + standalone
  installer into a portable folder with a timestamped name.
- **`--name` flag for export**: Custom folder name for exported bundles.
- **Multi-package export**: Export multiple bundles into a single folder
  with `portapkg export --name mydev --packages pkg1,pkg2`.
- **Documentation site**: Full MkDocs site with usage guide, CLI reference,
  FAQ, troubleshooting, and development docs.
- **Blue theme**: MkDocs-material documentation with slate scheme and
  blue/light-blue accent colors.
- **Documented `PORTAPKG_BUNDLES_DIR`**: Environment variable is now
  documented in README and docs.

## v0.1.0 (2026-05-22)

Initial release.

- `bundle` — multi-platform package bundling
- `list` — show all bundles
- `info` — show bundle details
- `install` — offline installation via `pip install --no-index`
- `update` — re-fetch a bundle
- Standalone `portapkg.py` — zero-dependency installer
- 6 platforms × 5 Python versions support
- Snapshot mode for single-platform bundling
