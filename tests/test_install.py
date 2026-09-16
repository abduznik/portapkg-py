import json
import os
import subprocess
import tempfile
from unittest.mock import patch

import pytest

from portapkg.installer.install import (
    check_pip_available,
    find_compatible_wheels,
    install_package,
)


class TestFindCompatibleWheels:
    def test_finds_compatible_wheels(self, tmp_bundle_dir):
        wheels_dir = os.path.join(tmp_bundle_dir, "wheels")
        wheel_files = [
            "pkg-1.0-py3-none-any.whl",
        ]
        for wf in wheel_files:
            with open(os.path.join(wheels_dir, wf), "w") as f:
                f.write("")

        result = find_compatible_wheels(wheels_dir, "linux_x86_64", "312")
        assert "pkg-1.0-py3-none-any.whl" in result

    def test_skips_incompatible_platform(self, tmp_bundle_dir):
        wheels_dir = os.path.join(tmp_bundle_dir, "wheels")
        with open(os.path.join(wheels_dir, "pkg-1.0-cp312-cp312-win_amd64.whl"), "w") as f:
            f.write("")

        result = find_compatible_wheels(wheels_dir, "linux_x86_64", "312")
        assert len(result) == 0

    def test_finds_platform_specific_wheels(self, tmp_bundle_dir):
        wheels_dir = os.path.join(tmp_bundle_dir, "wheels")
        with open(os.path.join(wheels_dir, "pkg-1.0-py3-none-linux_x86_64.whl"), "w") as f:
            f.write("")
        with open(os.path.join(wheels_dir, "pkg-1.0-py3-none-win_amd64.whl"), "w") as f:
            f.write("")

        result = find_compatible_wheels(wheels_dir, "linux_x86_64", "312")
        assert len(result) == 1
        assert result[0] == "pkg-1.0-py3-none-linux_x86_64.whl"

    def test_skips_non_wheel_files(self, tmp_bundle_dir):
        wheels_dir = os.path.join(tmp_bundle_dir, "wheels")
        with open(os.path.join(wheels_dir, "random-file.txt"), "w") as f:
            f.write("")
        with open(os.path.join(wheels_dir, "source.tar.gz"), "w") as f:
            f.write("")

        result = find_compatible_wheels(wheels_dir, "linux_x86_64", "312")
        assert len(result) == 0

    def test_empty_wheels_dir(self, tmp_bundle_dir):
        wheels_dir = os.path.join(tmp_bundle_dir, "wheels")
        result = find_compatible_wheels(wheels_dir, "linux_x86_64", "312")
        assert result == []


class TestInstallPackage:
    def test_no_manifest_raises(self, tmp_bundle_dir):
        with pytest.raises(RuntimeError, match="No manifest"):
            install_package(tmp_bundle_dir, "testpkg")

    def test_no_wheels_dir_raises(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            bundle_dir = os.path.join(tmpdir, "testpkg")
            os.makedirs(bundle_dir)
            with open(os.path.join(bundle_dir, "manifest.json"), "w") as f:
                json.dump({"name": "testpkg", "version": "1.0"}, f)
            with pytest.raises(RuntimeError, match="No wheels directory"):
                install_package(bundle_dir, "testpkg")

    def test_no_compatible_wheel_raises(self, tmp_bundle_dir):
        with open(os.path.join(tmp_bundle_dir, "manifest.json"), "w") as f:
            json.dump({
                "name": "testpkg", "version": "1.0",
                "dependencies": [{"name": "testpkg", "version": "1.0"}],
            }, f)
        with pytest.raises(RuntimeError, match="No compatible wheel"):
            install_package(tmp_bundle_dir, "testpkg")

    def test_successful_install(self, tmp_bundle_dir):
        with open(os.path.join(tmp_bundle_dir, "manifest.json"), "w") as f:
            json.dump({
                "name": "testpkg", "version": "1.0",
                "dependencies": [{"name": "testpkg", "version": "1.0"}],
            }, f)
        wheels_dir = os.path.join(tmp_bundle_dir, "wheels")
        with open(os.path.join(wheels_dir, "testpkg-1.0-py3-none-any.whl"), "w") as f:
            f.write("")

        mock_result = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="Successfully installed testpkg", stderr=""
        )

        with patch.object(subprocess, "run", return_value=mock_result) as mock_run:
            output = install_package(tmp_bundle_dir, "testpkg")

        assert "Successfully installed" in output
        call_args = mock_run.call_args[0][0]
        assert "--no-index" in call_args
        assert "--find-links" in call_args
        assert "testpkg" in call_args

    def test_install_with_target(self, tmp_bundle_dir):
        with open(os.path.join(tmp_bundle_dir, "manifest.json"), "w") as f:
            json.dump({
                "name": "testpkg", "version": "1.0",
                "dependencies": [{"name": "testpkg", "version": "1.0"}],
            }, f)
        wheels_dir = os.path.join(tmp_bundle_dir, "wheels")
        with open(os.path.join(wheels_dir, "testpkg-1.0-py3-none-any.whl"), "w") as f:
            f.write("")

        mock_result = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="Installed", stderr=""
        )

        with patch.object(subprocess, "run", return_value=mock_result) as mock_run:
            install_package(tmp_bundle_dir, "testpkg", target="/custom/path")

        call_args = mock_run.call_args[0][0]
        assert "--target" in call_args
        assert "/custom/path" in call_args


class TestCheckPipAvailable:
    def test_pip_available(self):
        mock_result = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="pip 23.0 from ...", stderr=""
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            assert check_pip_available() is True

    def test_pip_not_available(self):
        mock_result = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr="command not found"
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            assert check_pip_available() is False
