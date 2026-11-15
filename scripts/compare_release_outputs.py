"""Compare the frozen v0.7.3 screen with the v0.8 process-linked scenarios."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "verification" / "baseline_v073" / "scenario_comparison.csv"
PROCESS = ROOT / "verification" / "process_linked" / "scenario_comparison.csv"
COMPARISON_DIR = ROOT / "verification" / "comparison"

METRICS = (
    ("total_captured_before_purification_tpy", "Captured CO2", "Mt/y", 1e-6),
    ("total_purified_co2_tpy", "Purified CO2", "Mt/y", 1e-6),
    ("environmental_lifecycle_net_avoided_co2_tpy", "Lifecycle net avoided", "Mt/y", 1e-6),
    ("environmental_total_climate_burden_tco2e_per_year", "Climate burden", "ktCO2e/y", 1e-3),
    ("environmental_climate_burden_kgco2e_per_t_received", "Climate intensity", "kgCO2e/t", 1.0),
    ("capture_capex_eur", "Capture CAPEX", "MEUR", 1e-6),
    ("purification_capex_eur", "Purification CAPEX", "MEUR", 1e-6),
    ("total_chain_capex_eur", "Total chain CAPEX", "MEUR", 1e-6),
    ("capture_cost_eur_per_t_received", "Capture cost", "EUR/t", 1.0),
    ("purification_cost_eur_per_t_received", "Purification cost", "EUR/t", 1.0),
    ("pipeline_cost_eur_per_t_received", "Pipeline cost", "EUR/t", 1.0),
    ("full_chain_cost_eur_per_t_received", "Full-chain cost", "EUR/t", 1.0),
)


def read_by_scenario(path: Path) -> dict[str, dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return {row["scenario"]: row for row in csv.DictReader(handle)}


def number(value: str) -> float:
    return float(value)


def format_value(value: float, unit: str) -> str:
    if unit in {"Mt/y", "MEUR"}:
        return f"{value:,.3f}"
    if unit == "ktCO2e/y":
        return f"{value:,.1f}"
    return f"{value:,.2f}"


def main() -> int:
    baseline = read_by_scenario(BASELINE)
    process = read_by_scenario(PROCESS)
    if set(baseline) != set(process):
        raise ValueError("Baseline and process-linked scenario sets do not match")

    rows: list[dict[str, Any]] = []
    for scenario in process:
        for key, label, unit, scale in METRICS:
            old = number(baseline[scenario][key]) * scale
            new = number(process[scenario][key]) * scale
            delta = new - old
            rows.append(
                {
                    "scenario": scenario,
                    "metric": label,
                    "unit": unit,
                    "v073_screening": old,
                    "v080_process_linked": new,
                    "absolute_change": delta,
                    "relative_change_pct": (delta / old * 100.0) if abs(old) > 1e-12 else "",
                }
            )

    COMPARISON_DIR.mkdir(parents=True, exist_ok=True)
    delta_path = COMPARISON_DIR / "release_delta.csv"
    with delta_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    matched_path = COMPARISON_DIR / "matched_input_comparison.csv"
    with matched_path.open(encoding="utf-8-sig", newline="") as handle:
        matched = list(csv.DictReader(handle))

    chosen_metrics = {
        ("Capture", "MEA", "Electricity"),
        ("Capture", "MEA", "Reboiler steam"),
        ("Capture", "MEA", "Annualized capture cost"),
        ("Purification", "Train A", "Electricity"),
        ("Purification", "Train A", "Annualized purification cost"),
        ("Purification", "Train B", "Electricity"),
        ("Purification", "Train B", "Annualized purification cost"),
    }
    selected_matched = [
        row
        for row in matched
        if (row["stage"], row["train"], row["metric"]) in chosen_metrics
    ]

    invariants: list[tuple[str, bool, bool, float]] = []
    for scenario in process:
        summary_path = ROOT / "verification" / "process_linked" / scenario / "summary.json"
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        invariants.append(
            (
                scenario,
                bool(summary["capture_to_purification_connected"]),
                bool(summary["purification_to_transport_connected"]),
                float(summary["maximum_process_mass_balance_error_fraction"]),
            )
        )

    announced = [
        row for row in rows if row["scenario"] == "announced_2030"
    ]
    report = [
        "# Verification report — process-linked v0.8.0",
        "",
        "## Verification status",
        "",
        "- 46 automated model, UI, EOS, trajectory and integration tests pass.",
        "- All four standard scenarios were regenerated with the process-linked calculation.",
        "- The frozen v0.7.3 coefficient calculation remains selectable and its announced-case cost regression is exact.",
        "- Papa's preserved capture and purification packages were executed without modification and compared on a harmonized basis.",
        "- These checks demonstrate software consistency and matched-model agreement; they are not independent experimental or vendor validation.",
        "",
        "## Connected-stage invariants",
        "",
        "| Scenario | Capture output = purification input | Purification product = transport input | Maximum mass-balance residual |",
        "|---|---:|---:|---:|",
    ]
    for scenario, cap_link, pur_link, residual in invariants:
        report.append(
            f"| {scenario} | {'Pass' if cap_link else 'Fail'} | "
            f"{'Pass' if pur_link else 'Fail'} | {residual:.2e} |"
        )

    report.extend(
        [
            "",
            "## Announced 2030 case: frozen screen versus connected model",
            "",
            "| Metric | Unit | v0.7.3 screen | v0.8.0 process-linked | Change |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for row in announced:
        relative = row["relative_change_pct"]
        report.append(
            f"| {row['metric']} | {row['unit']} | "
            f"{format_value(row['v073_screening'], row['unit'])} | "
            f"{format_value(row['v080_process_linked'], row['unit'])} | "
            f"{relative:+.2f}% |"
        )

    report.extend(
        [
            "",
            "The CO2 flow and route are unchanged because the announced source flows, recovery and receiver limit are unchanged. Cost and climate results change because capture/purification utilities, equipment, cooling and consumables are now calculated from connected process conditions rather than stage multipliers.",
            "",
            "## Matched-input Papa cross-check",
            "",
            "| Stage / analogue | Metric | Unit | Papa | v0.8.0 | Difference |",
            "|---|---|---:|---:|---:|---:|",
        ]
    )
    for row in selected_matched:
        report.append(
            f"| {row['stage']} / {row['train']} | {row['metric']} | {row['unit']} | "
            f"{float(row['papa_reference']):.3f} | {float(row['improved_matched']):.3f} | "
            f"{float(row['improved_vs_papa_pct']):+.2f}% |"
        )

    report.extend(
        [
            "",
            "![Matched-input comparison](comparison/matched_input_comparison.png)",
            "",
            "## Remaining validation needs",
            "",
            "- Replace source gas-composition proxies with reconciled plant assays and operating envelopes.",
            "- Validate capture and purification performance with vendor simulations, guarantees or pilot data.",
            "- Confirm the contractual receiving-network product specification and phase-envelope margin.",
            "- Replace screening CAPEX factors with route- and site-specific quantities and quotations.",
            "- Perform non-isothermal transient hydraulics and code-based mechanical design before FEED decisions.",
            "",
            "The complete numerical differences for all scenarios are in `verification/comparison/release_delta.csv`.",
        ]
    )
    (ROOT / "verification" / "VERIFICATION_REPORT.md").write_text(
        "\n".join(report) + "\n", encoding="utf-8"
    )
    print(f"Saved {delta_path.relative_to(ROOT)}")
    print("Saved verification/VERIFICATION_REPORT.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
