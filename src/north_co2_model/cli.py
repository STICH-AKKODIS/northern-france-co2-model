from __future__ import annotations

import argparse
import json
from pathlib import Path

from .model import load_model_inputs, run_scenario
from .reporting import write_scenario_comparison, write_scenario_outputs


def _default_root() -> Path:
    return Path(__file__).resolve().parents[2]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the northern France three-stage CO2 capture, purification and pipeline transport model."
    )
    parser.add_argument("--root", type=Path, default=_default_root(), help="Project root containing config/ and data/.")
    parser.add_argument("--scenario", default="announced_2030", help="Scenario name from config/model.toml.")
    parser.add_argument("--all-scenarios", action="store_true", help="Run every configured scenario and write a comparison.")
    parser.add_argument("--output-dir", type=Path, default=None, help="Output root (default: <root>/outputs).")
    parser.add_argument(
        "--trajectory-json",
        type=Path,
        default=None,
        help="Optional v0.7 trajectory JSON exported by the dashboard.",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    inputs = load_model_inputs(args.root)
    output_root = (args.output_dir or inputs.root / "outputs").resolve()
    scenario_names = list(inputs.config["scenarios"]) if args.all_scenarios else [args.scenario]
    trajectory_overrides = (
        json.loads(args.trajectory_json.read_text(encoding="utf-8-sig"))
        if args.trajectory_json
        else None
    )

    results = []
    for scenario_name in scenario_names:
        print(f"Running scenario: {scenario_name}")
        result = run_scenario(
            inputs,
            scenario_name,
            trajectory_overrides=trajectory_overrides,
        )
        write_scenario_outputs(inputs, result, output_root / scenario_name)
        results.append(result)
        summary = result.summary
        print(
            f"  {summary['sink_received_after_pipeline_leakage_tpy'] / 1e6:.3f} Mt/y at sink; "
            f"{summary['pipeline_route_length_km']:.1f} km; "
            f"EUR {summary['full_chain_cost_eur_per_t_received']:.1f}/t received"
        )

    if len(results) > 1:
        write_scenario_comparison(results, output_root)
    print(f"Outputs: {output_root}")
