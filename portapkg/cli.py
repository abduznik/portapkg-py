import argparse
import datetime
import os
import random
import shutil
import string
import sys

from portapkg.bundler.fetch import download_wheels, download_single_platform
from portapkg.bundler.manifest import read_manifest, write_manifest, build_manifest
from portapkg.bundler.resolver import resolve_dependencies, freeze_snapshot
from portapkg.installer.platform import (
    DEFAULT_PLATFORMS,
    DEFAULT_PYTHON_VERSIONS,
    detect_current_platform,
    detect_current_python,
)


BUNDLES_DIR = os.path.abspath(
    os.environ.get("PORTAPKG_BUNDLES_DIR", os.path.join(os.getcwd(), "bundles"))
)


def _ensure_bundles_dir():
    os.makedirs(BUNDLES_DIR, exist_ok=True)


def _get_bundle_dir(package):
    return os.path.join(BUNDLES_DIR, package)


def _print_wheel_summary(wheels_dir):
    if not os.path.isdir(wheels_dir):
        return
    whls = [f for f in os.listdir(wheels_dir) if f.endswith(".whl")]
    print(f"  Total wheel files: {len(whls)}")


def _resolve_packages(args):
    """Resolve package list from --packages flag or positional package arg."""
    if args.packages:
        return [p.strip() for p in args.packages.split(",") if p.strip()]
    elif args.package:
        return [args.package]
    return []


def cmd_bundle(args):
    _ensure_bundles_dir()
    packages = _resolve_packages(args)
    if not packages:
        print("ERROR: specify a package or --packages to bundle.", file=sys.stderr)
        return 1
    for pkg in packages:
        print(f"\n{'='*50}")
        print(f"Bundling: {pkg}")
        print(f"{'='*50}")
        if args.snapshot:
            _bundle_snapshot(pkg)
        else:
            platforms = args.platforms.split(",") if args.platforms else DEFAULT_PLATFORMS
            _bundle_multi(pkg, platforms, DEFAULT_PYTHON_VERSIONS)


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


def _find_standalone():
    """Locate portapkg.py for export."""
    locations = [
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "portapkg.py"),
        os.path.join(os.getcwd(), "portapkg.py"),
    ]
    for loc in locations:
        if os.path.isfile(loc):
            return os.path.abspath(loc)
    return None


def cmd_export(args):
    """Export bundle(s) + portapkg.py into a portable folder."""
    # Determine which packages to export
    if args.packages:
        packages = [p.strip() for p in args.packages.split(",") if p.strip()]
    elif args.package:
        packages = [args.package]
    else:
        print("ERROR: specify a package or --packages to export.", file=sys.stderr)
        return 1

    # Determine the export name
    export_name = args.name or (args.package if args.package else "bundle")

    # Validate all bundles exist
    for pkg in packages:
        bundle_src = _get_bundle_dir(pkg)
        if not os.path.isdir(bundle_src):
            print(f"ERROR: Bundle for '{pkg}' not found in {BUNDLES_DIR}.\n"
                  f"Bundle it first: portapkg bundle {pkg}", file=sys.stderr)
            return 1

    standalone = _find_standalone()
    if standalone is None:
        print("ERROR: Could not find portapkg.py. "
              "Run this from the source repo or place portapkg.py in the current directory.",
              file=sys.stderr)
        return 1

    today = datetime.date.today().isoformat()
    rand_id = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    folder_name = f"{export_name}_{rand_id}_{today}"

    output_parent = os.path.abspath(args.output) if args.output else os.getcwd()
    output_dir = os.path.join(output_parent, folder_name)

    if os.path.exists(output_dir):
        print(f"ERROR: {output_dir} already exists.", file=sys.stderr)
        return 1

    # Build structure: {output_dir}/portapkg.py + bundles/{pkg1, pkg2, ...}/
    bundles_out = os.path.join(output_dir, "bundles")
    os.makedirs(bundles_out, exist_ok=True)

    # Copy portapkg.py
    shutil.copy2(standalone, os.path.join(output_dir, "portapkg.py"))
    os.chmod(os.path.join(output_dir, "portapkg.py"), 0o755)

    # Copy each bundle
    for pkg in packages:
        bundle_src = _get_bundle_dir(pkg)
        pkg_out = os.path.join(bundles_out, pkg)
        shutil.copytree(bundle_src, pkg_out)

    print(f"Exported to: {output_dir}")
    print(f"  Size: {_dir_size(output_dir):.1f} MB")
    print("  Contents:")
    print(f"    {output_dir}/portapkg.py")
    print(f"    {output_dir}/bundles/")
    for pkg in packages:
        print(f"      {pkg}/")
    return 0


def _dir_size(path):
    total = 0
    for dirpath, _, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.isfile(fp):
                total += os.path.getsize(fp)
    return total / (1024 * 1024)


def cmd_update(args):
    _ensure_bundles_dir()
    packages = _resolve_packages(args)
    if not packages:
        print("ERROR: specify a package or --packages to update.", file=sys.stderr)
        return 1
    for pkg in packages:
        print(f"\n{'='*50}")
        print(f"Updating: {pkg}")
        print(f"{'='*50}")
        if args.snapshot:
            _bundle_snapshot(pkg)
        else:
            platforms = args.platforms.split(",") if args.platforms else DEFAULT_PLATFORMS
            _bundle_multi(pkg, platforms, DEFAULT_PYTHON_VERSIONS)


def main():
    parser = argparse.ArgumentParser(
        prog="portapkg",
        description="Portable Python package bundler and installer",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_bundle = sub.add_parser("bundle", help="Bundle a package (or multiple) for offline install")
    p_bundle.add_argument("package", nargs="?", help="Package name (single-package shortcut)")
    p_bundle.add_argument("--packages", help="Comma-separated list of packages to bundle")
    p_bundle.add_argument(
        "--platforms",
        help=(
            "Comma-separated platform tags. "
            f"Valid: {', '.join(DEFAULT_PLATFORMS)}. "
            "Default: all of them."
        ),
    )
    p_bundle.add_argument("--snapshot", action="store_true", help="Snapshot current env (single-platform)")
    p_bundle.set_defaults(func=cmd_bundle)

    p_export = sub.add_parser("export", help="Export bundle(s) + portapkg.py into a portable folder")
    p_export.add_argument("package", nargs="?", help="Package name (single-package shortcut)")
    p_export.add_argument("--name", help="Custom export folder name (default: package name or 'bundle')")
    p_export.add_argument("--packages", help="Comma-separated list of packages to include")
    p_export.add_argument("--output", "-o", help="Output directory (default: current directory)")
    p_export.set_defaults(func=cmd_export)

    p_list = sub.add_parser("list", help="List all bundles")
    p_list.set_defaults(func=cmd_list)

    p_info = sub.add_parser("info", help="Show bundle details")
    p_info.add_argument("package", help="Package name")
    p_info.set_defaults(func=cmd_info)

    p_update = sub.add_parser("update", help="Re-fetch a bundle (or multiple)")
    p_update.add_argument("package", nargs="?", help="Package name (single-package shortcut)")
    p_update.add_argument("--packages", help="Comma-separated list of packages to update")
    p_update.add_argument(
        "--platforms",
        help=(
            "Comma-separated platform tags. "
            f"Valid: {', '.join(DEFAULT_PLATFORMS)}. "
            "Default: all of them."
        ),
    )
    p_update.add_argument("--snapshot", action="store_true", help="Snapshot mode")
    p_update.set_defaults(func=cmd_update)

    args = parser.parse_args()
    ret = args.func(args)
    if isinstance(ret, int) and ret != 0:
        sys.exit(ret)


if __name__ == "__main__":
    main()
