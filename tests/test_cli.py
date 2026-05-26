import os
import argparse
from unittest.mock import patch

from portapkg.cli import cmd_list, cmd_info, cmd_update


class TestCmdList:
    def test_list_no_bundles_dir(self, capsys):
        with patch("portapkg.cli.BUNDLES_DIR", "/nonexistent/path"):
            cmd_list(None)
        captured = capsys.readouterr()
        assert "No bundles" in captured.out or not captured.out

    def test_list_no_manifests(self, capsys, tmp_path):
        bundle_dir = tmp_path / "testpkg"
        bundle_dir.mkdir()
        with patch("portapkg.cli.BUNDLES_DIR", str(tmp_path)):
            cmd_list(None)
        captured = capsys.readouterr()
        assert "testpkg" in captured.out

    def test_list_with_bundles(self, capsys, manifest_with_wheels):
        bundle_dir, manifest_data, wheel_files = manifest_with_wheels
        bundles_parent = os.path.dirname(bundle_dir)
        with patch("portapkg.cli.BUNDLES_DIR", bundles_parent):
            cmd_list(None)
        captured = capsys.readouterr()
        assert "testpkg" in captured.out
        assert "1.0.0" in captured.out


class TestCmdInfo:
    def test_info_no_bundle(self, capsys):
        with patch("portapkg.cli.BUNDLES_DIR", "/nonexistent"):
            cmd_info(argparse.Namespace(package="nonexistent"))
        captured = capsys.readouterr()
        assert "not found" in captured.out

    def test_info_with_bundle(self, capsys, manifest_with_wheels):
        bundle_dir, manifest_data, wheel_files = manifest_with_wheels
        with patch("portapkg.cli._get_bundle_dir", return_value=bundle_dir):
            cmd_info(argparse.Namespace(package="testpkg"))
        captured = capsys.readouterr()
        assert "testpkg" in captured.out
        assert "1.0.0" in captured.out
        assert "dep1" in captured.out


class TestCmdUpdate:
    def test_update_multi_platform(self):
        with (
            patch("portapkg.cli._ensure_bundles_dir"),
            patch("portapkg.cli._bundle_multi") as mock_multi,
        ):
            args = argparse.Namespace(
                package="testpkg",
                packages=None,
                platforms=None,
                snapshot=False,
            )
            cmd_update(args)
            mock_multi.assert_called_once()

    def test_update_snapshot(self):
        with (
            patch("portapkg.cli._ensure_bundles_dir"),
            patch("portapkg.cli._bundle_snapshot") as mock_snapshot,
        ):
            args = argparse.Namespace(
                package="testpkg",
                packages=None,
                platforms=None,
                snapshot=True,
            )
            cmd_update(args)
            mock_snapshot.assert_called_once()
