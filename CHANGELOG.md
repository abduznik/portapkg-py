# Changelog

## [0.3.3] — 2026-09-16

### Added

- **`--json` flag** on `portapkg list` and `portapkg info`: machine-readable
  output for scripting and AI coding agents.
- **Inline `--help` examples**: every subcommand (and the top-level
  `portapkg --help`) now includes copy-pasteable usage examples, so the CLI
  is self-documenting without needing the README.

### Changed

- `portapkg info` now returns exit code `1` when the bundle or its manifest
  is missing (previously returned `0`/`None` on this error path).

### Fixed

- Pinned `ruff` to `0.16.7` in CI and dev dependencies (was previously
  unpinned/floor-only, so `pip install ruff` would silently pick up newer
  releases with different default rules and break CI without any code
  change).
- Resolved lint findings surfaced by the newer ruff release: explicit
  `check=False` on `subprocess.run` calls, merged `str.startswith()` tuple
  calls, timezone-aware `datetime.now()`, sorted imports/`__all__`, and
  marked `portapkg.py`'s shebang executable.

## [0.3.0] — 2026-05-26

### Added

- **Layered download fallback** (`fetch.py`): Four-layer strategy when
  the exact binary wheel is unavailable:
  - Layer 3: Unconstrained sdist download (`--no-binary :all:` without
    platform restrictions) — catches sdist-only packages like `Eel`.
  - Layer 4: Version bump — queries `pip index versions` and tries newer
    releases with binary wheel coverage.
- **Cross-platform conditional dependency resolution** (`resolver.py`):
  Scans every downloaded wheel's METADATA for `Requires-Dist` lines with
  `sys_platform` / `platform_system` / `implementation_name` markers.
  Evaluates them against each target platform using `packaging.markers`
  and recursively resolves any missing deps.
- **`--python-versions` CLI flag**: `portapkg bundle <pkg> --python-versions 313`
  narrows downloads to specific Python versions instead of all five.

### Fixed

- `_wheel_exists` now checks **both** platform tag and Python tag — no
  more false matches where a `cp39` wheel blocked a `cp313` download.
- METADATA parsing handles RFC 822 line folding (continuation lines with
  leading whitespace).
- Marker evaluation no longer strips internal quotes via `.strip('"')`,
  which was silently breaking conditions like `sys_platform == "win32"`.

### Changed

- `resolve_dependencies()` accepts a `platforms` parameter and performs
  a second pass for each target platform to catch conditional deps.

## [0.2.0] — 2026-05-25

### Added

- Multi-package bundle support (`--packages` flag).
- `--all` flag for offline installer (`portapkg.py install --all`).
- `testing_grounds/` directory for export sandbox.

### Fixed

- Various bundler and installer bug fixes.

## [0.1.0] — 2026-05-23

### Added

- Initial release.
- `portapkg bundle` — multi-platform wheel bundler.
- `portapkg export` — portable folder export with standalone installer.
- `portapkg list` / `portapkg info` — bundle inspection.
- `portapkg.py` — stdlib-only offline installer.
- Tests: 116 tests across CLI, fetch, resolver, installer, platform, manifest.
