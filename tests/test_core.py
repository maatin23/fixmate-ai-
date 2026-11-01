"""Network-free tests for safety guardrails, report validation and SQLite persistence."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ai_service import AIError
from database import (
    clear_diagnostics,
    delete_diagnostic,
    get_diagnostic,
    get_stats,
    init_db,
    list_diagnostics,
    save_diagnostic,
)
from diagnostic_engine import normalise_image_analysis, normalise_report
from safety import (
    apply_guardrails,
    hazard_level,
    mandatory_professional,
    scan_hazards,
    suppress_advanced_steps,
)


def _report(**overrides):
    report = {
        "summary": "The charger or charging port may be preventing power delivery.",
        "severity": "moderate",
        "confidence": "low",
        "causes": [
            {
                "title": "Faulty charging cable or adapter",
                "explanation": "A damaged cable can stop power delivery without an error code.",
                "likelihood": "high",
                "quick_test": "Try a known-good charger and cable.",
            }
        ],
        "safe_checks": [
            {"title": "Try another outlet", "detail": "Use a socket you know works.", "expected_result": "Power resumes."}
        ],
        "advanced_steps": [
            {"title": "Open the device", "detail": "Inspect the charging port internally."}
        ],
        "tools": [{"name": "Known-good charger", "purpose": "Swap test", "needed_for": "safe checks"}],
        "difficulty": "moderate",
        "estimated_time": "15–30 minutes",
        "professional_repair": {"recommended": False, "urgency": "routine", "reason": "Basic checks first."},
        "uncertainty": "No physical measurements were taken.",
        "when_to_stop": ["Stop if the battery is swollen."],
        "prevention": ["Avoid tight cable bends."],
    }
    report.update(overrides)
    return report


class SafetyGuardrailTests(unittest.TestCase):
    def test_swollen_battery_forces_urgent_referral_and_withholds_advanced_steps(self):
        hazards = scan_hazards("The rear casing is bulging and the battery looks swollen")

        self.assertEqual(hazard_level(hazards), "critical")
        self.assertTrue(mandatory_professional(hazards))
        self.assertTrue(suppress_advanced_steps(hazards))

        guarded, notices, withheld = apply_guardrails(_report(), hazards)
        self.assertTrue(withheld)
        self.assertTrue(guarded["professional_repair"]["recommended"])
        self.assertEqual(guarded["professional_repair"]["urgency"], "urgent")
        self.assertEqual(guarded["advanced_steps"], [])
        self.assertTrue(any("Advanced internal-repair steps are withheld" in notice for notice in notices))

    def test_live_work_instruction_is_removed(self):
        report = _report(
            safe_checks=[
                {"title": "Unplug the charger", "detail": "Keep the device powered off."},
                {"title": "Probe the capacitors with a multimeter", "detail": "Test for residual voltage."},
            ]
        )
        guarded, notices, _ = apply_guardrails(report, [])

        self.assertEqual([step["title"] for step in guarded["safe_checks"]], ["Unplug the charger"])
        self.assertTrue(any("removed one or more suggested actions" in notice for notice in notices))

    def test_refrigerant_text_is_flagged(self):
        hazards = scan_hazards("There is a gas leak from the air conditioner refrigerant line")

        self.assertEqual(hazard_level(hazards), "critical")
        self.assertTrue(mandatory_professional(hazards))


class ReportNormalisationTests(unittest.TestCase):
    def test_missing_summary_is_rejected(self):
        with self.assertRaises(AIError):
            normalise_report({"causes": [{"title": "Cause", "explanation": "Why"}]})

    def test_missing_causes_are_rejected(self):
        with self.assertRaises(AIError):
            normalise_report({"summary": "Something may be wrong."})

    def test_values_are_clamped_and_missing_professional_defaults_to_referral(self):
        raw = _report(severity="severe", confidence="certain")
        raw.pop("professional_repair")
        normalised = normalise_report(raw)

        self.assertEqual(normalised["severity"], "moderate")
        self.assertEqual(normalised["confidence"], "low")
        self.assertTrue(normalised["professional_repair"]["recommended"])
        self.assertTrue(normalised["professional_repair"]["reason"])

    def test_severe_visible_finding_forces_professional_review(self):
        analysis = normalise_image_analysis(
            {
                "summary": "A crack is visible across the display.",
                "visible_findings": [
                    {"area": "Display", "observation": "Cracked glass", "severity": "severe", "confidence": "high"}
                ],
                "professional_review": {"recommended": False, "urgency": "routine", "reason": ""},
            }
        )

        self.assertTrue(analysis["professional_review"]["recommended"])
        self.assertEqual(analysis["professional_review"]["urgency"], "soon")


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"
        init_db(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_save_list_stats_and_delete(self):
        diagnostic_id = save_diagnostic(
            category="smartphone",
            manufacturer="TestCo",
            model="Model One",
            age_range="1–3 years",
            description="The phone will not charge with any known-good cable.",
            symptoms=["Won't charge"],
            onset="Today",
            unusual_signs=[],
            error_code="",
            report=normalise_report(_report()),
            hazards=[],
            safety_notices=[],
            advanced_withheld=False,
            ai_model="test-model",
            db_path=self.db_path,
        )

        saved = get_diagnostic(diagnostic_id, db_path=self.db_path)
        self.assertIsNotNone(saved)
        self.assertEqual(saved["input"]["category_label"], "Smartphones")
        self.assertEqual(saved["model"], "test-model")

        items = list_diagnostics(search="TestCo", db_path=self.db_path)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["model"], "Model One")

        stats = get_stats(db_path=self.db_path)
        self.assertEqual(stats["total"], 1)
        self.assertEqual(stats["category_count"], 1)
        self.assertFalse(stats["professional_count"])

        self.assertTrue(delete_diagnostic(diagnostic_id, db_path=self.db_path))
        self.assertIsNone(get_diagnostic(diagnostic_id, db_path=self.db_path))
        self.assertEqual(clear_diagnostics(db_path=self.db_path), 0)


if __name__ == "__main__":
    unittest.main()
