import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from unittest.mock import patch

import pytest


@pytest.fixture(scope="module")
def standalone():
    spec = importlib.util.spec_from_file_location(
        "portapkg_standalone",
        os.path.join(os.path.dirname(__file__), "..", "portapkg.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestDetectPlatform:
    def test_macos_arm(self, standalone):
        with (
            patch("sys.platform", "darwin"),
            patch("platform.machine", return_value="arm64"),
        ):
            assert standalone._detect_platform() == "macosx_13_0_arm64"

    def test_linux_x86(self, standalone):
        with (
            patch("sys.platform", "linux"),
            patch("platform.machine", return_value="x86_64"),
        ):
            assert standalone._detect_platform() == "linux_x86_64"

    def test_windows_amd64(self, standalone):
        with (
            patch("sys.platform", "win32"),
            patch("platform.machine", return_value="AMD64"),
        ):
            assert standalone._detect_platform() == "win_amd64"


class TestDetectPython:
    def test_detect_python(self, standalone):
        expected = f"{sys.version_info.major}{sys.version_info.minor}"
        assert standalone._detect_python() == expected


class TestParseWheel:
    def test_standard_wheel(self, standalone):
        result = standalone._parse_wheel("pkg-1.0-py3-none-any.whl")
        assert result["python_tag"] == "py3"
        assert result["abi_tag"] == "none"
        assert result["platform_tag"] == "any"

    def test_not_wheel(self, standalone):
        assert standalone._parse_wheel("source.tar.gz") is None

    def test_malformed(self, standalone):
        assert standalone._parse_wheel("foo.whl") is None


class TestPyTagMatches:
    def test_py3_matches(self, standalone):
        assert standalone._py_tag_matches("py3", "312") is True


class TestPlatMatches:
    def test_any_matches(self, standalone):
        assert standalone._plat_matches("any", "linux_x86_64") is True

    def test_exact(self, standalone):
        assert standalone._plat_matches("win_amd64", "win_amd64") is True

    def test_manylinux_to_linux(self, standalone):
        assert (
            standalone._plat_matches("manylinux2014_x86_64", "linux_x86_64") is True
        )

    def test_diff_arch_no_match(self, standalone):
        assert (
            standalone._plat_matches("manylinux2014_aarch64", "linux_x86_64") is False
        )


class TestCheckPip:
    def test_pip_available(self, standalone):
        mock_result = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="pip 23.0", stderr=""
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            assert standalone._check_pip() is True

    def test_pip_not_available(self, standalone):
        mock_result = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr="not found"
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            assert standalone._check_pip() is False


class TestCmdInstall:
    def test_missing_pip(self, standalone, capsys):
        with patch.object(subprocess, "run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=1, stdout="", stderr=""
            )
            with pytest.raises(SystemExit):
                standalone.cmd_install(
                    type("Args", (), {"packages": ["testpkg"], "all": False, "target": None})()
                )
        captured = capsys.readouterr()
        assert "pip is not available" in captured.err

    def test_missing_bundle_dir(self, standalone, capsys):
        mock_run = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="pip 23.0", stderr=""
        )
        with patch.object(subprocess, "run", return_value=mock_run):
            with (
                patch.object(standalone, "BUNDLES_DIR", "/nonexistent"),
                pytest.raises(SystemExit),
            ):
                standalone.cmd_install(
                    type("Args", (), {"packages": ["testpkg"], "all": False, "target": None})()
                )
        captured = capsys.readouterr()
        assert "not found" in captured.err

    def test_successful_install(self, standalone, capsys):
        mock_success = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="pip 23.0", stderr=""
        )
        with (
            tempfile.TemporaryDirectory() as tmpdir,
        ):
            bundle_dir = os.path.join(tmpdir, "testpkg")
            wheels_dir = os.path.join(bundle_dir, "wheels")
            os.makedirs(wheels_dir)
            manifest = {
                "name": "testpkg",
                "version": "1.0",
                "dependencies": [{"name": "testpkg", "version": "1.0"}],
            }
            with open(os.path.join(bundle_dir, "manifest.json"), "w") as f:
                json.dump(manifest, f)
            with open(
                os.path.join(wheels_dir, "testpkg-1.0-py3-none-any.whl"), "w"
            ) as f:
                f.write("")

            def mock_run_side_effect(cmd, **kwargs):
                if "--version" in cmd:
                    return mock_success
                return subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="Installed", stderr=""
                )

            with (
                patch.object(subprocess, "run", side_effect=mock_run_side_effect),
                patch.object(standalone, "BUNDLES_DIR", tmpdir),
            ):
                standalone.cmd_install(
                    type("Args", (), {"packages": ["testpkg"], "all": False, "target": None})()
                )

        captured = capsys.readouterr()
        assert "Successfully installed" in captured.out

    def test_multiple_packages(self, standalone, capsys):
        """Install multiple packages in one command."""
        mock_success = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="pip 23.0", stderr=""
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            for pkg in ["pkg_a", "pkg_b"]:
                bundle_dir = os.path.join(tmpdir, pkg)
                wheels_dir = os.path.join(bundle_dir, "wheels")
                os.makedirs(wheels_dir)
                with open(os.path.join(bundle_dir, "manifest.json"), "w") as f:
                    json.dump({
                        "name": pkg, "version": "1.0",
                        "dependencies": [{"name": pkg, "version": "1.0"}],
                    }, f)
                with open(
                    os.path.join(wheels_dir, f"{pkg}-1.0-py3-none-any.whl"), "w"
                ) as f:
                    f.write("")

            def mock_run_side_effect(cmd, **kwargs):
                if "--version" in cmd:
                    return mock_success
                return subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="Installed", stderr=""
                )

            with (
                patch.object(subprocess, "run", side_effect=mock_run_side_effect),
                patch.object(standalone, "BUNDLES_DIR", tmpdir),
            ):
                standalone.cmd_install(
                    type("Args", (), {"packages": ["pkg_a", "pkg_b"], "all": False, "target": None})()
                )

        captured = capsys.readouterr()
        assert "All packages installed successfully" in captured.out

    def test_install_all(self, standalone, capsys):
        """Install all bundles via --all flag."""
        mock_success = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="pip 23.0", stderr=""
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            for pkg in ["pkg_a", "pkg_b", "pkg_c"]:
                bundle_dir = os.path.join(tmpdir, pkg)
                wheels_dir = os.path.join(bundle_dir, "wheels")
                os.makedirs(wheels_dir)
                with open(os.path.join(bundle_dir, "manifest.json"), "w") as f:
                    json.dump({
                        "name": pkg, "version": "1.0",
                        "dependencies": [{"name": pkg, "version": "1.0"}],
                    }, f)
                with open(
                    os.path.join(wheels_dir, f"{pkg}-1.0-py3-none-any.whl"), "w"
                ) as f:
                    f.write("")

            def mock_run_side_effect(cmd, **kwargs):
                if "--version" in cmd:
                    return mock_success
                return subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="Installed", stderr=""
                )

            with (
                patch.object(subprocess, "run", side_effect=mock_run_side_effect),
                patch.object(standalone, "BUNDLES_DIR", tmpdir),
            ):
                standalone.cmd_install(
                    type("Args", (), {"packages": [], "all": True, "target": None})()
                )

        captured = capsys.readouterr()
        assert "All packages installed successfully" in captured.out

    def test_install_all_empty(self, standalone, capsys):
        """--all with no bundles should error."""
        mock_success = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="pip 23.0", stderr=""
        )
        with patch.object(subprocess, "run", return_value=mock_success):
            with tempfile.TemporaryDirectory() as tmpdir:
                with patch.object(standalone, "BUNDLES_DIR", tmpdir):
                    with pytest.raises(SystemExit):
                        standalone.cmd_install(
                            type("Args", (), {"packages": [], "all": True, "target": None})()
                        )
        captured = capsys.readouterr()
        assert "specify package(s)" in captured.err


class TestCmdList:
    def test_no_bundles_dir(self, standalone, capsys):
        with patch.object(standalone, "BUNDLES_DIR", "/nonexistent"):
            standalone.cmd_list(None)
        captured = capsys.readouterr()
        assert "No bundles" in captured.out

    def test_with_bundles(self, standalone, capsys):
        with tempfile.TemporaryDirectory() as tmpdir:
            bundle_dir = os.path.join(tmpdir, "testpkg")
            os.makedirs(bundle_dir)
            manifest = {
                "name": "testpkg",
                "version": "1.0",
                "date_bundled": "2026-05-25T12:00:00",
            }
            with open(os.path.join(bundle_dir, "manifest.json"), "w") as f:
                json.dump(manifest, f)
            with patch.object(standalone, "BUNDLES_DIR", tmpdir):
                standalone.cmd_list(None)
        captured = capsys.readouterr()
        assert "testpkg" in captured.out
        assert "1.0" in captured.out
