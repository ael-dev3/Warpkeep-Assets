from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class RepositoryLicensingTests(unittest.TestCase):
    def test_creation_disclosure_is_visible_without_changing_license_scope(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("## Creation disclosure", readme)
        self.assertIn("GPT-5.6 Sol model at Ultra reasoning effort", readme)
        self.assertIn("does not change any license", readme)

    def test_mixed_license_map_keeps_asset_exceptions_explicit(self) -> None:
        license_map = (ROOT / "LICENSE").read_text(encoding="utf-8")

        self.assertIn("mixed-license repository", license_map)
        self.assertIn("LICENSES/Apache-2.0.txt", license_map)
        self.assertIn("LICENSES/CC-BY-4.0.txt", license_map)
        self.assertIn("no separate open-license grant asserted", license_map)
        self.assertIn("does not convert unresolved", license_map)

    def test_both_open_license_texts_are_complete_and_linked(self) -> None:
        apache = (ROOT / "LICENSES" / "Apache-2.0.txt").read_text(encoding="utf-8")
        creative_commons = (ROOT / "LICENSES" / "CC-BY-4.0.txt").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        asset_ledger = (ROOT / "ASSET-LICENSES.md").read_text(encoding="utf-8")

        self.assertIn("Apache License", apache)
        self.assertIn("Version 2.0, January 2004", apache)
        self.assertIn("END OF TERMS AND CONDITIONS", apache)
        self.assertIn("Creative Commons Attribution 4.0 International", creative_commons)
        self.assertIn("LICENSES/Apache-2.0.txt", readme)
        self.assertIn("LICENSES/CC-BY-4.0.txt", readme)
        self.assertIn("How to read the status labels", asset_ledger)
        self.assertIn("Openly licensed sets", asset_ledger)


if __name__ == "__main__":
    unittest.main()
