import platform
import sys


DEFAULT_PLATFORMS = [
    "win_amd64",
    "win32",
    "manylinux2014_x86_64",
    "manylinux2014_aarch64",
    "macosx_13_0_arm64",
    "macosx_13_0_x86_64",
]

DEFAULT_PYTHON_VERSIONS = ["39", "310", "311", "312", "313"]


def detect_current_platform():
    system = sys.platform
    machine = platform.machine().lower()

    if system == "win32":
        if machine in ("amd64", "x86_64"):
            return "win_amd64"
        return "win32"
    elif system == "linux":
        if machine in ("aarch64", "arm64"):
            return "linux_aarch64"
        return "linux_x86_64"
    elif system == "darwin":
        if machine in ("arm64", "aarch64"):
            return "macosx_13_0_arm64"
        return "macosx_13_0_x86_64"
    return f"{system}_{machine}"


def detect_current_python():
    return f"{sys.version_info.major}{sys.version_info.minor}"


def parse_wheel_filename(filename):
    if not filename.endswith(".whl"):
        return None
    stem = filename[:-4]
    parts = stem.split("-")
    if len(parts) < 5:
        return None
    py_tag = parts[-3]
    abi_tag = parts[-2]
    plat_tag = parts[-1]
    if "." in parts[-4]:
        version = parts[-4]
        name = "-".join(parts[:-4])
    elif len(parts) >= 6:
        version = parts[-5]
        name = "-".join(parts[:-5])
    else:
        return None
    return {
        "name": name,
        "version": version,
        "python_tag": py_tag,
        "abi_tag": abi_tag,
        "platform_tag": plat_tag,
    }


def python_tag_matches(python_tag, current_pyver):
    for tag in python_tag.split("."):
        tag = tag.strip()
        if tag == "*":
            return True
        ver_part = tag[2:] if tag.startswith("cp") or tag.startswith("py") else tag
        if not ver_part:
            return True
        major = sys.version_info.major
        minor = sys.version_info.minor
        if int(ver_part[0]) != major:
            continue
        if len(ver_part) < 2:
            return True
        if int(ver_part[1:]) == minor:
            return True
    return False


def platform_tag_matches(wheel_plat, current_plat):
    if wheel_plat == "any":
        return True
    a = wheel_plat.replace("-", "_").replace(".", "_").lower()
    b = current_plat.replace("-", "_").replace(".", "_").lower()
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
