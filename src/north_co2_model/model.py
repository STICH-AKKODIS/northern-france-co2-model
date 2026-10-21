from __future__ import annotations

import csv
import copy
import itertools
import json
import math
import tomllib
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any, Iterable

import networkx as nx
import numpy as np

from .environmental import calculate_environmental_study


@dataclass(frozen=True)
class Source:
    source_id: str
    source_name: str
    operator: str
    commune: str
    department: str
    region: str
    sector: str
    x_l93_m: float
    y_l93_m: float
    longitude: float
    latitude: float
    user_case_emissions_tpy: float
    irep_2024_total_co2_tpy: float
    irep_2024_fossil_co2_tpy: float
    irep_id: str
    announced_product_co2_tpy: float
    announced_start_year: int | None
    project_name: str
    project_status: str
    capture_technology_id: str
    capture_technology: str
    capturable_fraction: float
    capture_rate: float
    availability: float
    capture_electricity_mwh_per_t_captured: float
    capture_steam_gj_per_t_captured: float
    capture_variable_opex_eur_per_t_captured: float
    capture_reference_capex_meur: float
    capture_reference_capacity_tpy: float
    capture_scale_exponent: float
    capture_fixed_opex_fraction: float
    purification_technology_id: str
    purification_train: str
    purification_recovery: float
    product_co2_mol_pct: float
    product_h2o_ppmv: float
    product_o2_ppmv: float
    product_nox_ppmv: float
    product_sox_ppmv: float
    product_co_ppmv: float
    purification_electricity_mwh_per_t_product: float
    purification_variable_opex_eur_per_t_product: float
    purification_reference_capex_meur: float
    purification_reference_capacity_tpy: float
    purification_scale_exponent: float
    purification_fixed_opex_fraction: float
    priority: int
    routing_factor: float
    assumption_quality: str
    primary_source_url: str


@dataclass(frozen=True)
class ProductLimit:
    component: str
    limit_type: str
    limit_value: float
    unit: str
    source_url: str


@dataclass(frozen=True)
class ReferenceProductLimit:
    component: str
    limit_type: str
    limit_value: float
    unit: str
    screened_in_model: bool
    model_field: str
    validation_status: str
    source_url: str
    notes: str


@dataclass
class ModelInputs:
    root: Path
    config: dict[str, Any]
    sources: list[Source]
    product_limits: list[ProductLimit]
    reference_product_limits: list[ReferenceProductLimit]
    capture_technologies: dict[str, dict[str, Any]]
    purification_technologies: dict[str, dict[str, Any]]


@dataclass
class ScenarioResult:
    scenario: str
    source_results: list[dict[str, Any]]
    pipeline_segments: list[dict[str, Any]]
    summary: dict[str, Any]


def _float(value: str | float | int | None, default: float = 0.0) -> float:
    if value is None or str(value).strip() == "":
        return default
    return float(value)


def _optional_int(value: str | int | None) -> int | None:
    if value is None or str(value).strip() == "":
        return None
    return int(float(value))


def _load_sources(path: Path) -> list[Source]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    sources: list[Source] = []
    for row in rows:
        sources.append(
            Source(
                source_id=row["source_id"],
                source_name=row["source_name"],
                operator=row["operator"],
                commune=row["commune"],
                department=row["department"],
                region=row["region"],
                sector=row["sector"],
                x_l93_m=_float(row["x_l93_m"]),
                y_l93_m=_float(row["y_l93_m"]),
                longitude=_float(row["longitude"]),
                latitude=_float(row["latitude"]),
                user_case_emissions_tpy=_float(row["user_case_emissions_tpy"]),
                irep_2024_total_co2_tpy=_float(row["irep_2024_total_co2_tpy"]),
                irep_2024_fossil_co2_tpy=_float(row["irep_2024_fossil_co2_tpy"]),
                irep_id=row["irep_id"],
                announced_product_co2_tpy=_float(row["announced_product_co2_tpy"]),
                announced_start_year=_optional_int(row["announced_start_year"]),
                project_name=row["project_name"],
                project_status=row["project_status"],
                capture_technology_id=row["capture_technology_id"],
                capture_technology=row["capture_technology"],
                capturable_fraction=_float(row["capturable_fraction"]),
                capture_rate=_float(row["capture_rate"]),
                availability=_float(row["availability"]),
                capture_electricity_mwh_per_t_captured=_float(row["capture_electricity_mwh_per_t_captured"]),
                capture_steam_gj_per_t_captured=_float(row["capture_steam_gj_per_t_captured"]),
                capture_variable_opex_eur_per_t_captured=_float(row["capture_variable_opex_eur_per_t_captured"]),
                capture_reference_capex_meur=_float(row["capture_reference_capex_meur"]),
                capture_reference_capacity_tpy=_float(row["capture_reference_capacity_tpy"]),
                capture_scale_exponent=_float(row["capture_scale_exponent"]),
                capture_fixed_opex_fraction=_float(row["capture_fixed_opex_fraction"]),
                purification_technology_id=row["purification_technology_id"],
                purification_train=row["purification_train"],
                purification_recovery=_float(row["purification_recovery"]),
                product_co2_mol_pct=_float(row["product_co2_mol_pct"]),
                product_h2o_ppmv=_float(row["product_h2o_ppmv"]),
                product_o2_ppmv=_float(row["product_o2_ppmv"]),
                product_nox_ppmv=_float(row["product_nox_ppmv"]),
                product_sox_ppmv=_float(row["product_sox_ppmv"]),
                product_co_ppmv=_float(row["product_co_ppmv"]),
                purification_electricity_mwh_per_t_product=_float(row["purification_electricity_mwh_per_t_product"]),
                purification_variable_opex_eur_per_t_product=_float(row["purification_variable_opex_eur_per_t_product"]),
                purification_reference_capex_meur=_float(row["purification_reference_capex_meur"]),
                purification_reference_capacity_tpy=_float(row["purification_reference_capacity_tpy"]),
                purification_scale_exponent=_float(row["purification_scale_exponent"]),
                purification_fixed_opex_fraction=_float(row["purification_fixed_opex_fraction"]),
                priority=int(row["priority"]),
                routing_factor=_float(row["routing_factor"], 1.2),
                assumption_quality=row["assumption_quality"],
                primary_source_url=row["primary_source_url"],
            )
        )
    return sources


def _load_product_limits(path: Path) -> list[ProductLimit]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return [
        ProductLimit(
            component=row["component"],
            limit_type=row["limit_type"],
            limit_value=float(row["limit_value"]),
            unit=row["unit"],
            source_url=row["source_url"],
        )
        for row in rows
    ]


def _load_reference_product_limits(path: Path) -> list[ReferenceProductLimit]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return [
        ReferenceProductLimit(
            component=row["component"],
            limit_type=row["limit_type"],
            limit_value=float(row["limit_value"]),
            unit=row["unit"],
            screened_in_model=row["screened_in_model"].strip().lower() in {"1", "true", "yes"},
            model_field=row["model_field"],
            validation_status=row["validation_status"],
            source_url=row["source_url"],
            notes=row["notes"],
        )
        for row in rows
    ]


def load_model_inputs(root: Path) -> ModelInputs:
    root = root.resolve()
    with (root / "config" / "model.toml").open("rb") as handle:
        config = tomllib.load(handle)
    with (root / "config" / "technologies.toml").open("rb") as handle:
        technologies = tomllib.load(handle)
    sources = _load_sources(root / "data" / "source_inventory.csv")
    product_limits = _load_product_limits(root / "data" / "co2_product_specification.csv")
    reference_product_limits = _load_reference_product_limits(
        root / "data" / "co2_receiving_specification_reference.csv"
    )
    return ModelInputs(
        root=root,
        config=config,
        sources=sources,
        product_limits=product_limits,
        reference_product_limits=reference_product_limits,
        capture_technologies=technologies["capture"],
        purification_technologies=technologies["purification"],
    )


def capital_recovery_factor(discount_rate: float, years: int) -> float:
    if years <= 0:
        raise ValueError("Project life must be positive.")
    if discount_rate == 0:
        return 1.0 / years
    factor = (1.0 + discount_rate) ** years
    return discount_rate * factor / (factor - 1.0)


def _product_values(source: Source) -> dict[str, float]:
    return {
        "CO2": source.product_co2_mol_pct,
        "H2O": source.product_h2o_ppmv,
        "O2": source.product_o2_ppmv,
        "NOx": source.product_nox_ppmv,
        "SOx": source.product_sox_ppmv,
        "CO": source.product_co_ppmv,
    }


def check_product_spec(source: Source, limits: Iterable[ProductLimit]) -> tuple[bool, list[str]]:
    values = _product_values(source)
    failures: list[str] = []
    for limit in limits:
        value = values.get(limit.component)
        if value is None:
            failures.append(f"{limit.component}: no product estimate")
        elif limit.limit_type == "minimum" and value < limit.limit_value:
            failures.append(f"{limit.component}={value:g} < {limit.limit_value:g} {limit.unit}")
        elif limit.limit_type == "maximum" and value > limit.limit_value:
            failures.append(f"{limit.component}={value:g} > {limit.limit_value:g} {limit.unit}")
    return not failures, failures


def available_capture_technologies(
    inputs: ModelInputs, source: Source
) -> dict[str, dict[str, Any]]:
    """Return capture technologies whose configured sector screen includes the source."""
    return {
        technology_id: values
        for technology_id, values in inputs.capture_technologies.items()
        if source.sector in values.get("compatible_sectors", [])
    }


def available_purification_technologies(
    inputs: ModelInputs, source: Source | None = None
) -> dict[str, dict[str, Any]]:
    """Return the purification technologies available to the interactive model."""
    del source
    return dict(inputs.purification_technologies)


def _bounded_value(
    name: str,
    value: float,
    minimum: float,
    maximum: float,
) -> float:
    value = float(value)
    if not minimum <= value <= maximum:
        raise ValueError(
            f"{name}={value:g} is outside the configured technically screened "
            f"range {minimum:g} to {maximum:g}."
        )
    return value


def _piecewise_multiplier(
    value: float,
    minimum: float,
    reference: float,
    maximum: float,
    multiplier_at_minimum: float,
    multiplier_at_maximum: float,
) -> float:
    """Interpolate a transparent pre-FEED severity factor around a reference point."""
    if value <= reference:
        span = reference - minimum
        fraction = (value - minimum) / span if span > 0 else 1.0
        return multiplier_at_minimum + fraction * (1.0 - multiplier_at_minimum)
    span = maximum - reference
    fraction = (value - reference) / span if span > 0 else 0.0
    return 1.0 + fraction * (multiplier_at_maximum - 1.0)


def _normalised_increasing(value: float, minimum: float, maximum: float) -> float:
    if maximum <= minimum:
        return 0.0
    return min(max((value - minimum) / (maximum - minimum), 0.0), 1.0)


def _purification_effort(
    technology: dict[str, Any],
    recovery: float,
    co2_mol_pct: float,
    h2o_ppmv: float,
    o2_ppmv: float,
    nox_ppmv: float,
    sox_ppmv: float,
    co_ppmv: float,
) -> float:
    """Return a 0–1 separation-severity index used only for cost/energy interpolation."""
    purity = _normalised_increasing(
        co2_mol_pct,
        float(technology["minimum_co2_mol_pct"]),
        float(technology["maximum_co2_mol_pct"]),
    )
    recovery_effort = _normalised_increasing(
        recovery,
        float(technology["minimum_recovery"]),
        float(technology["maximum_recovery"]),
    )
    dryness = 1.0 - _normalised_increasing(
        h2o_ppmv,
        float(technology["minimum_h2o_ppmv"]),
        float(technology["maximum_h2o_ppmv"]),
    )
    impurity_targets = []
    for component, value in (
        ("o2", o2_ppmv),
        ("nox", nox_ppmv),
        ("sox", sox_ppmv),
        ("co", co_ppmv),
    ):
        permissiveness = _normalised_increasing(
            value,
            float(technology[f"minimum_{component}_ppmv"]),
            float(technology[f"maximum_{component}_ppmv"]),
        )
        impurity_targets.append(1.0 - permissiveness)
    impurity_effort = sum(impurity_targets) / len(impurity_targets)
    return 0.45 * purity + 0.25 * recovery_effort + 0.20 * dryness + 0.10 * impurity_effort


def _purification_multiplier(
    effort: float,
    reference_effort: float,
    minimum_multiplier: float,
    maximum_multiplier: float,
) -> float:
    return _piecewise_multiplier(
        effort,
        0.0,
        reference_effort,
        1.0,
        minimum_multiplier,
        maximum_multiplier,
    )


def _apply_source_configuration(
    inputs: ModelInputs,
    source: Source,
    override: dict[str, Any] | None,
) -> tuple[Source, dict[str, Any]]:
    """Resolve technology selections and operating targets to an effective source."""
    override = dict(override or {})
    allowed = {
        "capture_technology_id",
        "capture_rate",
        "purification_technology_id",
        "purification_recovery",
        "product_co2_mol_pct",
        "product_h2o_ppmv",
        "product_o2_ppmv",
        "product_nox_ppmv",
        "product_sox_ppmv",
        "product_co_ppmv",
    }
    unexpected = sorted(set(override) - allowed)
    if unexpected:
        raise ValueError(
            f"Unsupported source overrides for {source.source_id}: {', '.join(unexpected)}"
        )

    capture_id = str(
        override.get("capture_technology_id", source.capture_technology_id)
    )
    capture_options = available_capture_technologies(inputs, source)
    if capture_id not in capture_options:
        raise ValueError(
            f"Capture technology {capture_id!r} is not configured as compatible "
            f"with {source.source_id} ({source.sector})."
        )
    capture = capture_options[capture_id]
    capture_default = (
        source.capture_rate
        if capture_id == source.capture_technology_id
        else float(capture["reference_capture_rate"])
    )
    capture_rate = _bounded_value(
        f"{source.source_id} capture rate",
        float(override.get("capture_rate", capture_default)),
        float(capture["minimum_capture_rate"]),
        float(capture["maximum_capture_rate"]),
    )
    capture_energy_multiplier = _piecewise_multiplier(
        capture_rate,
        float(capture["minimum_capture_rate"]),
        float(capture["reference_capture_rate"]),
        float(capture["maximum_capture_rate"]),
        float(capture["energy_multiplier_at_minimum"]),
        float(capture["energy_multiplier_at_maximum"]),
    )
    capture_capex_multiplier = _piecewise_multiplier(
        capture_rate,
        float(capture["minimum_capture_rate"]),
        float(capture["reference_capture_rate"]),
        float(capture["maximum_capture_rate"]),
        float(capture["capex_multiplier_at_minimum"]),
        float(capture["capex_multiplier_at_maximum"]),
    )
    capture_opex_multiplier = _piecewise_multiplier(
        capture_rate,
        float(capture["minimum_capture_rate"]),
        float(capture["reference_capture_rate"]),
        float(capture["maximum_capture_rate"]),
        float(capture["variable_opex_multiplier_at_minimum"]),
        float(capture["variable_opex_multiplier_at_maximum"]),
    )

    purification_id = str(
        override.get(
            "purification_technology_id", source.purification_technology_id
        )
    )
    if purification_id not in inputs.purification_technologies:
        raise ValueError(f"Unknown purification technology: {purification_id}")
    purification = inputs.purification_technologies[purification_id]
    use_source_defaults = purification_id == source.purification_technology_id

    def target(field: str, source_value: float, reference_key: str) -> float:
        default = source_value if use_source_defaults else float(purification[reference_key])
        return float(override.get(field, default))

    recovery = _bounded_value(
        f"{source.source_id} purification recovery",
        target("purification_recovery", source.purification_recovery, "reference_recovery"),
        float(purification["minimum_recovery"]),
        float(purification["maximum_recovery"]),
    )
    product_targets: dict[str, float] = {}
    for field, source_value, component in (
        ("product_co2_mol_pct", source.product_co2_mol_pct, "co2_mol_pct"),
        ("product_h2o_ppmv", source.product_h2o_ppmv, "h2o_ppmv"),
        ("product_o2_ppmv", source.product_o2_ppmv, "o2_ppmv"),
        ("product_nox_ppmv", source.product_nox_ppmv, "nox_ppmv"),
        ("product_sox_ppmv", source.product_sox_ppmv, "sox_ppmv"),
        ("product_co_ppmv", source.product_co_ppmv, "co_ppmv"),
    ):
        value = target(field, source_value, f"reference_{component}")
        product_targets[field] = _bounded_value(
            f"{source.source_id} {field}",
            value,
            float(purification[f"minimum_{component}"]),
            float(purification[f"maximum_{component}"]),
        )
    trace_mol_pct = sum(
        product_targets[field] / 10_000.0
        for field in (
            "product_h2o_ppmv",
            "product_o2_ppmv",
            "product_nox_ppmv",
            "product_sox_ppmv",
            "product_co_ppmv",
        )
    )
    if product_targets["product_co2_mol_pct"] + trace_mol_pct > 100.0 + 1e-9:
        raise ValueError(
            f"{source.source_id} product composition exceeds 100 mol-% after "
            "including the selected trace-component targets."
        )

    effort = _purification_effort(
        purification,
        recovery,
        product_targets["product_co2_mol_pct"],
        product_targets["product_h2o_ppmv"],
        product_targets["product_o2_ppmv"],
        product_targets["product_nox_ppmv"],
        product_targets["product_sox_ppmv"],
        product_targets["product_co_ppmv"],
    )
    reference_effort = _purification_effort(
        purification,
        float(purification["reference_recovery"]),
        float(purification["reference_co2_mol_pct"]),
        float(purification["reference_h2o_ppmv"]),
        float(purification["reference_o2_ppmv"]),
        float(purification["reference_nox_ppmv"]),
        float(purification["reference_sox_ppmv"]),
        float(purification["reference_co_ppmv"]),
    )
    purification_energy_multiplier = _purification_multiplier(
        effort,
        reference_effort,
        float(purification["minimum_energy_multiplier"]),
        float(purification["maximum_energy_multiplier"]),
    )
    purification_capex_multiplier = _purification_multiplier(
        effort,
        reference_effort,
        float(purification["minimum_capex_multiplier"]),
        float(purification["maximum_capex_multiplier"]),
    )
    purification_opex_multiplier = _purification_multiplier(
        effort,
        reference_effort,
        float(purification["minimum_variable_opex_multiplier"]),
        float(purification["maximum_variable_opex_multiplier"]),
    )

    effective = replace(
        source,
        capture_technology_id=capture_id,
        capture_technology=str(capture["label"]),
        capture_rate=capture_rate,
        capture_electricity_mwh_per_t_captured=float(
            capture["electricity_mwh_per_t_captured"]
        )
        * capture_energy_multiplier,
        capture_steam_gj_per_t_captured=float(capture["steam_gj_per_t_captured"])
        * capture_energy_multiplier,
        capture_variable_opex_eur_per_t_captured=float(
            capture["variable_opex_eur_per_t_captured"]
        )
        * capture_opex_multiplier,
        capture_reference_capex_meur=float(capture["reference_capex_meur"])
        * capture_capex_multiplier,
        capture_reference_capacity_tpy=float(capture["reference_capacity_tpy"]),
        capture_scale_exponent=float(capture["scale_exponent"]),
        capture_fixed_opex_fraction=float(capture["fixed_opex_fraction"]),
        purification_technology_id=purification_id,
        purification_train=str(purification["label"]),
        purification_recovery=recovery,
        purification_electricity_mwh_per_t_product=float(
            purification["electricity_mwh_per_t_product"]
        )
        * purification_energy_multiplier,
        purification_variable_opex_eur_per_t_product=float(
            purification["variable_opex_eur_per_t_product"]
        )
        * purification_opex_multiplier,
        purification_reference_capex_meur=float(
            purification["reference_capex_meur"]
        )
        * purification_capex_multiplier,
        purification_reference_capacity_tpy=float(
            purification["reference_capacity_tpy"]
        ),
        purification_scale_exponent=float(purification["scale_exponent"]),
        purification_fixed_opex_fraction=float(
            purification["fixed_opex_fraction"]
        ),
        **product_targets,
    )
    configuration_customized = (
        capture_id != source.capture_technology_id
        or not math.isclose(capture_rate, source.capture_rate, rel_tol=0.0, abs_tol=1e-12)
        or purification_id != source.purification_technology_id
        or not math.isclose(recovery, source.purification_recovery, rel_tol=0.0, abs_tol=1e-12)
        or any(
            not math.isclose(
                product_targets[field],
                float(getattr(source, field)),
                rel_tol=0.0,
                abs_tol=1e-12,
            )
            for field in product_targets
        )
    )
    metadata = {
        "configuration_customized": configuration_customized,
        "capture_technology_readiness_level": int(
            capture["technology_readiness_level"]
        ),
        "capture_safety_category": str(capture["safety_category"]),
        "capture_safety_level": int(capture["safety_level"]),
        "capture_hazards": str(capture["hazards"]),
        "capture_basis_note": str(capture["basis_note"]),
        "capture_target_energy_multiplier": capture_energy_multiplier,
        "capture_target_capex_multiplier": capture_capex_multiplier,
        "purification_technology_readiness_level": int(
            purification["technology_readiness_level"]
        ),
        "purification_safety_category": str(purification["safety_category"]),
        "purification_safety_level": int(purification["safety_level"]),
        "purification_hazards": str(purification["hazards"]),
        "purification_basis_note": str(purification["basis_note"]),
        "purification_separation_effort_index": effort,
        "purification_target_energy_multiplier": purification_energy_multiplier,
        "purification_target_capex_multiplier": purification_capex_multiplier,
    }
    return effective, metadata


def _source_safety_screen(
    source: Source,
    spec_pass: bool,
    spec_failures: list[str],
    metadata: dict[str, Any],
) -> dict[str, Any]:
    """Provide a transparent hazard/quality screen, not a quantitative risk study."""
    flags: list[str] = []
    if not spec_pass:
        flags.append("Selected product misses the external receiver-quality benchmark")
    if source.product_co2_mol_pct < 99.81:
        flags.append("Detailed mixture phase-envelope verification required")
    if source.product_h2o_ppmv > 30.0:
        flags.append("Water target increases corrosion and hydrate-management concern")
    if source.product_o2_ppmv > 10.0:
        flags.append("Oxygen target requires corrosion and materials review")
    if int(metadata["capture_safety_level"]) >= 3:
        flags.append(str(metadata["capture_safety_category"]))
    if int(metadata["purification_safety_level"]) >= 3:
        flags.append(str(metadata["purification_safety_category"]))

    red = (
        source.product_co2_mol_pct < 95.0
        or source.product_h2o_ppmv > 100.0
        or source.product_o2_ppmv > 5000.0
    )
    status = "Red" if red else ("Amber" if flags else "Green")
    return {
        "process_safety_screen_status": status,
        "process_safety_screen_flags": "; ".join(flags),
        "receiver_quality_status": "PASS" if spec_pass else "FAIL",
        "phase_envelope_review_required": source.product_co2_mol_pct < 99.81
        or not spec_pass,
        "technical_target_within_catalogue_range": True,
        "product_spec_failure_count": len(spec_failures),
    }


def _emissions_for_basis(source: Source, flow_basis: str) -> float:
    if flow_basis == "irep_2024_total":
        return source.irep_2024_total_co2_tpy
    if flow_basis == "user_case":
        return source.user_case_emissions_tpy
    if flow_basis == "announced_product":
        if source.announced_product_co2_tpy <= 0:
            return 0.0
        denominator = (
            source.capturable_fraction
            * source.capture_rate
            * source.availability
            * source.purification_recovery
        )
        return source.announced_product_co2_tpy / denominator if denominator else 0.0
    raise ValueError(f"Unsupported flow basis: {flow_basis}")


def _potential_product_flow(
    source: Source,
    flow_basis: str,
    emissions_basis_tpy: float | None = None,
) -> tuple[float, float, float]:
    emissions = (
        _emissions_for_basis(source, flow_basis)
        if emissions_basis_tpy is None
        else float(emissions_basis_tpy)
    )
    captured = (
        emissions
        * source.capturable_fraction
        * source.capture_rate
        * source.availability
    )
    return captured, captured * source.purification_recovery, emissions


def _assumption_uncertainty_fraction(quality: str) -> float:
    return {
        "project-specific": 0.20,
        "project-plus-screening": 0.30,
        "pilot-plus-screening": 0.40,
        "screening": 0.40,
        "low-maturity-screening": 0.50,
    }.get(quality, 0.45)


def _capture_economics(source: Source, captured_flow_tpy: float, finance: dict[str, Any]) -> dict[str, float]:
    if captured_flow_tpy <= 0:
        return {
            "capture_capex_eur": 0.0,
            "annualized_capture_capex_eur": 0.0,
            "capture_fixed_opex_eur_per_year": 0.0,
            "capture_variable_energy_opex_eur_per_year": 0.0,
            "capture_annual_cost_eur": 0.0,
            "capture_cost_eur_per_t_captured": 0.0,
            "capture_electricity_mwh_per_year": 0.0,
            "capture_steam_gj_per_year": 0.0,
            "capture_energy_emissions_tpy": 0.0,
        }

    crf = capital_recovery_factor(finance["discount_rate"], finance["project_life_years"])
    reference_capex = source.capture_reference_capex_meur * 1e6
    scale = (captured_flow_tpy / source.capture_reference_capacity_tpy) ** source.capture_scale_exponent
    capex = reference_capex * scale
    annualized_capex = capex * crf
    fixed_opex = capex * source.capture_fixed_opex_fraction
    electricity = captured_flow_tpy * source.capture_electricity_mwh_per_t_captured
    steam = captured_flow_tpy * source.capture_steam_gj_per_t_captured
    variable_energy_opex = captured_flow_tpy * source.capture_variable_opex_eur_per_t_captured
    variable_energy_opex += electricity * finance["electricity_price_eur_per_mwh"]
    variable_energy_opex += steam * finance["steam_price_eur_per_gj"]
    annual_cost = annualized_capex + fixed_opex + variable_energy_opex
    energy_emissions = electricity * finance["electricity_emission_factor_tco2_per_mwh"]
    energy_emissions += steam * finance["steam_emission_factor_tco2_per_gj"]
    return {
        "capture_capex_eur": capex,
        "annualized_capture_capex_eur": annualized_capex,
        "capture_fixed_opex_eur_per_year": fixed_opex,
        "capture_variable_energy_opex_eur_per_year": variable_energy_opex,
        "capture_annual_cost_eur": annual_cost,
        "capture_cost_eur_per_t_captured": annual_cost / captured_flow_tpy,
        "capture_electricity_mwh_per_year": electricity,
        "capture_steam_gj_per_year": steam,
        "capture_energy_emissions_tpy": energy_emissions,
    }


def _purification_economics(source: Source, product_flow_tpy: float, finance: dict[str, Any]) -> dict[str, float]:
    if product_flow_tpy <= 0:
        return {
            "purification_capex_eur": 0.0,
            "annualized_purification_capex_eur": 0.0,
            "purification_fixed_opex_eur_per_year": 0.0,
            "purification_variable_energy_opex_eur_per_year": 0.0,
            "purification_annual_cost_eur": 0.0,
            "purification_cost_eur_per_t_product": 0.0,
            "purification_electricity_mwh_per_year": 0.0,
            "purification_energy_emissions_tpy": 0.0,
        }

    crf = capital_recovery_factor(finance["discount_rate"], finance["project_life_years"])
    reference_capex = source.purification_reference_capex_meur * 1e6
    scale = (product_flow_tpy / source.purification_reference_capacity_tpy) ** source.purification_scale_exponent
    capex = reference_capex * scale
    annualized_capex = capex * crf
    fixed_opex = capex * source.purification_fixed_opex_fraction
    electricity = product_flow_tpy * source.purification_electricity_mwh_per_t_product
    variable_energy_opex = product_flow_tpy * source.purification_variable_opex_eur_per_t_product
    variable_energy_opex += electricity * finance["electricity_price_eur_per_mwh"]
    annual_cost = annualized_capex + fixed_opex + variable_energy_opex
    energy_emissions = electricity * finance["electricity_emission_factor_tco2_per_mwh"]
    return {
        "purification_capex_eur": capex,
        "annualized_purification_capex_eur": annualized_capex,
        "purification_fixed_opex_eur_per_year": fixed_opex,
        "purification_variable_energy_opex_eur_per_year": variable_energy_opex,
        "purification_annual_cost_eur": annual_cost,
        "purification_cost_eur_per_t_product": annual_cost / product_flow_tpy,
        "purification_electricity_mwh_per_year": electricity,
        "purification_energy_emissions_tpy": energy_emissions,
    }


def build_source_results(
    inputs: ModelInputs,
    scenario_name: str,
    source_overrides: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    scenario = inputs.config["scenarios"][scenario_name]
    finance = inputs.config["finance"]
    active_ids = set(scenario["active_source_ids"])
    flow_basis = scenario["flow_basis"]

    working: list[dict[str, Any]] = []
    source_overrides = source_overrides or {}
    for baseline_source in inputs.sources:
        source, technology_metadata = _apply_source_configuration(
            inputs,
            baseline_source,
            source_overrides.get(baseline_source.source_id),
        )
        spec_pass, spec_failures = check_product_spec(source, inputs.product_limits)
        safety_screen = _source_safety_screen(
            source, spec_pass, spec_failures, technology_metadata
        )
        baseline_emissions = _emissions_for_basis(baseline_source, flow_basis)
        captured_potential, product_potential, emissions = _potential_product_flow(
            source, flow_basis, baseline_emissions
        )
        if source.source_id not in active_ids:
            captured_potential = 0.0
            product_potential = 0.0
        capture_screening = _capture_economics(source, captured_potential, finance)
        purification_screening = _purification_economics(source, product_potential, finance)
        screening_cost = (
            (capture_screening["capture_annual_cost_eur"] + purification_screening["purification_annual_cost_eur"])
            / product_potential
            if product_potential
            else 0.0
        )
        working.append(
            {
                "source": source,
                "emissions_basis_tpy": emissions,
                "potential_captured_tpy": captured_potential,
                "potential_product_tpy": product_potential,
                "spec_pass": spec_pass,
                "spec_failures": spec_failures,
                "technology_metadata": technology_metadata,
                "safety_screen": safety_screen,
                "screening_cost_eur_per_t": screening_cost,
            }
        )

    capacity = float(scenario["sink_capacity_tpy"])
    remaining = capacity
    enforce = bool(scenario["enforce_sink_capacity"])
    allocations: dict[str, float] = {source.source_id: 0.0 for source in inputs.sources}
    eligible = [item for item in working if item["potential_product_tpy"] > 0]
    eligible.sort(
        key=lambda item: (
            item["source"].priority,
            item["screening_cost_eur_per_t"],
            item["source"].source_id,
        )
    )
    for item in eligible:
        source = item["source"]
        potential = item["potential_product_tpy"]
        allocation = potential if not enforce else min(potential, max(remaining, 0.0))
        allocations[source.source_id] = allocation
        if enforce:
            remaining -= allocation

    results: list[dict[str, Any]] = []
    for item in working:
        source: Source = item["source"]
        allocation = allocations[source.source_id]
        captured_before_purification = allocation / source.purification_recovery if allocation else 0.0
        capture_economics = _capture_economics(source, captured_before_purification, finance)
        purification_economics = _purification_economics(source, allocation, finance)
        emissions = item["emissions_basis_tpy"]
        residual = max(emissions - captured_before_purification, 0.0) if emissions > 0 else None
        purification_loss = max(captured_before_purification - allocation, 0.0)
        uncertainty = _assumption_uncertainty_fraction(source.assumption_quality)
        result = {
            "scenario": scenario_name,
            "source_id": source.source_id,
            "source_name": source.source_name,
            "operator": source.operator,
            "commune": source.commune,
            "sector": source.sector,
            "project_name": source.project_name,
            "project_status": source.project_status,
            "capture_technology_id": source.capture_technology_id,
            "capture_technology": source.capture_technology,
            "purification_technology_id": source.purification_technology_id,
            "purification_train": source.purification_train,
            "assumption_quality": source.assumption_quality,
            "cost_uncertainty_fraction": uncertainty,
            "flow_basis": flow_basis,
            "emissions_basis_tpy": emissions,
            "irep_2024_total_co2_tpy": source.irep_2024_total_co2_tpy,
            "user_case_emissions_tpy": source.user_case_emissions_tpy,
            "capturable_fraction": source.capturable_fraction,
            "capture_rate": source.capture_rate,
            "availability": source.availability,
            "purification_recovery": source.purification_recovery,
            "potential_captured_co2_tpy": item["potential_captured_tpy"],
            "potential_product_co2_tpy": item["potential_product_tpy"],
            "allocated_product_co2_tpy": allocation,
            "curtailed_product_co2_tpy": item["potential_product_tpy"] - allocation,
            "captured_before_purification_tpy": captured_before_purification,
            "purification_loss_tpy": purification_loss,
            "residual_stack_co2_tpy": residual,
            "product_spec_screening_pass": item["spec_pass"],
            "product_spec_pass": item["spec_pass"],
            "product_spec_failures": "; ".join(item["spec_failures"]),
            "product_spec_components_screened": len(inputs.product_limits),
            "product_co2_mol_pct": source.product_co2_mol_pct,
            "product_h2o_ppmv": source.product_h2o_ppmv,
            "product_o2_ppmv": source.product_o2_ppmv,
            "product_nox_ppmv": source.product_nox_ppmv,
            "product_sox_ppmv": source.product_sox_ppmv,
            "product_co_ppmv": source.product_co_ppmv,
            "x_l93_m": source.x_l93_m,
            "y_l93_m": source.y_l93_m,
            "longitude": source.longitude,
            "latitude": source.latitude,
            "irep_id": source.irep_id,
            "primary_source_url": source.primary_source_url,
            **item["technology_metadata"],
            **item["safety_screen"],
            **capture_economics,
            **purification_economics,
        }
        result["capture_cost_eur_per_t_product"] = (
            capture_economics["capture_annual_cost_eur"] / allocation if allocation else 0.0
        )
        result["source_energy_emissions_tpy"] = (
            capture_economics["capture_energy_emissions_tpy"]
            + purification_economics["purification_energy_emissions_tpy"]
        )
        result["capture_annual_cost_low_eur"] = capture_economics["capture_annual_cost_eur"] * (1.0 - uncertainty)
        result["capture_annual_cost_high_eur"] = capture_economics["capture_annual_cost_eur"] * (1.0 + uncertainty)
        result["purification_annual_cost_low_eur"] = purification_economics["purification_annual_cost_eur"] * (1.0 - uncertainty)
        result["purification_annual_cost_high_eur"] = purification_economics["purification_annual_cost_eur"] * (1.0 + uncertainty)
        result["net_avoided_before_transport_tpy"] = max(
            allocation - result["source_energy_emissions_tpy"], 0.0
        )
        results.append(result)
    return results


PR_R_UNIVERSAL = 8.314462618
PR_COMPONENTS: dict[str, dict[str, float]] = {
    "CO2": {"Tc": 304.1282, "Pc": 7.3773e6, "omega": 0.22394, "MW": 44.0095e-3},
    "N2": {"Tc": 126.192, "Pc": 3.3958e6, "omega": 0.0372, "MW": 28.0134e-3},
    "O2": {"Tc": 154.581, "Pc": 5.0430e6, "omega": 0.0222, "MW": 31.9988e-3},
    "Ar": {"Tc": 150.687, "Pc": 4.8630e6, "omega": -0.0022, "MW": 39.9480e-3},
}


def _pr_kappa(omega: float) -> float:
    return 0.37464 + 1.54226 * omega - 0.26992 * omega**2


def _pr_ai_bi(component: str, temperature_k: float) -> tuple[float, float]:
    values = PR_COMPONENTS[component]
    tc = values["Tc"]
    pc = values["Pc"]
    omega = values["omega"]
    a0 = 0.45724 * PR_R_UNIVERSAL**2 * tc**2 / pc
    b = 0.07780 * PR_R_UNIVERSAL * tc / pc
    alpha = (1.0 + _pr_kappa(omega) * (1.0 - math.sqrt(temperature_k / tc))) ** 2
    return a0 * alpha, b


def _peng_robinson_properties(
    pressure_bar: float,
    temperature_c: float,
    composition: dict[str, float],
) -> dict[str, float]:
    """Mixture density and Z from the Peng-Robinson EOS.

    Classical quadratic mixing rules with kij=0 are used. At the model's 35 °C
    dense-phase transport condition the supported mixture has a single physical
    PR root across the operating pressure window. A residual-Gibbs criterion is
    retained for robustness if multiple admissible roots occur.
    """
    if pressure_bar <= 0:
        raise ValueError("PR pressure must be positive.")
    temperature_k = temperature_c + 273.15
    if temperature_k <= 0:
        raise ValueError("PR temperature must be above absolute zero.")

    unsupported = sorted(set(composition) - set(PR_COMPONENTS))
    if unsupported:
        raise ValueError(f"Unsupported PR components: {', '.join(unsupported)}")
    total = sum(float(value) for value in composition.values())
    if total <= 0:
        raise ValueError("PR composition must sum to a positive value.")

    names = [name for name in PR_COMPONENTS if float(composition.get(name, 0.0)) > 0]
    x = np.array([float(composition[name]) / total for name in names], dtype=float)
    ai = np.empty(len(names), dtype=float)
    bi = np.empty(len(names), dtype=float)
    for index, name in enumerate(names):
        ai[index], bi[index] = _pr_ai_bi(name, temperature_k)

    # Classical PR mixing rule, with binary interaction parameters set to zero.
    aij = np.sqrt(np.outer(ai, ai))
    a_mix = float(x @ aij @ x)
    b_mix = float(np.dot(x, bi))
    pressure_pa = pressure_bar * 100000.0
    A = a_mix * pressure_pa / (PR_R_UNIVERSAL**2 * temperature_k**2)
    B = b_mix * pressure_pa / (PR_R_UNIVERSAL * temperature_k)

    roots = np.roots([1.0, -(1.0 - B), A - 3.0 * B**2 - 2.0 * B, -(A * B - B**2 - B**3)])
    valid_roots = sorted(
        float(root.real)
        for root in roots
        if abs(root.imag) < 1e-9 and float(root.real) > B + 1e-12
    )
    if not valid_roots:
        raise RuntimeError("Peng-Robinson EOS returned no admissible real Z root.")

    def residual_gibbs_over_rt(z_factor: float) -> float:
        sqrt2 = math.sqrt(2.0)
        sum_aij = aij @ x
        log_ratio = math.log(
            max(
                (z_factor + (1.0 + sqrt2) * B)
                / max(z_factor + (1.0 - sqrt2) * B, 1e-18),
                1e-18,
            )
        )
        lnphi = np.zeros_like(x)
        for i in range(len(names)):
            bi_over_b = bi[i] / max(b_mix, 1e-18)
            lnphi[i] = (
                bi_over_b * (z_factor - 1.0)
                - math.log(max(z_factor - B, 1e-18))
                - (A / (2.0 * sqrt2 * max(B, 1e-18)))
                * ((2.0 * sum_aij[i] / max(a_mix, 1e-18)) - bi_over_b)
                * log_ratio
            )
        return float(np.dot(x, lnphi))

    z_factor = min(valid_roots, key=residual_gibbs_over_rt)
    molecular_weight = float(sum(x[i] * PR_COMPONENTS[name]["MW"] for i, name in enumerate(names)))
    density = pressure_pa * molecular_weight / (z_factor * PR_R_UNIVERSAL * temperature_k)
    return {
        "density_kg_per_m3": density,
        "compressibility_factor": z_factor,
        "molecular_weight_kg_per_mol": molecular_weight,
        "root_count": float(len(valid_roots)),
    }


def _pipe_hydraulics(flow_tpy: float, length_km: float, diameter_m: float, transport: dict[str, Any]) -> dict[str, float | str]:
    temperature_c = float(transport["temperature_c"])
    composition = {key: float(value) for key, value in transport["eos_composition"].items()}
    inlet_pressure_bar = float(transport["inlet_pressure_bar"])
    minimum_pressure_bar = float(transport["minimum_arrival_pressure_bar"])
    pressure_window_bar = inlet_pressure_bar - minimum_pressure_bar
    composition_total = sum(composition.values())
    mixture_mw = sum(
        mole_fraction / composition_total * PR_COMPONENTS[component]["MW"]
        for component, mole_fraction in composition.items()
    )
    co2_mass_fraction = (
        composition.get("CO2", 0.0)
        / composition_total
        * PR_COMPONENTS["CO2"]["MW"]
        / mixture_mw
    )

    if flow_tpy <= 0 or length_km <= 0:
        props = _peng_robinson_properties(inlet_pressure_bar, temperature_c, composition)
        return {
            "velocity_m_per_s": 0.0,
            "reynolds_number": 0.0,
            "darcy_factor": 0.0,
            "pressure_drop_bar": 0.0,
            "eos_density_kg_per_m3": props["density_kg_per_m3"],
            "eos_compressibility_factor": props["compressibility_factor"],
            "eos_reference_pressure_bar": inlet_pressure_bar,
            "eos_temperature_c": temperature_c,
            "equation_of_state": "Peng-Robinson",
            "co2_mass_fraction": co2_mass_fraction,
            "total_stream_flow_tpy": 0.0,
        }

    total_stream_flow_tpy = flow_tpy / max(co2_mass_fraction, 1e-12)
    mass_flow_kg_s = total_stream_flow_tpy * 1000.0 / (
        transport["operating_hours_per_year"] * 3600.0
    )
    area = math.pi * diameter_m**2 / 4.0
    viscosity = float(transport["co2_viscosity_pa_s"])

    # Iterate the PR density at an estimated segment mean pressure. This makes
    # the Darcy-Weisbach calculation depend on P/T/composition instead of a
    # fixed density, while remaining compatible with the screening network model.
    reference_pressure_bar = inlet_pressure_bar - 0.5 * pressure_window_bar
    pressure_drop_bar = 0.0
    for _ in range(12):
        props = _peng_robinson_properties(reference_pressure_bar, temperature_c, composition)
        density = props["density_kg_per_m3"]
        velocity = mass_flow_kg_s / (density * area)
        reynolds = density * velocity * diameter_m / viscosity
        if reynolds < 2300:
            darcy = 64.0 / max(reynolds, 1.0)
        else:
            term = transport["pipe_roughness_m"] / (3.7 * diameter_m) + 5.74 / reynolds**0.9
            darcy = 0.25 / math.log10(term) ** 2
        pressure_drop_pa = (
            darcy
            * (length_km * 1000.0 / diameter_m)
            * density
            * velocity**2
            / 2.0
        )
        pressure_drop_bar = pressure_drop_pa / 100000.0
        bounded_drop = min(max(pressure_drop_bar, 0.0), max(pressure_window_bar, 0.0))
        updated_reference = inlet_pressure_bar - 0.5 * bounded_drop
        if abs(updated_reference - reference_pressure_bar) < 1e-5:
            reference_pressure_bar = updated_reference
            break
        reference_pressure_bar = updated_reference

    props = _peng_robinson_properties(reference_pressure_bar, temperature_c, composition)
    density = props["density_kg_per_m3"]
    velocity = mass_flow_kg_s / (density * area)
    reynolds = density * velocity * diameter_m / viscosity
    if reynolds < 2300:
        darcy = 64.0 / max(reynolds, 1.0)
    else:
        term = transport["pipe_roughness_m"] / (3.7 * diameter_m) + 5.74 / reynolds**0.9
        darcy = 0.25 / math.log10(term) ** 2
    pressure_drop_pa = (
        darcy
        * (length_km * 1000.0 / diameter_m)
        * density
        * velocity**2
        / 2.0
    )
    return {
        "velocity_m_per_s": velocity,
        "reynolds_number": reynolds,
        "darcy_factor": darcy,
        "pressure_drop_bar": pressure_drop_pa / 100000.0,
        "eos_density_kg_per_m3": density,
        "eos_compressibility_factor": props["compressibility_factor"],
        "eos_reference_pressure_bar": reference_pressure_bar,
        "eos_temperature_c": temperature_c,
        "equation_of_state": "Peng-Robinson",
        "co2_mass_fraction": co2_mass_fraction,
        "total_stream_flow_tpy": total_stream_flow_tpy,
    }


def _tree_orientation(graph: nx.Graph, root: int, local_flows: dict[int, float]) -> tuple[dict[int, int], list[int], dict[tuple[int, int], float]]:
    parent: dict[int, int] = {}
    order = [root]
    for node in order:
        for neighbor in graph.neighbors(node):
            if neighbor == parent.get(node) or neighbor in parent or neighbor == root:
                continue
            parent[neighbor] = node
            order.append(neighbor)
    if len(order) != graph.number_of_nodes():
        raise RuntimeError("Candidate pipeline tree is disconnected.")

    accumulated = {node: local_flows.get(node, 0.0) for node in graph.nodes()}
    edge_flows: dict[tuple[int, int], float] = {}
    for node in reversed(order[1:]):
        downstream = parent[node]
        edge_flows[(node, downstream)] = accumulated[node]
        accumulated[downstream] += accumulated[node]
    return parent, order, edge_flows


def _path_edges(node: int, parent: dict[int, int], root: int) -> list[tuple[int, int]]:
    edges: list[tuple[int, int]] = []
    current = node
    while current != root:
        downstream = parent[current]
        edges.append((current, downstream))
        current = downstream
    return edges


def _material_properties(
    transport: dict[str, Any], material_id: str | None = None
) -> tuple[str, dict[str, Any]]:
    """Return one configured pipeline material and fail clearly on bad input."""
    materials = transport.get("materials", {})
    selected = material_id or transport.get("pipeline_material", "x65")
    if selected not in materials:
        options = ", ".join(sorted(materials))
        raise ValueError(f"Unknown pipeline material '{selected}'. Available: {options}")
    return selected, materials[selected]


def _pipe_material_metrics(
    diameter_m: float,
    length_km: float,
    transport: dict[str, Any],
    material_id: str | None = None,
) -> dict[str, float | str]:
    """Screen wall thickness, steel mass, cost, and material carbon.

    This is a management-level comparison based on the Barlow pressure relation.
    It is intentionally not a substitute for a code-compliant mechanical design.
    The hydraulic diameter is treated as the internal diameter so selecting a
    material does not alter the already-optimised hydraulic solution.
    """

    selected_id, selected = _material_properties(transport, material_id)
    baseline_id = str(transport.get("baseline_pipeline_material", "x65"))
    _, baseline = _material_properties(transport, baseline_id)

    design_pressure_pa = float(transport.get("design_pressure_bar", 120.0)) * 1.0e5
    design_factor = float(transport.get("design_factor", 0.72))
    minimum_wall_m = float(transport.get("minimum_wall_thickness_mm", 6.4)) / 1000.0
    steel_density = float(transport.get("steel_density_kg_per_m3", 7850.0))
    material_share = float(transport.get("pipeline_material_cost_fraction", 0.35))

    def calculate(material: dict[str, Any]) -> tuple[float, float, float]:
        smys_pa = float(material["smys_mpa"]) * 1.0e6
        corrosion_allowance_m = float(material["corrosion_allowance_mm"]) / 1000.0
        pressure_wall_m = design_pressure_pa * diameter_m / (2.0 * design_factor * smys_pa)
        wall_m = max(pressure_wall_m + corrosion_allowance_m, minimum_wall_m)
        outside_diameter_m = diameter_m + 2.0 * wall_m
        steel_area_m2 = math.pi * (
            outside_diameter_m**2 - diameter_m**2
        ) / 4.0
        steel_mass_t = steel_area_m2 * length_km * 1000.0 * steel_density / 1000.0
        embodied_tco2e = steel_mass_t * float(material["embodied_carbon_tco2e_per_t_steel"])
        return wall_m, steel_mass_t, embodied_tco2e

    wall_m, steel_mass_t, embodied_tco2e = calculate(selected)
    baseline_wall_m, baseline_mass_t, baseline_embodied_tco2e = calculate(baseline)
    relative_price = float(selected.get("relative_material_price", 1.0))
    material_cost_index = (
        steel_mass_t / baseline_mass_t * relative_price if baseline_mass_t > 0 else 1.0
    )
    capex_multiplier = (1.0 - material_share) + material_share * material_cost_index

    return {
        "pipeline_material_id": selected_id,
        "pipeline_material_label": str(selected.get("label", selected_id)),
        "pipeline_material_note": str(selected.get("management_note", "")),
        "material_smys_mpa": float(selected["smys_mpa"]),
        "wall_thickness_mm": wall_m * 1000.0,
        "steel_mass_t": steel_mass_t,
        "material_embodied_carbon_tco2e": embodied_tco2e,
        "baseline_wall_thickness_mm": baseline_wall_m * 1000.0,
        "baseline_steel_mass_t": baseline_mass_t,
        "baseline_material_embodied_carbon_tco2e": baseline_embodied_tco2e,
        "material_embodied_carbon_delta_tco2e": embodied_tco2e
        - baseline_embodied_tco2e,
        "material_cost_index": material_cost_index,
        "material_capex_multiplier": capex_multiplier,
    }


def _pipeline_segment_rows(pipeline: dict[str, Any]) -> list[dict[str, Any]]:
    """Locate the segment table without coupling management tools to a UI key."""
    for value in pipeline.values():
        if (
            isinstance(value, list)
            and value
            and isinstance(value[0], dict)
            and "segment_capex_eur" in value[0]
        ):
            return value
    return []


def _enrich_pipeline_material_summary(
    pipeline: dict[str, Any], transport: dict[str, Any]
) -> None:
    segments = _pipeline_segment_rows(pipeline)
    material_id, material = _material_properties(transport)
    pipeline.update(
        {
            "pipeline_material_id": material_id,
            "pipeline_material_label": str(material.get("label", material_id)),
            "pipeline_material_note": str(material.get("management_note", "")),
            "pipeline_steel_mass_t": sum(
                float(s.get("steel_mass_t", 0.0)) for s in segments
            ),
            "pipeline_material_embodied_carbon_tco2e": sum(
                float(s.get("material_embodied_carbon_tco2e", 0.0))
                for s in segments
            ),
            "pipeline_material_embodied_carbon_delta_tco2e": sum(
                float(s.get("material_embodied_carbon_delta_tco2e", 0.0))
                for s in segments
            ),
            "minimum_wall_thickness_mm": min(
                (float(s.get("wall_thickness_mm", 0.0)) for s in segments),
                default=0.0,
            ),
            "maximum_wall_thickness_mm": max(
                (float(s.get("wall_thickness_mm", 0.0)) for s in segments),
                default=0.0,
            ),
        }
    )


def _candidate_tree_result(
    graph: nx.Graph,
    nodes: list[dict[str, Any]],
    root: int,
    local_flows: dict[int, float],
    config: dict[str, Any],
) -> dict[str, Any] | None:
    transport = config["transport"]
    finance = config["finance"]
    pressure_window = transport["inlet_pressure_bar"] - transport["minimum_arrival_pressure_bar"]
    diameter_options = [value / 1000.0 for value in transport["diameter_candidates_mm"]]
    parent, order, edge_flows = _tree_orientation(graph, root, local_flows)

    lengths: dict[tuple[int, int], tuple[float, float, float]] = {}
    diameter_index: dict[tuple[int, int], int] = {}
    hydraulics: dict[tuple[int, int], dict[str, float]] = {}
    for edge, flow in edge_flows.items():
        a, b = (nodes[edge[0]], nodes[edge[1]])
        straight = math.hypot(a["x"] - b["x"], a["y"] - b["y"]) / 1000.0
        route_factor = max(a["routing_factor"], b["routing_factor"])
        route = straight * route_factor
        if route > transport["maximum_edge_length_km"]:
            return None
        lengths[edge] = (straight, route_factor, route)

        selected: int | None = None
        selected_hydraulics: dict[str, float] | None = None
        for index, diameter in enumerate(diameter_options):
            values = _pipe_hydraulics(flow, route, diameter, transport)
            if (
                values["velocity_m_per_s"] <= transport["maximum_velocity_m_per_s"]
                and values["pressure_drop_bar"] <= pressure_window
            ):
                selected = index
                selected_hydraulics = values
                break
        if selected is None or selected_hydraulics is None:
            return None
        diameter_index[edge] = selected
        hydraulics[edge] = selected_hydraulics

    source_indices = [index for index in range(root) if local_flows.get(index, 0.0) > 0]
    for _ in range(100):
        path_drops = {
            source: sum(hydraulics[edge]["pressure_drop_bar"] for edge in _path_edges(source, parent, root))
            for source in source_indices
        }
        if not path_drops or max(path_drops.values()) <= pressure_window + 1e-9:
            break
        worst_source = max(path_drops, key=path_drops.get)
        path = _path_edges(worst_source, parent, root)
        upsizeable = [edge for edge in path if diameter_index[edge] < len(diameter_options) - 1]
        if not upsizeable:
            return None
        target = max(upsizeable, key=lambda edge: hydraulics[edge]["pressure_drop_bar"])
        diameter_index[target] += 1
        diameter = diameter_options[diameter_index[target]]
        hydraulics[target] = _pipe_hydraulics(edge_flows[target], lengths[target][2], diameter, transport)
    else:
        return None

    crf = capital_recovery_factor(finance["discount_rate"], finance["project_life_years"])
    segment_rows: list[dict[str, Any]] = []
    total_capex = 0.0
    annual_cost = 0.0
    total_leakage = 0.0
    for edge, flow in edge_flows.items():
        diameter = diameter_options[diameter_index[edge]]
        straight, route_factor, route = lengths[edge]
        capex_per_km = transport["capex_eur_per_km_at_300mm"] * (diameter / 0.3) ** transport["diameter_cost_exponent"]
        base_capex = capex_per_km * route
        material_metrics = _pipe_material_metrics(diameter, route, transport)
        capex = base_capex * float(material_metrics["material_capex_multiplier"])
        fixed_opex = capex * transport["fixed_opex_fraction"]
        annualized_capex = capex * crf
        segment_annual_cost = annualized_capex + fixed_opex
        leakage = flow * transport["co2_leakage_fraction_per_100km"] * route / 100.0
        total_capex += capex
        annual_cost += segment_annual_cost
        total_leakage += leakage
        a, b = nodes[edge[0]], nodes[edge[1]]
        segment_rows.append(
            {
                "from_node": a["node_id"],
                "to_node": b["node_id"],
                "from_name": a["name"],
                "to_name": b["name"],
                "straight_distance_km": straight,
                "route_factor": route_factor,
                "route_length_km": route,
                "flow_tpy": flow,
                "nominal_diameter_mm": diameter * 1000.0,
                **hydraulics[edge],
                "base_segment_capex_eur": base_capex,
                "segment_capex_eur": capex,
                **material_metrics,
                "annualized_segment_capex_eur": annualized_capex,
                "fixed_opex_eur_per_year": fixed_opex,
                "segment_annual_cost_eur": segment_annual_cost,
                "estimated_co2_leakage_tpy": leakage,
            }
        )

    connection_capex = len(source_indices) * transport["source_connection_capex_eur"]
    total_capex += connection_capex
    annual_cost += connection_capex * (crf + transport["fixed_opex_fraction"])
    path_drops = {
        source: sum(hydraulics[edge]["pressure_drop_bar"] for edge in _path_edges(source, parent, root))
        for source in source_indices
    }
    return {
        "segments": segment_rows,
        "pipeline_capex_eur": total_capex,
        "pipeline_annual_cost_eur": annual_cost,
        "pipeline_leakage_tpy": total_leakage,
        "route_length_km": sum(row["route_length_km"] for row in segment_rows),
        "straight_length_km": sum(row["straight_distance_km"] for row in segment_rows),
        "maximum_path_pressure_drop_bar": max(path_drops.values(), default=0.0),
        "minimum_arrival_pressure_bar": transport["inlet_pressure_bar"] - max(path_drops.values(), default=0.0),
        "objective_eur_per_year": annual_cost,
    }


def optimize_pipeline_network(
    inputs: ModelInputs,
    source_results: list[dict[str, Any]],
) -> dict[str, Any]:
    active_results = [row for row in source_results if row["allocated_product_co2_tpy"] > 0]
    if not active_results:
        return {
            "segments": [],
            "pipeline_capex_eur": 0.0,
            "pipeline_annual_cost_eur": 0.0,
            "pipeline_leakage_tpy": 0.0,
            "route_length_km": 0.0,
            "straight_length_km": 0.0,
            "maximum_path_pressure_drop_bar": 0.0,
            "minimum_arrival_pressure_bar": inputs.config["transport"]["inlet_pressure_bar"],
            "candidate_trees_evaluated": 0,
        }

    source_by_id = {source.source_id: source for source in inputs.sources}
    nodes: list[dict[str, Any]] = []
    local_flows: dict[int, float] = {}
    for index, row in enumerate(active_results):
        source = source_by_id[row["source_id"]]
        nodes.append(
            {
                "node_id": source.source_id,
                "name": source.source_name,
                "x": source.x_l93_m,
                "y": source.y_l93_m,
                "routing_factor": source.routing_factor,
            }
        )
        local_flows[index] = row["allocated_product_co2_tpy"]

    sink = inputs.config["sink"]
    nodes.append(
        {
            "node_id": "SINK",
            "name": sink["name"],
            "x": sink["x_l93_m"],
            "y": sink["y_l93_m"],
            "routing_factor": 1.0,
        }
    )
    root = len(nodes) - 1
    local_flows[root] = 0.0

    if len(nodes) > 8:
        raise ValueError("Exact tree enumeration is limited to seven sources plus the sink.")

    best: dict[str, Any] | None = None
    evaluated = 0
    if len(nodes) == 2:
        graphs = [nx.Graph([(0, 1)])]
    else:
        graphs = (
            nx.from_prufer_sequence(list(sequence))
            for sequence in itertools.product(range(len(nodes)), repeat=len(nodes) - 2)
        )

    for graph in graphs:
        candidate = _candidate_tree_result(graph, nodes, root, local_flows, inputs.config)
        if candidate is None:
            continue
        evaluated += 1
        if best is None or candidate["objective_eur_per_year"] < best["objective_eur_per_year"]:
            best = candidate
    if best is None:
        raise RuntimeError("No feasible pipeline tree satisfies the distance, velocity and pressure constraints.")
    best["candidate_trees_evaluated"] = evaluated
    best["segments"].sort(key=lambda row: (row["to_node"] != "SINK", -row["flow_tpy"], row["from_node"]))
    return best


def _blended_transport_composition(
    source_results: list[dict[str, Any]],
    base_composition: dict[str, float],
) -> dict[str, float]:
    """Build a flow-weighted dry-gas PR composition from allocated source products."""
    active = [row for row in source_results if row["allocated_product_co2_tpy"] > 0]
    if not active:
        return {key: float(value) for key, value in base_composition.items()}

    total_flow = sum(float(row["allocated_product_co2_tpy"]) for row in active)
    co2 = sum(
        float(row["allocated_product_co2_tpy"])
        * float(row["product_co2_mol_pct"])
        / 100.0
        for row in active
    ) / total_flow
    o2 = sum(
        float(row["allocated_product_co2_tpy"])
        * float(row["product_o2_ppmv"])
        / 1_000_000.0
        for row in active
    ) / total_flow
    remainder = max(1.0 - co2 - o2, 0.0)
    base_n2 = float(base_composition.get("N2", 0.0))
    base_ar = float(base_composition.get("Ar", 0.0))
    inert_total = base_n2 + base_ar
    ar_share = base_ar / inert_total if inert_total > 0 else 0.25
    composition = {
        "CO2": co2,
        "N2": remainder * (1.0 - ar_share),
        "O2": o2,
        "Ar": remainder * ar_share,
    }
    total = sum(composition.values())
    return {key: value / total for key, value in composition.items()}


def run_scenario(
    inputs: ModelInputs,
    scenario_name: str,
    source_overrides: dict[str, dict[str, Any]] | None = None,
) -> ScenarioResult:
    if scenario_name not in inputs.config["scenarios"]:
        raise KeyError(f"Unknown scenario: {scenario_name}")
    scenario = inputs.config["scenarios"][scenario_name]
    source_results = build_source_results(inputs, scenario_name, source_overrides)
    calculation_config = copy.deepcopy(inputs.config)
    calculation_config["transport"]["eos_composition"] = _blended_transport_composition(
        source_results,
        calculation_config["transport"]["eos_composition"],
    )
    calculation_inputs = ModelInputs(
        root=inputs.root,
        config=calculation_config,
        sources=inputs.sources,
        product_limits=inputs.product_limits,
        reference_product_limits=inputs.reference_product_limits,
        capture_technologies=inputs.capture_technologies,
        purification_technologies=inputs.purification_technologies,
    )
    pipeline = optimize_pipeline_network(calculation_inputs, source_results)
    _enrich_pipeline_material_summary(pipeline, calculation_config["transport"])

    total_allocated = sum(row["allocated_product_co2_tpy"] for row in source_results)
    sink_received = max(total_allocated - pipeline["pipeline_leakage_tpy"], 0.0)
    sink_capacity = float(scenario["sink_capacity_tpy"])
    captured_before_purification = sum(row["captured_before_purification_tpy"] for row in source_results)
    purification_loss = sum(row["purification_loss_tpy"] for row in source_results)
    capture_capex = sum(row["capture_capex_eur"] for row in source_results)
    purification_capex = sum(row["purification_capex_eur"] for row in source_results)
    capture_annual_cost = sum(row["capture_annual_cost_eur"] for row in source_results)
    purification_annual_cost = sum(row["purification_annual_cost_eur"] for row in source_results)
    capture_energy_emissions = sum(row["capture_energy_emissions_tpy"] for row in source_results)
    purification_energy_emissions = sum(row["purification_energy_emissions_tpy"] for row in source_results)
    total_capex = capture_capex + purification_capex + pipeline["pipeline_capex_eur"]
    total_annual_cost = capture_annual_cost + purification_annual_cost + pipeline["pipeline_annual_cost_eur"]
    chain_net_avoided = max(
        sink_received - capture_energy_emissions - purification_energy_emissions,
        0.0,
    )
    environmental = calculate_environmental_study(
        source_results, pipeline, calculation_config
    )
    transport_uncertainty = float(
        calculation_config["transport"]["cost_uncertainty_fraction"]
    )
    annual_cost_low = (
        sum(row["capture_annual_cost_low_eur"] for row in source_results)
        + sum(row["purification_annual_cost_low_eur"] for row in source_results)
        + pipeline["pipeline_annual_cost_eur"] * (1.0 - transport_uncertainty)
    )
    annual_cost_high = (
        sum(row["capture_annual_cost_high_eur"] for row in source_results)
        + sum(row["purification_annual_cost_high_eur"] for row in source_results)
        + pipeline["pipeline_annual_cost_eur"] * (1.0 + transport_uncertainty)
    )

    screened_components = {limit.component for limit in inputs.product_limits}
    reference_components = {limit.component for limit in inputs.reference_product_limits}
    unscreened_components = sorted(reference_components - screened_components)
    summary: dict[str, Any] = {
        "scenario": scenario_name,
        "description": scenario["description"],
        "flow_basis": scenario["flow_basis"],
        "sink_name": inputs.config["sink"]["name"],
        "sink_node_type": inputs.config["sink"]["node_type"],
        "sink_x_l93_m": inputs.config["sink"]["x_l93_m"],
        "sink_y_l93_m": inputs.config["sink"]["y_l93_m"],
        "sink_capacity_tpy": sink_capacity,
        "sink_capacity_enforced": scenario["enforce_sink_capacity"],
        "active_sources": sum(row["allocated_product_co2_tpy"] > 0 for row in source_results),
        "total_captured_before_purification_tpy": captured_before_purification,
        "total_potential_product_co2_tpy": sum(row["potential_product_co2_tpy"] for row in source_results),
        "total_purified_co2_tpy": total_allocated,
        "total_purification_loss_tpy": purification_loss,
        "total_allocated_to_pipeline_tpy": total_allocated,
        "total_curtailed_product_co2_tpy": sum(row["curtailed_product_co2_tpy"] for row in source_results),
        "sink_received_after_pipeline_leakage_tpy": sink_received,
        "sink_utilization_fraction": total_allocated / sink_capacity if sink_capacity else 0.0,
        "all_active_streams_pass_screened_product_spec": all(
            row["product_spec_pass"] for row in source_results if row["allocated_product_co2_tpy"] > 0
        ),
        "active_streams_failing_screened_product_spec": sum(
            not row["product_spec_pass"]
            for row in source_results
            if row["allocated_product_co2_tpy"] > 0
        ),
        "customized_source_configurations": sum(
            row["configuration_customized"]
            for row in source_results
            if row["allocated_product_co2_tpy"] > 0
        ),
        "process_safety_green_sources": sum(
            row["process_safety_screen_status"] == "Green"
            for row in source_results
            if row["allocated_product_co2_tpy"] > 0
        ),
        "process_safety_amber_sources": sum(
            row["process_safety_screen_status"] == "Amber"
            for row in source_results
            if row["allocated_product_co2_tpy"] > 0
        ),
        "process_safety_red_sources": sum(
            row["process_safety_screen_status"] == "Red"
            for row in source_results
            if row["allocated_product_co2_tpy"] > 0
        ),
        "phase_envelope_review_source_count": sum(
            row["phase_envelope_review_required"]
            for row in source_results
            if row["allocated_product_co2_tpy"] > 0
        ),
        "product_spec_components_screened": len(inputs.product_limits),
        "product_spec_components_in_reference": len(inputs.reference_product_limits),
        "product_spec_screening_coverage_fraction": (
            len(inputs.product_limits) / len(inputs.reference_product_limits)
            if inputs.reference_product_limits
            else 0.0
        ),
        "product_spec_components_not_screened": unscreened_components,
        "product_spec_reference_role": (
            "External liquid-CO2 cargo benchmark; not a contractual Dunkerque pipeline acceptance specification."
        ),
        "capture_energy_emissions_tpy": capture_energy_emissions,
        "purification_energy_emissions_tpy": purification_energy_emissions,
        "capture_electricity_mwh_per_year": sum(
            row["capture_electricity_mwh_per_year"] for row in source_results
        ),
        "capture_steam_gj_per_year": sum(
            row["capture_steam_gj_per_year"] for row in source_results
        ),
        "purification_electricity_mwh_per_year": sum(
            row["purification_electricity_mwh_per_year"] for row in source_results
        ),
        "pipeline_leakage_tpy": pipeline["pipeline_leakage_tpy"],
        "chain_net_avoided_co2_tpy": chain_net_avoided,
        "capture_capex_eur": capture_capex,
        "purification_capex_eur": purification_capex,
        "pipeline_capex_eur": pipeline["pipeline_capex_eur"],
        "pipeline_material_id": pipeline["pipeline_material_id"],
        "pipeline_material_label": pipeline["pipeline_material_label"],
        "pipeline_material_note": pipeline["pipeline_material_note"],
        "pipeline_steel_mass_t": pipeline["pipeline_steel_mass_t"],
        "pipeline_material_embodied_carbon_tco2e": pipeline[
            "pipeline_material_embodied_carbon_tco2e"
        ],
        "pipeline_material_embodied_carbon_delta_tco2e": pipeline[
            "pipeline_material_embodied_carbon_delta_tco2e"
        ],
        "pipeline_wall_thickness_min_mm": pipeline["minimum_wall_thickness_mm"],
        "pipeline_wall_thickness_max_mm": pipeline["maximum_wall_thickness_mm"],
        "total_chain_capex_eur": total_capex,
        "capture_annual_cost_eur": capture_annual_cost,
        "purification_annual_cost_eur": purification_annual_cost,
        "pipeline_annual_cost_eur": pipeline["pipeline_annual_cost_eur"],
        "total_chain_annual_cost_eur": total_annual_cost,
        "capture_cost_eur_per_t_received": capture_annual_cost / sink_received if sink_received else 0.0,
        "purification_cost_eur_per_t_received": purification_annual_cost / sink_received if sink_received else 0.0,
        "pipeline_cost_eur_per_t_received": pipeline["pipeline_annual_cost_eur"] / sink_received if sink_received else 0.0,
        "full_chain_cost_eur_per_t_received": total_annual_cost / sink_received if sink_received else 0.0,
        "full_chain_cost_low_eur_per_t_received": annual_cost_low / sink_received if sink_received else 0.0,
        "full_chain_cost_high_eur_per_t_received": annual_cost_high / sink_received if sink_received else 0.0,
        "full_chain_cost_eur_per_t_net_avoided": total_annual_cost / chain_net_avoided if chain_net_avoided else 0.0,
        "full_chain_cost_eur_per_t_lifecycle_net_avoided": (
            total_annual_cost / environmental["environmental_lifecycle_net_avoided_co2_tpy"]
            if environmental["environmental_lifecycle_net_avoided_co2_tpy"]
            else 0.0
        ),
        "pipeline_route_length_km": pipeline["route_length_km"],
        "pipeline_straight_length_km": pipeline["straight_length_km"],
        "maximum_path_pressure_drop_bar": pipeline["maximum_path_pressure_drop_bar"],
        "minimum_arrival_pressure_bar": pipeline["minimum_arrival_pressure_bar"],
        "candidate_pipeline_trees_evaluated": pipeline["candidate_trees_evaluated"],
        "transport_equation_of_state": "Peng-Robinson",
        "transport_eos_temperature_c": float(calculation_config["transport"]["temperature_c"]),
        "transport_eos_composition_mol_fraction": dict(calculation_config["transport"]["eos_composition"]),
        "transport_eos_composition_basis": (
            "Flow-weighted selected product targets"
            if any(row["allocated_product_co2_tpy"] > 0 for row in source_results)
            else "Configured reference composition"
        ),
        "transport_eos_binary_interaction_parameters": "kij = 0 (classical screening mixing rule)",
        "transport_eos_density_min_kg_per_m3": min((row["eos_density_kg_per_m3"] for row in pipeline["segments"]), default=0.0),
        "transport_eos_density_max_kg_per_m3": max((row["eos_density_kg_per_m3"] for row in pipeline["segments"]), default=0.0),
        "transport_eos_z_min": min((row["eos_compressibility_factor"] for row in pipeline["segments"]), default=0.0),
        "transport_eos_z_max": max((row["eos_compressibility_factor"] for row in pipeline["segments"]), default=0.0),
        **environmental,
        "model_class": "screening / pre-FEED",
        "model_stages": ["capture", "purification", "transport_to_dunkerque_site"],
        "model_studies": ["techno_economic", "environmental"],
        "downstream_terminal_shipping_storage_included": False,
    }
    return ScenarioResult(
        scenario=scenario_name,
        source_results=source_results,
        pipeline_segments=pipeline["segments"],
        summary=summary,
    )


def build_material_comparison(
    result: ScenarioResult,
    config: dict[str, Any],
    carbon_value_eur_per_t: float = 100.0,
) -> list[dict[str, Any]]:
    """Compare configured materials on the selected topology and diameters.

    The comparison deliberately holds the network layout and hydraulic diameters
    fixed. It is a transparent pre-FEED decision screen, not a mechanical design or
    a claim that a material is suitable without fracture, corrosion, weldability,
    impurity, terrain, and code checks.
    """

    transport = config["transport"]
    finance = config["finance"]
    years = float(finance["project_life_years"])
    crf = capital_recovery_factor(
        float(finance["discount_rate"]), int(finance["project_life_years"])
    )
    source_connections = int(result.summary["active_sources"])
    connection_capex = source_connections * float(
        transport["source_connection_capex_eur"]
    )
    received = float(result.summary["sink_received_after_pipeline_leakage_tpy"])
    captured_product = float(result.summary["total_allocated_to_pipeline_tpy"])
    base_environmental_burden = float(
        result.summary["environmental_total_climate_burden_tco2e_per_year"]
    ) - float(
        result.summary.get(
            "environmental_pipeline_material_delta_annualized_tco2e_per_year",
            0.0,
        )
    )

    rows: list[dict[str, Any]] = []
    for material_id, material in transport.get("materials", {}).items():
        segment_capex = 0.0
        steel_mass = 0.0
        embodied = 0.0
        embodied_delta = 0.0
        wall_values: list[float] = []
        for segment in result.pipeline_segments:
            metrics = _pipe_material_metrics(
                float(segment["nominal_diameter_mm"]) / 1000.0,
                float(segment["route_length_km"]),
                transport,
                material_id,
            )
            base_capex = float(
                segment.get("base_segment_capex_eur", segment["segment_capex_eur"])
            )
            segment_capex += base_capex * float(
                metrics["material_capex_multiplier"]
            )
            steel_mass += float(metrics["steel_mass_t"])
            embodied += float(metrics["material_embodied_carbon_tco2e"])
            embodied_delta += float(metrics["material_embodied_carbon_delta_tco2e"])
            wall_values.append(float(metrics["wall_thickness_mm"]))

        pipeline_capex = segment_capex + connection_capex
        pipeline_annual_cost = pipeline_capex * (
            crf + float(transport["fixed_opex_fraction"])
        )
        total_capex = (
            float(result.summary["capture_capex_eur"])
            + float(result.summary["purification_capex_eur"])
            + pipeline_capex
        )
        total_annual_cost = (
            float(result.summary["capture_annual_cost_eur"])
            + float(result.summary["purification_annual_cost_eur"])
            + pipeline_annual_cost
        )
        material_delta_annual = embodied_delta / years if years > 0 else 0.0
        environmental_burden = base_environmental_burden + material_delta_annual
        lifecycle_net_avoided = max(captured_product - environmental_burden, 0.0)
        annual_carbon_value = lifecycle_net_avoided * carbon_value_eur_per_t
        annual_value_headroom = annual_carbon_value - total_annual_cost
        payback = (
            total_capex / annual_value_headroom
            if annual_value_headroom > 0
            else None
        )

        rows.append(
            {
                "material_id": material_id,
                "material": str(material.get("label", material_id)),
                "management_note": str(material.get("management_note", "")),
                "smys_mpa": float(material["smys_mpa"]),
                "wall_thickness_min_mm": min(wall_values, default=0.0),
                "wall_thickness_max_mm": max(wall_values, default=0.0),
                "pipeline_steel_mass_t": steel_mass,
                "pipeline_material_embodied_carbon_tco2e": embodied,
                "material_embodied_intensity_kgco2e_per_t_received": (
                    embodied * 1000.0 / (received * years)
                    if received > 0 and years > 0
                    else 0.0
                ),
                "pipeline_capex_eur": pipeline_capex,
                "total_chain_capex_eur": total_capex,
                "total_chain_annual_cost_eur": total_annual_cost,
                "full_chain_cost_eur_per_t_received": (
                    total_annual_cost / received if received > 0 else 0.0
                ),
                "full_chain_cost_eur_per_t_net_avoided": (
                    total_annual_cost / lifecycle_net_avoided
                    if lifecycle_net_avoided > 0
                    else 0.0
                ),
                "environmental_total_climate_burden_tco2e_per_year": environmental_burden,
                "environmental_lifecycle_net_avoided_co2_tpy": lifecycle_net_avoided,
                "annual_carbon_value_eur": annual_carbon_value,
                "annual_value_headroom_eur": annual_value_headroom,
                "simple_payback_years": payback,
                "calculation_basis": (
                    "Same optimized topology and hydraulic diameters; "
                    "material-sensitive cost and embodied-carbon screen."
                ),
            }
        )
    return rows


def run_custom_scenario(
    inputs: ModelInputs,
    *,
    active_source_ids: Iterable[str],
    flow_basis: str,
    sink_capacity_tpy: float,
    enforce_sink_capacity: bool = True,
    finance_overrides: dict[str, float] | None = None,
    transport_overrides: dict[str, str] | None = None,
    source_overrides: dict[str, dict[str, Any]] | None = None,
    scenario_name: str = "custom_case",
) -> ScenarioResult:
    """Run a UI-defined case without changing any files on disk."""
    valid_ids = {source.source_id for source in inputs.sources}
    selected_ids = list(dict.fromkeys(active_source_ids))
    unknown = sorted(set(selected_ids) - valid_ids)
    if unknown:
        raise ValueError(f"Unknown source IDs: {', '.join(unknown)}")
    if sink_capacity_tpy <= 0:
        raise ValueError("Sink receiving capacity must be positive.")
    unknown_override_ids = sorted(set(source_overrides or {}) - valid_ids)
    if unknown_override_ids:
        raise ValueError(
            f"Source overrides contain unknown IDs: {', '.join(unknown_override_ids)}"
        )

    custom_config = copy.deepcopy(inputs.config)
    if finance_overrides:
        allowed = {
            "discount_rate",
            "project_life_years",
            "electricity_price_eur_per_mwh",
            "steam_price_eur_per_gj",
        }
        unexpected = sorted(set(finance_overrides) - allowed)
        if unexpected:
            raise ValueError(f"Unsupported finance overrides: {', '.join(unexpected)}")
        custom_config["finance"].update(finance_overrides)
    if transport_overrides:
        unexpected = sorted(set(transport_overrides) - {"pipeline_material"})
        if unexpected:
            raise ValueError(
                f"Unsupported transport overrides: {', '.join(unexpected)}"
            )
        material_id = transport_overrides.get("pipeline_material")
        materials = custom_config["transport"].get("materials", {})
        if material_id not in materials:
            raise ValueError(f"Unknown pipeline material: {material_id}")
        custom_config["transport"]["pipeline_material"] = material_id
    custom_config["scenarios"][scenario_name] = {
        "description": "User-defined source selection and assumptions from the interactive dashboard.",
        "flow_basis": flow_basis,
        "active_source_ids": selected_ids,
        "sink_capacity_tpy": float(sink_capacity_tpy),
        "enforce_sink_capacity": bool(enforce_sink_capacity),
    }
    custom_inputs = ModelInputs(
        root=inputs.root,
        config=custom_config,
        sources=inputs.sources,
        product_limits=inputs.product_limits,
        reference_product_limits=inputs.reference_product_limits,
        capture_technologies=inputs.capture_technologies,
        purification_technologies=inputs.purification_technologies,
    )
    return run_scenario(custom_inputs, scenario_name, source_overrides)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def result_to_dict(result: ScenarioResult) -> dict[str, Any]:
    return asdict(result)
