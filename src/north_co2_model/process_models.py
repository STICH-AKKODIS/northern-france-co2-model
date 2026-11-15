"""Connected capture and purification engineering calculations.

The functions in this module are deliberately independent of Streamlit.  They
implement a transparent process-linked alternative to the legacy coefficient
screen.  Papa's detailed models informed the stage boundaries, MEA balance,
wet-product handoff, multistage compression, consumables and cost boundaries;
the code here remains a fast multi-source engineering model rather than a copy
of either reference package.
"""

from __future__ import annotations

import math
from typing import Any, Mapping


MW_KG_PER_KMOL = {
    "CO2": 44.0095,
    "H2O": 18.01528,
    "N2": 28.0134,
    "O2": 31.9988,
    "Ar": 39.948,
    "NOx": 46.0055,
    "SOx": 64.066,
    "CO": 28.0101,
    "MEA": 61.083,
}
R_J_PER_MOL_K = 8.314462618
MEA_MW_KG_PER_KMOL = 61.083
CO2_MW_KG_PER_KMOL = MW_KG_PER_KMOL["CO2"]


def _normalise(values: Mapping[str, float]) -> dict[str, float]:
    cleaned = {key: max(float(value), 0.0) for key, value in values.items()}
    total = sum(cleaned.values())
    if total <= 0.0:
        raise ValueError("A gas composition must have a positive total.")
    return {key: value / total for key, value in cleaned.items() if value > 0.0}


def source_flue_composition(process_input: Mapping[str, Any]) -> dict[str, float]:
    """Return a normalized wet flue-gas composition from configurable inputs."""

    co2 = float(process_input["flue_co2_mol_pct"]) / 100.0
    h2o = float(process_input["flue_h2o_mol_pct"]) / 100.0
    o2 = float(process_input["flue_o2_mol_pct"]) / 100.0
    ar = float(process_input.get("flue_ar_mol_pct", 0.9)) / 100.0
    sox = float(process_input.get("flue_sox_ppmv", 0.0)) / 1_000_000.0
    nox = float(process_input.get("flue_nox_ppmv", 0.0)) / 1_000_000.0
    co = float(process_input.get("flue_co_ppmv", 0.0)) / 1_000_000.0
    specified = co2 + h2o + o2 + ar + sox + nox + co
    if co2 <= 0.0:
        raise ValueError("Flue-gas CO2 concentration must be positive.")
    if specified >= 1.0:
        raise ValueError(
            "Configured flue-gas CO2, H2O, O2, Ar and trace components must sum to less than 100 mol-%."
        )
    return _normalise(
        {
            "CO2": co2,
            "H2O": h2o,
            "O2": o2,
            "Ar": ar,
            "SOx": sox,
            "NOx": nox,
            "CO": co,
            "N2": 1.0 - specified,
        }
    )


def _water_saturation_fraction(temperature_c: float, pressure_bar: float) -> float:
    """Water vapour fraction from a Buck-type saturation-pressure correlation."""

    p_sat_kpa = 0.61121 * math.exp(
        (18.678 - temperature_c / 234.5)
        * (temperature_c / (257.14 + temperature_c))
    )
    return min(max(p_sat_kpa / max(pressure_bar * 100.0, 1e-12), 0.0), 0.35)


def _recovery_severity(recovery: float) -> float:
    return -math.log(max(1.0 - min(max(recovery, 0.0), 0.9999), 1e-4))


def _capture_raw_product(
    family: str,
    flue: Mapping[str, float],
    capture_rate: float,
    technology: Mapping[str, Any],
    process_input: Mapping[str, Any],
) -> dict[str, float]:
    pressure_bar = float(
        process_input.get(
            "capture_product_pressure_bar",
            technology.get("capture_product_pressure_bar", 1.5),
        )
    )
    temperature_c = float(
        process_input.get(
            "capture_product_temperature_c",
            technology.get("capture_product_temperature_c", 40.0),
        )
    )
    absorption_family = family in {"mea_absorption", "dmx_absorption"}
    if not absorption_family:
        co2 = float(technology.get("raw_product_co2_mol_pct", 97.0)) / 100.0
        h2o = float(technology.get("raw_product_h2o_ppmv", 10_000.0)) / 1_000_000.0
        o2 = float(technology.get("raw_product_o2_ppmv", 100.0)) / 1_000_000.0
        nox = float(technology.get("raw_product_nox_ppmv", 20.0)) / 1_000_000.0
        sox = float(technology.get("raw_product_sox_ppmv", 20.0)) / 1_000_000.0
        co = float(technology.get("raw_product_co_ppmv", 100.0)) / 1_000_000.0
        ar_share = float(technology.get("raw_product_ar_share_of_inerts", 0.05))
        remainder = max(1.0 - co2 - h2o - o2 - nox - sox - co, 0.0)
        return _normalise(
            {
                "CO2": co2,
                "H2O": h2o,
                "O2": o2,
                "NOx": nox,
                "SOx": sox,
                "CO": co,
                "Ar": remainder * ar_share,
                "N2": remainder * (1.0 - ar_share),
            }
        )

    # Papa's absorber/stripper model transfers traces source by source and then
    # condenses the wet product.  The factors below are configurable and retain
    # the same physical interpretation (fraction of inlet species accompanying
    # one mole of regenerated CO2), without applying MEA energy equations to DMX.
    transfer = {
        "N2": float(technology.get("raw_transfer_fraction_n2", 1.5e-4)),
        "O2": float(technology.get("raw_transfer_fraction_o2", 4.0e-4)),
        "Ar": float(technology.get("raw_transfer_fraction_ar", 5.0e-5)),
        "CO": float(technology.get("raw_transfer_fraction_co", 1.0e-2)),
        "NOx": float(technology.get("raw_transfer_fraction_nox", 0.30)),
        "SOx": float(technology.get("raw_transfer_fraction_sox", 0.81)),
    }
    co2_feed = max(float(flue["CO2"]), 1e-12)
    dry_relative: dict[str, float] = {"CO2": 1.0}
    for component, factor in transfer.items():
        dry_relative[component] = (
            float(flue.get(component, 0.0))
            / co2_feed
            * factor
            / max(capture_rate, 1e-12)
        )
    if family == "mea_absorption":
        dry_relative["MEA"] = float(technology.get("raw_mea_ppmv", 35.0)) / 1_000_000.0
    dry = _normalise(dry_relative)
    condensation_approach = float(technology.get("condenser_saturation_fraction", 0.90))
    water = min(
        _water_saturation_fraction(temperature_c, pressure_bar)
        * condensation_approach,
        0.25,
    )
    return {**{key: value * (1.0 - water) for key, value in dry.items()}, "H2O": water}


def _zero_capture_result(
    family: str,
    raw_composition: Mapping[str, float],
    temperature_c: float,
    pressure_bar: float,
) -> dict[str, Any]:
    return {
        "capture_calculation_method": "process_linked",
        "capture_process_family": family,
        "capture_capex_eur": 0.0,
        "annualized_capture_capex_eur": 0.0,
        "capture_fixed_opex_eur_per_year": 0.0,
        "capture_variable_energy_opex_eur_per_year": 0.0,
        "capture_annual_cost_eur": 0.0,
        "capture_cost_eur_per_t_captured": 0.0,
        "capture_electricity_mwh_per_year": 0.0,
        "capture_steam_gj_per_year": 0.0,
        "capture_cooling_gj_per_year": 0.0,
        "capture_energy_emissions_tpy": 0.0,
        "capture_nonenergy_emissions_tpy": 0.0,
        "capture_solvent_makeup_tpy": 0.0,
        "capture_mea_makeup_tpy": 0.0,
        "capture_water_makeup_tpy": 0.0,
        "capture_specific_electricity_mwh_per_t": 0.0,
        "capture_specific_steam_gj_per_t": 0.0,
        "capture_specific_cooling_gj_per_t": 0.0,
        "capture_specific_solvent_kg_per_t": 0.0,
        "capture_raw_product_composition_mol_fraction": dict(raw_composition),
        "capture_raw_product_temperature_c": temperature_c,
        "capture_raw_product_pressure_bar": pressure_bar,
        "capture_raw_product_co2_tpy": 0.0,
        "capture_mass_balance_error_fraction": 0.0,
        "capture_compression_included": False,
    }


def calculate_capture_process(
    source: Any,
    technology: Mapping[str, Any],
    process_input: Mapping[str, Any],
    captured_flow_tpy: float,
    finance: Mapping[str, Any],
) -> dict[str, Any]:
    """Calculate capture utilities, consumables, cost and wet-product handoff."""

    family = str(technology.get("process_family", "screening_reference"))
    flue = source_flue_composition(process_input)
    raw = _capture_raw_product(
        family, flue, float(source.capture_rate), technology, process_input
    )
    temperature_c = float(
        process_input.get(
            "capture_product_temperature_c",
            technology.get("capture_product_temperature_c", 40.0),
        )
    )
    pressure_bar = float(
        process_input.get(
            "capture_product_pressure_bar",
            technology.get("capture_product_pressure_bar", 1.5),
        )
    )
    if captured_flow_tpy <= 0.0:
        return _zero_capture_result(family, raw, temperature_c, pressure_bar)

    capture_rate = float(source.capture_rate)
    reference_rate = float(technology["reference_capture_rate"])
    reference_co2 = float(technology.get("reference_flue_co2_mol_pct", 14.0)) / 100.0
    flue_co2 = float(flue["CO2"])
    rate_severity = _recovery_severity(capture_rate) / _recovery_severity(reference_rate)

    solvent_makeup_kg_t = 0.0
    mea_makeup_kg_t = 0.0
    water_makeup_kg_t = float(technology.get("water_makeup_kg_per_t", 0.0))
    cooling_gj_t = float(technology.get("cooling_gj_per_t_captured", 0.0))
    if family == "mea_absorption":
        wt_mea = float(technology.get("solvent_active_mass_fraction", 0.30))
        alpha_lean = float(technology.get("lean_loading_mol_per_mol", 0.20))
        delta_alpha_ref = float(
            technology.get("reference_cyclic_loading_mol_per_mol", 0.24)
        )
        high_rate_fraction = max(
            (capture_rate - reference_rate)
            / max(float(technology["maximum_capture_rate"]) - reference_rate, 1e-12),
            0.0,
        )
        delta_alpha = delta_alpha_ref * (
            1.0
            - float(
                technology.get("cyclic_capacity_high_rate_penalty", 0.10)
            )
            * high_rate_fraction
        )
        delta_alpha = min(max(delta_alpha, 0.10), max(0.55 - alpha_lean, 0.10))
        co2_kmol_t = 1000.0 / CO2_MW_KG_PER_KMOL
        solution_kg_t = (
            co2_kmol_t * MEA_MW_KG_PER_KMOL / max(delta_alpha * wt_mea, 1e-12)
        )
        reaction_gj_t = (
            float(technology.get("absorption_heat_kj_per_mol", 84.0))
            * co2_kmol_t
            / 1000.0
        )
        sensible_gj_t = (
            solution_kg_t
            * float(technology.get("solvent_cp_kj_per_kg_k", 3.70))
            * (
                float(technology.get("reboiler_temperature_c", 120.0))
                - float(technology.get("absorber_temperature_c", 40.0))
            )
            * (1.0 - float(technology.get("rich_lean_hx_effectiveness", 0.78)))
            / 1_000_000.0
        )
        water_vaporisation_gj_t = float(
            technology.get("reference_water_vaporisation_gj_per_t", 0.65)
        ) * (solution_kg_t / max(
            co2_kmol_t * MEA_MW_KG_PER_KMOL / (delta_alpha_ref * wt_mea),
            1e-12,
        ))
        steam_gj_t = (
            reaction_gj_t + sensible_gj_t + water_vaporisation_gj_t
        ) * float(technology.get("reboiler_heat_loss_factor", 1.06))
        dilution_factor = 1.0 + float(
            technology.get("dilute_feed_steam_penalty", 0.15)
        ) * max(math.log(max(reference_co2 / flue_co2, 1.0)), 0.0)
        steam_gj_t *= dilution_factor

        # Isothermal blower work across the absorber pressure drop plus the rich
        # solvent pump.  The calculation is per tonne actually captured.
        co2_mol_t = co2_kmol_t * 1000.0
        flue_mol_t = co2_mol_t / max(flue_co2 * capture_rate, 1e-12)
        delta_p_kpa = float(technology.get("absorber_pressure_drop_kpa", 4.8))
        pressure_ratio = (101.325 + delta_p_kpa) / 101.325
        blower_kwh_t = (
            flue_mol_t
            * R_J_PER_MOL_K
            * (float(technology.get("absorber_temperature_c", 40.0)) + 273.15)
            * math.log(pressure_ratio)
            / max(float(technology.get("blower_efficiency", 0.78)), 1e-12)
            / 3_600_000.0
        )
        pump_delta_p_pa = max(
            (float(technology.get("stripper_pressure_bar", 1.5))
             - float(technology.get("absorber_pressure_bar", 1.1)))
            * 100_000.0,
            0.0,
        )
        pump_kwh_t = (
            solution_kg_t
            / max(float(technology.get("solvent_density_kg_per_m3", 1012.0)), 1e-12)
            * pump_delta_p_pa
            / max(float(technology.get("pump_efficiency", 0.75)), 1e-12)
            / 3_600_000.0
        )
        electricity_mwh_t = (blower_kwh_t + pump_kwh_t) / 1000.0
        o2_vol_pct = float(flue.get("O2", 0.0)) * 100.0
        sox_ppmv = float(flue.get("SOx", 0.0)) * 1_000_000.0
        mea_makeup_kg_t = (
            float(technology.get("base_solvent_degradation_kg_per_t", 1.5))
            + float(technology.get("o2_degradation_kg_per_t_per_vol_pct", 0.30))
            * o2_vol_pct
            + float(technology.get("sox_degradation_kg_per_t_per_ppmv", 0.002))
            * sox_ppmv
        )
        solvent_makeup_kg_t = mea_makeup_kg_t
        water_makeup_kg_t = float(technology.get("water_makeup_kg_per_t", 19.0))

        mixture_mw = sum(flue.get(key, 0.0) * MW_KG_PER_KMOL[key] for key in flue)
        flue_mass_kg_t = flue_mol_t / 1000.0 * mixture_mw
        conditioning_gj_t = (
            flue_mass_kg_t
            * float(technology.get("flue_cp_kj_per_kg_k", 1.01))
            * max(float(process_input.get("flue_temperature_c", 120.0)) - 40.0, 0.0)
            / 1_000_000.0
        )
        cooling_gj_t = steam_gj_t * float(
            technology.get("cooling_to_reboiler_ratio", 1.10)
        ) + conditioning_gj_t
    else:
        # Non-MEA technologies retain their technology-specific reference duties.
        # A logarithmic recovery severity follows the increasing reversible work
        # near complete separation; no MEA circulation/degradation equation is used.
        fixed_energy_share = float(technology.get("fixed_energy_share", 0.65))
        severity_factor = fixed_energy_share + (1.0 - fixed_energy_share) * rate_severity
        concentration_factor = (
            max(reference_co2 / flue_co2, 0.25)
            ** float(technology.get("concentration_energy_exponent", 0.12))
        )
        electricity_mwh_t = (
            float(technology["electricity_mwh_per_t_captured"])
            * severity_factor
            * concentration_factor
        )
        steam_gj_t = (
            float(technology["steam_gj_per_t_captured"])
            * severity_factor
            * concentration_factor
        )
        solvent_makeup_kg_t = float(
            technology.get("process_solvent_makeup_kg_per_t", 0.0)
        )
        water_makeup_kg_t = float(technology.get("water_makeup_kg_per_t", 0.0))
        cooling_gj_t = float(
            technology.get("cooling_gj_per_t_captured", steam_gj_t * 1.05)
        )

    reference_capex = float(
        technology.get("process_reference_capex_meur", technology["reference_capex_meur"])
    ) * 1_000_000.0
    scale = (
        captured_flow_tpy / float(technology["reference_capacity_tpy"])
    ) ** float(technology["scale_exponent"])
    gas_handling_ratio = (
        reference_co2 * reference_rate / max(flue_co2 * capture_rate, 1e-12)
    )
    gas_side_fraction = float(technology.get("gas_side_capex_fraction", 0.30))
    capex_factor = (
        1.0 - gas_side_fraction
        + gas_side_fraction * gas_handling_ratio ** 0.60
    ) * (0.85 + 0.15 * rate_severity ** 0.50)
    capex = reference_capex * scale * capex_factor
    discount_rate = float(finance["discount_rate"])
    years = int(finance["project_life_years"])
    if discount_rate == 0.0:
        crf = 1.0 / years
    else:
        factor = (1.0 + discount_rate) ** years
        crf = discount_rate * factor / (factor - 1.0)
    annualized_capex = capex * crf
    fixed_opex = capex * float(technology["fixed_opex_fraction"])
    electricity = captured_flow_tpy * electricity_mwh_t
    steam = captured_flow_tpy * steam_gj_t
    cooling = captured_flow_tpy * cooling_gj_t
    solvent_tpy = captured_flow_tpy * solvent_makeup_kg_t / 1000.0
    water_tpy = captured_flow_tpy * water_makeup_kg_t / 1000.0
    solvent_price = float(technology.get("process_solvent_price_eur_per_kg", 1.82))
    water_price = float(technology.get("process_water_price_eur_per_t", 2.32))
    other_variable = captured_flow_tpy * float(
        technology.get("process_other_variable_opex_eur_per_t", 2.0)
    )
    variable_opex = (
        electricity * float(finance["electricity_price_eur_per_mwh"])
        + steam * float(finance["steam_price_eur_per_gj"])
        + solvent_tpy * 1000.0 * solvent_price
        + water_tpy * water_price
        + other_variable
    )
    annual_cost = annualized_capex + fixed_opex + variable_opex
    energy_emissions = (
        electricity * float(finance["electricity_emission_factor_tco2_per_mwh"])
        + steam * float(finance["steam_emission_factor_tco2_per_gj"])
    )
    solvent_factor = float(technology.get("solvent_emission_factor_tco2e_per_t", 2.50))
    water_factor = float(technology.get("water_emission_factor_tco2e_per_t", 0.000344))
    equipment_factor = float(technology.get("equipment_emission_tco2e_per_meur", 180.0))
    nonenergy_emissions = (
        solvent_tpy * solvent_factor
        + water_tpy * water_factor
        + capex / 1_000_000.0 * equipment_factor / max(years, 1)
    )
    return {
        "capture_calculation_method": "process_linked",
        "capture_process_family": family,
        "capture_capex_eur": capex,
        "annualized_capture_capex_eur": annualized_capex,
        "capture_fixed_opex_eur_per_year": fixed_opex,
        "capture_variable_energy_opex_eur_per_year": variable_opex,
        "capture_annual_cost_eur": annual_cost,
        "capture_cost_eur_per_t_captured": annual_cost / captured_flow_tpy,
        "capture_electricity_mwh_per_year": electricity,
        "capture_steam_gj_per_year": steam,
        "capture_cooling_gj_per_year": cooling,
        "capture_energy_emissions_tpy": energy_emissions,
        "capture_nonenergy_emissions_tpy": nonenergy_emissions,
        "capture_solvent_makeup_tpy": solvent_tpy,
        "capture_mea_makeup_tpy": (
            captured_flow_tpy * mea_makeup_kg_t / 1000.0
        ),
        "capture_water_makeup_tpy": water_tpy,
        "capture_specific_electricity_mwh_per_t": electricity_mwh_t,
        "capture_specific_steam_gj_per_t": steam_gj_t,
        "capture_specific_cooling_gj_per_t": cooling_gj_t,
        "capture_specific_solvent_kg_per_t": solvent_makeup_kg_t,
        "capture_raw_product_composition_mol_fraction": raw,
        "capture_raw_product_temperature_c": temperature_c,
        "capture_raw_product_pressure_bar": pressure_bar,
        "capture_raw_product_co2_tpy": captured_flow_tpy,
        "capture_mass_balance_error_fraction": 0.0,
        "capture_compression_included": False,
    }


def _compression_energy_kwh_per_t_co2(
    composition: Mapping[str, float],
    inlet_pressure_bar: float,
    outlet_pressure_bar: float,
    inlet_temperature_c: float,
    stages: int,
    efficiency: float,
) -> float:
    if outlet_pressure_bar <= inlet_pressure_bar:
        return 0.0
    stages = max(int(stages), 1)
    y = _normalise(composition)
    mixture_mw_kg_per_kmol = sum(
        fraction * MW_KG_PER_KMOL.get(component, MW_KG_PER_KMOL["N2"])
        for component, fraction in y.items()
    )
    r_specific = R_J_PER_MOL_K * 1000.0 / mixture_mw_kg_per_kmol
    kappa = 1.29
    stage_ratio = (outlet_pressure_bar / inlet_pressure_bar) ** (1.0 / stages)
    work_j_kg_mixture = (
        stages
        * kappa
        / (kappa - 1.0)
        * r_specific
        * (inlet_temperature_c + 273.15)
        * (stage_ratio ** ((kappa - 1.0) / kappa) - 1.0)
        / max(efficiency, 1e-12)
    )
    co2_mass_fraction = (
        y.get("CO2", 0.0) * CO2_MW_KG_PER_KMOL / mixture_mw_kg_per_kmol
    )
    return work_j_kg_mixture / 3_600.0 / max(co2_mass_fraction, 1e-12)


def _zero_purification_result(capture: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "purification_calculation_method": "process_linked",
        "purification_capex_eur": 0.0,
        "annualized_purification_capex_eur": 0.0,
        "purification_fixed_opex_eur_per_year": 0.0,
        "purification_variable_energy_opex_eur_per_year": 0.0,
        "purification_annual_cost_eur": 0.0,
        "purification_cost_eur_per_t_product": 0.0,
        "purification_electricity_mwh_per_year": 0.0,
        "purification_thermal_mwh_per_year": 0.0,
        "purification_cooling_mwh_per_year": 0.0,
        "purification_energy_emissions_tpy": 0.0,
        "purification_nonenergy_emissions_tpy": 0.0,
        "purification_specific_electricity_mwh_per_t": 0.0,
        "purification_specific_thermal_mwh_per_t": 0.0,
        "purification_specific_cooling_mwh_per_t": 0.0,
        "purification_compression_electricity_mwh_per_t": 0.0,
        "purification_feed_composition_mol_fraction": dict(
            capture["capture_raw_product_composition_mol_fraction"]
        ),
        "purification_product_composition_mol_fraction": {},
        "purification_feed_co2_tpy": 0.0,
        "purification_product_co2_tpy": 0.0,
        "purification_side_stream_co2_tpy": 0.0,
        "purification_mass_balance_error_fraction": 0.0,
        "purification_compression_included": True,
        "purification_feed_pressure_bar": float(
            capture["capture_raw_product_pressure_bar"]
        ),
        "purification_product_pressure_bar": 0.0,
        "purification_h2_consumption_tpy": 0.0,
        "purification_sorbent_replacement_tpy": 0.0,
        "purification_product_target_composition_feasible": True,
    }


def calculate_purification_process(
    source: Any,
    technology: Mapping[str, Any],
    capture: Mapping[str, Any],
    captured_feed_co2_tpy: float,
    product_co2_tpy: float,
    finance: Mapping[str, Any],
    pipeline_pressure_bar: float,
) -> dict[str, Any]:
    """Condition the actual capture product and transmit it to transport."""

    if captured_feed_co2_tpy <= 0.0 or product_co2_tpy <= 0.0:
        return _zero_purification_result(capture)
    feed_y = _normalise(capture["capture_raw_product_composition_mol_fraction"])
    feed_co2_kmol_y = captured_feed_co2_tpy * 1000.0 / CO2_MW_KG_PER_KMOL
    feed_total_kmol_y = feed_co2_kmol_y / max(feed_y.get("CO2", 0.0), 1e-12)
    feed_kmol_y = {
        component: fraction * feed_total_kmol_y
        for component, fraction in feed_y.items()
    }
    product_co2_kmol_y = product_co2_tpy * 1000.0 / CO2_MW_KG_PER_KMOL
    target_y_co2 = float(source.product_co2_mol_pct) / 100.0
    desired_total_kmol_y = product_co2_kmol_y / max(target_y_co2, 1e-12)

    target_fractions = {
        "H2O": float(source.product_h2o_ppmv) / 1_000_000.0,
        "O2": float(source.product_o2_ppmv) / 1_000_000.0,
        "NOx": float(source.product_nox_ppmv) / 1_000_000.0,
        "SOx": float(source.product_sox_ppmv) / 1_000_000.0,
        "CO": float(source.product_co_ppmv) / 1_000_000.0,
    }
    product_kmol_y: dict[str, float] = {"CO2": product_co2_kmol_y}
    for component, fraction in target_fractions.items():
        product_kmol_y[component] = min(
            desired_total_kmol_y * fraction,
            feed_kmol_y.get(component, 0.0),
        )
    remaining_budget = max(
        desired_total_kmol_y - sum(product_kmol_y.values()), 0.0
    )
    available_inerts = {
        component: feed_kmol_y.get(component, 0.0)
        for component in ("N2", "Ar", "MEA")
    }
    inert_total = sum(available_inerts.values())
    retained_inerts = min(remaining_budget, inert_total)
    for component, available in available_inerts.items():
        if available > 0.0 and inert_total > 0.0:
            product_kmol_y[component] = retained_inerts * available / inert_total
    # If the feed cannot supply enough inert gas to reach a deliberately low CO2
    # target, the actual product becomes purer.  Re-cap each regulated trace on
    # that smaller total so a maximum target is never exceeded by normalization.
    for _ in range(8):
        changed = False
        total_now = sum(product_kmol_y.values())
        for component, target_fraction in target_fractions.items():
            current = product_kmol_y.get(component, 0.0)
            other = total_now - current
            maximum = (
                target_fraction / max(1.0 - target_fraction, 1e-12) * other
            )
            if current > maximum * (1.0 + 1e-12):
                product_kmol_y[component] = maximum
                total_now -= current - maximum
                changed = True
        if not changed:
            break
    product_total_kmol_y = sum(product_kmol_y.values())
    product_y = _normalise(product_kmol_y)
    product_target_feasible = math.isclose(
        product_y.get("CO2", 0.0), target_y_co2, rel_tol=0.0, abs_tol=1e-5
    )

    side_kmol_y = {
        component: max(feed_kmol_y.get(component, 0.0) - product_kmol_y.get(component, 0.0), 0.0)
        for component in set(feed_kmol_y) | set(product_kmol_y)
    }
    balance_error = (
        sum(feed_kmol_y.values())
        - sum(product_kmol_y.values())
        - sum(side_kmol_y.values())
    ) / max(sum(feed_kmol_y.values()), 1e-12)

    stages = int(technology.get("compression_stages", 4))
    efficiency = float(technology.get("compression_isentropic_efficiency", 0.78))
    inlet_pressure = float(capture["capture_raw_product_pressure_bar"])
    compression_kwh_t = _compression_energy_kwh_per_t_co2(
        product_y,
        inlet_pressure,
        pipeline_pressure_bar,
        float(technology.get("compression_intercool_temperature_c", 35.0)),
        stages,
        efficiency,
    )
    family = str(technology.get("process_family", "dehydration_polishing"))
    treatment_kwh_t = float(technology.get("treatment_electricity_kwh_per_t", 5.0))
    purity_min = float(technology["minimum_co2_mol_pct"]) / 100.0
    purity_max = float(technology["maximum_co2_mol_pct"]) / 100.0
    purity_effort = (
        (_recovery_severity(target_y_co2) - _recovery_severity(purity_min))
        / max(
            _recovery_severity(purity_max) - _recovery_severity(purity_min),
            1e-12,
        )
    )
    purity_effort = min(max(purity_effort, 0.0), 1.0)
    treatment_kwh_t += float(
        technology.get("purity_polishing_kwh_per_t_at_maximum", 1.0)
    ) * purity_effort**1.5
    if family == "cryogenic_polishing":
        treatment_kwh_t += float(technology.get("cryogenic_electricity_kwh_per_t", 42.0))
    elif family == "membrane_hybrid":
        recovery = product_co2_tpy / captured_feed_co2_tpy
        treatment_kwh_t += float(technology.get("membrane_reference_kwh_per_t", 18.0)) * (
            _recovery_severity(recovery)
            / _recovery_severity(float(technology["reference_recovery"]))
        )
    elif family == "noncondensable_removal":
        treatment_kwh_t += float(technology.get("separation_electricity_kwh_per_t", 12.0))

    # Bulk water is condensed in the precooler/interstage knockout.  Only water
    # remaining at the configured dryer inlet pressure is assigned to TEG or a
    # molecular sieve regeneration duty.
    dryer_pressure_bar = float(technology.get("drying_inlet_pressure_bar", 25.0))
    dryer_temperature_c = float(technology.get("drying_inlet_temperature_c", 35.0))
    dryer_water_fraction = _water_saturation_fraction(
        dryer_temperature_c, dryer_pressure_bar
    )
    feed_dry_kmol_y = max(
        feed_total_kmol_y - feed_kmol_y.get("H2O", 0.0), 0.0
    )
    dryer_inlet_water_kmol_y = min(
        feed_kmol_y.get("H2O", 0.0),
        dryer_water_fraction
        / max(1.0 - dryer_water_fraction, 1e-12)
        * feed_dry_kmol_y,
    )
    dryer_removed_h2o_kg_y = max(
        dryer_inlet_water_kmol_y - product_kmol_y.get("H2O", 0.0), 0.0
    ) * MW_KG_PER_KMOL["H2O"]
    drying_heat_mj_kg = float(technology.get("drying_regeneration_mj_per_kg_h2o", 4.5))
    drying_hot_kwh_t = (
        dryer_removed_h2o_kg_y
        * drying_heat_mj_kg
        / 3.6
        / max(product_co2_tpy, 1e-12)
        + float(technology.get("drying_fixed_regeneration_kwh_per_t", 0.0))
    )
    deoxygenation = bool(technology.get("deoxygenation", False))
    removed_o2_kmol_y = side_kmol_y.get("O2", 0.0)
    h2_kg_y = removed_o2_kmol_y * 2.0 * 2.01588 if deoxygenation else 0.0
    preheat_kwh_t = (
        float(technology.get("deoxo_preheat_kwh_per_t", 0.0))
        if deoxygenation and removed_o2_kmol_y > 0.0
        else 0.0
    )
    thermal_kwh_t = drying_hot_kwh_t + preheat_kwh_t

    feed_mw = sum(feed_y.get(key, 0.0) * MW_KG_PER_KMOL.get(key, 28.0134) for key in feed_y)
    feed_mass_kg_y = feed_total_kmol_y * feed_mw
    feed_cooling_kwh_t = (
        feed_mass_kg_y
        * float(technology.get("feed_gas_cp_kj_per_kg_k", 0.90))
        * max(float(capture["capture_raw_product_temperature_c"]) - 35.0, 0.0)
        / 3600.0
        / max(product_co2_tpy, 1e-12)
    )
    cooling_kwh_t = (
        compression_kwh_t * float(technology.get("compression_cooling_ratio", 1.05))
        + feed_cooling_kwh_t
        + float(technology.get("additional_cooling_kwh_per_t", 0.0))
    )
    electricity_mwh_t = (compression_kwh_t + treatment_kwh_t) / 1000.0
    thermal_mwh_t = thermal_kwh_t / 1000.0
    cooling_mwh_t = cooling_kwh_t / 1000.0

    reference_capex = float(
        technology.get("process_reference_capex_meur", technology["reference_capex_meur"])
    ) * 1_000_000.0
    scale = (
        product_co2_tpy / float(technology["reference_capacity_tpy"])
    ) ** float(technology["scale_exponent"])
    reference_feed_co2 = float(technology.get("reference_feed_co2_mol_pct", 95.0)) / 100.0
    feed_factor = (
        reference_feed_co2 / max(feed_y.get("CO2", 0.0), 1e-12)
    ) ** float(technology.get("feed_dilution_capex_exponent", 0.18))
    reference_compression = float(technology.get("reference_compression_kwh_per_t", 100.0))
    compression_factor = max(compression_kwh_t / max(reference_compression, 1e-12), 0.20) ** 0.35
    removed_impurity_fraction = (
        sum(side_kmol_y.get(key, 0.0) for key in ("H2O", "O2", "NOx", "SOx", "CO", "N2", "Ar"))
        / max(sum(feed_kmol_y.values()) - feed_co2_kmol_y, 1e-12)
    )
    treatment_factor = feed_factor * (0.90 + 0.20 * removed_impurity_fraction)
    compression_capex_fraction = float(technology.get("compression_capex_fraction", 0.35))
    capex = reference_capex * scale * (
        (1.0 - compression_capex_fraction) * treatment_factor
        + compression_capex_fraction * compression_factor
    )
    discount_rate = float(finance["discount_rate"])
    years = int(finance["project_life_years"])
    if discount_rate == 0.0:
        crf = 1.0 / years
    else:
        factor = (1.0 + discount_rate) ** years
        crf = discount_rate * factor / (factor - 1.0)
    annualized_capex = capex * crf
    fixed_opex = capex * float(technology["fixed_opex_fraction"])
    electricity = product_co2_tpy * electricity_mwh_t
    thermal = product_co2_tpy * thermal_mwh_t
    cooling = product_co2_tpy * cooling_mwh_t
    h2_tpy = h2_kg_y / 1000.0
    sorbent_kg_t = float(technology.get("sorbent_replacement_kg_per_t", 0.02))
    sorbent_tpy = product_co2_tpy * sorbent_kg_t / 1000.0
    variable_opex = (
        electricity * float(finance["electricity_price_eur_per_mwh"])
        + thermal * 3.6 * float(finance["steam_price_eur_per_gj"])
        + cooling * float(finance.get("cooling_price_eur_per_mwh", 5.0))
        + h2_tpy * 1000.0 * float(technology.get("hydrogen_price_eur_per_kg", 6.0))
        + sorbent_tpy * 1000.0 * float(technology.get("sorbent_price_eur_per_kg", 4.0))
        + product_co2_tpy * float(technology.get("process_other_variable_opex_eur_per_t", 2.0))
    )
    annual_cost = annualized_capex + fixed_opex + variable_opex
    cooling_cop = float(technology.get("cooling_cop", 5.0))
    energy_emissions = (
        (electricity + cooling / max(cooling_cop, 1e-12))
        * float(finance["electricity_emission_factor_tco2_per_mwh"])
        + thermal * 3.6 * float(finance["steam_emission_factor_tco2_per_gj"])
    )
    equipment_factor = float(technology.get("equipment_emission_tco2e_per_meur", 180.0))
    sorbent_factor = float(technology.get("sorbent_emission_tco2e_per_t", 1.2))
    h2_factor = float(technology.get("hydrogen_emission_tco2e_per_t", 10.0))
    nonenergy_emissions = (
        capex / 1_000_000.0 * equipment_factor / max(years, 1)
        + sorbent_tpy * sorbent_factor
        + h2_tpy * h2_factor
    )
    return {
        "purification_calculation_method": "process_linked",
        "purification_process_family": family,
        "purification_capex_eur": capex,
        "annualized_purification_capex_eur": annualized_capex,
        "purification_fixed_opex_eur_per_year": fixed_opex,
        "purification_variable_energy_opex_eur_per_year": variable_opex,
        "purification_annual_cost_eur": annual_cost,
        "purification_cost_eur_per_t_product": annual_cost / product_co2_tpy,
        "purification_electricity_mwh_per_year": electricity,
        "purification_thermal_mwh_per_year": thermal,
        "purification_cooling_mwh_per_year": cooling,
        "purification_energy_emissions_tpy": energy_emissions,
        "purification_nonenergy_emissions_tpy": nonenergy_emissions,
        "purification_specific_electricity_mwh_per_t": electricity_mwh_t,
        "purification_specific_thermal_mwh_per_t": thermal_mwh_t,
        "purification_specific_cooling_mwh_per_t": cooling_mwh_t,
        "purification_compression_electricity_mwh_per_t": compression_kwh_t / 1000.0,
        "purification_feed_composition_mol_fraction": feed_y,
        "purification_product_composition_mol_fraction": product_y,
        "purification_feed_co2_tpy": captured_feed_co2_tpy,
        "purification_product_co2_tpy": product_co2_tpy,
        "purification_side_stream_co2_tpy": max(
            captured_feed_co2_tpy - product_co2_tpy, 0.0
        ),
        "purification_mass_balance_error_fraction": balance_error,
        "purification_compression_included": True,
        "purification_feed_pressure_bar": inlet_pressure,
        "purification_product_pressure_bar": pipeline_pressure_bar,
        "purification_h2_consumption_tpy": h2_tpy,
        "purification_sorbent_replacement_tpy": sorbent_tpy,
        "purification_product_target_composition_feasible": product_target_feasible,
        "product_co2_mol_pct_achieved": product_y.get("CO2", 0.0) * 100.0,
        "product_h2o_ppmv_achieved": product_y.get("H2O", 0.0) * 1_000_000.0,
        "product_o2_ppmv_achieved": product_y.get("O2", 0.0) * 1_000_000.0,
        "product_nox_ppmv_achieved": product_y.get("NOx", 0.0) * 1_000_000.0,
        "product_sox_ppmv_achieved": product_y.get("SOx", 0.0) * 1_000_000.0,
        "product_co_ppmv_achieved": product_y.get("CO", 0.0) * 1_000_000.0,
    }
