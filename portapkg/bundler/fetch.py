import os
import subprocess
import sys

from portapkg.installer.platform import (
    DEFAULT_PLATFORMS,
    DEFAULT_PYTHON_VERSIONS,
    parse_wheel_filename,
    platform_tag_matches,
)



def _wheel_exists(package, version, dest_dir, plat=None):
    """Check if a compatible wheel for (package, version) already exists.

    If plat is provided, also checks that the existing wheel's platform
    tag is compatible with the requested platform.
    """
    if not os.path.isdir(dest_dir):
        return False
    normalized = package.lower().replace("_", "-")
    prefix = f"{normalized}-{version}-"
    for fname in os.listdir(dest_dir):
        if not (fname.lower().startswith(prefix) and fname.endswith(".whl")):
            continue
        if plat is None:
            return True
        parsed = parse_wheel_filename(fname)
        if parsed is None:
            continue
        if platform_tag_matches(parsed["platform_tag"], plat):
            return True
    return False


def download_wheels(
    package,
    version,
    dest_dir,
    platforms=None,
    python_versions=None,
    no_binary_fallback=True,
):
    if platforms is None:
        platforms = DEFAULT_PLATFORMS
    if python_versions is None:
        python_versions = DEFAULT_PYTHON_VERSIONS

    failures = []
    successes = []
    spec = f"{package}=={version}"

    for plat in platforms:
        for pyver in python_versions:
            if _wheel_exists(package, version, dest_dir, plat):
                successes.append((plat, pyver, "binary"))
                continue
            pyver_dotted = f"{pyver[0]}.{pyver[1:]}"
            cmd = [
                sys.executable,
                "-m",
                "pip",
                "download",
                "--dest",
                dest_dir,
                "--platform",
                plat,
                "--python-version",
                pyver_dotted,
                "--only-binary=:all:",
                "--no-deps",
                spec,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                successes.append((plat, pyver, "binary"))
            else:
                if no_binary_fallback:
                    cmd_fallback = [
                        sys.executable,
                        "-m",
                        "pip",
                        "download",
                        "--dest",
                        dest_dir,
                        "--platform",
                        plat,
                        "--python-version",
                        pyver_dotted,
                        spec,
                    ]
                    result2 = subprocess.run(
                        cmd_fallback, capture_output=True, text=True
                    )
                    if result2.returncode == 0:
                        successes.append((plat, pyver, "source"))
                        _warn(
                            f"{package}=={version}: no binary wheel for "
                            f"{plat}/{pyver}, using source dist"
                        )
                    else:
                        failures.append((plat, pyver, result2.stderr))
                        _warn(
                            f"{package}=={version}: no wheel available for "
                            f"{plat}/{pyver}"
                        )
                else:
                    failures.append((plat, pyver, result.stderr))

    return successes, failures


def download_single_platform(package, version, dest_dir):
    spec = f"{package}=={version}"
    cmd = [
        sys.executable,
        "-m",
        "pip",
        "download",
        "--dest",
        dest_dir,
        "--no-deps",
        spec,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"Failed to download {spec}:\n{result.stderr}"
        )
    return True


def _warn(msg):
    print(f"WARNING: {msg}", file=sys.stderr)
