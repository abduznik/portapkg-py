import os
import subprocess
import sys

from portapkg.installer.platform import (
    DEFAULT_PLATFORMS,
    DEFAULT_PYTHON_VERSIONS,
    _normalize_pkg,
    parse_wheel_filename,
    platform_tag_matches,
    python_tag_matches,
)


def _wheel_exists(package, version, dest_dir, plat=None, pyver=None):
    """Check if a compatible wheel for (package, version) already exists.

    If plat is provided, also checks that the existing wheel's platform
    tag is compatible with the requested platform.
    If pyver is provided, also checks that the python tag is compatible.
    """
    if not os.path.isdir(dest_dir):
        return False
    normalized = _normalize_pkg(package)
    prefix = f"{normalized}-{version}-"
    for fname in os.listdir(dest_dir):
        if not (fname.lower().startswith(prefix) and fname.endswith(".whl")):
            continue
        parsed = parse_wheel_filename(fname)
        if parsed is None:
            continue
        if plat and not platform_tag_matches(parsed["platform_tag"], plat):
            continue
        if pyver and not python_tag_matches(parsed["python_tag"], pyver):
            continue
        return True
    return False


def _pip_download(spec, dest_dir, plat=None, pyver_dotted=None, only_binary=None):
    cmd = [
        sys.executable,
        "-m",
        "pip",
        "download",
        "--dest",
        dest_dir,
        "--no-deps",
    ]
    if plat:
        cmd.extend(["--platform", plat])
    if pyver_dotted:
        cmd.extend(["--python-version", pyver_dotted])
    if only_binary is True:
        cmd.append("--only-binary=:all:")
    elif only_binary is False:
        cmd.extend(["--no-binary", ":all:"])
    cmd.append(spec)
    return subprocess.run(cmd, capture_output=True, text=True)


def _try_newer_version(package, cur_version, dest_dir, plat, pyver_dotted):
    """Try to find a newer version of package with binary wheels for the target.

    Uses the PyPI JSON API (works with all pip versions).
    """
    try:
        import urllib.request
        import json as _json

        url = f"https://pypi.org/pypi/{package}/json"
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = _json.loads(resp.read().decode())

        versions = sorted(data.get("releases", {}).keys(), reverse=True)
        try:
            cur_idx = versions.index(cur_version)
        except ValueError:
            cur_idx = -1
        if cur_idx <= 0:
            return None

        for ver in versions[:cur_idx]:
            new_spec = f"{package}=={ver}"
            result = _pip_download(
                new_spec,
                dest_dir,
                plat,
                pyver_dotted,
                only_binary=True,
            )
            if result.returncode == 0:
                return ver
    except (subprocess.SubprocessError, OSError, ValueError):
        pass
    return None


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
    sdist_grabbed = False

    for plat in platforms:
        for pyver in python_versions:
            if _wheel_exists(package, version, dest_dir, plat, pyver):
                successes.append((plat, pyver, "binary"))
                continue

            pyver_dotted = f"{pyver[0]}.{pyver[1:]}"

            # Layer 1 — pre-built binary wheel
            result = _pip_download(spec, dest_dir, plat, pyver_dotted, only_binary=True)
            if result.returncode == 0:
                successes.append((plat, pyver, "binary"))
                continue

            if not no_binary_fallback:
                failures.append((plat, pyver, "no binary wheel"))
                _warn(f"{spec}: no binary for {plat}/{pyver}")
                continue

            # Layer 2 — platform-constrained source dist
            result = _pip_download(spec, dest_dir, plat, pyver_dotted)
            if result.returncode == 0:
                successes.append((plat, pyver, "source"))
                _warn(f"{spec}: no binary for {plat}/{pyver}, using source dist")
                continue

            # Layer 3 — unconstrained sdist (Fix 1: Eel-like cases)
            if not sdist_grabbed:
                result = _pip_download(spec, dest_dir, only_binary=False)
                if result.returncode == 0:
                    sdist_grabbed = True
                    successes.append((plat, pyver, "source"))
                    _warn(f"{spec}: no compatible dist for {plat}/{pyver}, using sdist")
                    continue

            # Layer 4 — newer version with binary wheels (Fix 2: msgpack-like cases)
            bumped = _try_newer_version(package, version, dest_dir, plat, pyver_dotted)
            if bumped:
                successes.append((plat, pyver, "binary", bumped))
                _warn(
                    f"{spec}: no wheel for {plat}/{pyver}, "
                    f"using {package}=={bumped} instead"
                )
                continue

            failures.append((plat, pyver, "no distribution found"))
            _warn(f"{spec}: no distribution available for {plat}/{pyver}")

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
        raise RuntimeError(f"Failed to download {spec}:\n{result.stderr}")
    return True


def _warn(msg):
    print(f"WARNING: {msg}", file=sys.stderr)
