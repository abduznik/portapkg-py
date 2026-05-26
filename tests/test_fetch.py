import subprocess
import tempfile
from unittest.mock import patch

from portapkg.bundler.fetch import (
    _wheel_exists,
    download_single_platform,
    download_wheels,
)


class TestDownloadWheels:
    def test_successful_download(self):
        mock_result = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )
        with (
            patch.object(subprocess, "run", return_value=mock_result),
            tempfile.TemporaryDirectory() as tmpdir,
        ):
            successes, failures = download_wheels(
                "testpkg",
                "1.0",
                tmpdir,
                platforms=["win_amd64"],
                python_versions=["312"],
            )

        assert len(successes) == 1
        assert successes[0] == ("win_amd64", "312", "binary")
        assert len(failures) == 0

    def test_successful_on_multiple_platforms(self):
        mock_result = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )
        with (
            patch.object(subprocess, "run", return_value=mock_result),
            tempfile.TemporaryDirectory() as tmpdir,
        ):
            successes, failures = download_wheels(
                "testpkg",
                "1.0",
                tmpdir,
                platforms=["win_amd64", "linux_x86_64"],
                python_versions=["312", "311"],
            )
        assert len(successes) == 4
        assert len(failures) == 0

    def test_binary_failure_with_source_fallback(self):
        def mock_run(cmd, **kwargs):
            if "--only-binary=:all:" in cmd:
                return subprocess.CompletedProcess(
                    args=[], returncode=1, stdout="", stderr="No matching wheel"
                )
            return subprocess.CompletedProcess(
                args=[], returncode=0, stdout="", stderr=""
            )

        with (
            patch.object(subprocess, "run", side_effect=mock_run),
            tempfile.TemporaryDirectory() as tmpdir,
        ):
            successes, failures = download_wheels(
                "testpkg",
                "1.0",
                tmpdir,
                platforms=["win_amd64"],
                python_versions=["312"],
            )
        assert len(successes) == 1
        assert successes[0] == ("win_amd64", "312", "source")

    def test_binary_and_source_both_fail(self):
        mock_result_fail = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr="No matching distribution"
        )

        with (
            patch.object(subprocess, "run", return_value=mock_result_fail),
            tempfile.TemporaryDirectory() as tmpdir,
        ):
            successes, failures = download_wheels(
                "testpkg",
                "1.0",
                tmpdir,
                platforms=["win_amd64"],
                python_versions=["312"],
            )
        assert len(successes) == 0
        assert len(failures) == 1
        assert failures[0][0] == "win_amd64"
        assert failures[0][1] == "312"

    def test_no_binary_fallback_disabled(self):
        def mock_run(cmd, **kwargs):
            if "--only-binary=:all:" in cmd:
                return subprocess.CompletedProcess(
                    args=[], returncode=1, stdout="", stderr="No matching wheel"
                )
            return subprocess.CompletedProcess(
                args=[], returncode=0, stdout="", stderr=""
            )

        with (
            patch.object(subprocess, "run", side_effect=mock_run),
            tempfile.TemporaryDirectory() as tmpdir,
        ):
            successes, failures = download_wheels(
                "testpkg",
                "1.0",
                tmpdir,
                platforms=["win_amd64"],
                python_versions=["312"],
                no_binary_fallback=False,
            )
        assert len(successes) == 0
        assert len(failures) == 1

    def test_default_platforms_and_versions(self):
        mock_result = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )
        with (
            patch.object(subprocess, "run", return_value=mock_result),
            tempfile.TemporaryDirectory() as tmpdir,
        ):
            successes, failures = download_wheels("testpkg", "1.0", tmpdir)
        from portapkg.installer.platform import (
            DEFAULT_PLATFORMS,
            DEFAULT_PYTHON_VERSIONS,
        )

        expected = len(DEFAULT_PLATFORMS) * len(DEFAULT_PYTHON_VERSIONS)
        assert len(successes) == expected
        assert len(failures) == 0

    def test_python_version_dotted_format(self):
        mock_result = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )

        with (
            patch.object(subprocess, "run", return_value=mock_result) as mock_run,
            tempfile.TemporaryDirectory() as tmpdir,
        ):
            download_wheels(
                "testpkg",
                "1.0",
                tmpdir,
                platforms=["win_amd64"],
                python_versions=["312"],
            )

        call_args = mock_run.call_args[0][0]
        pyver_idx = call_args.index("--python-version") + 1
        assert call_args[pyver_idx] == "3.12"

    def test_correct_pip_command(self):
        mock_result = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )

        with (
            patch.object(subprocess, "run", return_value=mock_result) as mock_run,
            tempfile.TemporaryDirectory() as tmpdir,
        ):
            download_wheels(
                "testpkg",
                "1.0",
                tmpdir,
                platforms=["win_amd64"],
                python_versions=["312"],
            )

        call_args = mock_run.call_args[0][0]
        assert "pip" in call_args
        assert "download" in call_args
        assert "--dest" in call_args
        assert "--platform" in call_args
        assert "--python-version" in call_args
        assert "--only-binary=:all:" in call_args
        assert "--no-deps" in call_args
        assert "testpkg==1.0" in call_args


class TestDownloadSinglePlatform:
    def test_successful_download(self):
        mock_result = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )
        with (
            patch.object(subprocess, "run", return_value=mock_result),
            tempfile.TemporaryDirectory() as tmpdir,
        ):
            result = download_single_platform("testpkg", "1.0", tmpdir)
        assert result is True

    def test_failed_download(self):
        mock_result = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr="ERROR"
        )
        with (
            patch.object(subprocess, "run", return_value=mock_result),
            tempfile.TemporaryDirectory() as tmpdir,
        ):
            import pytest
            with pytest.raises(RuntimeError, match="Failed to download"):
                download_single_platform("testpkg", "1.0", tmpdir)

    def test_correct_command(self):
        mock_result = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )
        with (
            patch.object(subprocess, "run", return_value=mock_result) as mock_run,
            tempfile.TemporaryDirectory() as tmpdir,
        ):
            download_single_platform("testpkg", "1.0", tmpdir)

        call_args = mock_run.call_args[0][0]
        assert "pip" in call_args
        assert "download" in call_args
        assert "--no-deps" in call_args
        assert "testpkg==1.0" in call_args
        assert "--platform" not in call_args
        assert "--only-binary" not in call_args


class TestWheelExists:
    def test_no_dest_dir(self, tmp_path):
        assert _wheel_exists("pkg", "1.0", str(tmp_path / "nonexistent")) is False

    def test_empty_dir(self, tmp_path):
        assert _wheel_exists("pkg", "1.0", str(tmp_path)) is False

    def test_skips_non_wheel_files(self, tmp_path):
        (tmp_path / "pkg-1.0.tar.gz").write_text("")
        (tmp_path / "random.txt").write_text("")
        assert _wheel_exists("pkg", "1.0", str(tmp_path)) is False

    def test_matching_wheel_exists(self, tmp_path):
        (tmp_path / "pkg-1.0-py3-none-any.whl").write_text("")
        assert _wheel_exists("pkg", "1.0", str(tmp_path)) is True

    def test_wrong_version_no_match(self, tmp_path):
        (tmp_path / "pkg-2.0-py3-none-any.whl").write_text("")
        assert _wheel_exists("pkg", "1.0", str(tmp_path)) is False

    def test_name_case_insensitive(self, tmp_path):
        (tmp_path / "MyPkg-1.0-py3-none-any.whl").write_text("")
        assert _wheel_exists("mypkg", "1.0", str(tmp_path)) is True

    def test_underscore_normalized_in_name(self, tmp_path):
        (tmp_path / "my-pkg-1.0-py3-none-any.whl").write_text("")
        assert _wheel_exists("my_pkg", "1.0", str(tmp_path)) is True

    def test_platform_match(self, tmp_path):
        (tmp_path / "pkg-1.0-cp312-cp312-win_amd64.whl").write_text("")
        assert _wheel_exists("pkg", "1.0", str(tmp_path), plat="win_amd64") is True

    def test_platform_mismatch(self, tmp_path):
        (tmp_path / "pkg-1.0-cp312-cp312-win_amd64.whl").write_text("")
        assert _wheel_exists("pkg", "1.0", str(tmp_path), plat="linux_x86_64") is False

    def test_platform_mismatch_but_any_wheel_skips(self, tmp_path):
        (tmp_path / "pkg-1.0-py3-none-any.whl").write_text("")
        assert _wheel_exists("pkg", "1.0", str(tmp_path), plat="linux_x86_64") is True

    def test_macos_matching_arch(self, tmp_path):
        (tmp_path / "pkg-1.0-cp312-cp312-macosx_12_0_arm64.whl").write_text("")
        assert _wheel_exists("pkg", "1.0", str(tmp_path), plat="macosx_13_0_arm64") is True

    def test_macos_mismatched_arch(self, tmp_path):
        (tmp_path / "pkg-1.0-cp312-cp312-macosx_12_0_arm64.whl").write_text("")
        assert _wheel_exists("pkg", "1.0", str(tmp_path), plat="macosx_13_0_x86_64") is False
