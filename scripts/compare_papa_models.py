"""Create reproducible matched-input comparisons with Papa's local reference runs."""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from north_co2_model.model import (  # noqa: E402
    _capture_economics,
    _purification_economics,
    load_model_inputs,
)
from north_co2_model.process_models import (  # noqa: E402
    calculate_capture_process,
    calculate_purification_process,
)


def _pct_difference(value: float, reference: float) -> float | None:
    return (value - reference) / reference * 100.0 if abs(reference) > 1e-12 else None


def _combined_ppm(composition: dict[str, float], *components: str) -> float:
    return sum(float(composition.get(key, 0.0)) for key in components) * 1_000_000.0


def _metric_row(
    stage: str,
    train: str,
    metric: str,
    unit: str,
    papa: float,
    improved: float,
    screening: float | None,
    note: str,
) -> dict[str, Any]:
    return {
        "stage": stage,
        "train": train,
        "metric": metric,
        "unit": unit,
        "papa_reference": papa,
        "improved_matched": improved,
        "improved_vs_papa_pct": _pct_difference(improved, papa),
        "legacy_screening": screening,
        "legacy_vs_papa_pct": (
            _pct_difference(screening, papa) if screening is not None else None
        ),
        "interpretation": note,
    }


def build_comparison(reference_json: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    reference = json.loads(reference_json.read_text(encoding="utf-8"))
    inputs = load_model_inputs(ROOT)
    base_source = next(source for source in inputs.sources if source.source_id == "S2")
    papa_capture = reference["capture"]
    capture_capacity = float(papa_capture["economics"]["capture_capacity_tco2_yr"])
    capture_rate = float(papa_capture["capture_rate"])
    source = replace(base_source, capture_rate=capture_rate)
    finance = {
        **inputs.config["finance"],
        "discount_rate": 0.08,
        "project_life_years": 25,
        "electricity_price_eur_per_mwh": 165.0,
        "steam_price_eur_per_gj": 7.0,
        "cooling_price_eur_per_mwh": 20.625,
    }
    capture_technology = {
        **inputs.capture_technologies["post_combustion_amine"],
        "process_reference_capex_meur": 250.0,
        "reference_capacity_tpy": 1_000_000.0,
        "scale_exponent": 0.65,
        "fixed_opex_fraction": 0.04,
    }
    improved_capture = calculate_capture_process(
        source,
        capture_technology,
        inputs.process_source_inputs["S2"],
        capture_capacity,
        finance,
    )
    screening_source = replace(
        source,
        capture_electricity_mwh_per_t_captured=0.03,
        capture_steam_gj_per_t_captured=3.5,
        capture_variable_opex_eur_per_t_captured=14.0,
        capture_reference_capex_meur=250.0,
        capture_reference_capacity_tpy=1_000_000.0,
        capture_scale_exponent=0.65,
        capture_fixed_opex_fraction=0.04,
    )
    legacy_capture = _capture_economics(screening_source, capture_capacity, finance)
    papa_steam_gj_t = (
        float(papa_capture["economics"]["Vapeur"])
        / 7.0
        / capture_capacity
    )
    papa_solvent_kg_t = float(papa_capture["makeup"]["MEA_total_kg_tCO2"])
    papa_raw_co2 = float(papa_capture["raw_product_y_mol"]["CO2"]) * 100.0
    papa_capture_cost = float(papa_capture["economics"]["Cost_per_t"])
    papa_capture_capex = float(papa_capture["economics"]["CAPEX_total"]) / 1e6

    rows = [
        _metric_row("Capture", "MEA", "CO2 capture efficiency", "%", capture_rate * 100.0, capture_rate * 100.0, capture_rate * 100.0, "Identical operating target."),
        _metric_row("Capture", "MEA", "Wet raw-product CO2", "mol-%", papa_raw_co2, improved_capture["capture_raw_product_composition_mol_fraction"]["CO2"] * 100.0, None, "Connected composition calculated from absorber/stripper trace transfer and condensation."),
        _metric_row("Capture", "MEA", "Electricity", "kWh/t captured CO2", float(papa_capture["energy"]["W_elec_kWh_t"]), improved_capture["capture_specific_electricity_mwh_per_t"] * 1000.0, 30.0, "Blower and solvent-pump work replace a fixed coefficient."),
        _metric_row("Capture", "MEA", "Reboiler steam", "GJ/t captured CO2", papa_steam_gj_t, improved_capture["capture_specific_steam_gj_per_t"], 3.5, "Reaction, solvent sensible heat, water vaporisation and losses are explicit."),
        _metric_row("Capture", "MEA", "MEA makeup", "kg/t captured CO2", papa_solvent_kg_t, improved_capture["capture_specific_solvent_kg_per_t"], None, "O2- and SOx-sensitive degradation from Papa's method."),
        _metric_row("Capture", "MEA", "CAPEX", "MEUR", papa_capture_capex, improved_capture["capture_capex_eur"] / 1e6, legacy_capture["capture_capex_eur"] / 1e6, "Same 250 MEUR/1 Mt/y, 0.65 scaling basis."),
        _metric_row("Capture", "MEA", "Annualized capture cost", "EUR/t captured CO2", papa_capture_cost, improved_capture["capture_cost_eur_per_t_captured"], legacy_capture["capture_cost_eur_per_t_captured"], "Same finance and utility-price boundary."),
    ]

    purification_summaries: dict[str, Any] = {}
    for train_key, label, technology_id, ref_capex in (
        ("purification_train_a", "Train A", "standard_dehydration", 74.0),
        ("purification_train_b", "Train B", "cryogenic_polishing", 137.0),
    ):
        papa = reference[train_key]
        final = papa["final_y_mol"]
        feed_co2 = float(papa["economics"]["feed_CO2_tCO2_yr"])
        product_co2 = float(papa["economics"]["capacity_tCO2_yr"])
        recovery = product_co2 / feed_co2
        target_source = replace(
            source,
            purification_recovery=recovery,
            product_co2_mol_pct=float(final.get("CO2", 0.0)) * 100.0,
            product_h2o_ppmv=_combined_ppm(final, "H2O"),
            product_o2_ppmv=_combined_ppm(final, "O2"),
            product_nox_ppmv=_combined_ppm(final, "NO", "NO2"),
            product_sox_ppmv=_combined_ppm(final, "SO2", "H2S"),
            product_co_ppmv=_combined_ppm(final, "CO"),
            purification_reference_capex_meur=ref_capex,
            purification_reference_capacity_tpy=1_000_000.0,
            purification_scale_exponent=0.68,
            purification_fixed_opex_fraction=0.04,
            purification_electricity_mwh_per_t_product=(
                0.12 if label == "Train A" else 0.17
            ),
            purification_variable_opex_eur_per_t_product=(4.0 if label == "Train A" else 3.0),
        )
        technology = {
            **inputs.purification_technologies[technology_id],
            "process_reference_capex_meur": ref_capex,
            "reference_capacity_tpy": 1_000_000.0,
            "scale_exponent": 0.68,
            "fixed_opex_fraction": 0.04,
        }
        purification_finance = {
            **finance,
            "steam_price_eur_per_gj": 20.0,
        }
        improved = calculate_purification_process(
            target_source,
            technology,
            improved_capture,
            feed_co2,
            product_co2,
            purification_finance,
            110.0,
        )
        legacy = _purification_economics(
            target_source, product_co2, purification_finance
        )
        papa_recovery = product_co2 / feed_co2 * 100.0
        rows.extend(
            [
                _metric_row("Purification", label, "CO2 recovery", "%", papa_recovery, product_co2 / feed_co2 * 100.0, target_source.purification_recovery * 100.0, "Identical mass-flow target."),
                _metric_row("Purification", label, "Product CO2", "mol-%", float(final.get("CO2", 0.0)) * 100.0, improved["product_co2_mol_pct_achieved"], target_source.product_co2_mol_pct, "Actual connected product, not a display-only target."),
                _metric_row("Purification", label, "Electricity", "kWh/t feed CO2", float(papa["energy"]["elec_kWh_tCO2"]), improved["purification_specific_electricity_mwh_per_t"] * 1000.0 * product_co2 / feed_co2, legacy["purification_electricity_mwh_per_year"] / feed_co2 * 1000.0, "Multistage compression is included exactly once; Train B includes refrigeration."),
                _metric_row("Purification", label, "Thermal duty", "kWhth/t feed CO2", float(papa["energy"]["hot_kWh_tCO2"]), improved["purification_specific_thermal_mwh_per_t"] * 1000.0 * product_co2 / feed_co2, 0.0, "Dehydration regeneration and deoxygenation preheat are explicit."),
                _metric_row("Purification", label, "Cooling duty", "kWhth/t feed CO2", float(papa["energy"]["cooling_kWh_tCO2"]), improved["purification_specific_cooling_mwh_per_t"] * 1000.0 * product_co2 / feed_co2, 0.0, "Compression/intercooling and feed cooling are explicit."),
                _metric_row("Purification", label, "CAPEX", "MEUR", float(papa["economics"]["CAPEX_total"]) / 1e6, improved["purification_capex_eur"] / 1e6, legacy["purification_capex_eur"] / 1e6, "Reference component totals and finance basis harmonized."),
                _metric_row("Purification", label, "Annualized purification cost", "EUR/t product CO2", float(papa["economics"]["cost_per_tCO2"]), improved["purification_cost_eur_per_t_product"], legacy["purification_cost_eur_per_t_product"], "Utilities and project finance harmonized; consumable detail remains model-specific."),
            ]
        )
        purification_summaries[label] = {
            "papa": papa,
            "improved": improved,
            "legacy": legacy,
        }

    summary = {
        "reference_file": str(reference_json.relative_to(ROOT)).replace("\\", "/"),
        "matched_basis": {
            "capture_feed": papa_capture["flue_y_mol"],
            "capture_capacity_tpy": capture_capacity,
            "capture_rate": capture_rate,
            "operating_hours_per_year": 8000,
            "pipeline_delivery_pressure_bar": 110.0,
            "discount_rate": 0.08,
            "project_life_years": 25,
            "electricity_price_eur_per_mwh": 165.0,
            "capture_steam_price_eur_per_gj": 7.0,
            "purification_thermal_price_eur_per_mwh": 72.0,
        },
        "limitations": [
            "Papa's capture model is stagewise and closes lean-loading recycle; the improved interface uses an analytical multi-source surrogate with the same energy terms.",
            "Papa's purification trains resolve individual unit operations and species; the interface aggregates them into configurable train families while preserving the wet-feed handoff, component balance and utility boundaries.",
            "Exact agreement is not expected where unit sizing, trace chemistry, refrigerant treatment or consumable inventories differ.",
            "The matched comparison is a numerical cross-check, not independent experimental validation.",
        ],
    }
    return rows, summary


def write_outputs(rows: list[dict[str, Any]], summary: dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "matched_input_comparison.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (output_dir / "comparison_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    selected = [
        row
        for row in rows
        if row["metric"] in {"Reboiler steam", "Electricity", "Annualized capture cost", "Annualized purification cost"}
    ]
    labels = [f"{row['stage']} / {row['train']}  ·  {row['metric']}" for row in selected]
    positions = list(range(len(selected)))
    improved_difference = [float(row["improved_vs_papa_pct"]) for row in selected]
    legacy_difference = [float(row["legacy_vs_papa_pct"]) for row in selected]
    fig, axes = plt.subplots(1, 2, figsize=(13.4, 6.2), sharey=True)
    for ax, values, title, colour in (
        (axes[0], improved_difference, "Process-linked v0.8.0", "#0F8B8D"),
        (axes[1], legacy_difference, "Legacy v0.7.3 screen", "#64748B"),
    ):
        bars = ax.barh(positions, values, color=colour, alpha=0.92)
        ax.axvline(0.0, color="#172033", linewidth=0.9)
        ax.grid(axis="x", alpha=0.22)
        ax.set_title(title, fontsize=11, weight="bold")
        ax.set_xlabel("Difference from Papa reference (%)")
        ax.bar_label(
            bars,
            labels=[f"{value:+.1f}%" for value in values],
            padding=3,
            fontsize=8,
        )
        span = max(max(abs(value) for value in values), 1.0)
        ax.set_xlim(min(min(values), 0.0) - span * 0.12, max(max(values), 0.0) + span * 0.18)
    axes[0].set_yticks(positions, labels, fontsize=8.5)
    axes[0].invert_yaxis()
    fig.suptitle(
        "Matched-input deviation from Papa reference models",
        fontsize=14,
        weight="bold",
    )
    fig.text(
        0.5,
        0.01,
        "Zero denotes agreement; panels use independent horizontal scales.",
        ha="center",
        fontsize=9,
        color="#475569",
    )
    fig.tight_layout(rect=(0.0, 0.045, 1.0, 0.94))
    fig.savefig(output_dir / "matched_input_comparison.png", dpi=180)
    plt.close(fig)

    def table(stage: str, train: str) -> str:
        subset = [row for row in rows if row["stage"] == stage and row["train"] == train]
        lines = [
            "| Metric | Unit | Papa | Improved | Difference | Legacy |",
            "|---|---:|---:|---:|---:|---:|",
        ]
        for row in subset:
            difference = row["improved_vs_papa_pct"]
            legacy = row["legacy_screening"]
            lines.append(
                f"| {row['metric']} | {row['unit']} | {row['papa_reference']:.4g} | "
                f"{row['improved_matched']:.4g} | "
                f"{difference:+.1f}% | "
                f"{legacy:.4g} |" if legacy is not None else
                f"| {row['metric']} | {row['unit']} | {row['papa_reference']:.4g} | "
                f"{row['improved_matched']:.4g} | {difference:+.1f}% | — |"
            )
        return "\n".join(lines)

    report = f"""# Technical comparison: v0.7.3 screen, Papa references and process-linked interface

## Purpose and model boundary

This report documents the matched-input numerical cross-check used for the process-linked model. Capture ends at the wet, low-pressure CO₂ product. Purification receives that exact flow and composition, removes water and impurities, accounts for CO₂ loss, and performs compression to 110 bar. Pipeline hydraulics begin at 110 bar; compression is therefore not counted again in transport.

Papa's unmodified packages were executed locally from the preserved extraction directory. Their files were not copied into or changed by the application. The comparison runner reads the compact reference JSON created by `scripts/run_papa_reference.py`.

## Harmonized basis

- Wet flue gas: 14 mol-% CO₂, 11 mol-% H₂O, 4 mol-% O₂ and the same trace composition as Papa NB01.
- Capture throughput: {summary['matched_basis']['capture_capacity_tpy']:,.1f} t CO₂/y; operating time: 8,000 h/y.
- Capture target: {summary['matched_basis']['capture_rate']:.3%}.
- Product delivery pressure: 110 bar.
- Economics: 8% discount rate, 25 years; electricity €165/MWh. Capture steam is €7/GJ; purification thermal energy is €72/MWhth, matching the respective reference configurations.
- Papa and the improved model were run independently. The improved model adopts Papa's physical stage boundaries and reference assumptions; agreement therefore measures implementation consistency, not independent validation.

## Capture comparison

{table('Capture', 'MEA')}

![Matched-input comparison](../verification/comparison/matched_input_comparison.png)

The process-linked MEA calculation uses a molar cyclic-capacity balance for solvent circulation. Reboiler heat is the sum of CO₂ reaction heat, residual solvent sensible heat after the rich/lean exchanger, water vaporisation and a heat-loss allowance. Electricity is calculated from flue-gas blower work and rich-solvent pumping. MEA makeup responds to O₂ and SOₓ. The wet product composition is calculated from condensation and component-specific transfer factors and becomes the purification inlet.

## Purification comparison — Train A analogue

{table('Purification', 'Train A')}

The interface analogue represents knockout/cooling, impurity polishing, deoxygenation, dehydration and multistage compression. It is intentionally faster and less unit-resolved than Papa Train A, but uses the same connected wet feed and reports electrical, thermal and cooling duties separately.

## Purification comparison — Train B analogue

{table('Purification', 'Train B')}

The cryogenic analogue adds deep dehydration, non-condensable removal and refrigeration. Papa's detailed column, guard-bed, solid-risk and phase-equilibrium diagnostics remain more detailed; the interface exposes this train as a configurable engineering family for cluster scenarios.

## Implemented scientific changes

1. The capture wet-product flow, temperature, pressure and component composition are transmitted directly into purification.
2. Purification performs a component balance and returns the achieved composition; it never creates inert gas merely to satisfy an inconsistent purity/trace target.
3. Multistage compression work is calculated from pressure ratio, mixture molecular weight, stage count and isentropic efficiency, and is counted only in purification.
4. MEA heat and degradation equations are restricted to the MEA technology family. Cryogenic, oxyfuel, DMX and membrane routes retain separate technology-family equations.
5. Utilities, consumables, annualized equipment, fixed O&M and variable O&M have explicit cost and environmental boundaries.
6. The v0.7.3 coefficient screen remains selectable and reproduces its cost results for regression comparison.

## Interpretation and limitations

{chr(10).join(f'- {item}' for item in summary['limitations'])}

Source-specific flue-gas defaults in `config/process_sources.toml` are labelled engineering proxies. They are editable in the interface and must be replaced by plant assays for FEED. Product acceptance remains governed by the receiving-system specification. The present cross-check supports code verification and model consistency; it does not replace vendor design, pilot testing or independent experimental validation.

## Reproduction

```powershell
python scripts/run_papa_reference.py
python scripts/compare_papa_models.py
python -m unittest discover -s tests -v
```

Generated numerical files and the comparison figure are in `verification/comparison/`.
"""
    (ROOT / "docs" / "TECHNICAL_COMPARISON_REPORT.md").write_text(
        report, encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--reference-json",
        type=Path,
        default=ROOT / "verification" / "papa_reference" / "reference_case.json",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "verification" / "comparison",
    )
    args = parser.parse_args()
    rows, summary = build_comparison(args.reference_json)
    write_outputs(rows, summary, args.output_dir)
    print(f"Saved comparison outputs to {args.output_dir.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
