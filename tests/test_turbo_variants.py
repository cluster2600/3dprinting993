import json
import unittest

from scripts.generate_turbo_variants import EXPECTED_VARIANTS, MANIFEST, validate_manifest


class TurboVariantValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_manifest_is_valid(self) -> None:
        self.assertEqual(validate_manifest(self.payload), [])

    def test_manifest_contains_the_three_comparison_variants(self) -> None:
        ids = {variant["variant_id"] for variant in self.payload["variants"]}
        self.assertEqual(ids, EXPECTED_VARIANTS)

    def test_variants_keep_the_same_mass_flow(self) -> None:
        flows = {variant["flow"]["mass_flow_per_case_kg_s"] for variant in self.payload["variants"]}
        self.assertEqual(flows, {self.payload["comparison"]["mass_flow_per_case_kg_s"]})


if __name__ == "__main__":
    unittest.main()
