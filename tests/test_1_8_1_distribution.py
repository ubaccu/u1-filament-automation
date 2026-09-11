import pathlib
import unittest

import u1_filament_automation


ROOT = pathlib.Path(__file__).resolve().parents[1]


class Final181DistributionTests(unittest.TestCase):
    def test_version_is_1_8_1_everywhere(self):
        self.assertEqual(u1_filament_automation.__version__, "1.8.1")
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('version = "1.8.1"', pyproject)
        self.assertTrue((ROOT / "RELEASE_NOTES_1.8.1.md").is_file())

    def test_desktop_packages_keep_stable_entrypoint(self):
        for platform_name in ("macos", "windows", "linux"):
            bootstrap = (
                ROOT / "packaging" / platform_name / "u1fa_bootstrap.py"
            ).read_text(encoding="utf-8")
            self.assertIn("desktop_app_v180", bootstrap)
            self.assertNotIn("desktop_app_b24", bootstrap)

    def test_stable_entrypoint_layers_patches_in_release_order(self):
        entrypoint = (
            ROOT / "src" / "u1_filament_automation" / "desktop_app_v180.py"
        ).read_text(encoding="utf-8")
        b23 = entrypoint.index("install_b23_patch(gui_module)")
        b24 = entrypoint.index("install_b24_patch(gui_module)")
        final = entrypoint.index("install_v180_patch(gui_module)")
        self.assertLess(b23, b24)
        self.assertLess(b24, final)

    def test_181_release_notes_are_bilingual_and_document_safety(self):
        notes = (ROOT / "RELEASE_NOTES_1.8.1.md").read_text(encoding="utf-8")
        self.assertLess(notes.index("## Italiano"), notes.index("# English"))
        self.assertIn("produttore reale di Spoolman", notes)
        self.assertIn("standalone", notes)
        self.assertIn("Pressure Advance", notes)
        self.assertIn("backup byte-per-byte", notes)
        self.assertIn("Recognizable existing U1FA 1.8.0 profiles are migrated", notes)
        self.assertIn("without losing an existing PA calibration", notes)

    def test_source_archive_contains_final_support_docs_without_dev_ci(self):
        script = (
            ROOT / "packaging" / "source" / "build_source_archive.sh"
        ).read_text(encoding="utf-8")
        for item in (
            '"SUPPORT.md"',
            '"SUPPORT.it.md"',
            '"SECURITY.md"',
            '"docs/APP_UPDATES.md"',
            '"docs/COMPATIBILITA_FIRMWARE.md"',
            '"docs/README.md"',
            '"docs/README.it.md"',
        ):
            self.assertIn(item, script)
        self.assertNotIn('".github/SECURITY.md"', script)

    def test_publish_workflow_maps_stable_version_to_stable_tag(self):
        workflow = (
            ROOT / ".github" / "workflows" / "publish-public-release.yml"
        ).read_text(encoding="utf-8")
        self.assertIn('tag = f"v{actual}"', workflow)
        self.assertIn('prerelease = "false"', workflow)
        self.assertIn('notes = pathlib.Path(f"RELEASE_NOTES_{actual}.md")', workflow)


if __name__ == "__main__":
    unittest.main()
