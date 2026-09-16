import datetime
import json
import os


def read_manifest(bundle_dir):
    path = os.path.join(bundle_dir, "manifest.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_manifest(bundle_dir, data):
    path = os.path.join(bundle_dir, "manifest.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return path


def build_manifest(name, version, deps, source_platform, source_python):
    return {
        "name": name,
        "version": version,
        "date_bundled": datetime.datetime.now(tz=datetime.timezone.utc).isoformat(),
        "source_platform": source_platform,
        "source_python": source_python,
        "dependencies": deps,
    }
