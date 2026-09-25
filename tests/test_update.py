import hashlib
import io
import json
import ssl
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from u1_filament_automation.update import (
    DEFAULT_UPDATE_TIMEOUT,
    UpdateAsset,
    UpdateError,
    UpdateInfo,
    asset_marker,
    check_for_update,
    download_update,
    github_ssl_context,
    is_newer_version,
    open_update_package,
    select_update,
    update_channel_for_version,
)


class Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        self.close()


def release(
    tag: str,
    asset_name: str,
    payload: bytes = b"installer",
    prerelease: bool = False,
):
    digest = hashlib.sha256(payload).hexdigest()
    return {
        "tag_name": tag,
        "name": f"U1FA {tag}",
        "body": "Fix sicuri / Safe fixes",
        "draft": False,
        "prerelease": prerelease,
        "html_url": f"https://github.com/ubaccu/u1-filament-automation/releases/tag/{tag}",
        "assets": [{
            "name": asset_name,
            "browser_download_url": (
                "https://github.com/ubaccu/u1-filament-automation/releases/"
                f"download/{tag}/{asset_name}"
            ),
            "size": len(payload),
            "digest": f"sha256:{digest}",
        }],
    }


class UpdateTests(unittest.TestCase):
    def test_understands_python_and_github_beta_versions(self):
        self.assertTrue(is_newer_version("v1.7.0-beta.2", "1.7.0b1"))
        self.assertTrue(is_newer_version("v1.7.0", "1.7.0b9"))
        self.assertFalse(is_newer_version("v1.6.9", "1.7.0b1"))
        self.assertEqual(update_channel_for_version("1.7.0b1"), "beta")
        self.assertEqual(update_channel_for_version("1.7.0"), "stable")

    def test_selects_exact_package_for_each_supported_platform(self):
        assets = [
            "U1-Filament-Automation-v1.8.0-macOS-arm64.dmg",
            "U1-Filament-Automation-v1.8.0-macOS-x86_64.dmg",
            "U1-Filament-Automation-v1.8.0-Windows-x64-Setup.exe",
            "U1-Filament-Automation-v1.8.0-Linux-x86_64.AppImage",
        ]
        releases = []
        for name in assets:
            releases.append(release("v1.8.0", name))
        cases = (
            ("Darwin", "arm64", "macOS-arm64.dmg"),
            ("Darwin", "x86_64", "macOS-x86_64.dmg"),
            ("Windows", "AMD64", "Windows-x64-Setup.exe"),
            ("Linux", "x86_64", "Linux-x86_64.AppImage"),
        )
        for system, machine, marker in cases:
            with self.subTest(system=system, machine=machine):
                result = select_update(
                    releases,
                    "1.7.0",
                    "stable",
                    system,
                    machine,
                )
                self.assertIsNotNone(result)
                self.assertTrue(result.asset.name.endswith(marker))
                self.assertEqual(asset_marker(system, machine), marker)

    def test_stable_channel_ignores_prereleases(self):
        beta = release(
            "v1.9.0-beta.1",
            "U1-Filament-Automation-v1.9.0b1-macOS-arm64.dmg",
            prerelease=True,
        )
        stable = release(
            "v1.8.0",
            "U1-Filament-Automation-v1.8.0-macOS-arm64.dmg",
        )
        result = select_update(
            [beta, stable], "1.7.0", "stable", "Darwin", "arm64"
        )
        self.assertEqual(result.version, "1.8.0")

    def test_github_check_uses_public_api_without_credentials(self):
        payload = json.dumps([
            release(
                "v1.8.0-beta.1",
                "U1-Filament-Automation-v1.8.0b1-macOS-arm64.dmg",
                prerelease=True,
            )
        ]).encode()
        captured = {}

        def opener(request, timeout):
            captured["url"] = request.full_url
            captured["headers"] = dict(request.header_items())
            captured["timeout"] = timeout
            return Response(payload)

        result = check_for_update(
            "1.7.0b1",
            system="Darwin",
            machine="arm64",
            opener=opener,
        )
        self.assertEqual(result.version, "1.8.0-beta.1")
        self.assertIn("/releases?per_page=10", captured["url"])
        self.assertNotIn("Authorization", captured["headers"])
        self.assertEqual(captured["timeout"], DEFAULT_UPDATE_TIMEOUT)

    def test_timeout_error_reports_the_effective_limit(self):
        def opener(request, timeout):
            raise TimeoutError("timed out")

        with self.assertRaisesRegex(UpdateError, r"GitHub: timeout dopo 15 s"):
            check_for_update(
                "1.8.0b11",
                system="Darwin",
                machine="x86_64",
                opener=opener,
            )

    def test_default_github_connection_uses_bundled_ca_context(self):
        payload = json.dumps([
            release(
                "v1.8.0-beta.14",
                "U1-Filament-Automation-v1.8.0b14-macOS-x86_64.dmg",
                prerelease=True,
            )
        ]).encode()
        with patch(
            "u1_filament_automation.update.urllib.request.urlopen",
            return_value=Response(payload),
        ) as opener:
            result = check_for_update(
                "1.8.0b13",
                system="Darwin",
                machine="x86_64",
            )
        self.assertEqual(result.version, "1.8.0-beta.14")
        context = opener.call_args.kwargs["context"]
        self.assertIsInstance(context, ssl.SSLContext)
        self.assertTrue(context.get_ca_certs())

    def test_bundled_ca_context_contains_trusted_certificates(self):
        self.assertTrue(github_ssl_context().get_ca_certs())

    def test_download_is_kept_only_after_size_and_sha_match(self):
        payload = b"verified installer bytes"
        digest = hashlib.sha256(payload).hexdigest()
        info = UpdateInfo(
            version="1.8.0",
            tag="v1.8.0",
            title="U1FA 1.8.0",
            notes="",
            release_url="https://github.com/ubaccu/u1-filament-automation/releases/tag/v1.8.0",
            prerelease=False,
            asset=UpdateAsset(
                "U1-Filament-Automation-v1.8.0-macOS-arm64.dmg",
                "https://github.com/ubaccu/u1-filament-automation/releases/download/v1.8.0/app.dmg",
                len(payload),
                digest,
            ),
        )
        with tempfile.TemporaryDirectory() as temporary:
            target = download_update(
                info,
                Path(temporary),
                opener=lambda request, timeout: Response(payload),
            )
            self.assertEqual(target.read_bytes(), payload)
            self.assertFalse(any(Path(temporary).glob("*.part")))

    def test_bad_sha_is_deleted_and_never_becomes_installer(self):
        payload = b"tampered"
        info = UpdateInfo(
            version="1.8.0",
            tag="v1.8.0",
            title="U1FA 1.8.0",
            notes="",
            release_url="https://github.com/ubaccu/u1-filament-automation/releases/tag/v1.8.0",
            prerelease=False,
            asset=UpdateAsset(
                "U1-Filament-Automation-v1.8.0-Windows-x64-Setup.exe",
                "https://github.com/ubaccu/u1-filament-automation/releases/download/v1.8.0/app.exe",
                len(payload),
                "0" * 64,
            ),
        )
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(UpdateError):
                download_update(
                    info,
                    Path(temporary),
                    opener=lambda request, timeout: Response(payload),
                )
            self.assertEqual(list(Path(temporary).iterdir()), [])

    def test_opening_verified_package_is_platform_specific(self):
        with tempfile.TemporaryDirectory() as temporary:
            dmg = Path(temporary) / "update.dmg"
            dmg.write_bytes(b"dmg")
            with patch("u1_filament_automation.update.subprocess.Popen") as launch:
                open_update_package(dmg, "Darwin")
            launch.assert_called_once_with(["/usr/bin/open", str(dmg.resolve())])


if __name__ == "__main__":
    unittest.main()
