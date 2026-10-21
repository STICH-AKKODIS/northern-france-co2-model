from __future__ import annotations

import unittest
from pathlib import Path

from north_co2_model.model import (
    build_material_comparison,
    load_model_inputs,
    run_custom_scenario,
    run_scenario,
)


class ModelRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(__file__).resolve().parents[1]
        cls.inputs = load_model_inputs(cls.root)
        cls.announced = run_scenario(cls.inputs, "announced_2030")
        cls.user_case = run_scenario(cls.inputs, "user_inventory_4mt")

    def test_sink_coordinate_and_boundary(self) -> None:
        sink = self.inputs.config["sink"]
        self.assertEqual(sink["x_l93_m"], 636000.0)
        self.assertEqual(sink["y_l93_m"], 7105000.0)
        self.assertEqual(sink["node_type"], "receiving_site")
        self.assertFalse(self.announced.summary["downstream_terminal_shipping_storage_included"])
        self.assertEqual(
            self.announced.summary["model_stages"],
            ["capture", "purification", "transport_to_dunkerque_site"],
        )

    def test_irep_inventory_reconciles(self) -> None:
        total = sum(source.irep_2024_total_co2_tpy for source in self.inputs.sources)
        self.assertAlmostEqual(total, 7_539_800.0, places=3)

    def test_announced_case_uses_anchor_projects(self) -> None:
        active = {
            row["source_id"]
            for row in self.announced.source_results
            if row["allocated_product_co2_tpy"] > 0
        }
        self.assertEqual(active, {"S1", "S3"})
        self.assertAlmostEqual(self.announced.summary["total_purified_co2_tpy"], 1_410_000.0, places=3)
        self.assertLessEqual(
            self.announced.summary["total_purified_co2_tpy"],
            self.announced.summary["sink_capacity_tpy"],
        )

    def test_stage_mass_balances(self) -> None:
        for result in (self.announced, self.user_case):
            for row in result.source_results:
                self.assertAlmostEqual(
                    row["captured_before_purification_tpy"],
                    row["allocated_product_co2_tpy"] + row["purification_loss_tpy"],
                    places=6,
                )
            self.assertAlmostEqual(
                result.summary["total_purified_co2_tpy"] - result.summary["pipeline_leakage_tpy"],
                result.summary["sink_received_after_pipeline_leakage_tpy"],
                places=6,
            )

    def test_sink_capacity_is_enforced(self) -> None:
        self.assertLessEqual(
            self.user_case.summary["total_purified_co2_tpy"],
            self.user_case.summary["sink_capacity_tpy"] + 1e-6,
        )
        self.assertGreaterEqual(self.user_case.summary["total_curtailed_product_co2_tpy"], 0.0)

    def test_active_inventory_is_compact_five_source_set(self) -> None:
        self.assertEqual([source.source_id for source in self.inputs.sources], ["S1", "S2", "S3", "S4", "S5"])
        self.assertEqual(len(self.inputs.sources), 5)

    def test_peng_robinson_is_used_in_transport(self) -> None:
        self.assertEqual(self.announced.summary["transport_equation_of_state"], "Peng-Robinson")
        self.assertGreater(self.announced.summary["transport_eos_density_min_kg_per_m3"], 0.0)
        for segment in self.announced.pipeline_segments:
            self.assertEqual(segment["equation_of_state"], "Peng-Robinson")
            self.assertGreater(segment["eos_density_kg_per_m3"], 0.0)
            self.assertGreater(segment["eos_compressibility_factor"], 0.0)

    def test_environmental_study_reconciles(self) -> None:
        summary = self.announced.summary
        self.assertTrue(summary["environmental_study_included"])
        self.assertGreater(summary["environmental_total_climate_burden_tco2e_per_year"], 0.0)
        self.assertLessEqual(
            summary["environmental_lifecycle_net_avoided_co2_tpy"],
            summary["chain_net_avoided_co2_tpy"],
        )
        self.assertGreater(len(summary["environmental_transport_benchmarks"]), 0)

    def test_hydraulic_constraints(self) -> None:
        transport = self.inputs.config["transport"]
        for result in (self.announced, self.user_case):
            self.assertGreaterEqual(
                result.summary["minimum_arrival_pressure_bar"] + 1e-8,
                transport["minimum_arrival_pressure_bar"],
            )
            for segment in result.pipeline_segments:
                self.assertLessEqual(
                    segment["velocity_m_per_s"],
                    transport["maximum_velocity_m_per_s"] + 1e-8,
                )


    def test_pipeline_material_screen_reconciles(self) -> None:
        summary = self.announced.summary
        self.assertEqual(summary["pipeline_material_id"], "x65")
        self.assertGreater(summary["pipeline_steel_mass_t"], 0.0)
        self.assertGreater(summary["pipeline_wall_thickness_min_mm"], 0.0)
        self.assertAlmostEqual(
            summary["pipeline_material_embodied_carbon_delta_tco2e"],
            0.0,
            places=6,
        )
        for segment in self.announced.pipeline_segments:
            self.assertAlmostEqual(segment["material_capex_multiplier"], 1.0, places=12)

    def test_low_carbon_steel_tradeoff_is_visible(self) -> None:
        comparison = {
            row["material_id"]: row
            for row in build_material_comparison(
                self.announced, self.inputs.config, carbon_value_eur_per_t=100.0
            )
        }
        self.assertEqual(set(comparison), set(self.inputs.config["transport"]["materials"]))
        self.assertLess(
            comparison["x65_low_carbon"]["pipeline_material_embodied_carbon_tco2e"],
            comparison["x65"]["pipeline_material_embodied_carbon_tco2e"],
        )
        self.assertGreater(
            comparison["x65_low_carbon"]["pipeline_capex_eur"],
            comparison["x65"]["pipeline_capex_eur"],
        )

    def test_custom_material_override_does_not_mutate_inputs(self) -> None:
        custom = run_custom_scenario(
            self.inputs,
            active_source_ids=["S1", "S3"],
            flow_basis="announced_product",
            sink_capacity_tpy=1_500_000.0,
            transport_overrides={"pipeline_material": "x65_low_carbon"},
        )
        self.assertEqual(custom.summary["pipeline_material_id"], "x65_low_carbon")
        self.assertEqual(self.inputs.config["transport"]["pipeline_material"], "x65")
        self.assertLess(
            custom.summary[
                "environmental_pipeline_material_delta_annualized_tco2e_per_year"
            ],
            0.0,
        )

    def test_three_stage_costs_are_separate_and_reconcile(self) -> None:
        summary = self.announced.summary
        self.assertGreater(summary["capture_capex_eur"], 0.0)
        self.assertGreater(summary["purification_capex_eur"], 0.0)
        self.assertGreater(summary["pipeline_capex_eur"], 0.0)
        self.assertNotIn("terminal_capex_eur", summary)
        self.assertAlmostEqual(
            summary["total_chain_capex_eur"],
            summary["capture_capex_eur"]
            + summary["purification_capex_eur"]
            + summary["pipeline_capex_eur"],
            places=6,
        )
        self.assertAlmostEqual(
            summary["total_chain_annual_cost_eur"],
            summary["capture_annual_cost_eur"]
            + summary["purification_annual_cost_eur"]
            + summary["pipeline_annual_cost_eur"],
            places=6,
        )

    def test_active_products_pass_six_component_screen(self) -> None:
        self.assertEqual(self.user_case.summary["product_spec_components_screened"], 6)
        self.assertEqual(self.user_case.summary["product_spec_components_in_reference"], 27)
        self.assertAlmostEqual(
            self.user_case.summary["product_spec_screening_coverage_fraction"],
            6 / 27,
            places=12,
        )
        screened = {limit.component for limit in self.inputs.product_limits}
        referenced = {limit.component for limit in self.inputs.reference_product_limits}
        self.assertTrue(screened.issubset(referenced))
        self.assertEqual(
            set(self.user_case.summary["product_spec_components_not_screened"]),
            referenced - screened,
        )
        for row in self.user_case.source_results:
            if row["allocated_product_co2_tpy"] > 0:
                self.assertTrue(row["product_spec_screening_pass"], row["product_spec_failures"])

    def test_uncertainty_range_contains_base_case(self) -> None:
        summary = self.user_case.summary
        self.assertLess(summary["full_chain_cost_low_eur_per_t_received"], summary["full_chain_cost_eur_per_t_received"])
        self.assertGreater(summary["full_chain_cost_high_eur_per_t_received"], summary["full_chain_cost_eur_per_t_received"])

    def test_custom_case_does_not_modify_base_inputs(self) -> None:
        original_scenarios = set(self.inputs.config["scenarios"])
        custom = run_custom_scenario(
            self.inputs,
            active_source_ids=["S1"],
            flow_basis="irep_2024_total",
            sink_capacity_tpy=1_500_000.0,
            finance_overrides={"electricity_price_eur_per_mwh": 100.0},
        )
        self.assertEqual(custom.summary["active_sources"], 1)
        self.assertEqual(set(self.inputs.config["scenarios"]), original_scenarios)

    def test_source_specific_capture_target_propagates(self) -> None:
        base = run_custom_scenario(
            self.inputs,
            active_source_ids=["S2"],
            flow_basis="irep_2024_total",
            sink_capacity_tpy=1_500_000.0,
        )
        high_capture = run_custom_scenario(
            self.inputs,
            active_source_ids=["S2"],
            flow_basis="irep_2024_total",
            sink_capacity_tpy=1_500_000.0,
            source_overrides={"S2": {"capture_rate": 0.98}},
        )
        base_row = next(row for row in base.source_results if row["source_id"] == "S2")
        high_row = next(row for row in high_capture.source_results if row["source_id"] == "S2")
        self.assertAlmostEqual(high_row["capture_rate"], 0.98)
        self.assertGreater(
            high_row["allocated_product_co2_tpy"],
            base_row["allocated_product_co2_tpy"],
        )
        self.assertGreater(
            high_row["capture_electricity_mwh_per_year"],
            base_row["capture_electricity_mwh_per_year"],
        )
        self.assertGreater(
            high_capture.summary["capture_annual_cost_eur"],
            base.summary["capture_annual_cost_eur"],
        )

    def test_purity_target_changes_cost_quality_safety_and_eos(self) -> None:
        low_purity = run_custom_scenario(
            self.inputs,
            active_source_ids=["S2"],
            flow_basis="irep_2024_total",
            sink_capacity_tpy=1_500_000.0,
            source_overrides={"S2": {"product_co2_mol_pct": 95.0}},
        )
        high_purity = run_custom_scenario(
            self.inputs,
            active_source_ids=["S2"],
            flow_basis="irep_2024_total",
            sink_capacity_tpy=1_500_000.0,
            source_overrides={"S2": {"product_co2_mol_pct": 99.95}},
        )
        low_row = next(row for row in low_purity.source_results if row["source_id"] == "S2")
        high_row = next(row for row in high_purity.source_results if row["source_id"] == "S2")
        self.assertFalse(low_row["product_spec_pass"])
        self.assertEqual(low_row["process_safety_screen_status"], "Amber")
        self.assertTrue(high_row["product_spec_pass"])
        self.assertGreater(
            high_row["purification_electricity_mwh_per_year"]
            / high_row["allocated_product_co2_tpy"],
            low_row["purification_electricity_mwh_per_year"]
            / low_row["allocated_product_co2_tpy"],
        )
        self.assertAlmostEqual(
            low_purity.summary["transport_eos_composition_mol_fraction"]["CO2"],
            0.95,
            places=6,
        )
        self.assertGreater(
            high_purity.summary["transport_eos_density_min_kg_per_m3"],
            low_purity.summary["transport_eos_density_min_kg_per_m3"],
        )

    def test_capture_and_purification_technologies_are_independent_by_source(self) -> None:
        custom = run_custom_scenario(
            self.inputs,
            active_source_ids=["S1", "S3"],
            flow_basis="irep_2024_total",
            sink_capacity_tpy=1_500_000.0,
            source_overrides={
                "S1": {
                    "capture_technology_id": "post_combustion_amine",
                    "capture_rate": 0.95,
                    "purification_technology_id": "membrane_hybrid",
                    "purification_recovery": 0.97,
                    "product_co2_mol_pct": 98.0,
                    "product_h2o_ppmv": 30.0,
                    "product_o2_ppmv": 100.0,
                    "product_nox_ppmv": 2.0,
                    "product_sox_ppmv": 2.0,
                    "product_co_ppmv": 100.0,
                }
            },
        )
        rows = {row["source_id"]: row for row in custom.source_results}
        self.assertEqual(rows["S1"]["capture_technology_id"], "post_combustion_amine")
        self.assertEqual(rows["S1"]["purification_technology_id"], "membrane_hybrid")
        self.assertEqual(rows["S3"]["capture_technology_id"], "oxyfuel_cryocap")
        self.assertEqual(rows["S3"]["purification_technology_id"], "cryogenic_polishing")
        self.assertEqual(
            next(source for source in self.inputs.sources if source.source_id == "S1").capture_technology_id,
            "cryocap_fg",
        )

    def test_infeasible_target_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "outside the configured technically screened range"):
            run_custom_scenario(
                self.inputs,
                active_source_ids=["S4"],
                flow_basis="irep_2024_total",
                sink_capacity_tpy=1_500_000.0,
                source_overrides={"S4": {"capture_rate": 0.98}},
            )


if __name__ == "__main__":
    unittest.main()
