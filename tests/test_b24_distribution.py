import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class B24DistributionTests(unittest.TestCase):
    def test_b24_release_contract_remains_available(self):
        self.assertTrue(
            (ROOT / "src" / "u1_filament_automation" / "desktop_app_b24.py").is_file()
        )
        self.assertTrue((ROOT / "RELEASE_NOTES_1.8.0b24.md").is_file())

    def test_b24_entrypoint_layers_b23_before_b24(self):
        entrypoint = (
            ROOT / "src" / "u1_filament_automation" / "desktop_app_b24.py"
        ).read_text(encoding="utf-8")
        self.assertLess(
            entrypoint.index("install_b23_patch(gui_module)"),
            entrypoint.index("install_b24_patch(gui_module)"),
        )

    def test_public_release_cleanup_happens_only_after_verification(self):
        workflow = (
            ROOT / ".github" / "workflows" / "publish-public-release.yml"
        ).read_text(encoding="utf-8")
        verify = workflow.index("Release tag SHA does not match the exact source snapshot")
        release_view = workflow.index('gh release view "$TAG" --repo "$PUBLIC_RELEASE_REPOSITORY" --json')
        cleanup = workflow.index('push origin --delete "$PUBLIC_SOURCE_BRANCH"')
        cleanup_check = workflow.index("Temporary public source branch still exists after cleanup")
        self.assertLess(verify, release_view)
        self.assertLess(release_view, cleanup)
        self.assertLess(cleanup, cleanup_check)


if __name__ == "__main__":
    unittest.main()
