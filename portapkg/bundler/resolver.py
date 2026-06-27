import os
import re
import subprocess
import sys
import tempfile
import zipfile

from portapkg.installer.platform import _normalize_pkg


def _parse_package_version(filename):
    if filename.endswith(".whl"):
        stem = filename[:-4]
        parts = stem.split("-")
        if len(parts) < 5:
            return None, None
        name = "-".join(parts[:-4])
        version = parts[-4]
        return _normalize_pkg(name), version
    elif filename.endswith((".tar.gz", ".zip", ".tar.bz2")):
        for suffix in (".tar.gz", ".tar.bz2", ".zip"):
            if filename.endswith(suffix):
                stem = filename[: -len(suffix)]
                break
        parts = stem.rsplit("-", 1)
        if len(parts) == 2 and re.match(r"^\d", parts[1]):
            return _normalize_pkg(parts[0]), parts[1]
    return None, None


def _unfold_metadata(text):
    """Unfold RFC 822 continuation lines (folded with leading whitespace)."""
    lines = text.splitlines()
    unfolded = []
    for line in lines:
        if unfolded and (line.startswith(" ") or line.startswith("\t")):
            unfolded[-1] += line
        else:
            unfolded.append(line)
    return unfolded


def _target_env(plat):
    """Build a PEP 508 evaluation environment for a target platform tag."""
    from pip._vendor.packaging.markers import default_environment

    env = default_environment()
    if plat.startswith(("win_", "win32")):
        env["sys_platform"] = "win32"
        env["platform_system"] = "Windows"
        env["os_name"] = "nt"
    elif plat.startswith(("linux", "manylinux")):
        env["sys_platform"] = "linux"
        env["platform_system"] = "Linux"
        env["os_name"] = "posix"
    elif plat.startswith("macosx"):
        env["sys_platform"] = "darwin"
        env["platform_system"] = "Darwin"
        env["os_name"] = "posix"
    return env


def _conditional_matches_platform(condition, env):
    """Evaluate a PEP 508 conditional marker against a target environment."""
    from pip._vendor.packaging.markers import Marker

    try:
        return Marker(condition.strip()).evaluate(env)
    except (ValueError, KeyError, TypeError):
        return False


def _scan_conditional_deps(tmpdir, platforms):
    """Scan all wheel METADATA files in tmpdir for deps with conditionals
    that evaluate True for any of the given target platforms."""
    found = set()
    for fname in os.listdir(tmpdir):
        if not fname.endswith(".whl"):
            continue
        whl_path = os.path.join(tmpdir, fname)
        try:
            with zipfile.ZipFile(whl_path) as zf:
                for name in zf.namelist():
                    if not name.endswith(".dist-info/METADATA") and not name.endswith("/METADATA"):
                        continue
                    text = zf.read(name).decode("utf-8")
                    for line in _unfold_metadata(text):
                        line = line.strip()
                        if not line.startswith("Requires-Dist:") or "; " not in line:
                            continue
                        _, _, raw_cond = line.partition("; ")
                        for plat in platforms:
                            env = _target_env(plat)
                            if _conditional_matches_platform(raw_cond, env):
                                body = line[len("Requires-Dist:"):].split(";")[0].strip()
                                pkg_name = re.split(r"[<>=!~\[]", body)[0].strip()
                                found.add(_normalize_pkg(pkg_name))
                                break
                    break
        except (zipfile.BadZipFile, KeyError, UnicodeDecodeError, OSError):
            continue
    return found


def resolve_dependencies(package, platforms=None):
    all_deps = {}

    with tempfile.TemporaryDirectory(prefix="portapkg-resolve-") as tmpdir:
        # Pass 1 — native resolution (catches all host-platform deps)
        cmd = [
            sys.executable,
            "-m",
            "pip",
            "download",
            "--dest",
            tmpdir,
            package,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(
                f"Failed to resolve dependencies for {package}:\n{result.stderr}"
            )

        for fname in os.listdir(tmpdir):
            pkg_name, version = _parse_package_version(fname)
            if pkg_name and version:
                pkg_name = _normalize_pkg(pkg_name)
                if pkg_name not in all_deps:
                    all_deps[pkg_name] = version

        # Pass 2 — recursively scan for platform-conditional deps
        if platforms:
            _resolve_conditional_tree(package, all_deps, tmpdir, platforms)

    for k, v in all_deps.items():
        if v is None:
            print(f"WARNING: Could not resolve '{k}', it will be skipped.", file=sys.stderr)
    all_deps = {k: v for k, v in all_deps.items() if v is not None}
    return all_deps


def _resolve_conditional_tree(package, all_deps, tmpdir, platforms):
    """Recursively find and resolve platform-conditional deps.

    Scans every wheel's METADATA in tmpdir for conditionals matching
    target platforms.  Any newly discovered deps are downloaded into
    tmpdir and the scan repeats until the dep tree is stable.
    """
    while True:
        extra = _scan_conditional_deps(tmpdir, platforms)
        new_deps = extra - set(all_deps.keys())
        if not new_deps:
            break

        for name in new_deps:
            all_deps[name] = None  # placeholder
            cmd = [
                sys.executable,
                "-m",
                "pip",
                "download",
                "--dest",
                tmpdir,
                "--no-deps",
                name,
            ]
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode == 0:
                for fname in os.listdir(tmpdir):
                    n, v = _parse_package_version(fname)
                    if n and _normalize_pkg(n) == name:
                        all_deps[name] = v
                        break


def freeze_snapshot():
    result = subprocess.run(
        [sys.executable, "-m", "pip", "freeze"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"pip freeze failed:\n{result.stderr}")

    packages = {}
    for line in result.stdout.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-e") or " @ " in line:
            continue
        if "==" in line:
            name, version = line.split("==", 1)
            packages[_normalize_pkg(name)] = version
    return packages
