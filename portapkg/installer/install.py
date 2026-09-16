import os
import subprocess
import sys

from portapkg.bundler.manifest import read_manifest
from portapkg.installer.platform import (
    detect_current_platform,
    detect_current_python,
    parse_wheel_filename,
    platform_tag_matches,
    python_tag_matches,
)


def find_compatible_wheels(wheels_dir, cur_plat, cur_pyver):
    compatible = []
    for fname in os.listdir(wheels_dir):
        parsed = parse_wheel_filename(fname)
        if parsed is None:
            continue
        if python_tag_matches(parsed["python_tag"], cur_pyver) and (
            platform_tag_matches(parsed["platform_tag"], cur_plat)
        ):
            compatible.append(fname)
    return compatible


def install_package(bundle_dir, package, target=None):
    manifest = read_manifest(bundle_dir)
    if manifest is None:
        raise RuntimeError(
            f"No manifest found in {bundle_dir}. " f"Is '{package}' bundled?"
        )

    if manifest.get("name") != package:
        raise RuntimeError(
            f"Package name mismatch: requested '{package}' "
            f"but manifest declares '{manifest.get('name')}'."
        )

    cur_plat = detect_current_platform()
    cur_pyver = detect_current_python()
    wheels_dir = os.path.join(bundle_dir, "wheels")

    if not os.path.isdir(wheels_dir):
        raise RuntimeError(f"No wheels directory found in {bundle_dir}")

    compatible = find_compatible_wheels(wheels_dir, cur_plat, cur_pyver)

    if not compatible:
        raise RuntimeError(
            f"No compatible wheel found for {package} on "
            f"{cur_plat} / Python {cur_pyver}.\n"
            f"Bundle supports: see manifest.json in {bundle_dir}\n"
            f"Try bundling with --snapshot on the target machine."
        )

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

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"Installation failed:\n{result.stdout}\n{result.stderr}")
    return result.stdout


def check_pip_available():
    result = subprocess.run(
        [sys.executable, "-m", "pip", "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0
