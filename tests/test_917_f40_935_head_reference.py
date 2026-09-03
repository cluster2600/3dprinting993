"""Garde-fous documentaires et geometriques de la reference culasse F40."""

from __future__ import annotations

import json
import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "twins/reference-917-engine/935-head-reference-f40.json"
DOC = ROOT / "docs/917_935_HEAD_REFERENCE_F40.md"
AUDIT_SCRIPT = ROOT / "twins/reference-917-engine/source/audit_935_scan_scale_f40.py"
OUTER_BUILDER = ROOT / "twins/reference-917-engine/source/build_scan_locked_outer_brep_f40.py"
PACKAGING_RENDERER = ROOT / "twins/reference-917-engine/source/render_scan_locked_4v_packaging_f40.py"
FUNCTIONAL_TRIAL = ROOT / "twins/reference-917-engine/source/build_scan_locked_functional_trial_f40.py"
THICKNESS_AUDIT = ROOT / "twins/reference-917-engine/source/audit_scan_locked_functional_f40.py"


def load_audit_module():
    spec = importlib.util.spec_from_file_location("audit_935_scan_scale_f40", AUDIT_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("impossible de charger l'audit F40")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class HeadReferenceF40Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        cls.doc = DOC.read_text(encoding="utf-8")

    def test_air_and_water_cooled_935_variants_are_separated(self) -> None:
        variants = self.contract["variant_separation"]
        self.assertEqual(variants["selected_reference_family"], "935_air_cooled_two_valve_twin_plug")
        self.assertIn("water_cooled", variants["excluded_as_outer_geometry_reference"])
        self.assertEqual(len(variants["exclusion_source_ids"]), 2)

    def test_scan_is_the_outer_geometry_authority(self) -> None:
        baseline = self.contract["baseline"]
        self.assertEqual(
            baseline["sha256"],
            "4623d5d3b73fe3d03ca988a47543a8dd1be7834d3040e6f7efd1e1e95c766486",
        )
        self.assertFalse(baseline["outer_shape_change_allowed_without_quantified_AB_benefit"])
        self.assertFalse(baseline["global_ellipse_or_box_substitution_allowed"])
        self.assertEqual(baseline["raw_and_derived_geometry_policy"], "local_only_not_committed")
        normalized_doc = " ".join(self.doc.split())
        self.assertIn("noyau elliptique global F39 est rejeté", normalized_doc)

    def test_single_external_ports_and_internal_Y_are_locked(self) -> None:
        race = self.contract["documentary_constraints"]["retro_sport_935_race_head"]
        rules = self.contract["four_valve_design_rules"]
        self.assertEqual(race["external_intake_port_diameter_mm"], 41.0)
        self.assertEqual(race["external_exhaust_port_diameter_mm"], 40.0)
        self.assertEqual(rules["external_intake_interface_count"], 1)
        self.assertEqual(rules["external_exhaust_interface_count"], 1)
        self.assertIn("smooth_Y", rules["internal_branching"])
        self.assertTrue(rules["external_manifold_interface_preserved"])

    def test_scale_is_cross_checked_but_not_certified(self) -> None:
        scale = self.contract["scale_checks"]
        candidates = scale["intake_scale_candidates_mm_per_obj_unit"] + scale["exhaust_scale_candidates_mm_per_obj_unit"]
        self.assertTrue(all(0.97 < value < 1.02 for value in candidates))
        self.assertTrue(0.98 < scale["working_scale_mm_per_obj_unit"] < 1.01)
        self.assertFalse(scale["metrologically_confirmed"])
        self.assertFalse(scale["porsche_917_fitment_certified"])

    def test_only_external_surface_screen_is_open(self) -> None:
        gates = self.contract["release_gates"]
        self.assertTrue(gates["surface_reconstruction_scan_deviation_passed"])
        self.assertTrue(all(value is False for key, value in gates.items() if key != "surface_reconstruction_scan_deviation_passed"))

    def test_outer_builder_uses_local_scan_profiles_without_global_primitives(self) -> None:
        source = OUTER_BUILDER.read_text(encoding="utf-8")
        self.assertIn("largest_section_loop", source)
        self.assertIn("resample_closed", source)
        self.assertIn("addThruSections", source)
        self.assertNotIn("addEllipse", source)
        self.assertNotIn("addBox", source)
        evidence = self.contract["outer_brep_evidence"]
        self.assertEqual(evidence["solid_count"], 1)
        self.assertEqual(evidence["fin_count"], 14)
        self.assertLessEqual(evidence["scan_external_skin_deviation_obj_units"]["p95"], 2.0)
        self.assertLessEqual(evidence["section_profile_deviation_obj_units"]["p95"], 1.5)

    def test_four_valve_packaging_renderer_is_explicitly_non_releasing(self) -> None:
        source = PACKAGING_RENDERER.read_text(encoding="utf-8")
        self.assertIn("COMPONENTS", source)
        self.assertIn("exact_functional_booleans_complete", source)
        self.assertIn('"metal_print_authorized": False', source)

    def test_functional_trial_preserves_robust_boolean_and_blocks_release(self) -> None:
        source = FUNCTIONAL_TRIAL.read_text(encoding="utf-8")
        self.assertIn('engine="manifold"', source)
        self.assertNotIn("result.merge_vertices", source)
        self.assertIn('"oil_gallery_candidate_geometry_included": True', source)
        self.assertIn('"thread_forms_included": False', source)
        self.assertIn('"metal_print_authorized": False', source)
        self.assertIn('"engine_start_authorized": False', source)
        evidence = self.contract["functional_trial_evidence"]
        self.assertTrue(evidence["watertight"])
        self.assertTrue(evidence["is_volume"])
        self.assertEqual(evidence["result_body_count"], 1)
        self.assertEqual(evidence["integrated_openings"]["spark_plug_pilots"], 2)
        self.assertEqual(evidence["integrated_openings"]["head_stud_passages"], 4)
        self.assertTrue(evidence["oil_gallery_candidate"]["geometry_included"])
        self.assertTrue(evidence["oil_gallery_candidate"]["all_passages_straight_and_open_ended"])
        self.assertEqual(evidence["oil_gallery_candidate"]["gas_core_intersection_obj_units3"], 0.0)
        self.assertFalse(evidence["oil_gallery_candidate"]["historical_Porsche_dimensions"])
        self.assertFalse(evidence["oil_gallery_candidate"]["flow_and_pressure_validated"])
        self.assertFalse(evidence["continuous_wall_thickness_verified"])
        self.assertEqual(evidence["release_status"], "blocked")

    def test_exhaustive_thickness_screen_fails_closed(self) -> None:
        source = THICKNESS_AUDIT.read_text(encoding="utf-8")
        self.assertIn("exhaustive_normal_chords", source)
        self.assertIn('"continuous_wall_thickness_verified": False', source)
        self.assertIn('"ct_verified": False', source)
        screen = self.contract["functional_thickness_screen"]
        self.assertEqual(screen["triangle_count"], 391666)
        self.assertGreater(screen["resolved_fraction"], 0.999)
        self.assertFalse(screen["all_resolved_chords_meet_1_5_obj_units"])
        self.assertGreater(screen["resolved_area_below_1_5_obj_units_fraction"], 0.08)
        self.assertFalse(screen["continuous_surface_proof"])

    def test_scale_audit_keeps_geometry_unscaled(self) -> None:
        audit = load_audit_module()
        interfaces = {
            "port_sections": {
                "high_B": [{"diameter_obj_units": value} for value in (41.48, 41.40, 41.60, 41.49, 42.2)],
                "low_B": [{"diameter_obj_units": value} for value in (45.6, 40.04, 40.71)],
            }
        }
        report = audit.build_report(self.contract, interfaces, audit.np.asarray([[-60, -80, -5], [63, 107, 84.0]]))
        self.assertFalse(report["decision"]["geometry_rescaled"])
        self.assertFalse(report["decision"]["global_scale_certified"])
        self.assertLess(report["scale_candidates_mm_per_obj_unit"]["ports_median"], 1.0)
        self.assertGreater(report["scale_candidates_mm_per_obj_unit"]["height_midpoint"], 1.0)


if __name__ == "__main__":
    unittest.main()
