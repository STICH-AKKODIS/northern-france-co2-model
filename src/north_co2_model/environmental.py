from __future__ import annotations

from typing import Any


# Screening lifecycle factors retained from the project's earlier transport-LCA study.
# Values are climate-change indicators in g CO2-eq per tonne-kilometre.
PIPELINE_USE_GCO2E_PER_TKM_BY_YEAR: dict[int, float] = {
    2020: 4.0,
    2025: 3.5,
    2030: 3.0,
    2035: 2.4,
    2040: 1.9,
    2045: 1.5,
    2050: 1.2,
    2060: 0.8,
    2070: 0.6,
    2080: 0.5,
    2090: 0.4,
    2100: 0.4,
}

ALTERNATIVE_TRANSPORT_GCO2E_PER_TKM_2020: dict[str, float] = {
    "Truck (diesel)": 165.0,
    "Truck (electric)": 155.0,
    "Truck (H2)": 160.0,
    "Barge (diesel)": 98.0,
    "Train (electric)": 72.0,
}


def _interpolate_year(table: dict[int, float], year: int) -> float:
    years = sorted(table)
    if year <= years[0]:
        return float(table[years[0]])
    if year >= years[-1]:
        return float(table[years[-1]])
    for low, high in zip(years[:-1], years[1:]):
        if low <= year <= high:
            fraction = (year - low) / (high - low)
            return float(table[low] + fraction * (table[high] - table[low]))
    raise RuntimeError("Could not interpolate environmental factor.")


def _alternative_factor_for_year(base_2020: float, year: int) -> float:
    """Apply the same screening decarbonisation trajectory used by the prior LCA module."""
    reduction = 0.80 * (year - 2020) / 80.0
    return float(base_2020 * max(1.0 - reduction, 0.20))


def calculate_environmental_study(
    source_results: list[dict[str, Any]],
    pipeline: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    """Return the environmental screening layer for one scenario.

    The engineering model already quantifies capture/purification energy emissions and
    direct pipeline leakage. This layer adds a transparent transport-LCA screening
    estimate based on tonne-kilometres, together with energy totals and alternative
    transport benchmarks. It is intentionally climate/energy focused: site-specific
    biodiversity, water, land-use and construction-corridor impacts require routed
    project data and are not assigned invented numerical scores here.
    """

    env = config["environment"]
    assessment_year = int(env["assessment_year"])
    construction_factor = float(env["pipeline_construction_gco2e_per_tkm"])
    pipeline_use_factor = _interpolate_year(PIPELINE_USE_GCO2E_PER_TKM_BY_YEAR, assessment_year)

    segments = pipeline.get("segments", [])
    tonne_km_per_year = sum(
        float(row["flow_tpy"]) * float(row["route_length_km"])
        for row in segments
    )
    newbuild_tonne_km_per_year = sum(
        float(row["flow_tpy"]) * float(row["route_length_km"])
        for row in segments
        if bool(row.get("include_in_cost", True))
    )

    pipeline_use_emissions = tonne_km_per_year * pipeline_use_factor / 1_000_000.0
    pipeline_construction_emissions = (
        newbuild_tonne_km_per_year * construction_factor / 1_000_000.0
    )
    project_life_years = float(config["finance"]["project_life_years"])
    material_embodied_total = float(
        pipeline.get("pipeline_material_embodied_carbon_tco2e", 0.0)
    )
    material_embodied_delta_total = float(
        pipeline.get("pipeline_material_embodied_carbon_delta_tco2e", 0.0)
    )
    material_embodied_delta_annual = (
        material_embodied_delta_total / project_life_years
        if project_life_years > 0
        else 0.0
    )

    capture_energy_emissions = sum(float(row["capture_energy_emissions_tpy"]) for row in source_results)
    purification_energy_emissions = sum(float(row["purification_energy_emissions_tpy"]) for row in source_results)
    pipeline_leakage = float(pipeline.get("pipeline_leakage_tpy", 0.0))

    capture_electricity = sum(float(row["capture_electricity_mwh_per_year"]) for row in source_results)
    purification_electricity = sum(float(row["purification_electricity_mwh_per_year"]) for row in source_results)
    capture_steam = sum(float(row["capture_steam_gj_per_year"]) for row in source_results)

    allocated_product = sum(float(row["allocated_product_co2_tpy"]) for row in source_results)
    sink_received = max(allocated_product - pipeline_leakage, 0.0)

    total_burden = (
        capture_energy_emissions
        + purification_energy_emissions
        + pipeline_leakage
        + pipeline_use_emissions
        + pipeline_construction_emissions
        + material_embodied_delta_annual
    )
    lifecycle_net_avoided = max(allocated_product - total_burden, 0.0)

    benchmark_rows: list[dict[str, Any]] = []
    effective_construction_factor = (
        construction_factor * newbuild_tonne_km_per_year / tonne_km_per_year
        if tonne_km_per_year > 0.0
        else 0.0
    )
    pipeline_total_factor = pipeline_use_factor + effective_construction_factor
    for mode, base_factor in ALTERNATIVE_TRANSPORT_GCO2E_PER_TKM_2020.items():
        mode_factor = _alternative_factor_for_year(base_factor, assessment_year)
        avoided = max(mode_factor - pipeline_total_factor, 0.0) * tonne_km_per_year / 1_000_000.0
        reduction = (
            1.0 - pipeline_total_factor / mode_factor
            if mode_factor > 0
            else 0.0
        )
        benchmark_rows.append(
            {
                "mode": mode,
                "assessment_year": assessment_year,
                "mode_gco2e_per_tkm": mode_factor,
                "pipeline_gco2e_per_tkm_including_construction": pipeline_total_factor,
                "pipeline_intensity_reduction_fraction": reduction,
                "avoided_transport_emissions_tco2e_per_year": avoided,
            }
        )

    burden_per_t_received = total_burden / sink_received if sink_received else 0.0
    net_efficiency = lifecycle_net_avoided / allocated_product if allocated_product else 0.0

    return {
        "environmental_study_included": True,
        "environmental_assessment_year": assessment_year,
        "environmental_scope": "Climate, energy demand, direct pipeline leakage and transport lifecycle screening",
        "environmental_tonne_km_per_year": tonne_km_per_year,
        "environmental_newbuild_tonne_km_per_year": newbuild_tonne_km_per_year,
        "environmental_capture_electricity_mwh_per_year": capture_electricity,
        "environmental_purification_electricity_mwh_per_year": purification_electricity,
        "environmental_total_electricity_mwh_per_year": capture_electricity + purification_electricity,
        "environmental_capture_steam_gj_per_year": capture_steam,
        "environmental_capture_energy_emissions_tco2e_per_year": capture_energy_emissions,
        "environmental_purification_energy_emissions_tco2e_per_year": purification_energy_emissions,
        "environmental_pipeline_leakage_tco2e_per_year": pipeline_leakage,
        "environmental_pipeline_use_factor_gco2e_per_tkm": pipeline_use_factor,
        "environmental_pipeline_construction_factor_gco2e_per_tkm": construction_factor,
        "environmental_pipeline_effective_construction_factor_gco2e_per_tkm": effective_construction_factor,
        "environmental_pipeline_use_emissions_tco2e_per_year": pipeline_use_emissions,
        "environmental_pipeline_construction_emissions_tco2e_per_year": pipeline_construction_emissions,
        "environmental_pipeline_material_embodied_carbon_tco2e": material_embodied_total,
        "environmental_pipeline_material_delta_vs_baseline_tco2e": material_embodied_delta_total,
        "environmental_pipeline_material_delta_annualized_tco2e_per_year": material_embodied_delta_annual,
        "environmental_total_climate_burden_tco2e_per_year": total_burden,
        "environmental_lifecycle_net_avoided_co2_tpy": lifecycle_net_avoided,
        "environmental_climate_burden_kgco2e_per_t_received": burden_per_t_received * 1000.0,
        "environmental_net_avoidance_efficiency_fraction": net_efficiency,
        "environmental_transport_benchmarks": benchmark_rows,
        "environmental_limitations": [
            "The transport lifecycle factors are screening values, not a project-specific EPD or ISO-compliant LCA.",
            "Only the selected material's embodied-carbon difference versus the X65 reference is added to the annual burden; the generic construction factor already represents the baseline pipeline construction burden.",
            "Segments marked as existing retain use-phase emissions and leakage, but receive no new-construction or new-material burden in this project screen.",
            "Biodiversity, land occupation, water impacts, construction crossings, noise and local air-quality impacts require a routed corridor and site-specific inventory.",
            "No downstream terminal, shipping, injection or geological-storage impacts are included because they remain outside the model boundary.",
        ],
    }
