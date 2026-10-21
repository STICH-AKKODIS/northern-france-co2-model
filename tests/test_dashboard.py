from __future__ import annotations

import logging
import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest


class DashboardSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        app_path = Path(__file__).resolve().parents[1] / "ui" / "app.py"
        prior_logging_disable = logging.root.manager.disable
        logging.disable(logging.WARNING)
        try:
            cls.dashboard = AppTest.from_file(str(app_path), default_timeout=30).run()
        finally:
            logging.disable(prior_logging_disable)

    def test_dashboard_loads_without_exception(self) -> None:
        self.assertEqual(len(self.dashboard.exception), 0)

    def test_dashboard_has_engineering_and_environmental_tabs(self) -> None:
        self.assertEqual(
            [tab.label for tab in self.dashboard.tabs],
            [
                "1  Capture",
                "2  Purification",
                "3  Transport to sink",
                "4  Environmental study",
                "5  Decision lab",
            ],
        )

    def test_default_scenario_and_run_control_are_present(self) -> None:
        self.assertEqual(self.dashboard.selectbox[0].value, "Announced projects · 2030")
        self.assertTrue(any("Run selected scenario" in button.label for button in self.dashboard.button))

    def test_source_technology_and_quality_controls_are_present(self) -> None:
        selectbox_labels = [element.label for element in self.dashboard.selectbox]
        slider_labels = [element.label for element in self.dashboard.slider]
        number_input_labels = [element.label for element in self.dashboard.number_input]
        self.assertIn("Capture technology", selectbox_labels)
        self.assertIn("Purification technology", selectbox_labels)
        self.assertIn("CO₂ capture efficiency", slider_labels)
        self.assertIn("CO₂ recovery through purification", slider_labels)
        self.assertIn("Product CO₂ purity (mol-%)", number_input_labels)
        self.assertIn("Product H₂O (ppmv)", number_input_labels)


if __name__ == "__main__":
    unittest.main()
