#!/usr/bin/env python3
"""
portapkg.py - Portable offline Python package installer.

Self-contained single file (stdlib + subprocess only).
Copy this file + bundles/ folder to an offline machine and run:
    python portapkg.py install <package>
    python portapkg.py list
"""

import argparse
import datetime
import json
import os
import platform as _platform
import random
import shutil
import string
import subprocess
import sys


BUNDLES_DIR = os.path.abspath(
    os.environ.get("PORTAPKG_BUNDLES_DIR", os.path.join(os.getcwd(), "bundles"))
)


def _read_manifest(bundle_dir):
    path = os.path.join(bundle_dir, "manifest.json")
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        return json.load(f)


def _detect_platform():
    system = sys.platform
    machine = _platform.machine().lower()
    if system == "win32":
        return "win_amd64" if machine in ("amd64", "x86_64") else "win32"
    elif system == "linux":
        return "linux_aarch64" if machine in ("aarch64", "arm64") else "linux_x86_64"
    elif system == "darwin":
        return "macosx_13_0_arm64" if machine in ("arm64", "aarch64") else "macosx_13_0_x86_64"
    return f"{system}_{machine}"


def _detect_python():
    return f"{sys.version_info.major}{sys.version_info.minor}"


def _parse_wheel(filename):
    if not filename.endswith(".whl"):
        return None
    parts = filename[:-4].split("-")
    if len(parts) < 5:
        return None
    return {"python_tag": parts[-3], "abi_tag": parts[-2], "platform_tag": parts[-1]}


def _py_tag_matches(tag, cur_ver):
    for t in tag.split("."):
        t = t.strip()
        if t == "*":
            return True
        v = t[2:] if t.startswith("cp") or t.startswith("py") else t
        if not v:
            return True
        major = sys.version_info.major
        minor = sys.version_info.minor
        if int(v[0]) != major:
            continue
        if len(v) < 2:
            return True
        if int(v[1:]) == minor:
            return True
    return False


def _plat_matches(wheel_plat, cur_plat):
    if wheel_plat == "any":
        return True
    a = wheel_plat.replace("-", "_").replace(".", "_").lower()
    b = cur_plat.replace("-", "_").replace(".", "_").lower()
    if a == b:
        return True
    if (a.startswith("linux") or a.startswith("manylinux")) and (
        b.startswith("linux") or b.startswith("manylinux")
    ):
        a_arch = a.split("_")[-1]
        b_arch = b.split("_")[-1]
        if a_arch == b_arch:
            return True
    if a.startswith("macosx") and b.startswith("macosx"):
        a_arch = a.split("_")[-1]
        b_arch = b.split("_")[-1]
        return a_arch == b_arch
    if a.startswith("win") and b.startswith("win"):
        a_arch = a.split("_")[-1] if "_" in a else a
        b_arch = b.split("_")[-1] if "_" in b else b
        if a_arch == b_arch:
            return True
    return False


def _check_pip():
    r = subprocess.run(
        [sys.executable, "-m", "pip", "--version"], capture_output=True, text=True
    )
    return r.returncode == 0


def _resolve_install_packages(args):
    """Resolve package list from positional args or --all flag."""
    if args.all:
        if not os.path.isdir(BUNDLES_DIR):
            return []
        return sorted(
            d for d in os.listdir(BUNDLES_DIR)
            if os.path.isdir(os.path.join(BUNDLES_DIR, d))
        )
    elif args.packages:
        return args.packages
    return []


def _install_single(package, target):
    """Install a single package from its bundle. Returns True on success."""
    if not _check_pip():
        print("ERROR: pip is not available. Cannot install.", file=sys.stderr)
        return False

    bundle_dir = os.path.join(BUNDLES_DIR, package)
    if not os.path.isdir(bundle_dir):
        print(
            f"ERROR: Bundle for '{package}' not found in {BUNDLES_DIR}.\n"
            f"Copy the bundle directory to this machine first.",
            file=sys.stderr,
        )
        return False

    manifest = _read_manifest(bundle_dir)
    if manifest is None:
        print(f"ERROR: No manifest in {bundle_dir}", file=sys.stderr)
        return False

    cur_plat = _detect_platform()
    cur_py = _detect_python()
    wheels_dir = os.path.join(bundle_dir, "wheels")

    if not os.path.isdir(wheels_dir):
        print(f"ERROR: No wheels directory in {bundle_dir}", file=sys.stderr)
        return False

    compatible = []
    for fname in os.listdir(wheels_dir):
        parsed = _parse_wheel(fname)
        if parsed is None:
            continue
        if not _py_tag_matches(parsed["python_tag"], cur_py):
            continue
        if not _plat_matches(parsed["platform_tag"], cur_plat):
            continue
        compatible.append(fname)

    if not compatible:
        dep_info = []
        for d in manifest.get("dependencies") or []:
            dep_info.append(f"{d.get('name', '?')}=={d.get('version', '?')}")
        print(
            f"ERROR: No compatible wheel found for {package}\n"
            f"  Current platform: {cur_plat}\n"
            f"  Current Python:   {cur_py}\n"
            f"  Bundled deps:     {', '.join(dep_info) if dep_info else 'none'}\n"
            f"Try bundling with --snapshot on this machine.",
            file=sys.stderr,
        )
        return False

    print(f"\n{'='*50}")
    print(f"Installing {package}...")
    print(f"  Platform: {cur_plat}")
    print(f"  Python:   {cur_py}")
    print(f"  Wheels:   {len(compatible)} compatible found")

    cmd = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--no-index",
        "--find-links",
        wheels_dir,
        package,
    ]
    if target:
        cmd.extend(["--target", target])

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ERROR: Installation failed:\n{result.stderr}", file=sys.stderr)
        return False

    print(result.stdout)
    print(f"Successfully installed {package}")
    return True


def cmd_install(args):
    if not _check_pip():
        print("ERROR: pip is not available. Cannot install.", file=sys.stderr)
        sys.exit(1)

    packages = _resolve_install_packages(args)
    if not packages:
        print(
            "ERROR: specify package(s) to install or use --all.\n"
            f"  Usage: python {os.path.basename(__file__)} install <package> [package ...]\n"
            f"  Usage: python {os.path.basename(__file__)} install --all",
            file=sys.stderr,
        )
        sys.exit(1)

    any_failed = False
    for pkg in packages:
        if not _install_single(pkg, target=args.target):
            any_failed = True

    if any_failed:
        print("\nSome packages failed to install. Check errors above.", file=sys.stderr)
        sys.exit(1)
    else:
        print("\nAll packages installed successfully.")


def cmd_export(args):
    """Export bundle(s) + this script into a portable folder."""
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
        bundle_src = os.path.join(BUNDLES_DIR, pkg)
        if not os.path.isdir(bundle_src):
            print(
                f"ERROR: Bundle for '{pkg}' not found in {BUNDLES_DIR}.\n"
                f"Bundle it first: python {os.path.basename(__file__)} bundle {pkg}",
                file=sys.stderr,
            )
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

    # Copy this script (standalone)
    script_path = os.path.abspath(__file__)
    shutil.copy2(script_path, os.path.join(output_dir, os.path.basename(__file__)))

    # Copy each bundle
    for pkg in packages:
        bundle_src = os.path.join(BUNDLES_DIR, pkg)
        pkg_out = os.path.join(bundles_out, pkg)
        shutil.copytree(bundle_src, pkg_out)

    # Calculate size
    total_bytes = 0
    for dirpath, _, filenames in os.walk(output_dir):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.isfile(fp):
                total_bytes += os.path.getsize(fp)
    size_mb = total_bytes / (1024 * 1024)

    print(f"Exported to: {output_dir}")
    print(f"  Size: {size_mb:.1f} MB")
    print("  Contents:")
    print(f"    {output_dir}/{os.path.basename(__file__)}")
    print(f"    {output_dir}/bundles/")
    for pkg in packages:
        print(f"      {pkg}/")
    return 0


def cmd_list(args):
    if not os.path.isdir(BUNDLES_DIR):
        print("No bundles directory found.")
        return
    bundles = sorted(
        d
        for d in os.listdir(BUNDLES_DIR)
        if os.path.isdir(os.path.join(BUNDLES_DIR, d))
    )
    if not bundles:
        print("No bundles available.")
        return
    print("Available bundles:")
    for name in bundles:
        m = _read_manifest(os.path.join(BUNDLES_DIR, name))
        if m:
            print(
                f"  {name}  v{m.get('version', '?')}  ({m.get('date_bundled', '?')})"
            )
        else:
            print(f"  {name}  (no manifest)")


def main():
    parser = argparse.ArgumentParser(
        prog="portapkg.py",
        description="Portable offline Python package installer",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_install = sub.add_parser("install", help="Install one or more bundled packages")
    p_install.add_argument("packages", nargs="*", help="Package name(s) to install")
    p_install.add_argument("--all", action="store_true", help="Install all available bundles")
    p_install.add_argument(
        "--target", help="Custom install path (e.g. ./venv/Lib/site-packages)"
    )
    p_install.set_defaults(func=cmd_install)

    p_export = sub.add_parser("export", help="Export bundle(s) into a portable folder")
    p_export.add_argument("package", nargs="?", help="Package name (single-package shortcut)")
    p_export.add_argument("--name", help="Custom export folder name (default: package name or 'bundle')")
    p_export.add_argument("--packages", help="Comma-separated list of packages to include")
    p_export.add_argument("--output", "-o", help="Output directory (default: current directory)")
    p_export.set_defaults(func=cmd_export)

    p_list = sub.add_parser("list", help="List available bundles")
    p_list.set_defaults(func=cmd_list)

    args = parser.parse_args()
    ret = args.func(args)
    if isinstance(ret, int) and ret != 0:
        sys.exit(ret)


if __name__ == "__main__":
    main()
