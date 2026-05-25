import argparse
import os

from portapkg.bundler.fetch import download_wheels, download_single_platform
from portapkg.bundler.manifest import read_manifest, write_manifest, build_manifest
from portapkg.bundler.resolver import resolve_dependencies, freeze_snapshot
from portapkg.installer.platform import (
    DEFAULT_PLATFORMS,
    DEFAULT_PYTHON_VERSIONS,
    detect_current_platform,
    detect_current_python,
)


BUNDLES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "bundles")
BUNDLES_DIR = os.path.abspath(BUNDLES_DIR)


def _ensure_bundles_dir():
    os.makedirs(BUNDLES_DIR, exist_ok=True)


def _get_bundle_dir(package):
    return os.path.join(BUNDLES_DIR, package)


def _print_wheel_summary(wheels_dir):
    if not os.path.isdir(wheels_dir):
        return
    whls = [f for f in os.listdir(wheels_dir) if f.endswith(".whl")]
    print(f"  Total wheel files: {len(whls)}")


def cmd_bundle(args):
    _ensure_bundles_dir()
    if args.snapshot:
        _bundle_snapshot(args.package)
    else:
        platforms = args.platforms.split(",") if args.platforms else DEFAULT_PLATFORMS
        _bundle_multi(args.package, platforms, DEFAULT_PYTHON_VERSIONS)


def _bundle_multi(package, platforms, python_versions):
    print(f"Resolving dependencies for {package}...")
    deps = resolve_dependencies(package)
    print(f"Found {len(deps)} package(s): {', '.join(deps.keys())}")

    pkg_key = package.lower().replace("_", "-")
    pkg_version = deps.get(pkg_key)
    if not pkg_version:
        raise RuntimeError(f"Could not determine version for {package}")

    bundle_dir = _get_bundle_dir(package)
    wheels_dir = os.path.join(bundle_dir, "wheels")
    os.makedirs(wheels_dir, exist_ok=True)

    all_failures = {}
    dep_entries = []

    for dep_name, dep_version in deps.items():
        print(f"  Fetching {dep_name}=={dep_version} ...")
        successes, failures = download_wheels(
            dep_name, dep_version, wheels_dir, platforms, python_versions
        )
        if failures:
            all_failures[dep_name] = failures
        dep_entries.append({
            "name": dep_name,
            "version": dep_version,
        })

    source_plat = detect_current_platform()
    source_py = detect_current_python()
    manifest = build_manifest(package, pkg_version, dep_entries, source_plat, source_py)
    write_manifest(bundle_dir, manifest)

    print(f"\nBundle saved to {bundle_dir}")
    _print_wheel_summary(wheels_dir)

    if all_failures:
        print(f"\nWarnings: {len(all_failures)} package(s) had missing platforms")
        for pkg, fails in all_failures.items():
            for plat, pyver, _ in fails:
                print(f"  {pkg}: no wheel for {plat}/py{pyver}")


def _bundle_snapshot(package):
    print("Taking snapshot of current environment...")
    frozen = freeze_snapshot()
    print(f"Found {len(frozen)} packages in environment")

    deps = resolve_dependencies(package)
    print(f"Resolved dependency tree for {package}: {len(deps)} package(s)")

    bundle_dir = _get_bundle_dir(package)
    wheels_dir = os.path.join(bundle_dir, "wheels")
    os.makedirs(wheels_dir, exist_ok=True)

    dep_entries = []
    for dep_name in deps:
        dep_version = frozen.get(dep_name)
        if not dep_version:
            print(f"  WARNING: {dep_name} not in freeze, using resolved version {deps[dep_name]}")
            dep_version = deps[dep_name]

        print(f"  Downloading {dep_name}=={dep_version}...")
        download_single_platform(dep_name, dep_version, wheels_dir)
        dep_entries.append({
            "name": dep_name,
            "version": dep_version,
        })

    pkg_key = package.lower().replace("_", "-")
    pkg_version = frozen.get(pkg_key) or deps.get(pkg_key)

    source_plat = detect_current_platform()
    source_py = detect_current_python()
    manifest = build_manifest(package, pkg_version, dep_entries, source_plat, source_py)
    write_manifest(bundle_dir, manifest)

    print(f"\nSnapshot bundle saved to {bundle_dir}")
    _print_wheel_summary(wheels_dir)


def cmd_list(args):
    if not os.path.isdir(BUNDLES_DIR):
        print("No bundles directory found.")
        return

    bundles = sorted(
        d for d in os.listdir(BUNDLES_DIR)
        if os.path.isdir(os.path.join(BUNDLES_DIR, d))
    )

    if not bundles:
        print("No bundles found.")
        return

    print(f"Bundles ({len(bundles)}):\n")
    for name in bundles:
        manifest = read_manifest(os.path.join(BUNDLES_DIR, name))
        if manifest:
            whl_dir = os.path.join(BUNDLES_DIR, name, "wheels")
            wc = len([f for f in os.listdir(whl_dir) if f.endswith(".whl")]) if os.path.isdir(whl_dir) else 0
            print(f"  {name}")
            print(f"    Version: {manifest.get('version', '?')}")
            print(f"    Bundled: {manifest.get('date_bundled', '?')}")
            print(f"    Wheels:  {wc}\n")
        else:
            print(f"  {name}  (no manifest)")


def cmd_info(args):
    bundle_dir = _get_bundle_dir(args.package)
    if not os.path.isdir(bundle_dir):
        print(f"Bundle '{args.package}' not found.")
        return

    manifest = read_manifest(bundle_dir)
    if not manifest:
        print(f"No manifest in {bundle_dir}")
        return

    whl_dir = os.path.join(bundle_dir, "wheels")
    wheel_files = sorted(f for f in os.listdir(whl_dir) if f.endswith(".whl")) if os.path.isdir(whl_dir) else []

    print(f"Package:  {manifest.get('name', '?')}")
    print(f"Version:  {manifest.get('version', '?')}")
    print(f"Bundled:  {manifest.get('date_bundled', '?')}")
    print(f"Source:   {manifest.get('source_platform', '?')} / py{manifest.get('source_python', '?')}")
    print(f"Dependencies ({len(manifest.get('dependencies', []))}):")
    for dep in manifest["dependencies"]:
        print(f"  - {dep['name']}=={dep['version']}")
    print(f"Wheels ({len(wheel_files)}):")
    for wf in wheel_files:
        print(f"  {wf}")


def cmd_update(args):
    _ensure_bundles_dir()
    if args.snapshot:
        _bundle_snapshot(args.package)
    else:
        platforms = args.platforms.split(",") if args.platforms else DEFAULT_PLATFORMS
        _bundle_multi(args.package, platforms, DEFAULT_PYTHON_VERSIONS)


def main():
    parser = argparse.ArgumentParser(
        prog="portapkg",
        description="Portable Python package bundler and installer",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_bundle = sub.add_parser("bundle", help="Bundle a package for offline install")
    p_bundle.add_argument("package", help="Package name")
p_bundle.add_argument(
    "--platforms",
    help=(
        "Comma-separated platform tags. "
        f"Valid: {', '.join(DEFAULT_PLATFORMS)}. "
        f"Default: all of them."
    ),
)
    p_bundle.add_argument("--snapshot", action="store_true", help="Snapshot current env (single-platform)")
    p_bundle.set_defaults(func=cmd_bundle)

    p_list = sub.add_parser("list", help="List all bundles")
    p_list.set_defaults(func=cmd_list)
p_update.add_argument(
    "--platforms",
    help=(
        "Comma-separated platform tags. "
        f"Valid: {', '.join(DEFAULT_PLATFORMS)}. "
        f"Default: all of them."
    ),
)
    p_info = sub.add_parser("info", help="Show bundle details")
    p_info.add_argument("package", help="Package name")
    p_info.set_defaults(func=cmd_info)

    p_update = sub.add_parser("update", help="Re-fetch a bundle")
    p_update.add_argument("package", help="Package name")
    p_update.add_argument(
    "--platforms",
    help=(
        "Comma-separated platform tags. "
        f"Valid: {', '.join(DEFAULT_PLATFORMS)}. "
        f"Default: all of them."
    ),
)
    p_update.add_argument("--snapshot", action="store_true", help="Snapshot mode")
    p_update.set_defaults(func=cmd_update)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
