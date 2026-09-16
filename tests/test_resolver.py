import subprocess
from unittest.mock import patch

from portapkg.bundler.resolver import (
    _parse_package_version,
    freeze_snapshot,
    resolve_dependencies,
)


class TestParsePackageVersion:
    def test_wheel_simple(self):
        name, version = _parse_package_version("instrumation-0.3.0-py3-none-any.whl")
        assert name == "instrumation"
        assert version == "0.3.0"

    def test_wheel_with_hyphens(self):
        name, version = _parse_package_version(
            "my-package-1.2.3-cp312-cp312-manylinux2014_x86_64.whl"
        )
        assert name == "my-package"
        assert version == "1.2.3"

    def test_sdist_tar_gz(self):
        name, version = _parse_package_version("package-1.0.0.tar.gz")
        assert name == "package"
        assert version == "1.0.0"

    def test_sdist_zip(self):
        name, version = _parse_package_version("package-2.0.0.zip")
        assert name == "package"
        assert version == "2.0.0"

    def test_sdist_tar_bz2(self):
        name, version = _parse_package_version("package-3.0.0.tar.bz2")
        assert name == "package"
        assert version == "3.0.0"

    def test_unknown_extension(self):
        name, version = _parse_package_version("file.whl.not")
        assert name is None
        assert version is None

    def test_no_extension(self):
        name, version = _parse_package_version("somefile")
        assert name is None
        assert version is None


class TestFreezeSnapshot:
    def test_freeze_parses_packages(self):
        fake_output = "pip==23.0\nsetuptools==68.0.0\nrequests==2.31.0\n"
        mock_result = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=fake_output, stderr=""
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            result = freeze_snapshot()
        assert result["pip"] == "23.0"
        assert result["setuptools"] == "68.0.0"
        assert result["requests"] == "2.31.0"

    def test_freeze_skips_editable_and_urls(self):
        fake_output = (
            "pip==23.0\n"
            "-e /path/to/pkg\n"
            "mypkg @ file:///local/pkg\n"
            "setuptools==68.0.0\n"
        )
        mock_result = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=fake_output, stderr=""
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            result = freeze_snapshot()
        assert "pip" in result
        assert "setuptools" in result
        assert len(result) == 2

    def test_freeze_handles_empty_output(self):
        mock_result = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            result = freeze_snapshot()
        assert result == {}

    def test_freeze_raises_on_failure(self):
        mock_result = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr="ERROR"
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            import pytest

            with pytest.raises(RuntimeError, match="pip freeze failed"):
                freeze_snapshot()

    def test_freeze_handles_comment_lines(self):
        fake_output = (
            "# This is a comment\npip==23.0\n## Another comment\nsetuptools==68.0.0\n"
        )
        mock_result = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=fake_output, stderr=""
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            result = freeze_snapshot()
        assert result["pip"] == "23.0"
        assert result["setuptools"] == "68.0.0"
        assert len(result) == 2


class TestResolveDroppedDeps:
    def test_warns_on_unresolved_dep(self, capsys):
        fake_download = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )

        def inject_none_dep(pkg, all_deps, tmpdir, platforms):
            all_deps["colorama"] = None

        with (
            patch.object(subprocess, "run", return_value=fake_download),
            patch(
                "portapkg.bundler.resolver._resolve_conditional_tree",
                side_effect=inject_none_dep,
            ),
            patch("portapkg.bundler.resolver.tempfile.TemporaryDirectory") as mock_tmp,
            patch("os.listdir", return_value=[]),
        ):
            mock_tmp.return_value.__enter__ = lambda s, *a: "/tmp/fake"
            mock_tmp.return_value.__exit__ = lambda s, *a: None
            result = resolve_dependencies("requests", platforms=["win_amd64"])

        captured = capsys.readouterr()
        assert "WARNING" in captured.err
        assert "colorama" in captured.err
        assert "colorama" not in result

    def test_no_warning_when_all_deps_resolved(self, capsys):
        fake_download = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )

        with (
            patch.object(subprocess, "run", return_value=fake_download),
            patch("portapkg.bundler.resolver.tempfile.TemporaryDirectory") as mock_tmp,
            patch("os.listdir", return_value=[]),
        ):
            mock_tmp.return_value.__enter__ = lambda s, *a: "/tmp/fake"
            mock_tmp.return_value.__exit__ = lambda s, *a: None
            resolve_dependencies("requests")

        captured = capsys.readouterr()
        assert "WARNING" not in captured.err
