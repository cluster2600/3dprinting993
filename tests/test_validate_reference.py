import json
import unittest
from copy import deepcopy

from scripts.validate_reference import ROOT, known_source_ids, validate_file


class ReferenceValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.path = ROOT / "catalog" / "reference" / "993-declared-part-data.json"
        cls.payload = json.loads(cls.path.read_text(encoding="utf-8"))
        cls.sources = known_source_ids()

    def test_shipped_data_is_valid(self) -> None:
        self.assertEqual(validate_file(self.payload, self.sources), [])

    def test_every_entry_names_a_registered_source(self) -> None:
        for entry in self.payload["entries"]:
            self.assertIn(entry["source_id"], self.sources, entry["entry_id"])

    def test_unregistered_source_is_rejected(self) -> None:
        payload = deepcopy(self.payload)
        payload["entries"][0]["source_id"] = "SRC-DOES-NOT-EXIST"

        errors = validate_file(payload, self.sources)

        self.assertTrue(any("is not a registered source" in error for error in errors))

    def test_entry_without_any_fact_is_rejected(self) -> None:
        payload = deepcopy(self.payload)
        entry = payload["entries"][0]
        entry.pop("mass_kg", None)
        entry.pop("dimensions_mm", None)
        entry.pop("material", None)

        errors = validate_file(payload, self.sources)

        self.assertTrue(any("neither mass, dimensions nor material" in error for error in errors))

    def test_negative_mass_is_rejected(self) -> None:
        payload = deepcopy(self.payload)
        payload["entries"][0]["mass_kg"] = -1

        errors = validate_file(payload, self.sources)

        self.assertTrue(any("expected a positive number" in error for error in errors))

    def test_parts_that_delete_safety_carry_a_caveat(self) -> None:
        """Doors, roof, seat, steering wheel and ventilation must warn the reader."""
        flagged = {"993-DOOR-COMPLETE", "993-ROOF-SKIN", "993-VENTILATION-SET", "993-SEAT", "993-STEERING-WHEEL"}
        for entry in self.payload["entries"]:
            if entry["entry_id"] in flagged:
                self.assertIn("caveat", entry, entry["entry_id"])


if __name__ == "__main__":
    unittest.main()
