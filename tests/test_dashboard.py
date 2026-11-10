"""Dashboard smoke checks.

The CSV-import contract is verified without the optional Streamlit runtime.
When Streamlit is installed, additional AppTest checks exercise the live UI.
"""

from __future__ import annotations

import logging
import unittest
from pathlib import Path

try:
    from streamlit.testing.v1 import AppTest
except ModuleNotFoundError as exc:
    if exc.name != "streamlit":
        raise
    AppTest = None


APP_PATH = Path(__file__).resolve().parents[1] / "ui" / "app.py"


class DashboardSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if AppTest is None:
            cls.dashboard = None
            return
        prior_logging_disable = logging.root.manager.disable
        logging.disable(logging.WARNING)
        try:
            cls.dashboard = AppTest.from_file(str(APP_PATH), default_timeout=30).run()
        finally:
            logging.disable(prior_logging_disable)

    def require_streamlit(self) -> None:
        if self.dashboard is None:
            self.skipTest(
                "Interactive dashboard tests require Streamlit; "
                "install it with: python -m pip install -r requirements.txt"
            )

    def test_dashboard_loads_without_exception(self) -> None:
        self.require_streamlit()
        self.assertEqual(len(self.dashboard.exception), 0)

    def test_dashboard_has_engineering_and_environmental_tabs(self) -> None:
        self.require_streamlit()
        self.assertEqual(
            [tab.label for tab in self.dashboard.tabs],
            [
                "1  Capture",
                "2  Purification",
                "3  Pipeline trajectory",
                "4  Transport to sink",
                "5  Environmental study",
                "6  Decision lab",
            ],
        )

    def test_default_scenario_and_run_control_are_present(self) -> None:
        self.require_streamlit()
        scenario = next(
            element
            for element in self.dashboard.selectbox
            if element.label == "Choose a scenario"
        )
        self.assertEqual(scenario.value, "Announced projects · 2030")
        self.assertTrue(
            any("Run selected scenario" in button.label for button in self.dashboard.button)
        )

    def test_pipeline_trajectory_uses_csv_import_instead_of_manual_editor(self) -> None:
        # Check the CSV-import workflow even when only the model dependencies are
        # installed (Streamlit's UI-testing package is not available).
        source = APP_PATH.read_text(encoding="utf-8")
        compile(source, str(APP_PATH), "exec")
        self.assertNotIn('"Source route to edit"', source)
        self.assertNotIn('"Use user-defined trajectories"', source)
        self.assertIn("st.file_uploader(", source)
        self.assertIn("parse_route_csv(file.getvalue(), file.name)", source)
        self.assertIn("Upload your route CSV file to begin", source)

        if self.dashboard is not None:
            self.assertFalse(any(
                element.label == "Source route to edit"
                for element in self.dashboard.selectbox
            ))
            self.assertFalse(any(
                element.label == "Use user-defined trajectories"
                for element in self.dashboard.toggle
            ))
            # Streamlit testing alert elements expose their content as `.value`,
            # not `.message` (which previously raised AttributeError).
            self.assertTrue(any(
                "Upload your route CSV file to begin" in element.value
                for element in self.dashboard.info
            ))

    def test_source_technology_and_quality_controls_are_present(self) -> None:
        self.require_streamlit()
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
