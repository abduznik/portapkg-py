import sys
from unittest.mock import patch

from portapkg.installer.platform import (
    DEFAULT_PLATFORMS,
    DEFAULT_PYTHON_VERSIONS,
    WHEELS_SUBDIR,
    detect_current_platform,
    detect_current_python,
    parse_wheel_filename,
    platform_tag_matches,
    python_tag_matches,
)


class TestDetectCurrentPlatform:
    def test_windows_amd64(self, monkeypatch):
        monkeypatch.setattr("sys.platform", "win32")
        monkeypatch.setattr("platform.machine", lambda: "AMD64")
        assert detect_current_platform() == "win_amd64"

    def test_windows_x86(self, monkeypatch):
        monkeypatch.setattr("sys.platform", "win32")
        monkeypatch.setattr("platform.machine", lambda: "x86")
        assert detect_current_platform() == "win32"

    def test_linux_x86_64(self, monkeypatch):
        monkeypatch.setattr("sys.platform", "linux")
        monkeypatch.setattr("platform.machine", lambda: "x86_64")
        assert detect_current_platform() == "linux_x86_64"

    def test_linux_aarch64(self, monkeypatch):
        monkeypatch.setattr("sys.platform", "linux")
        monkeypatch.setattr("platform.machine", lambda: "aarch64")
        assert detect_current_platform() == "linux_aarch64"

    def test_macos_arm64(self, monkeypatch):
        monkeypatch.setattr("sys.platform", "darwin")
        monkeypatch.setattr("platform.machine", lambda: "arm64")
        assert detect_current_platform() == "macosx_13_0_arm64"

    def test_macos_x86_64(self, monkeypatch):
        monkeypatch.setattr("sys.platform", "darwin")
        monkeypatch.setattr("platform.machine", lambda: "x86_64")
        assert detect_current_platform() == "macosx_13_0_x86_64"

    def test_unknown(self, monkeypatch):
        monkeypatch.setattr("sys.platform", "freebsd")
        monkeypatch.setattr("platform.machine", lambda: "amd64")
        assert detect_current_platform() == "freebsd_amd64"


class TestDetectCurrentPython:
    def test_detect_current_python(self):
        major = sys.version_info.major
        minor = sys.version_info.minor
        expected = f"{major}{minor}"
        assert detect_current_python() == expected


class TestParseWheelFilename:
    def test_standard_wheel(self):
        result = parse_wheel_filename("instrumation-0.3.0-py3-none-any.whl")
        assert result["name"] == "instrumation"
        assert result["version"] == "0.3.0"
        assert result["python_tag"] == "py3"
        assert result["abi_tag"] == "none"
        assert result["platform_tag"] == "any"

    def test_platform_specific_wheel(self):
        result = parse_wheel_filename(
            "numpy-1.26.0-cp312-cp312-manylinux2014_x86_64.whl"
        )
        assert result["name"] == "numpy"
        assert result["version"] == "1.26.0"
        assert result["platform_tag"] == "manylinux2014_x86_64"

    def test_package_with_hyphens(self):
        result = parse_wheel_filename(
            "my-package-2.1.0-py3-none-any.whl"
        )
        assert result["name"] == "my-package"
        assert result["version"] == "2.1.0"

    def test_build_tag_wheel(self):
        result = parse_wheel_filename(
            "cryptography-41.0.0-1-cp312-cp312-manylinux2014_x86_64.whl"
        )
        assert result["name"] == "cryptography"
        assert result["version"] == "41.0.0"

    def test_not_a_wheel(self):
        assert parse_wheel_filename("source.tar.gz") is None

    def test_malformed_too_few_parts(self):
        assert parse_wheel_filename("foo.whl") is None


class TestPythonTagMatches:
    def test_py3_matches_any_python3(self):
        assert python_tag_matches("py3", "312") is True

    @staticmethod
    def _make_vi(major, minor):
        from types import SimpleNamespace
        return SimpleNamespace(major=major, minor=minor, micro=0)

    def test_cp312_matches_python312(self):
        with patch(
            "portapkg.installer.platform.sys.version_info",
            new=self._make_vi(3, 12),
        ):
            assert python_tag_matches("cp312", "312") is True

    def test_cp312_not_match_python311(self):
        with patch(
            "portapkg.installer.platform.sys.version_info",
            new=self._make_vi(3, 11),
        ):
            assert python_tag_matches("cp312", "311") is False

    def test_py2_py3_matches_python3(self):
        assert python_tag_matches("py2.py3", "312") is True

    def test_wildcard_matches(self):
        assert python_tag_matches("*", "312") is True

    def test_py3_only_matches_python3(self):
        assert python_tag_matches("py3", "39") is True

    def test_cp39_not_match_python310(self):
        with patch(
            "portapkg.installer.platform.sys.version_info",
            new=self._make_vi(3, 10),
        ):
            assert python_tag_matches("cp39", "310") is False

    def test_empty_tag(self):
        assert python_tag_matches("", "312") is True

    def test_bare_cp_tag(self):
        assert python_tag_matches("cp", "312") is True

    def test_bare_py_tag(self):
        assert python_tag_matches("py", "312") is True

    def test_none_tag(self):
        assert python_tag_matches("none", "312") is False

    def test_cp3_major_only(self):
        assert python_tag_matches("cp3", "312") is True

    def test_py3_major_only(self):
        assert python_tag_matches("py3", "39") is True


class TestPlatformTagMatches:
    def test_any_matches_everything(self):
        assert platform_tag_matches("any", "win_amd64") is True
        assert platform_tag_matches("any", "linux_x86_64") is True
        assert platform_tag_matches("any", "macosx_13_0_arm64") is True

    def test_exact_match(self):
        assert (
            platform_tag_matches("win_amd64", "win_amd64") is True
        )

    def test_manylinux_to_linux_same_arch(self):
        assert (
            platform_tag_matches("manylinux2014_x86_64", "linux_x86_64") is True
        )

    def test_manylinux_to_linux_diff_arch(self):
        assert (
            platform_tag_matches("manylinux2014_aarch64", "linux_x86_64") is False
        )

    def test_linux_to_manylinux_same_arch(self):
        assert (
            platform_tag_matches("linux_x86_64", "manylinux2014_x86_64") is True
        )

    def test_macos_cross_version(self):
        assert (
            platform_tag_matches("macosx_12_0_arm64", "macosx_13_0_arm64") is True
        )

    def test_win_diff_arch(self):
        assert (
            platform_tag_matches("win_amd64", "win32") is False
        )

    def test_win_same_arch(self):
        assert platform_tag_matches("win32", "win32") is True

    def test_cross_platform_no_match(self):
        assert (
            platform_tag_matches("win_amd64", "linux_x86_64") is False
        )
        assert (
            platform_tag_matches("macosx_13_0_arm64", "linux_aarch64") is False
        )


class TestConstants:
    def test_default_platforms_count(self):
        assert len(DEFAULT_PLATFORMS) == 6

    def test_default_python_versions_count(self):
        assert len(DEFAULT_PYTHON_VERSIONS) == 5

    def test_default_platforms_content(self):
        assert "win_amd64" in DEFAULT_PLATFORMS
        assert "win32" in DEFAULT_PLATFORMS
        assert "manylinux2014_x86_64" in DEFAULT_PLATFORMS
        assert "manylinux2014_aarch64" in DEFAULT_PLATFORMS
        assert "macosx_13_0_arm64" in DEFAULT_PLATFORMS
        assert "macosx_13_0_x86_64" in DEFAULT_PLATFORMS

    def test_wheels_subdir(self):
        assert WHEELS_SUBDIR == "wheels"
