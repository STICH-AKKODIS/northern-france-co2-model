from __future__ import annotations

import unittest
from dataclasses import replace
from pathlib import Path

from north_co2_model.model import load_model_inputs, run_custom_scenario
from north_co2_model.process_models import (
    calculate_capture_process,
    calculate_purification_process,
    source_flue_composition,
)


class ProcessLinkedModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(__file__).resolve().parents[1]
        cls.inputs = load_model_inputs(cls.root)

    def _s2_case(self, **source_override: float):
        overrides = {"S2": source_override} if source_override else None
        return run_custom_scenario(
            self.inputs,
            active_source_ids=["S2"],
            flow_basis="irep_2024_total",
            sink_capacity_tpy=1_500_000.0,
            calculation_mode="process_linked",
            source_overrides=overrides,
        )

    def test_papa_mea_reference_quantities_are_reproduced_on_matched_basis(self) -> None:
        source = next(item for item in self.inputs.sources if item.source_id == "S2")
        source = replace(source, capture_rate=0.924545765780385)
        technology = self.inputs.capture_technologies["post_combustion_amine"]
        result = calculate_capture_process(
            source,
            technology,
            self.inputs.process_source_inputs["S2"],
            747_469.18487926,
            {
                **self.inputs.config["finance"],
                "electricity_price_eur_per_mwh": 165.0,
                "steam_price_eur_per_gj": 7.0,
            },
        )
        # Papa NB01: 4.050 GJ/t, 2.829 kg MEA/t, 95.416 mol-% wet CO2.
        self.assertAlmostEqual(result["capture_specific_steam_gj_per_t"], 4.05, delta=0.25)
        self.assertAlmostEqual(result["capture_specific_solvent_kg_per_t"], 2.829, delta=0.15)
        self.assertAlmostEqual(
            result["capture_raw_product_composition_mol_fraction"]["CO2"],
            0.95416,
            delta=0.003,
        )

    def test_papa_train_a_energy_is_matched_on_connected_capture_product(self) -> None:
        source = next(item for item in self.inputs.sources if item.source_id == "S2")
        source = replace(source, capture_rate=0.924545765780385)
        capture = calculate_capture_process(
            source,
            self.inputs.capture_technologies["post_combustion_amine"],
            self.inputs.process_source_inputs["S2"],
            747_469.18487926,
            self.inputs.config["finance"],
        )
        product = 747_469.18487926 * source.purification_recovery
        purification = calculate_purification_process(
            source,
            self.inputs.purification_technologies["standard_dehydration"],
            capture,
            747_469.18487926,
            product,
            self.inputs.config["finance"],
            110.0,
        )
        # Papa train A: 105.94 kWh/t feed CO2 and 42.84 kWhth/t feed CO2.
        self.assertAlmostEqual(
            purification["purification_specific_electricity_mwh_per_t"] * 1000.0,
            105.94,
            delta=8.0,
        )
        self.assertAlmostEqual(
            purification["purification_specific_thermal_mwh_per_t"] * 1000.0,
            42.84,
            delta=8.0,
        )

    def test_stage_handoffs_and_mass_balances_are_explicit(self) -> None:
        result = self._s2_case()
        row = next(item for item in result.source_results if item["source_id"] == "S2")
        self.assertAlmostEqual(
            row["capture_raw_product_co2_tpy"],
            row["purification_feed_co2_tpy"],
            places=8,
        )
        self.assertAlmostEqual(
            row["purification_product_co2_tpy"],
            row["allocated_product_co2_tpy"],
            places=8,
        )
        self.assertLess(abs(row["purification_mass_balance_error_fraction"]), 1e-12)
        self.assertTrue(result.summary["capture_to_purification_connected"])
        self.assertTrue(result.summary["purification_to_transport_connected"])

    def test_compression_is_counted_once_at_purification_boundary(self) -> None:
        row = next(
            item for item in self._s2_case().source_results if item["source_id"] == "S2"
        )
        self.assertFalse(row["capture_compression_included"])
        self.assertTrue(row["purification_compression_included"])
        self.assertGreater(row["purification_compression_electricity_mwh_per_t"], 0.0)

    def test_lower_feed_co2_increases_mea_gas_handling(self) -> None:
        reference = next(
            item for item in self._s2_case().source_results if item["source_id"] == "S2"
        )
        dilute = next(
            item
            for item in self._s2_case(flue_co2_mol_pct=7.0).source_results
            if item["source_id"] == "S2"
        )
        self.assertGreater(
            dilute["capture_specific_electricity_mwh_per_t"],
            reference["capture_specific_electricity_mwh_per_t"],
        )
        self.assertGreater(dilute["capture_capex_eur"], reference["capture_capex_eur"])

    def test_non_mea_capture_does_not_report_mea_consumption(self) -> None:
        result = run_custom_scenario(
            self.inputs,
            active_source_ids=["S1"],
            flow_basis="irep_2024_total",
            sink_capacity_tpy=1_500_000.0,
            calculation_mode="process_linked",
        )
        row = next(item for item in result.source_results if item["source_id"] == "S1")
        self.assertEqual(row["capture_process_family"], "cryogenic_flue_gas")
        self.assertEqual(row["capture_mea_makeup_tpy"], 0.0)

    def test_legacy_screening_mode_reproduces_v073_cost_boundary(self) -> None:
        result = run_custom_scenario(
            self.inputs,
            active_source_ids=["S1", "S3"],
            flow_basis="announced_product",
            sink_capacity_tpy=1_500_000.0,
            calculation_mode="screening",
        )
        self.assertEqual(result.summary["calculation_mode"], "screening")
        self.assertAlmostEqual(
            result.summary["full_chain_cost_eur_per_t_received"],
            82.1755631599236,
            places=8,
        )

    def test_inconsistent_product_targets_are_flagged_without_inventing_inert_gas(self) -> None:
        row = next(
            item
            for item in self._s2_case(product_co2_mol_pct=95.0).source_results
            if item["source_id"] == "S2"
        )
        self.assertFalse(row["purification_product_target_composition_feasible"])
        self.assertGreater(row["product_co2_mol_pct"], 95.0)
        self.assertEqual(row["process_safety_screen_status"], "Amber")

    def test_invalid_flue_composition_is_rejected(self) -> None:
        invalid = {
            **self.inputs.process_source_inputs["S2"],
            "flue_co2_mol_pct": 80.0,
            "flue_h2o_mol_pct": 15.0,
            "flue_o2_mol_pct": 10.0,
        }
        with self.assertRaisesRegex(ValueError, "sum to less than 100 mol-%"):
            source_flue_composition(invalid)


if __name__ == "__main__":
    unittest.main()
