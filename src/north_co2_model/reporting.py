from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from .model import ModelInputs, ScenarioResult, write_csv, write_json


SECTOR_STYLE = {
    "lime": ("#2563EB", "o"),
    "gypsum_plaster": ("#94A3B8", "h"),
    "cement": ("#7C3AED", "D"),
    "aluminium": ("#F59E0B", "P"),
    "iron_steel": ("#9A3412", "s"),
}

LABEL_OFFSETS = {
    "S1": (-85, 10),
    "S2": (-90, -22),
    "S3": (-105, -30),
    "S4": (-112, -28),
    "S5": (18, -30),
}


def _money(value: float) -> str:
    if abs(value) >= 1e9:
        return f"€{value / 1e9:,.2f} bn"
    if abs(value) >= 1e6:
        return f"€{value / 1e6:,.1f} m"
    return f"€{value:,.0f}"


def plot_network(inputs: ModelInputs, result: ScenarioResult, path: Path) -> None:
    summary = result.summary
    source_rows = {row["source_id"]: row for row in result.source_results}
    source_lookup = {source.source_id: source for source in inputs.sources}
    sink = inputs.config["sink"]
    node_xy = {
        source.source_id: (source.x_l93_m / 1000.0, source.y_l93_m / 1000.0)
        for source in inputs.sources
    }
    node_xy["SINK"] = (sink["x_l93_m"] / 1000.0, sink["y_l93_m"] / 1000.0)

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9.5,
            "axes.labelsize": 10.5,
            "figure.facecolor": "white",
        }
    )
    fig = plt.figure(figsize=(15.5, 8.5), constrained_layout=False)
    grid = fig.add_gridspec(
        1,
        2,
        width_ratios=[5.1, 1.65],
        left=0.06,
        right=0.97,
        top=0.86,
        bottom=0.10,
        wspace=0.08,
    )
    ax = fig.add_subplot(grid[0, 0])
    panel = fig.add_subplot(grid[0, 1])
    panel.axis("off")
    ax.set_facecolor("#F8FAFC")
    ax.grid(True, color="#DCE3EA", linewidth=0.7, alpha=0.85)

    for segment in result.pipeline_segments:
        x1, y1 = node_xy[segment["from_node"]]
        x2, y2 = node_xy[segment["to_node"]]
        linewidth = 1.5 + segment["nominal_diameter_mm"] / 100.0
        ax.plot(
            [x1, x2],
            [y1, y2],
            color="white",
            linewidth=linewidth + 2.6,
            solid_capstyle="round",
            zorder=1,
        )
        ax.plot(
            [x1, x2],
            [y1, y2],
            color="#0F766E",
            linewidth=linewidth,
            solid_capstyle="round",
            zorder=2,
        )

    for source_id, source in source_lookup.items():
        row = source_rows[source_id]
        active = row["allocated_product_co2_tpy"] > 0
        color, marker = SECTOR_STYLE[source.sector]
        x, y = node_xy[source_id]
        ax.scatter(
            [x],
            [y],
            s=105 if active else 72,
            marker=marker,
            facecolor=color if active else "#E2E8F0",
            edgecolor="#1E293B" if active else "#94A3B8",
            linewidth=1.0,
            zorder=7,
        )
        label = f"{source_id}  {source.commune}"
        if not active:
            label += "  (not selected)"
        ax.annotate(
            label,
            xy=(x, y),
            xytext=LABEL_OFFSETS[source_id],
            textcoords="offset points",
            fontsize=8.3,
            fontweight="bold" if active else "normal",
            color="#1E293B" if active else "#64748B",
            arrowprops={"arrowstyle": "-", "color": "#94A3B8", "linewidth": 0.8},
            bbox={"boxstyle": "round,pad=0.24", "facecolor": "white", "edgecolor": "#CBD5E1", "alpha": 0.96},
            zorder=8,
        )

    sx, sy = node_xy["SINK"]
    ax.scatter([sx], [sy], marker="*", s=260, facecolor="#14B8A6", edgecolor="#0F172A", linewidth=1.0, zorder=9)
    ax.annotate(
        "Port of Dunkerque receiving site",
        xy=(sx, sy),
        xytext=(0, 32),
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontsize=8.4,
        fontweight="bold",
        color="#134E4A",
        arrowprops={"arrowstyle": "-", "color": "#0F766E", "linewidth": 0.9},
        bbox={"boxstyle": "round,pad=0.28", "facecolor": "#ECFDF5", "edgecolor": "#5EEAD4"},
        zorder=10,
    )

    all_x = [coord[0] for coord in node_xy.values()]
    all_y = [coord[1] for coord in node_xy.values()]
    ax.set_xlim(min(all_x) - 9, max(all_x) + 10)
    ax.set_ylim(min(all_y) - 9, max(all_y) + 11)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("Lambert-93 X coordinate (km)")
    ax.set_ylabel("Lambert-93 Y coordinate (km)")
    fig.suptitle(
        "Northern France industrial CO₂ model",
        x=0.06,
        y=0.96,
        ha="left",
        fontsize=22,
        fontweight="bold",
        color="#0F172A",
    )
    fig.text(
        0.06,
        0.905,
        f"Scenario: {result.scenario} · Capture → Purification → Transport to Dunkerque",
        ha="left",
        fontsize=11.5,
        color="#475569",
    )

    diameters = [segment["nominal_diameter_mm"] for segment in result.pipeline_segments]
    diameter_range = f"DN {min(diameters):.0f}–{max(diameters):.0f}" if diameters else "—"
    panel.text(0.0, 0.97, "Scenario summary", fontsize=15, fontweight="bold", color="#0F172A", transform=panel.transAxes)
    metrics = [
        ("Calculation", summary.get("calculation_mode", "screening").replace("_", " ").title()),
        ("Active sources", f"{summary['active_sources']} / {len(inputs.sources)}"),
        ("Captured", f"{summary['total_captured_before_purification_tpy'] / 1e6:.2f} Mt/y"),
        ("Purified", f"{summary['total_purified_co2_tpy'] / 1e6:.2f} Mt/y"),
        ("Received at sink", f"{summary['sink_received_after_pipeline_leakage_tpy'] / 1e6:.2f} Mt/y"),
        ("Route length", f"{summary['pipeline_route_length_km']:.1f} km"),
        ("Pipeline sizes", diameter_range),
        ("Minimum arrival pressure", f"{summary['minimum_arrival_pressure_bar']:.1f} bar"),
        ("Three-stage CAPEX", _money(summary["total_chain_capex_eur"])),
        ("Three-stage cost", f"€{summary['full_chain_cost_eur_per_t_received']:.0f}/t received"),
        ("Net avoided", f"{summary['chain_net_avoided_co2_tpy'] / 1e6:.2f} Mt/y"),
    ]
    y = 0.90
    for label, value in metrics:
        panel.text(0.0, y, label, fontsize=9.2, color="#64748B", transform=panel.transAxes)
        panel.text(1.0, y, value, ha="right", fontsize=9.4, fontweight="bold", color="#0F172A", transform=panel.transAxes)
        panel.plot([0, 1], [y - 0.025, y - 0.025], transform=panel.transAxes, color="#E2E8F0", linewidth=0.8)
        y -= 0.061

    panel.text(0.0, y - 0.005, "Source sectors", fontsize=11.5, fontweight="bold", color="#0F172A", transform=panel.transAxes)
    handles = [
        Line2D(
            [0],
            [0],
            marker=marker,
            linestyle="None",
            markerfacecolor=color,
            markeredgecolor="#1E293B",
            markersize=7,
            label=sector.replace("_", " ").title(),
        )
        for sector, (color, marker) in SECTOR_STYLE.items()
        if any(source.sector == sector for source in inputs.sources)
    ]
    panel.legend(handles=handles, loc="upper left", bbox_to_anchor=(-0.03, y - 0.02), frameon=False, fontsize=8.3, ncol=2, columnspacing=0.8, handletextpad=0.5)
    panel.text(
        0.0,
        -0.005,
        "Engineering / pre-FEED result. Source assays,\nsurveyed corridors, phase envelopes and transient\noperation remain project inputs.",
        fontsize=7.8,
        color="#64748B",
        transform=panel.transAxes,
        va="bottom",
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=220, bbox_inches="tight")
    fig.savefig(path.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)


def write_markdown_report(inputs: ModelInputs, result: ScenarioResult, path: Path) -> None:
    s = result.summary
    lines = [
        f"# Three-stage scenario report: `{result.scenario}`",
        "",
        s["description"],
        "",
        f"Calculation mode: **{s.get('calculation_mode', 'screening').replace('_', ' ')}**. Capture → purification connected: **{s.get('capture_to_purification_connected', False)}**. Purification → transport connected: **{s.get('purification_to_transport_connected', False)}**.",
        "",
        "| Headline metric | Result |",
        "|---|---:|",
        f"| CO₂ captured | {s['total_captured_before_purification_tpy'] / 1e6:.3f} Mt/y |",
        f"| CO₂ purified to pipeline specification | {s['total_purified_co2_tpy'] / 1e6:.3f} Mt/y |",
        f"| CO₂ received at Port of Dunkerque | {s['sink_received_after_pipeline_leakage_tpy'] / 1e6:.3f} Mt/y |",
        f"| Net CO₂ avoided within model boundary | {s['chain_net_avoided_co2_tpy'] / 1e6:.3f} Mt/y |",
        f"| Three-stage CAPEX | {_money(s['total_chain_capex_eur'])} |",
        f"| Base levelized cost | €{s['full_chain_cost_eur_per_t_received']:.1f}/t received |",
        f"| Screening cost range | €{s['full_chain_cost_low_eur_per_t_received']:.1f}–{s['full_chain_cost_high_eur_per_t_received']:.1f}/t received |",
        "",
        "## 1. Capture",
        "",
        f"Capture CAPEX: **{_money(s['capture_capex_eur'])}**. Annualized capture cost: **€{s['capture_cost_eur_per_t_received']:.1f}/t received**.",
        "",
        "| ID | Source | Emissions basis (kt/y) | Captured (kt/y) | Technology | Method | Capture rate | Availability |",
        "|---|---|---:|---:|---|---|---:|---:|",
    ]
    for row in result.source_results:
        lines.append(
            f"| {row['source_id']} | {row['source_name']} | {row['emissions_basis_tpy'] / 1000:,.1f} | "
            f"{row['captured_before_purification_tpy'] / 1000:,.1f} | {row['capture_technology']} | {row.get('capture_calculation_method', 'screening')} | "
            f"{row['capture_rate']:.1%} | {row['availability']:.1%} |"
        )

    lines.extend(
        [
            "",
            "## 2. Purification",
            "",
            f"Purification CAPEX: **{_money(s['purification_capex_eur'])}**. Annualized purification cost: **€{s['purification_cost_eur_per_t_received']:.1f}/t received**.",
            "",
            "| ID | Captured feed (kt/y) | Product (kt/y) | Recovery | Target / achieved CO₂ | Target / achieved H₂O | Method | Target benchmark | Achieved benchmark |",
            "|---|---:|---:|---:|---:|---:|---|---|---|",
        ]
    )
    for row in result.source_results:
        target_status = "Pass" if row["product_spec_screening_pass"] else "Fail"
        achieved_status = "Pass" if row["achieved_product_spec_pass"] else "Fail"
        lines.append(
            f"| {row['source_id']} | {row['captured_before_purification_tpy'] / 1000:,.1f} | "
            f"{row['allocated_product_co2_tpy'] / 1000:,.1f} | {row['purification_recovery']:.1%} | "
            f"{row['target_product_co2_mol_pct']:.2f} / {row['product_co2_mol_pct']:.2f} mol-% | "
            f"{row['target_product_h2o_ppmv']:.0f} / {row['product_h2o_ppmv']:.0f} ppmv | "
            f"{row.get('purification_calculation_method', 'screening')} | {target_status} | {achieved_status} |"
        )

    lines.extend(
        [
            "",
            "## 3. Transport to the sink site",
            "",
            f"Pipeline CAPEX: **{_money(s['pipeline_capex_eur'])}**. Annualized transport cost: **€{s['pipeline_cost_eur_per_t_received']:.1f}/t received**.",
            "",
            f"The optimized screening network contains {len(result.pipeline_segments)} segments, totals {s['pipeline_route_length_km']:.1f} km, starts at {inputs.config['transport']['inlet_pressure_bar']:.0f} bar and reaches Dunkerque at no less than {s['minimum_arrival_pressure_bar']:.1f} bar.",
            "",
            f"Transport properties are calculated with the **{s['transport_equation_of_state']} equation of state** at {s['transport_eos_temperature_c']:.1f} °C. PR density and compressibility are evaluated iteratively at the representative mean pressure of each segment.",
            "",
            f"Selected material screen: **{s['pipeline_material_label']}**; calculated pipe steel **{s['pipeline_steel_mass_t'] / 1000:,.1f} kt**; wall range **{s['pipeline_wall_thickness_min_mm']:.1f}–{s['pipeline_wall_thickness_max_mm']:.1f} mm**.",
            "",
            "| From | To | Route (km) | Flow (Mt/y) | Diameter | Wall (mm) | Density (kg/m³) | Z | Velocity (m/s) | ΔP (bar) |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in result.pipeline_segments:
        destination = "Sink" if row["to_node"] == "SINK" else row["to_node"]
        lines.append(
            f"| {row['from_node']} | {destination} | {row['route_length_km']:.1f} | "
            f"{row['flow_tpy'] / 1e6:.3f} | DN {row['nominal_diameter_mm']:.0f} | "
            f"{row['wall_thickness_mm']:.1f} | {row['eos_density_kg_per_m3']:.1f} | {row['eos_compressibility_factor']:.4f} | "
            f"{row['velocity_m_per_s']:.2f} | {row['pressure_drop_bar']:.2f} |"
        )

    env_benchmarks = s["environmental_transport_benchmarks"]
    lines.extend(
        [
            "",
            "## 4. Environmental study",
            "",
            f"Assessment year: **{s['environmental_assessment_year']}**. The layer combines process utility/consumable/equipment emissions, direct pipeline leakage, and lifecycle transport factors based on annual tonne-kilometres.",
            "",
            "| Environmental metric | Result |",
            "|---|---:|",
            f"| Total electricity demand | {s['environmental_total_electricity_mwh_per_year'] / 1000:,.1f} GWh/y |",
            f"| Capture steam demand | {s['environmental_capture_steam_gj_per_year'] / 1000:,.1f} TJ/y |",
            f"| Capture cooling demand | {s['environmental_capture_cooling_gj_per_year'] / 1000:,.1f} TJ/y |",
            f"| Purification thermal demand | {s['environmental_purification_thermal_mwh_per_year'] / 1000:,.1f} GWhth/y |",
            f"| Purification cooling demand | {s['environmental_purification_cooling_mwh_per_year'] / 1000:,.1f} GWhth/y |",
            f"| Process consumable/equipment climate burden | {s['environmental_process_nonenergy_emissions_tco2e_per_year']:,.1f} t CO₂-eq/y |",
            f"| Direct pipeline leakage | {s['environmental_pipeline_leakage_tco2e_per_year']:,.1f} t CO₂/y |",
            f"| Pipeline use-phase climate burden | {s['environmental_pipeline_use_emissions_tco2e_per_year']:,.1f} t CO₂-eq/y |",
            f"| Pipeline construction climate burden | {s['environmental_pipeline_construction_emissions_tco2e_per_year']:,.1f} t CO₂-eq/y |",
            f"| Selected pipe-material embodied carbon | {s['environmental_pipeline_material_embodied_carbon_tco2e']:,.1f} t CO₂-eq total inventory |",
            f"| Annualized material delta versus X65 | {s['environmental_pipeline_material_delta_annualized_tco2e_per_year']:,.1f} t CO₂-eq/y |",
            f"| Total modeled climate burden | {s['environmental_total_climate_burden_tco2e_per_year']:,.1f} t CO₂-eq/y |",
            f"| Lifecycle net CO₂ avoided | {s['environmental_lifecycle_net_avoided_co2_tpy'] / 1e6:.3f} Mt/y |",
            f"| Climate burden intensity | {s['environmental_climate_burden_kgco2e_per_t_received']:.1f} kg CO₂-eq/t received |",
            f"| Net avoidance efficiency | {s['environmental_net_avoidance_efficiency_fraction']:.1%} |",
            "",
            "### Transport climate benchmark",
            "",
            "| Alternative mode | Mode intensity (g CO₂-eq/tkm) | Pipeline incl. construction | Pipeline reduction |",
            "|---|---:|---:|---:|",
        ]
    )
    for row in env_benchmarks:
        lines.append(
            f"| {row['mode']} | {row['mode_gco2e_per_tkm']:.1f} | "
            f"{row['pipeline_gco2e_per_tkm_including_construction']:.1f} | "
            f"{row['pipeline_intensity_reduction_fraction']:.1%} |"
        )
    lines.extend(
        [
            "",
            "**Environmental scope note.** This is a screening climate/energy study, not an ISO-compliant project LCA. A routed corridor is required before quantifying biodiversity, land occupation, water, crossings, construction disturbance, noise or local air-quality impacts.",
            "",
            "---",
            "",
            "**Model boundary.** The calculation ends when pipeline-quality CO₂ reaches the Port of Dunkerque coordinates supplied for this study. Liquefaction, buffer storage, ship loading, shipping, geological injection and storage are excluded.",
            "",
            "**Precision statement.** Results are deterministic screening estimates in 2026 euros. The displayed range applies maturity-based uncertainty to capture/purification costs and ±35% to routed pipeline cost; it is not a statistical confidence interval. Six product components are screened, but a complete vendor assay and receiving specification are required before FEED.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_environmental_outputs(result: ScenarioResult, output_dir: Path) -> None:
    s = result.summary
    scalar_fields = [
        "scenario",
        "environmental_assessment_year",
        "environmental_scope",
        "environmental_tonne_km_per_year",
        "environmental_capture_electricity_mwh_per_year",
        "environmental_purification_electricity_mwh_per_year",
        "environmental_total_electricity_mwh_per_year",
        "environmental_capture_steam_gj_per_year",
        "environmental_capture_cooling_gj_per_year",
        "environmental_purification_thermal_mwh_per_year",
        "environmental_purification_cooling_mwh_per_year",
        "environmental_capture_energy_emissions_tco2e_per_year",
        "environmental_purification_energy_emissions_tco2e_per_year",
        "environmental_capture_nonenergy_emissions_tco2e_per_year",
        "environmental_purification_nonenergy_emissions_tco2e_per_year",
        "environmental_process_nonenergy_emissions_tco2e_per_year",
        "environmental_pipeline_leakage_tco2e_per_year",
        "environmental_pipeline_use_factor_gco2e_per_tkm",
        "environmental_pipeline_construction_factor_gco2e_per_tkm",
        "environmental_pipeline_use_emissions_tco2e_per_year",
        "environmental_pipeline_construction_emissions_tco2e_per_year",
        "environmental_pipeline_material_embodied_carbon_tco2e",
        "environmental_pipeline_material_delta_vs_baseline_tco2e",
        "environmental_pipeline_material_delta_annualized_tco2e_per_year",
        "environmental_total_climate_burden_tco2e_per_year",
        "environmental_lifecycle_net_avoided_co2_tpy",
        "environmental_climate_burden_kgco2e_per_t_received",
        "environmental_net_avoidance_efficiency_fraction",
    ]
    write_csv(output_dir / "environmental_summary.csv", [{field: s[field] for field in scalar_fields}])
    write_csv(output_dir / "environmental_transport_benchmarks.csv", s["environmental_transport_benchmarks"])

    lines = [
        f"# Environmental study: `{result.scenario}`",
        "",
        f"Assessment year: **{s['environmental_assessment_year']}**",
        "",
        f"- Lifecycle net CO₂ avoided: **{s['environmental_lifecycle_net_avoided_co2_tpy'] / 1e6:.3f} Mt/y**",
        f"- Total modeled climate burden: **{s['environmental_total_climate_burden_tco2e_per_year']:,.0f} t CO₂-eq/y**",
        f"- Climate burden intensity: **{s['environmental_climate_burden_kgco2e_per_t_received']:.1f} kg CO₂-eq/t received**",
        f"- Net avoidance efficiency: **{s['environmental_net_avoidance_efficiency_fraction']:.1%}**",
        f"- Annual transport work: **{s['environmental_tonne_km_per_year'] / 1e9:.3f} billion tkm/y**",
        "",
        "## Boundary and limitations",
        "",
    ]
    lines.extend(f"- {item}" for item in s["environmental_limitations"])
    (output_dir / "environmental_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_scenario_outputs(inputs: ModelInputs, result: ScenarioResult, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "source_results.csv", result.source_results)
    write_csv(output_dir / "pipeline_segments.csv", result.pipeline_segments)
    write_json(output_dir / "summary.json", result.summary)
    write_markdown_report(inputs, result, output_dir / "report.md")
    write_environmental_outputs(result, output_dir)
    plot_network(inputs, result, output_dir / "network.png")


def write_scenario_comparison(results: list[ScenarioResult], output_dir: Path) -> None:
    fields = [
        "scenario",
        "calculation_mode",
        "flow_basis",
        "active_sources",
        "sink_capacity_tpy",
        "total_captured_before_purification_tpy",
        "total_purified_co2_tpy",
        "total_curtailed_product_co2_tpy",
        "sink_received_after_pipeline_leakage_tpy",
        "sink_utilization_fraction",
        "chain_net_avoided_co2_tpy",
        "environmental_lifecycle_net_avoided_co2_tpy",
        "environmental_total_climate_burden_tco2e_per_year",
        "environmental_climate_burden_kgco2e_per_t_received",
        "environmental_net_avoidance_efficiency_fraction",
        "pipeline_route_length_km",
        "pipeline_material_id",
        "pipeline_steel_mass_t",
        "pipeline_material_embodied_carbon_tco2e",
        "capture_capex_eur",
        "purification_capex_eur",
        "pipeline_capex_eur",
        "total_chain_capex_eur",
        "capture_cost_eur_per_t_received",
        "purification_cost_eur_per_t_received",
        "pipeline_cost_eur_per_t_received",
        "full_chain_cost_eur_per_t_received",
        "full_chain_cost_eur_per_t_lifecycle_net_avoided",
        "full_chain_cost_low_eur_per_t_received",
        "full_chain_cost_high_eur_per_t_received",
    ]
    rows = [{field: result.summary[field] for field in fields} for result in results]
    write_csv(output_dir / "scenario_comparison.csv", rows)

    lines = [
        "# Scenario comparison",
        "",
        "| Scenario | Active | Captured (Mt/y) | At sink (Mt/y) | Operational net avoided (Mt/y) | Lifecycle net avoided (Mt/y) | Climate burden (kg/t) | CAPEX | Cost (€/t received) | Range |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for result in results:
        s = result.summary
        lines.append(
            f"| {result.scenario} | {s['active_sources']} | {s['total_captured_before_purification_tpy'] / 1e6:.3f} | "
            f"{s['sink_received_after_pipeline_leakage_tpy'] / 1e6:.3f} | "
            f"{s['chain_net_avoided_co2_tpy'] / 1e6:.3f} | "
            f"{s['environmental_lifecycle_net_avoided_co2_tpy'] / 1e6:.3f} | "
            f"{s['environmental_climate_burden_kgco2e_per_t_received']:.1f} | {_money(s['total_chain_capex_eur'])} | "
            f"{s['full_chain_cost_eur_per_t_received']:.1f} | "
            f"{s['full_chain_cost_low_eur_per_t_received']:.1f}–{s['full_chain_cost_high_eur_per_t_received']:.1f} |"
        )
    (output_dir / "scenario_comparison.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
