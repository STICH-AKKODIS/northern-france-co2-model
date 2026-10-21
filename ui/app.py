from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from north_co2_model.model import (
    ModelInputs,
    ScenarioResult,
    available_capture_technologies,
    available_purification_technologies,
    build_material_comparison,
    load_model_inputs,
    run_custom_scenario,
)


st.set_page_config(
    page_title="Northern France CO₂ Model",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)


SCENARIOS: dict[str, dict[str, Any]] = {
    "Announced projects · 2030": {
        "id": "announced_2030",
        "tag": "Recommended base case",
        "description": "CalCC at Réty and K6 at Lumbres, limited to the announced 1.5 Mt/y Dunkerque receiving capacity.",
    },
    "Verified 2024 cluster potential": {
        "id": "reported_2024_cluster",
        "tag": "Official emissions basis",
        "description": "All five sites, using the verified 2024 IREP inventory and source-specific capture assumptions.",
    },
    "Original inventory · 4 Mt/y limit": {
        "id": "user_inventory_4mt",
        "tag": "User data comparison",
        "description": "All five sites using the original supplied emissions, constrained to 4 Mt/y at Dunkerque.",
    },
    "Original inventory · unconstrained": {
        "id": "user_inventory_unconstrained",
        "tag": "Diagnostic upper bound",
        "description": "The original supplied emissions without a binding receiving-capacity constraint.",
    },
    "Build a custom case": {
        "id": "custom_case",
        "tag": "Interactive case",
        "description": "Choose the sources, emissions basis, receiving capacity and economic assumptions.",
    },
}

FLOW_BASES = {
    "Verified IREP 2024 emissions": "irep_2024_total",
    "Original supplied emissions": "user_case",
    "Announced project product flows": "announced_product",
}

SECTOR_LABELS = {
    "lime": "Lime",
    "gypsum_plaster": "Gypsum / plaster",
    "cement": "Cement",
    "aluminium": "Aluminium",
    "iron_steel": "Iron & steel",
}

COLORS = {
    "ink": "#102235",
    "muted": "#64748B",
    "capture": "#176B87",
    "purification": "#17A398",
    "transport": "#E59A31",
    "inactive": "#CBD5E1",
}


def _load_css() -> None:
    st.markdown(f"<style>{(ROOT / 'ui' / 'theme.css').read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


@st.cache_resource
def get_inputs() -> ModelInputs:
    return load_model_inputs(ROOT)


@st.cache_data(show_spinner=False)
def calculate_case(
    scenario_name: str,
    active_ids: tuple[str, ...],
    flow_basis: str,
    sink_capacity_tpy: float,
    enforce_capacity: bool,
    electricity_price: float,
    steam_price: float,
    discount_rate: float,
    project_life: int,
    pipeline_material: str,
    source_overrides_json: str,
) -> ScenarioResult:
    return run_custom_scenario(
        get_inputs(),
        active_source_ids=active_ids,
        flow_basis=flow_basis,
        sink_capacity_tpy=sink_capacity_tpy,
        enforce_sink_capacity=enforce_capacity,
        finance_overrides={
            "electricity_price_eur_per_mwh": electricity_price,
            "steam_price_eur_per_gj": steam_price,
            "discount_rate": discount_rate,
            "project_life_years": project_life,
        },
        transport_overrides={"pipeline_material": pipeline_material},
        source_overrides=json.loads(source_overrides_json),
        scenario_name=scenario_name,
    )


def fmt_mt(value: float, digits: int = 2) -> str:
    return f"{value / 1e6:.{digits}f} Mt/y"


def fmt_money(value: float) -> str:
    if value >= 1e9:
        return f"€{value / 1e9:.2f} bn"
    if value >= 1e6:
        return f"€{value / 1e6:.1f} m"
    return f"€{value:,.0f}"


def stage_card(number: int, title: str, value: str, detail: str) -> None:
    st.markdown(
        f"""
        <div class="stage-card">
          <span class="stage-number">{number}</span>
          <div class="stage-title">{title}</div>
          <div class="stage-value">{value}</div>
          <div class="stage-detail">{detail}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def confidence_label(quality: str) -> tuple[str, str]:
    if quality == "project-specific":
        return "Higher confidence", "confidence-high"
    if quality in {"project-plus-screening", "pilot-plus-screening"}:
        return "Medium confidence", "confidence-medium"
    return "Screening assumption", "confidence-low"


def source_display(source: Any) -> str:
    return f"{source.source_id} · {source.commune} — {SECTOR_LABELS[source.sector]}"


def standard_parameters(inputs: ModelInputs, scenario_id: str) -> dict[str, Any]:
    case = inputs.config["scenarios"][scenario_id]
    return {
        "active_ids": tuple(case["active_source_ids"]),
        "flow_basis": case["flow_basis"],
        "sink_capacity_tpy": float(case["sink_capacity_tpy"]),
        "enforce_capacity": bool(case["enforce_sink_capacity"]),
    }


def source_configuration_controls(
    inputs: ModelInputs,
    active_ids: tuple[str, ...],
) -> dict[str, dict[str, Any]]:
    """Render per-source technology and product-target controls."""
    st.markdown("#### Source technology & targets")
    st.caption(
        "Each source is independent. Options are filtered by sector and every target "
        "is bounded by the selected technology's configured screening range."
    )
    overrides: dict[str, dict[str, Any]] = {}
    active_set = set(active_ids)
    for source in inputs.sources:
        if source.source_id not in active_set:
            continue
        capture_options = available_capture_technologies(inputs, source)
        purification_options = available_purification_technologies(inputs, source)
        with st.expander(
            f"{source.source_id} · {source.commune} · {SECTOR_LABELS[source.sector]}",
            expanded=False,
        ):
            capture_labels = {
                str(values["label"]): technology_id
                for technology_id, values in capture_options.items()
            }
            default_capture_label = str(
                capture_options[source.capture_technology_id]["label"]
            )
            capture_label = st.selectbox(
                "Capture technology",
                list(capture_labels),
                index=list(capture_labels).index(default_capture_label),
                key=f"{source.source_id}_capture_technology",
            )
            capture_id = capture_labels[capture_label]
            capture = capture_options[capture_id]
            capture_rate_key = f"{source.source_id}_capture_rate_pct"
            capture_last_key = f"{source.source_id}_capture_last_selection"
            if st.session_state.get(capture_last_key) != capture_id:
                default_capture_rate = (
                    source.capture_rate
                    if capture_id == source.capture_technology_id
                    else float(capture["reference_capture_rate"])
                )
                st.session_state[capture_rate_key] = default_capture_rate * 100.0
                st.session_state[capture_last_key] = capture_id
            capture_rate_pct = st.slider(
                "CO₂ capture efficiency",
                min_value=float(capture["minimum_capture_rate"]) * 100.0,
                max_value=float(capture["maximum_capture_rate"]) * 100.0,
                step=0.5,
                format="%.1f%%",
                key=capture_rate_key,
                help="Fraction of CO₂ in the capturable source stream separated by the selected capture process.",
            )
            st.caption(
                f"TRL {int(capture['technology_readiness_level'])} · "
                f"{capture['safety_category']}"
            )

            purification_labels = {
                str(values["label"]): technology_id
                for technology_id, values in purification_options.items()
            }
            default_purification_label = str(
                purification_options[source.purification_technology_id]["label"]
            )
            purification_label = st.selectbox(
                "Purification technology",
                list(purification_labels),
                index=list(purification_labels).index(default_purification_label),
                key=f"{source.source_id}_purification_technology",
            )
            purification_id = purification_labels[purification_label]
            purification = purification_options[purification_id]
            purification_last_key = f"{source.source_id}_purification_last_selection"
            target_keys = {
                "recovery": f"{source.source_id}_purification_recovery_pct",
                "co2": f"{source.source_id}_product_co2_mol_pct",
                "h2o": f"{source.source_id}_product_h2o_ppmv",
                "o2": f"{source.source_id}_product_o2_ppmv",
                "nox": f"{source.source_id}_product_nox_ppmv",
                "sox": f"{source.source_id}_product_sox_ppmv",
                "co": f"{source.source_id}_product_co_ppmv",
            }
            if st.session_state.get(purification_last_key) != purification_id:
                same_as_source = (
                    purification_id == source.purification_technology_id
                )
                st.session_state[target_keys["recovery"]] = 100.0 * (
                    source.purification_recovery
                    if same_as_source
                    else float(purification["reference_recovery"])
                )
                for short_name, source_field, reference_field in (
                    ("co2", "product_co2_mol_pct", "reference_co2_mol_pct"),
                    ("h2o", "product_h2o_ppmv", "reference_h2o_ppmv"),
                    ("o2", "product_o2_ppmv", "reference_o2_ppmv"),
                    ("nox", "product_nox_ppmv", "reference_nox_ppmv"),
                    ("sox", "product_sox_ppmv", "reference_sox_ppmv"),
                    ("co", "product_co_ppmv", "reference_co_ppmv"),
                ):
                    st.session_state[target_keys[short_name]] = (
                        float(getattr(source, source_field))
                        if same_as_source
                        else float(purification[reference_field])
                    )
                st.session_state[purification_last_key] = purification_id

            recovery_pct = st.slider(
                "CO₂ recovery through purification",
                min_value=float(purification["minimum_recovery"]) * 100.0,
                max_value=float(purification["maximum_recovery"]) * 100.0,
                step=0.1,
                format="%.1f%%",
                key=target_keys["recovery"],
            )
            product_co2 = st.number_input(
                "Product CO₂ purity (mol-%)",
                min_value=float(purification["minimum_co2_mol_pct"]),
                max_value=float(purification["maximum_co2_mol_pct"]),
                step=0.05,
                format="%.3f",
                key=target_keys["co2"],
            )
            product_h2o = st.number_input(
                "Product H₂O (ppmv)",
                min_value=float(purification["minimum_h2o_ppmv"]),
                max_value=float(purification["maximum_h2o_ppmv"]),
                step=1.0,
                format="%.1f",
                key=target_keys["h2o"],
            )
            advanced = st.checkbox(
                "Adjust O₂, NOₓ, SOₓ and CO targets",
                key=f"{source.source_id}_advanced_impurities",
            )
            impurity_values: dict[str, float] = {}
            for short_name, label in (
                ("o2", "O₂"),
                ("nox", "NOₓ"),
                ("sox", "SOₓ"),
                ("co", "CO"),
            ):
                if advanced:
                    impurity_values[short_name] = st.number_input(
                        f"Product {label} (ppmv)",
                        min_value=float(purification[f"minimum_{short_name}_ppmv"]),
                        max_value=float(purification[f"maximum_{short_name}_ppmv"]),
                        step=1.0 if short_name in {"o2", "co"} else 0.1,
                        format="%.1f",
                        key=target_keys[short_name],
                    )
                else:
                    impurity_values[short_name] = float(
                        st.session_state[target_keys[short_name]]
                    )
            st.caption(
                f"TRL {int(purification['technology_readiness_level'])} · "
                f"{purification['safety_category']}"
            )
            overrides[source.source_id] = {
                "capture_technology_id": capture_id,
                "capture_rate": capture_rate_pct / 100.0,
                "purification_technology_id": purification_id,
                "purification_recovery": recovery_pct / 100.0,
                "product_co2_mol_pct": float(product_co2),
                "product_h2o_ppmv": float(product_h2o),
                "product_o2_ppmv": impurity_values["o2"],
                "product_nox_ppmv": impurity_values["nox"],
                "product_sox_ppmv": impurity_values["sox"],
                "product_co_ppmv": impurity_values["co"],
            }
    return overrides


def pipeline_figure(inputs: ModelInputs, result: ScenarioResult) -> go.Figure:
    source_lookup = {source.source_id: source for source in inputs.sources}
    result_lookup = {row["source_id"]: row for row in result.source_results}
    sink = inputs.config["sink"]
    coordinates = {
        source.source_id: (source.x_l93_m / 1000.0, source.y_l93_m / 1000.0)
        for source in inputs.sources
    }
    coordinates["SINK"] = (sink["x_l93_m"] / 1000.0, sink["y_l93_m"] / 1000.0)
    fig = go.Figure()

    for segment in result.pipeline_segments:
        x1, y1 = coordinates[segment["from_node"]]
        x2, y2 = coordinates[segment["to_node"]]
        destination = "Port of Dunkerque" if segment["to_node"] == "SINK" else segment["to_name"]
        hover = (
            f"<b>{segment['from_name']} → {destination}</b><br>"
            f"Route: {segment['route_length_km']:.1f} km<br>"
            f"Flow: {segment['flow_tpy'] / 1e6:.3f} Mt/y<br>"
            f"Diameter: DN {segment['nominal_diameter_mm']:.0f}<br>"
            f"Material: {segment['pipeline_material_label']}<br>"
            f"Screened wall: {segment['wall_thickness_mm']:.1f} mm<br>"
            f"Velocity: {segment['velocity_m_per_s']:.2f} m/s<br>"
            f"Pressure drop: {segment['pressure_drop_bar']:.2f} bar<extra></extra>"
        )
        fig.add_trace(
            go.Scatter(
                x=[x1, x2],
                y=[y1, y2],
                mode="lines",
                line={"color": COLORS["transport"], "width": 2.2 + segment["nominal_diameter_mm"] / 90.0},
                hovertemplate=hover,
                showlegend=False,
            )
        )

    for active in (False, True):
        sources = [
            source
            for source in inputs.sources
            if (result_lookup[source.source_id]["allocated_product_co2_tpy"] > 0) is active
        ]
        if not sources:
            continue
        fig.add_trace(
            go.Scatter(
                x=[source.x_l93_m / 1000.0 for source in sources],
                y=[source.y_l93_m / 1000.0 for source in sources],
                mode="markers+text" if active else "markers",
                text=[source.source_id for source in sources] if active else None,
                textposition="top center",
                marker={
                    "size": 13 if active else 9,
                    "color": COLORS["capture"] if active else COLORS["inactive"],
                    "line": {"color": COLORS["ink"], "width": 1},
                },
                name="Selected source" if active else "Not selected",
                customdata=[
                    [source.source_name, source.commune, result_lookup[source.source_id]["allocated_product_co2_tpy"] / 1e6]
                    for source in sources
                ],
                hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}<br>Pipeline product: %{customdata[2]:.3f} Mt/y<extra></extra>",
            )
        )

    fig.add_trace(
        go.Scatter(
            x=[sink["x_l93_m"] / 1000.0],
            y=[sink["y_l93_m"] / 1000.0],
            mode="markers+text",
            text=["Dunkerque sink"],
            textposition="top center",
            marker={"size": 21, "symbol": "star", "color": "#16B3A6", "line": {"color": COLORS["ink"], "width": 1.2}},
            name="Receiving site",
            hovertemplate="<b>Port of Dunkerque receiving site</b><br>Model boundary endpoint<extra></extra>",
        )
    )
    fig.update_layout(
        height=590,
        margin={"l": 12, "r": 12, "t": 22, "b": 12},
        paper_bgcolor="white",
        plot_bgcolor="#F8FAFC",
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.01, "xanchor": "left", "x": 0},
        hoverlabel={"bgcolor": "white", "font_color": COLORS["ink"]},
        xaxis={"title": "Lambert-93 X (km)", "gridcolor": "#E2E8F0", "zeroline": False},
        yaxis={
            "title": "Lambert-93 Y (km)",
            "gridcolor": "#E2E8F0",
            "zeroline": False,
            "scaleanchor": "x",
            "scaleratio": 1,
        },
    )
    return fig


def cost_figure(summary: dict[str, Any]) -> go.Figure:
    labels = ["Capture", "Purification", "Transport"]
    values = [
        summary["capture_cost_eur_per_t_received"],
        summary["purification_cost_eur_per_t_received"],
        summary["pipeline_cost_eur_per_t_received"],
    ]
    fig = go.Figure(
        go.Bar(
            x=labels,
            y=values,
            marker_color=[COLORS["capture"], COLORS["purification"], COLORS["transport"]],
            text=[f"€{value:.1f}/t" for value in values],
            textposition="outside",
            hovertemplate="%{x}: €%{y:.2f}/t received<extra></extra>",
        )
    )
    fig.update_layout(
        height=335,
        margin={"l": 15, "r": 15, "t": 30, "b": 10},
        paper_bgcolor="white",
        plot_bgcolor="white",
        yaxis={"title": "€/t received at sink", "gridcolor": "#E2E8F0", "rangemode": "tozero"},
        xaxis={"title": None},
        showlegend=False,
    )
    return fig


_load_css()
inputs = get_inputs()
finance_defaults = inputs.config["finance"]

with st.sidebar:
    st.markdown(
        """
        <div class="brand-lockup">
          <div class="brand-kicker">North sector</div>
          <div class="brand-name">CO₂ Decision Model</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    selected_label = st.selectbox(
        "Choose a scenario",
        list(SCENARIOS),
        help="Start with the announced-project case for the most defensible presentation basis.",
    )
    meta = SCENARIOS[selected_label]
    st.caption(meta["description"])

    if meta["id"] == "custom_case":
        label_to_id = {source_display(source): source.source_id for source in inputs.sources}
        selected_sources = st.multiselect(
            "Sources to include",
            list(label_to_id),
            default=list(label_to_id),
        )
        active_ids = tuple(label_to_id[label] for label in selected_sources)
        basis_label = st.selectbox("Emissions basis", list(FLOW_BASES))
        flow_basis = FLOW_BASES[basis_label]
        capacity_choice = st.radio(
            "Dunkerque receiving capacity",
            ["1.5 Mt/y", "4.0 Mt/y", "No binding limit"],
            index=1,
        )
        capacity_map = {"1.5 Mt/y": 1_500_000.0, "4.0 Mt/y": 4_000_000.0, "No binding limit": 12_000_000.0}
        sink_capacity_tpy = capacity_map[capacity_choice]
        enforce_capacity = capacity_choice != "No binding limit"
    else:
        params = standard_parameters(inputs, meta["id"])
        active_ids = params["active_ids"]
        flow_basis = params["flow_basis"]
        sink_capacity_tpy = params["sink_capacity_tpy"]
        enforce_capacity = params["enforce_capacity"]

    source_overrides = source_configuration_controls(inputs, active_ids)
    source_overrides_json = json.dumps(
        source_overrides, sort_keys=True, separators=(",", ":")
    )

    with st.expander("Economic sensitivity", expanded=False):
        electricity_price = st.number_input(
            "Electricity price (€/MWh)",
            min_value=0.0,
            max_value=300.0,
            value=float(finance_defaults["electricity_price_eur_per_mwh"]),
            step=5.0,
        )
        steam_price = st.number_input(
            "Steam price (€/GJ)",
            min_value=0.0,
            max_value=60.0,
            value=float(finance_defaults["steam_price_eur_per_gj"]),
            step=1.0,
        )
        discount_rate_pct = st.slider(
            "Discount rate",
            min_value=0.0,
            max_value=15.0,
            value=float(finance_defaults["discount_rate"] * 100),
            step=0.5,
            format="%.1f%%",
        )
        project_life = st.slider(
            "Project life (years)",
            min_value=10,
            max_value=40,
            value=int(finance_defaults["project_life_years"]),
            step=1,
        )

    with st.expander("Management and pipeline choices", expanded=True):
        materials = inputs.config["transport"]["materials"]
        material_labels = {
            str(values["label"]): material_id
            for material_id, values in materials.items()
        }
        default_material_id = str(inputs.config["transport"]["pipeline_material"])
        default_material_label = str(materials[default_material_id]["label"])
        selected_material_label = st.selectbox(
            "Pipeline material screen",
            list(material_labels),
            index=list(material_labels).index(default_material_label),
            help=(
                "Compares pressure wall, steel mass, the material-sensitive share of "
                "CAPEX, and embodied carbon. Final material selection requires FEED."
            ),
        )
        pipeline_material = material_labels[selected_material_label]
        carbon_value = st.slider(
            "CO₂ value / avoided-cost threshold (€/t)",
            min_value=0,
            max_value=300,
            value=100,
            step=5,
            help=(
                "Management comparator only: the value placed on one lifecycle tonne "
                "of CO₂ avoided. It is not booked revenue."
            ),
        )
        st.caption(str(materials[pipeline_material]["management_note"]))

    signature = (
        meta["id"],
        active_ids,
        flow_basis,
        sink_capacity_tpy,
        enforce_capacity,
        electricity_price,
        steam_price,
        discount_rate_pct,
        project_life,
        pipeline_material,
        carbon_value,
        source_overrides_json,
    )
    run_clicked = st.button(
        "▶  Run selected scenario",
        type="primary",
        width="stretch",
        disabled=not active_ids,
    )
    st.markdown(
        """
        <div class="scope-note">
          <b>Model boundary</b><br>
          Capture → Purification → PR-based pipeline transport to the Port of Dunkerque, plus an environmental screening study. No liquefaction, shipping, injection or storage.
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("Version 0.6 · source technology and product-quality configurator")

if run_clicked or "result" not in st.session_state:
    with st.spinner("Calculating the capture, purification and transport chain…"):
        calculated_result = calculate_case(
            meta["id"],
            active_ids,
            flow_basis,
            sink_capacity_tpy,
            enforce_capacity,
            electricity_price,
            steam_price,
            discount_rate_pct / 100.0,
            project_life,
            pipeline_material,
            source_overrides_json,
        )
        st.session_state.result = calculated_result
        st.session_state.baseline_result = (
            calculate_case(
                meta["id"],
                active_ids,
                flow_basis,
                sink_capacity_tpy,
                enforce_capacity,
                electricity_price,
                steam_price,
                discount_rate_pct / 100.0,
                project_life,
                pipeline_material,
                "{}",
            )
            if calculated_result.summary["customized_source_configurations"] > 0
            else calculated_result
        )
        st.session_state.signature = signature
        st.session_state.display_label = selected_label
        st.session_state.display_description = meta["description"]
        st.session_state.active_ids = active_ids
        st.session_state.carbon_value = carbon_value
        st.session_state.run_electricity_price = electricity_price
        st.session_state.run_steam_price = steam_price
        st.session_state.run_discount_rate = discount_rate_pct / 100.0
        st.session_state.run_project_life = project_life

result: ScenarioResult = st.session_state.result
baseline_result: ScenarioResult = st.session_state.get("baseline_result", result)
summary = result.summary
baseline_summary = baseline_result.summary
result_label = st.session_state.display_label
result_description = st.session_state.display_description
carbon_value = float(st.session_state.get("carbon_value", carbon_value))
run_electricity_price = float(
    st.session_state.get("run_electricity_price", electricity_price)
)
run_steam_price = float(st.session_state.get("run_steam_price", steam_price))
run_discount_rate = float(
    st.session_state.get("run_discount_rate", discount_rate_pct / 100.0)
)
run_project_life = int(st.session_state.get("run_project_life", project_life))
comparison_config = {
    **inputs.config,
    "finance": {
        **inputs.config["finance"],
        "discount_rate": run_discount_rate,
        "project_life_years": run_project_life,
    },
}
material_comparison = build_material_comparison(
    result, comparison_config, carbon_value
)
selected_material_decision = next(
    row
    for row in material_comparison
    if row["material_id"] == summary["pipeline_material_id"]
)

st.markdown(
    """
    <div class="hero">
      <div class="hero-kicker">Integrated industrial decarbonisation</div>
      <h1>Northern France CO₂ chain</h1>
      <p>A guided decision model for five industrial sources—from separation at the stack to specification-compliant CO₂ received at Dunkerque.</p>
      <div class="status-row">
        <span class="status-pill">3 physical stages + environmental study</span>
        <span class="status-pill">Mass & cost reconciled</span>
        <span class="status-pill">PR EOS pressure-checked network</span>
        <span class="status-pill">2026 € basis</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="scenario-strip">
      <div><strong>{result_label}</strong><br><span>{result_description}</span></div>
      <span>{summary['active_sources']} active source{'s' if summary['active_sources'] != 1 else ''} · {summary['sink_utilization_fraction']:.0%} of receiving capacity</span>
    </div>
    """,
    unsafe_allow_html=True,
)
if st.session_state.signature != signature:
    st.info("The controls have changed. Click **Run selected scenario** to update the displayed results.", icon="ℹ️")

stage_columns = st.columns(3, gap="medium")
with stage_columns[0]:
    stage_card(
        1,
        "Capture",
        fmt_mt(summary["total_captured_before_purification_tpy"]),
        f"{fmt_money(summary['capture_capex_eur'])} CAPEX · €{summary['capture_cost_eur_per_t_received']:.1f}/t received",
    )
with stage_columns[1]:
    weighted_recovery = (
        summary["total_purified_co2_tpy"] / summary["total_captured_before_purification_tpy"]
        if summary["total_captured_before_purification_tpy"]
        else 0.0
    )
    stage_card(
        2,
        "Purification",
        fmt_mt(summary["total_purified_co2_tpy"]),
        f"{weighted_recovery:.1%} recovery · {summary['product_spec_components_screened']}/{summary['product_spec_components_in_reference']} component screen · 110 bar delivery",
    )
with stage_columns[2]:
    stage_card(
        3,
        "Transport to sink",
        fmt_mt(summary["sink_received_after_pipeline_leakage_tpy"]),
        f"{summary['pipeline_route_length_km']:.1f} km · {summary['minimum_arrival_pressure_bar']:.1f} bar arrival · {summary['pipeline_material_label']}",
    )

st.write("")
lifecycle_cost_eur_per_t_avoided = (
    summary["total_chain_annual_cost_eur"]
    / summary["environmental_lifecycle_net_avoided_co2_tpy"]
    if summary["environmental_lifecycle_net_avoided_co2_tpy"] > 0
    else 0.0
)
kpis = st.columns(6, gap="small")
kpis[0].metric(
    "Lifecycle CO₂ avoided",
    fmt_mt(summary["environmental_lifecycle_net_avoided_co2_tpy"]),
    help="Pipeline product minus all modeled annual climate burdens.",
)
kpis[1].metric("Total CAPEX", fmt_money(summary["total_chain_capex_eur"]))
kpis[2].metric(
    "Cost / t received",
    f"€{summary['full_chain_cost_eur_per_t_received']:.1f}/t",
    help="Annualized capture, purification and transport cost per tonne received.",
)
kpis[3].metric(
    "Value headroom",
    f"€{carbon_value - lifecycle_cost_eur_per_t_avoided:.1f}/t",
    delta=f"threshold €{carbon_value:.0f}/t",
    help="Selected CO₂ value less modeled full-chain cost per lifecycle tonne avoided.",
)
kpis[4].metric(
    "Receiver utilization",
    f"{summary['sink_utilization_fraction']:.0%}",
    help="Pipeline product divided by the selected Dunkerque receiving capacity.",
)
pressure_margin = (
    summary["minimum_arrival_pressure_bar"]
    - inputs.config["transport"]["minimum_arrival_pressure_bar"]
)
kpis[5].metric(
    "Pressure margin",
    f"{pressure_margin:.1f} bar",
    help="Minimum modeled arrival pressure above the configured 85 bar constraint.",
)

active_rows = [row for row in result.source_results if row["potential_product_co2_tpy"] > 0]
conceptual_count = sum(row["project_status"] in {"conceptual", "pilot-completed"} for row in active_rows)
if conceptual_count:
    st.warning(
        f"{conceptual_count} selected source{'s use' if conceptual_count != 1 else ' uses'} conceptual or pilot-derived assumptions. "
        "Use the uncertainty range for group decisions; do not present the base value as a vendor quotation.",
        icon="⚠️",
    )

annual_value_headroom = (
    carbon_value * summary["environmental_lifecycle_net_avoided_co2_tpy"]
    - summary["total_chain_annual_cost_eur"]
)
economics_ratio = (
    lifecycle_cost_eur_per_t_avoided / carbon_value
    if carbon_value > 0
    else float("inf")
)
economics_payback = selected_material_decision["simple_payback_years"]
coverage = summary["product_spec_screening_coverage_fraction"]
decision_rows = [
    {
        "Decision gate": "Economics vs selected CO₂ value",
        "Status": (
            "● Green"
            if economics_ratio <= 1.0
            and economics_payback is not None
            and economics_payback <= run_project_life
            else ("● Amber" if economics_ratio <= 1.2 and economics_payback is not None else "● Red")
        ),
        "Result": (
            f"{fmt_money(annual_value_headroom)}/y; "
            + (f"{economics_payback:.1f} y simple payback" if economics_payback is not None else "no positive payback")
        ),
        "Management meaning": "Positive headroom is indicative, before tax, grants, financing structure and commercial terms.",
    },
    {
        "Decision gate": "Hydraulic operating margin",
        "Status": "● Green" if pressure_margin >= 5.0 else ("● Amber" if pressure_margin >= 2.0 else "● Red"),
        "Result": f"{pressure_margin:.1f} bar above constraint",
        "Management meaning": "Steady-state screening only; transients and booster philosophy remain FEED work.",
    },
    {
        "Decision gate": "Receiving-capacity use",
        "Status": "● Green" if summary["sink_utilization_fraction"] >= 0.70 else ("● Amber" if summary["sink_utilization_fraction"] >= 0.40 else "● Red"),
        "Result": f"{summary['sink_utilization_fraction']:.0%} utilized",
        "Management meaning": "Low use can indicate stranded capacity; high use leaves less expansion margin.",
    },
    {
        "Decision gate": "Source evidence maturity",
        "Status": "● Green" if conceptual_count == 0 else ("● Amber" if conceptual_count <= 2 else "● Red"),
        "Result": f"{conceptual_count} conceptual / pilot-derived source(s)",
        "Management meaning": "Advance vendor data and source testing before sanction.",
    },
    {
        "Decision gate": "Selected product and process-safety screen",
        "Status": (
            "● Red"
            if summary["process_safety_red_sources"] > 0
            else (
                "● Amber"
                if summary["process_safety_amber_sources"] > 0
                or summary["active_streams_failing_screened_product_spec"] > 0
                else "● Green"
            )
        ),
        "Result": (
            f"{summary['active_streams_failing_screened_product_spec']} quality fail; "
            f"{summary['process_safety_amber_sources']} amber / "
            f"{summary['process_safety_red_sources']} red safety screens"
        ),
        "Management meaning": "Flags respond to the selected technology, purity, water and impurity targets; they are a hazard screen, not a QRA.",
    },
    {
        "Decision gate": "Product-quality evidence",
        "Status": "● Green" if coverage >= 1.0 else ("● Amber" if coverage >= 0.50 else "● Red"),
        "Result": f"{summary['product_spec_components_screened']}/{summary['product_spec_components_in_reference']} benchmark components",
        "Management meaning": "A pass is a partial screen, not a complete receiver acceptance certificate.",
    },
]
with st.expander("Executive decision gates", expanded=True):
    st.caption(
        "Independent gates are shown instead of a single composite score so that a strong result cannot hide a critical weakness."
    )
    st.dataframe(pd.DataFrame(decision_rows), hide_index=True, width="stretch")

tabs = st.tabs(
    [
        "1  Capture",
        "2  Purification",
        "3  Transport to sink",
        "4  Environmental study",
        "5  Decision lab",
    ]
)

with tabs[0]:
    st.markdown(
        """
        <div class="section-lead"><b>What happens here:</b> eligible flue-gas streams are selected, CO₂ is separated using a source-specific technology, and annual plant availability is applied. Capture excludes later dehydration, polishing and compression.</div>
        """,
        unsafe_allow_html=True,
    )
    capture_left, capture_right = st.columns([1.7, 1], gap="large")
    capture_df = pd.DataFrame(
        [
            {
                "ID": row["source_id"],
                "Source": row["source_name"],
                "Sector": SECTOR_LABELS[row["sector"]],
                "Capture technology": row["capture_technology"],
                "Emissions basis (kt/y)": row["emissions_basis_tpy"] / 1000.0,
                "Captured (kt/y)": row["captured_before_purification_tpy"] / 1000.0,
                "Capture rate": row["capture_rate"],
                "Availability": row["availability"],
                "Electricity (MWh/t captured)": row["capture_electricity_mwh_per_year"] / row["captured_before_purification_tpy"] if row["captured_before_purification_tpy"] else 0.0,
                "Steam (GJ/t captured)": row["capture_steam_gj_per_year"] / row["captured_before_purification_tpy"] if row["captured_before_purification_tpy"] else 0.0,
                "CAPEX (€m)": row["capture_capex_eur"] / 1e6,
                "Cost (€/t product)": row["capture_cost_eur_per_t_product"],
                "TRL": row["capture_technology_readiness_level"],
                "Maturity": row["project_status"].replace("-", " ").title(),
            }
            for row in active_rows
        ]
    )
    with capture_left:
        fig = go.Figure()
        fig.add_trace(go.Bar(name="Emissions basis", x=capture_df["ID"], y=capture_df["Emissions basis (kt/y)"], marker_color="#B6C4CF"))
        fig.add_trace(go.Bar(name="Captured", x=capture_df["ID"], y=capture_df["Captured (kt/y)"], marker_color=COLORS["capture"]))
        fig.update_layout(
            barmode="group",
            height=390,
            margin={"l": 10, "r": 10, "t": 35, "b": 10},
            paper_bgcolor="white",
            plot_bgcolor="white",
            yaxis={"title": "kt CO₂/year", "gridcolor": "#E2E8F0"},
            legend={"orientation": "h", "y": 1.12},
        )
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
    with capture_right:
        st.subheader("Cost position")
        st.plotly_chart(cost_figure(summary), width="stretch", config={"displayModeBar": False})

    st.dataframe(
        capture_df,
        hide_index=True,
        width="stretch",
        column_config={
            "Capture rate": st.column_config.ProgressColumn(format="percent", min_value=0, max_value=1),
            "Availability": st.column_config.ProgressColumn(format="percent", min_value=0, max_value=1),
            "Emissions basis (kt/y)": st.column_config.NumberColumn(format="%.1f"),
            "Captured (kt/y)": st.column_config.NumberColumn(format="%.1f"),
            "CAPEX (€m)": st.column_config.NumberColumn(format="%.1f"),
            "Cost (€/t product)": st.column_config.NumberColumn(format="%.1f"),
            "Electricity (MWh/t captured)": st.column_config.NumberColumn(format="%.3f"),
            "Steam (GJ/t captured)": st.column_config.NumberColumn(format="%.2f"),
        },
    )
    with st.expander("How the capture result is calculated"):
        st.markdown(
            "**Captured CO₂ = emissions basis × capturable fraction × capture rate × annual availability.**  "
            "CAPEX is scaled from the reference train using a 0.67 exponent, then annualized over the selected project life. "
            "Electricity, steam, consumables and fixed O&M are added separately."
        )
    st.download_button(
        "Download capture results (CSV)",
        capture_df.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"{result.scenario}_capture.csv",
        mime="text/csv",
    )

with tabs[1]:
    st.markdown(
        """
        <div class="section-lead"><b>What happens here:</b> captured gas is dehydrated, polished for key impurities and compressed to the 110 bar pipeline inlet. Recovery losses, power, CAPEX and OPEX are accounted independently from capture.</div>
        """,
        unsafe_allow_html=True,
    )
    pur_kpis = st.columns(4)
    pur_kpis[0].metric("Purification feed", fmt_mt(summary["total_captured_before_purification_tpy"]))
    pur_kpis[1].metric("Pipeline product", fmt_mt(summary["total_purified_co2_tpy"]))
    pur_kpis[2].metric("Recovery loss", f"{summary['total_purification_loss_tpy'] / 1000:.1f} kt/y")
    pur_kpis[3].metric("Purification cost", f"€{summary['purification_cost_eur_per_t_received']:.1f}/t")

    purification_df = pd.DataFrame(
        [
            {
                "ID": row["source_id"],
                "Source": row["source_name"],
                "Purification technology": row["purification_train"],
                "Captured feed (kt/y)": row["captured_before_purification_tpy"] / 1000.0,
                "Product (kt/y)": row["allocated_product_co2_tpy"] / 1000.0,
                "Recovery": row["purification_recovery"],
                "CO₂ (mol-%)": row["product_co2_mol_pct"],
                "H₂O (ppmv)": row["product_h2o_ppmv"],
                "O₂ (ppmv)": row["product_o2_ppmv"],
                "NOₓ (ppmv)": row["product_nox_ppmv"],
                "SOₓ (ppmv)": row["product_sox_ppmv"],
                "CO (ppmv)": row["product_co_ppmv"],
                "Quality benchmark": row["receiver_quality_status"],
                "Safety screen": row["process_safety_screen_status"],
                "Safety / quality flags": row["process_safety_screen_flags"] or "No flag in the configured screen",
                "Electricity (MWh/t product)": row["purification_electricity_mwh_per_year"] / row["allocated_product_co2_tpy"] if row["allocated_product_co2_tpy"] else 0.0,
                "Cost (€/t product)": row["purification_cost_eur_per_t_product"],
                "CAPEX (€m)": row["purification_capex_eur"] / 1e6,
            }
            for row in active_rows
        ]
    )
    st.dataframe(
        purification_df,
        hide_index=True,
        width="stretch",
        column_config={
            "Captured feed (kt/y)": st.column_config.NumberColumn(format="%.1f"),
            "Product (kt/y)": st.column_config.NumberColumn(format="%.1f"),
            "Recovery": st.column_config.ProgressColumn(format="percent", min_value=0.90, max_value=1.0),
            "CAPEX (€m)": st.column_config.NumberColumn(format="%.1f"),
            "Electricity (MWh/t product)": st.column_config.NumberColumn(format="%.3f"),
            "Cost (€/t product)": st.column_config.NumberColumn(format="%.1f"),
        },
    )

    if summary["active_streams_failing_screened_product_spec"]:
        st.warning(
            f"{summary['active_streams_failing_screened_product_spec']} selected stream(s) miss the external product-quality benchmark. "
            "Their economics and hydraulics are retained for comparison, but the configuration is visibly flagged for additional conditioning or a different receiver specification.",
            icon="⚠️",
        )

    limit_df = pd.DataFrame(
        [
            {
                "Component": limit.component.replace("2", "₂").replace("x", "ₓ"),
                "Requirement": "Minimum" if limit.limit_type == "minimum" else "Maximum",
                "Limit": limit.limit_value,
                "Unit": limit.unit,
            }
            for limit in inputs.product_limits
        ]
    )
    st.markdown("#### Product-quality screen")
    st.caption(
        f"The dashboard checks {summary['product_spec_components_screened']} of "
        f"{summary['product_spec_components_in_reference']} components in the selected public cargo benchmark "
        f"({summary['product_spec_screening_coverage_fraction']:.0%} coverage). Passing this screen is not a "
        "substitute for a complete compositional assay, a Dunkerque pipeline specification or a shipper agreement."
    )
    st.dataframe(limit_df, hide_index=True, width="stretch")
    with st.expander("Full benchmark coverage and remaining validation"):
        st.write(
            "These are the components for which the available source assumptions support a defensible screening estimate. "
            "The reference cargo specification lists additional trace components. They must be measured and guaranteed during FEED; the model does not silently assume them to be zero."
        )
        full_limit_df = pd.DataFrame(
            [
                {
                    "Component": limit.component,
                    "Requirement": "Minimum" if limit.limit_type == "minimum" else "Maximum",
                    "Limit": limit.limit_value,
                    "Unit": limit.unit,
                    "Model status": "Screened" if limit.screened_in_model else "Assay required",
                    "Validation": limit.validation_status,
                }
                for limit in inputs.reference_product_limits
            ]
        )
        st.dataframe(full_limit_df, hide_index=True, width="stretch")
        st.caption(
            "Northern Lights' June 2025 liquid-CO₂ cargo limits are used only as an external quality benchmark. "
            "A binding Dunkerque receiver specification may differ and takes precedence when available."
        )
    st.download_button(
        "Download purification results (CSV)",
        purification_df.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"{result.scenario}_purification.csv",
        mime="text/csv",
    )

with tabs[2]:
    st.markdown(
        """
        <div class="section-lead"><b>What happens here:</b> pipeline-quality CO₂ enters a dense-phase collection network at 110 bar. The model evaluates every feasible source/sink tree without free junction nodes, aggregates branch flows, selects a standard diameter and checks velocity and cumulative pressure drop to the Dunkerque sink. Density and compressibility are calculated with the Peng–Robinson equation of state from pressure, temperature and mixture composition.</div>
        """,
        unsafe_allow_html=True,
    )
    transport_kpis = st.columns(6)
    diameters = [row["nominal_diameter_mm"] for row in result.pipeline_segments]
    max_velocity = max((row["velocity_m_per_s"] for row in result.pipeline_segments), default=0.0)
    transport_kpis[0].metric("Indicative route", f"{summary['pipeline_route_length_km']:.1f} km")
    transport_kpis[1].metric("Pipe sizes", f"DN{min(diameters):.0f}–{max(diameters):.0f}" if diameters else "—")
    transport_kpis[2].metric("Minimum arrival pressure", f"{summary['minimum_arrival_pressure_bar']:.1f} bar", delta=f"{summary['minimum_arrival_pressure_bar'] - inputs.config['transport']['minimum_arrival_pressure_bar']:.1f} bar margin")
    transport_kpis[3].metric("Maximum velocity", f"{max_velocity:.2f} m/s")
    transport_kpis[4].metric(
        "Screened wall",
        f"{summary['pipeline_wall_thickness_min_mm']:.1f}–{summary['pipeline_wall_thickness_max_mm']:.1f} mm",
        help="Barlow pressure-wall screen including configured corrosion allowance and minimum wall; not final code design.",
    )
    transport_kpis[5].metric(
        "Indicative steel",
        f"{summary['pipeline_steel_mass_t'] / 1000:.1f} kt",
        help="Calculated pipe steel mass for the selected material screen; excludes fittings, valves and facilities.",
    )

    eos_composition = summary["transport_eos_composition_mol_fraction"]
    st.caption(
        "Peng–Robinson mixture used for hydraulics: "
        f"CO₂ {100 * eos_composition['CO2']:.3f} mol-% · "
        f"N₂ {100 * eos_composition['N2']:.3f} mol-% · "
        f"O₂ {1_000_000 * eos_composition['O2']:.1f} ppmv · "
        f"Ar {100 * eos_composition['Ar']:.3f} mol-% · "
        f"{summary['transport_eos_composition_basis']}."
    )
    if summary["phase_envelope_review_source_count"]:
        st.warning(
            f"{summary['phase_envelope_review_source_count']} allocated stream(s) require a detailed multi-component phase-envelope check. "
            "The PR EOS still updates density and pressure loss for scenario comparison, but this flag must be cleared before fixing the operating envelope.",
            icon="⚠️",
        )

    st.plotly_chart(pipeline_figure(inputs, result), width="stretch", config={"displayModeBar": False})

    transport_df = pd.DataFrame(
        [
            {
                "From": row["from_node"],
                "To": "Dunkerque sink" if row["to_node"] == "SINK" else row["to_node"],
                "Route (km)": row["route_length_km"],
                "CO₂ flow (Mt/y)": row["flow_tpy"] / 1e6,
                "Total stream (Mt/y)": row["total_stream_flow_tpy"] / 1e6,
                "CO₂ mass fraction": row["co2_mass_fraction"],
                "Diameter": f"DN {row['nominal_diameter_mm']:.0f}",
                "Material": row["pipeline_material_label"],
                "Wall (mm)": row["wall_thickness_mm"],
                "Steel (t)": row["steel_mass_t"],
                "PR density (kg/m³)": row["eos_density_kg_per_m3"],
                "PR Z (-)": row["eos_compressibility_factor"],
                "EOS P-ref (bar)": row["eos_reference_pressure_bar"],
                "Velocity (m/s)": row["velocity_m_per_s"],
                "Pressure drop (bar)": row["pressure_drop_bar"],
                "CAPEX (€m)": row["segment_capex_eur"] / 1e6,
            }
            for row in result.pipeline_segments
        ]
    )
    st.dataframe(
        transport_df,
        hide_index=True,
        width="stretch",
        column_config={
            "Route (km)": st.column_config.NumberColumn(format="%.1f"),
            "CO₂ flow (Mt/y)": st.column_config.NumberColumn(format="%.3f"),
            "Total stream (Mt/y)": st.column_config.NumberColumn(format="%.3f"),
            "CO₂ mass fraction": st.column_config.ProgressColumn(format="percent", min_value=0.90, max_value=1.0),
            "Wall (mm)": st.column_config.NumberColumn(format="%.1f"),
            "Steel (t)": st.column_config.NumberColumn(format="%.0f"),
            "PR density (kg/m³)": st.column_config.NumberColumn(format="%.1f"),
            "PR Z (-)": st.column_config.NumberColumn(format="%.4f"),
            "EOS P-ref (bar)": st.column_config.NumberColumn(format="%.1f"),
            "Velocity (m/s)": st.column_config.NumberColumn(format="%.2f"),
            "Pressure drop (bar)": st.column_config.NumberColumn(format="%.2f"),
            "CAPEX (€m)": st.column_config.NumberColumn(format="%.1f"),
        },
    )
    with st.expander("How the network is selected"):
        st.markdown(
            f"The model evaluated **{summary['candidate_pipeline_trees_evaluated']:,} feasible network trees** for this case. "
            "For every segment it uses source-specific route uplifts, Peng–Robinson density/compressibility, Darcy–Weisbach pressure loss with a Swamee–Jain friction factor, "
            "standard nominal diameters, a 2.5 m/s velocity ceiling and an 85 bar minimum arrival pressure. The least annualized-cost feasible tree is retained."
        )
        st.markdown(
            "**Material screen.** Wall thickness uses the Barlow pressure relation at the configured 120 bar design pressure, "
            "with material SMYS, a 0.72 design factor, corrosion allowance, and a 6.4 mm minimum wall. "
            "The hydraulic diameter is held fixed; 35% of route CAPEX is treated as material-sensitive. "
            "Fracture control, decompression, toughness, weldability, impurity corrosion, fatigue, fittings, and code-class location factors require FEED."
        )

    download_columns = st.columns(3)
    with download_columns[0]:
        st.download_button(
            "Download pipeline results",
            transport_df.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"{result.scenario}_transport.csv",
            mime="text/csv",
            width="stretch",
        )
    with download_columns[1]:
        st.download_button(
            "Download source audit data",
            pd.DataFrame(result.source_results).to_csv(index=False).encode("utf-8-sig"),
            file_name=f"{result.scenario}_source_audit.csv",
            mime="text/csv",
            width="stretch",
        )
    with download_columns[2]:
        st.download_button(
            "Download full summary",
            json.dumps(summary, indent=2, ensure_ascii=False).encode("utf-8"),
            file_name=f"{result.scenario}_summary.json",
            mime="application/json",
            width="stretch",
        )

    st.markdown(
        """
        <div class="scope-note">
          <b>Precision boundary:</b> the route is an optimized screening topology, not a surveyed right-of-way. Land ownership, protected areas, road/rail/water crossings, elevation, geotechnics, transient operation, fracture control and material compatibility require FEED studies. The endpoint is the supplied Port of Dunkerque site; downstream terminal and storage activities are excluded.
        </div>
        """,
        unsafe_allow_html=True,
    )

with tabs[3]:
    st.markdown(
        """
        <div class="section-lead"><b>What happens here:</b> the model converts the engineering result into an environmental screening study. It combines capture and purification energy emissions, direct pipeline leakage, and tonne-kilometre lifecycle factors for pipeline operation and construction. It also benchmarks pipeline transport against alternative transport modes.</div>
        """,
        unsafe_allow_html=True,
    )

    env_kpis = st.columns(4)
    env_kpis[0].metric(
        "Lifecycle net CO₂ avoided",
        fmt_mt(summary["environmental_lifecycle_net_avoided_co2_tpy"]),
        help="Pipeline product minus direct leakage, capture/purification energy emissions and the screening transport lifecycle burden.",
    )
    env_kpis[1].metric(
        "Climate burden",
        f"{summary['environmental_total_climate_burden_tco2e_per_year'] / 1000:.1f} kt CO₂-eq/y",
    )
    env_kpis[2].metric(
        "Burden intensity",
        f"{summary['environmental_climate_burden_kgco2e_per_t_received']:.1f} kg CO₂-eq/t",
    )
    env_kpis[3].metric(
        "Net avoidance efficiency",
        f"{summary['environmental_net_avoidance_efficiency_fraction']:.1%}",
    )

    burden_labels = [
        "Capture energy",
        "Purification energy",
        "Pipeline leakage",
        "Pipeline operation LCA",
        "Pipeline construction LCA",
        "Material delta vs X65",
    ]
    burden_values = [
        summary["environmental_capture_energy_emissions_tco2e_per_year"],
        summary["environmental_purification_energy_emissions_tco2e_per_year"],
        summary["environmental_pipeline_leakage_tco2e_per_year"],
        summary["environmental_pipeline_use_emissions_tco2e_per_year"],
        summary["environmental_pipeline_construction_emissions_tco2e_per_year"],
        summary["environmental_pipeline_material_delta_annualized_tco2e_per_year"],
    ]
    env_fig = go.Figure(
        go.Bar(
            x=burden_labels,
            y=burden_values,
            text=[f"{value / 1000:.1f} kt" for value in burden_values],
            textposition="outside",
            hovertemplate="%{x}: %{y:,.0f} t CO₂-eq/y<extra></extra>",
        )
    )
    env_fig.update_layout(
        height=370,
        margin={"l": 15, "r": 15, "t": 35, "b": 10},
        paper_bgcolor="white",
        plot_bgcolor="white",
        yaxis={"title": "t CO₂-eq/y", "gridcolor": "#E2E8F0", "rangemode": "tozero"},
        xaxis={"title": None},
        showlegend=False,
        title={"text": "Modeled annual climate-burden breakdown", "x": 0.0, "xanchor": "left"},
    )
    st.plotly_chart(env_fig, width="stretch", config={"displayModeBar": False})

    energy_cols = st.columns(3)
    energy_cols[0].metric(
        "Capture electricity",
        f"{summary['environmental_capture_electricity_mwh_per_year'] / 1000:.1f} GWh/y",
    )
    energy_cols[1].metric(
        "Purification electricity",
        f"{summary['environmental_purification_electricity_mwh_per_year'] / 1000:.1f} GWh/y",
    )
    energy_cols[2].metric(
        "Capture steam",
        f"{summary['environmental_capture_steam_gj_per_year'] / 1000:.1f} TJ/y",
    )

    st.markdown("#### Transport lifecycle benchmark")
    st.caption(
        f"Assessment year: {summary['environmental_assessment_year']}. "
        "The dense-pipeline factor is compared on a tonne-kilometre basis with alternative transport modes. "
        "Pipeline construction is included in the pipeline benchmark."
    )
    benchmark_df = pd.DataFrame(summary["environmental_transport_benchmarks"]).rename(
        columns={
            "mode": "Alternative mode",
            "mode_gco2e_per_tkm": "Mode (g CO₂-eq/tkm)",
            "pipeline_gco2e_per_tkm_including_construction": "Pipeline incl. construction (g CO₂-eq/tkm)",
            "pipeline_intensity_reduction_fraction": "Pipeline reduction",
            "avoided_transport_emissions_tco2e_per_year": "Indicative avoided transport emissions (t CO₂-eq/y)",
        }
    )
    benchmark_df = benchmark_df[[
        "Alternative mode",
        "Mode (g CO₂-eq/tkm)",
        "Pipeline incl. construction (g CO₂-eq/tkm)",
        "Pipeline reduction",
        "Indicative avoided transport emissions (t CO₂-eq/y)",
    ]]
    st.dataframe(
        benchmark_df,
        hide_index=True,
        width="stretch",
        column_config={
            "Mode (g CO₂-eq/tkm)": st.column_config.NumberColumn(format="%.1f"),
            "Pipeline incl. construction (g CO₂-eq/tkm)": st.column_config.NumberColumn(format="%.1f"),
            "Pipeline reduction": st.column_config.ProgressColumn(format="percent", min_value=0, max_value=1),
            "Indicative avoided transport emissions (t CO₂-eq/y)": st.column_config.NumberColumn(format="%.0f"),
        },
    )

    env_download = pd.DataFrame(
        [{
            "scenario": result.scenario,
            "assessment_year": summary["environmental_assessment_year"],
            "total_climate_burden_tco2e_per_year": summary["environmental_total_climate_burden_tco2e_per_year"],
            "lifecycle_net_avoided_co2_tpy": summary["environmental_lifecycle_net_avoided_co2_tpy"],
            "climate_burden_kgco2e_per_t_received": summary["environmental_climate_burden_kgco2e_per_t_received"],
            "net_avoidance_efficiency_fraction": summary["environmental_net_avoidance_efficiency_fraction"],
            "annual_tonne_km": summary["environmental_tonne_km_per_year"],
        }]
    )
    st.download_button(
        "Download environmental study (CSV)",
        env_download.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"{result.scenario}_environmental_study.csv",
        mime="text/csv",
    )

    with st.expander("Environmental-study assumptions and limitations"):
        st.markdown(
            f"**Pipeline use-phase climate factor:** {summary['environmental_pipeline_use_factor_gco2e_per_tkm']:.1f} g CO₂-eq/tkm  \n"
            f"**Pipeline construction factor:** {summary['environmental_pipeline_construction_factor_gco2e_per_tkm']:.1f} g CO₂-eq/tkm  \n"
            f"**Annual transport work:** {summary['environmental_tonne_km_per_year'] / 1e9:.3f} billion tkm/y  \n"
            f"**Selected pipe-material embodied carbon:** {summary['environmental_pipeline_material_embodied_carbon_tco2e'] / 1000:.1f} kt CO₂-eq over the material inventory  \n"
            f"**Annualized material delta versus X65:** {summary['environmental_pipeline_material_delta_annualized_tco2e_per_year'] / 1000:.2f} kt CO₂-eq/y"
        )
        for item in summary["environmental_limitations"]:
            st.markdown(f"- {item}")

with tabs[4]:
    st.markdown(
        """
        <div class="section-lead"><b>Management question:</b> which pipeline material gives the most useful balance of cost, carbon and robustness, and which assumptions move the decision most? The material comparison holds the selected topology and hydraulic diameters fixed so the trade-off remains understandable.</div>
        """,
        unsafe_allow_html=True,
    )

    if summary["customized_source_configurations"] > 0:
        st.markdown("#### Impact versus source defaults")
        impact_kpis = st.columns(4)
        impact_kpis[0].metric(
            "Pipeline product",
            fmt_mt(summary["total_purified_co2_tpy"]),
            delta=f"{(summary['total_purified_co2_tpy'] - baseline_summary['total_purified_co2_tpy']) / 1000:+.1f} kt/y",
        )
        impact_kpis[1].metric(
            "Full-chain cost",
            f"€{summary['full_chain_cost_eur_per_t_received']:.1f}/t",
            delta=f"€{summary['full_chain_cost_eur_per_t_received'] - baseline_summary['full_chain_cost_eur_per_t_received']:+.1f}/t",
            delta_color="inverse",
        )
        impact_kpis[2].metric(
            "Lifecycle climate burden",
            f"{summary['environmental_total_climate_burden_tco2e_per_year'] / 1000:.1f} kt/y",
            delta=f"{(summary['environmental_total_climate_burden_tco2e_per_year'] - baseline_summary['environmental_total_climate_burden_tco2e_per_year']) / 1000:+.1f} kt/y",
            delta_color="inverse",
        )
        impact_kpis[3].metric(
            "Lifecycle CO₂ avoided",
            fmt_mt(summary["environmental_lifecycle_net_avoided_co2_tpy"]),
            delta=f"{(summary['environmental_lifecycle_net_avoided_co2_tpy'] - baseline_summary['environmental_lifecycle_net_avoided_co2_tpy']) / 1000:+.1f} kt/y",
        )
        st.caption(
            "The comparator keeps the same scenario, sources, economics, receiver capacity and pipeline material, but restores each source's default capture and purification configuration."
        )

    st.markdown("#### Selected source configurations")
    baseline_source_lookup = {
        row["source_id"]: row for row in baseline_result.source_results
    }
    configuration_df = pd.DataFrame(
        [
            {
                "ID": row["source_id"],
                "Capture technology": row["capture_technology"],
                "Capture": row["capture_rate"],
                "Purification technology": row["purification_train"],
                "Recovery": row["purification_recovery"],
                "CO₂ purity (mol-%)": row["product_co2_mol_pct"],
                "H₂O (ppmv)": row["product_h2o_ppmv"],
                "Product (kt/y)": row["allocated_product_co2_tpy"] / 1000.0,
                "Δ product vs default (kt/y)": (
                    row["allocated_product_co2_tpy"]
                    - baseline_source_lookup[row["source_id"]]["allocated_product_co2_tpy"]
                )
                / 1000.0,
                "Source energy (kt CO₂-eq/y)": row["source_energy_emissions_tpy"] / 1000.0,
                "Capture + purification cost (€/t product)": (
                    row["capture_cost_eur_per_t_product"]
                    + row["purification_cost_eur_per_t_product"]
                ),
                "Δ source cost vs default (€/t)": (
                    row["capture_cost_eur_per_t_product"]
                    + row["purification_cost_eur_per_t_product"]
                    - baseline_source_lookup[row["source_id"]]["capture_cost_eur_per_t_product"]
                    - baseline_source_lookup[row["source_id"]]["purification_cost_eur_per_t_product"]
                ),
                "Quality": row["receiver_quality_status"],
                "Safety": row["process_safety_screen_status"],
            }
            for row in active_rows
        ]
    )
    st.dataframe(
        configuration_df,
        hide_index=True,
        width="stretch",
        column_config={
            "Capture": st.column_config.ProgressColumn(
                format="percent", min_value=0.80, max_value=1.0
            ),
            "Recovery": st.column_config.ProgressColumn(
                format="percent", min_value=0.90, max_value=1.0
            ),
            "CO₂ purity (mol-%)": st.column_config.NumberColumn(format="%.3f"),
            "H₂O (ppmv)": st.column_config.NumberColumn(format="%.1f"),
            "Product (kt/y)": st.column_config.NumberColumn(format="%.1f"),
            "Δ product vs default (kt/y)": st.column_config.NumberColumn(format="%+.1f"),
            "Source energy (kt CO₂-eq/y)": st.column_config.NumberColumn(
                format="%.1f"
            ),
            "Capture + purification cost (€/t product)": st.column_config.NumberColumn(
                format="%.1f"
            ),
            "Δ source cost vs default (€/t)": st.column_config.NumberColumn(
                format="%+.1f"
            ),
        },
    )
    st.caption(
        "Change any source technology or target in the sidebar, then run the scenario. "
        "Mass balance, source CAPEX/OPEX, energy emissions, product quality, PR composition, hydraulics and management indicators are recalculated together."
    )

    selected_material_row = selected_material_decision
    decision_kpis = st.columns(4)
    decision_kpis[0].metric(
        "Selected material",
        selected_material_row["material"],
        help=selected_material_row["management_note"],
    )
    decision_kpis[1].metric(
        "Cost / lifecycle t avoided",
        f"€{selected_material_row['full_chain_cost_eur_per_t_net_avoided']:.1f}/t",
    )
    decision_kpis[2].metric(
        "Annual value headroom",
        fmt_money(selected_material_row["annual_value_headroom_eur"]),
        help="Selected CO₂ value multiplied by lifecycle tonnes avoided, less modeled annual chain cost. This is not booked revenue.",
    )
    payback = selected_material_row["simple_payback_years"]
    decision_kpis[3].metric(
        "Indicative simple payback",
        f"{payback:.1f} years" if payback is not None else "No positive headroom",
        help="Total modeled CAPEX divided by annual value headroom; excludes tax, grants, construction phasing and financing structure.",
    )

    comparison_df = pd.DataFrame(material_comparison)
    material_fig = go.Figure()
    material_fig.add_trace(
        go.Scatter(
            x=comparison_df["full_chain_cost_eur_per_t_received"],
            y=comparison_df["material_embodied_intensity_kgco2e_per_t_received"],
            mode="markers+text",
            text=comparison_df["material"],
            textposition="top center",
            marker={
                "size": 18,
                "color": comparison_df["pipeline_capex_eur"] / 1e6,
                "colorscale": "Tealgrn",
                "showscale": True,
                "colorbar": {"title": "Pipeline<br>CAPEX (€m)"},
                "line": {"color": COLORS["ink"], "width": 1},
            },
            customdata=comparison_df[
                [
                    "pipeline_steel_mass_t",
                    "wall_thickness_min_mm",
                    "wall_thickness_max_mm",
                    "pipeline_material_embodied_carbon_tco2e",
                ]
            ],
            hovertemplate=(
                "<b>%{text}</b><br>Cost: €%{x:.1f}/t received<br>"
                "Annualized material carbon: %{y:.2f} kg CO₂-eq/t received<br>"
                "Steel: %{customdata[0]:,.0f} t<br>Wall: %{customdata[1]:.1f}–%{customdata[2]:.1f} mm<br>"
                "Whole material inventory: %{customdata[3]:,.0f} t CO₂-eq<extra></extra>"
            ),
        )
    )
    material_fig.update_layout(
        height=470,
        margin={"l": 20, "r": 20, "t": 55, "b": 20},
        title={"text": "Pipeline material trade-off · lower-left is preferable", "x": 0.0},
        xaxis={"title": "Full-chain cost (€ per t received)", "gridcolor": "#E2E8F0"},
        yaxis={"title": "Annualized pipe-material carbon (kg CO₂-eq per t received)", "gridcolor": "#E2E8F0"},
        paper_bgcolor="white",
        plot_bgcolor="white",
    )
    st.plotly_chart(material_fig, width="stretch", config={"displayModeBar": False})

    display_comparison = comparison_df.rename(
        columns={
            "material": "Material",
            "smys_mpa": "SMYS (MPa)",
            "wall_thickness_min_mm": "Wall min (mm)",
            "wall_thickness_max_mm": "Wall max (mm)",
            "pipeline_steel_mass_t": "Steel (t)",
            "pipeline_material_embodied_carbon_tco2e": "Material carbon (t CO₂-eq)",
            "pipeline_capex_eur": "Pipeline CAPEX (€m)",
            "full_chain_cost_eur_per_t_received": "Chain cost (€/t received)",
            "full_chain_cost_eur_per_t_net_avoided": "Chain cost (€/t avoided)",
            "annual_value_headroom_eur": "Annual value headroom (€m/y)",
            "simple_payback_years": "Simple payback (y)",
        }
    )
    display_comparison["Pipeline CAPEX (€m)"] /= 1e6
    display_comparison["Annual value headroom (€m/y)"] /= 1e6
    st.dataframe(
        display_comparison[
            [
                "Material",
                "SMYS (MPa)",
                "Wall min (mm)",
                "Wall max (mm)",
                "Steel (t)",
                "Material carbon (t CO₂-eq)",
                "Pipeline CAPEX (€m)",
                "Chain cost (€/t received)",
                "Chain cost (€/t avoided)",
                "Annual value headroom (€m/y)",
                "Simple payback (y)",
            ]
        ],
        hide_index=True,
        width="stretch",
    )

    received = max(summary["sink_received_after_pipeline_leakage_tpy"], 1.0)
    rate = run_discount_rate
    crf = (
        rate * (1.0 + rate) ** run_project_life / ((1.0 + rate) ** run_project_life - 1.0)
        if rate > 0
        else 1.0 / run_project_life
    )
    sensitivity_rows = [
        ("Electricity price", summary["environmental_total_electricity_mwh_per_year"] * run_electricity_price * 0.20 / received),
        ("Capture CAPEX", summary["capture_capex_eur"] * crf * 0.20 / received),
        ("Purification CAPEX", summary["purification_capex_eur"] * crf * 0.20 / received),
        ("Pipeline CAPEX", summary["pipeline_capex_eur"] * crf * 0.20 / received),
        ("Steam price", summary["environmental_capture_steam_gj_per_year"] * run_steam_price * 0.20 / received),
    ]
    sensitivity_rows.sort(key=lambda item: item[1])
    sensitivity_fig = go.Figure(
        go.Bar(
            x=[value for _, value in sensitivity_rows],
            y=[label for label, _ in sensitivity_rows],
            orientation="h",
            marker_color=COLORS["capture"],
            text=[f"±€{value:.1f}/t" for _, value in sensitivity_rows],
            textposition="outside",
            hovertemplate="%{y}: ±€%{x:.2f}/t received<extra></extra>",
        )
    )
    sensitivity_fig.update_layout(
        height=360,
        margin={"l": 20, "r": 55, "t": 55, "b": 20},
        title={"text": "One-at-a-time cost exposure for a ±20% input change", "x": 0.0},
        xaxis={"title": "Absolute change in levelized cost (€/t received)", "gridcolor": "#E2E8F0"},
        yaxis={"title": None},
        paper_bgcolor="white",
        plot_bgcolor="white",
    )
    st.plotly_chart(sensitivity_fig, width="stretch", config={"displayModeBar": False})

    st.info(
        "Decision-use boundary: material results are comparative screens on the same network. "
        "Do not select a grade from this chart alone; confirm CO₂ composition, water specification, decompression/fracture behaviour, toughness, corrosion management, welding, availability, route class, and applicable pipeline code during FEED.",
        icon="ℹ️",
    )
    st.download_button(
        "Download material decision table (CSV)",
        comparison_df.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"{result.scenario}_material_decision_table.csv",
        mime="text/csv",
    )
