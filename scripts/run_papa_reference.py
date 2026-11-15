"""Run Papa's unmodified capture and purification packages locally.

The script loads the extracted packages under private module aliases, executes the
notebook reference case, and writes a compact machine-readable summary.  It never
modifies the reference packages.
"""

from __future__ import annotations

import argparse
import contextlib
import importlib.util
import io
import json
import os
import sys
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REFERENCE_ROOT = Path(
    os.environ.get(
        "PAPA_REFERENCE_ROOT",
        ROOT.parent.parent / "papa_models_local_20261115",
    )
)


def _load_package(alias: str, package_dir: Path) -> Any:
    init_path = package_dir / "__init__.py"
    if not init_path.exists():
        raise FileNotFoundError(f"Reference package not found: {init_path}")
    spec = importlib.util.spec_from_file_location(
        alias,
        init_path,
        submodule_search_locations=[str(package_dir)],
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load reference package from {package_dir}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[alias] = module
    spec.loader.exec_module(module)
    return module


def _plain(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, dict):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    try:
        return _plain(asdict(value))
    except (TypeError, ValueError):
        return str(value)


def _composition(stream: dict[str, float]) -> dict[str, float]:
    total = sum(float(value) for value in stream.values())
    if total <= 0.0:
        return {}
    return {key: float(value) / total for key, value in stream.items()}


def _pick(mapping: dict[str, Any], *keys: str) -> dict[str, Any]:
    return {key: _plain(mapping[key]) for key in keys if key in mapping}


def run(reference_root: Path) -> dict[str, Any]:
    capture_dir = reference_root / "CAPTURE-main"
    purification_dir = reference_root / "Purification-Optimisation-main"
    capture = _load_package("papa_capture_reference", capture_dir)
    purification = _load_package("papa_purification_reference", purification_dir)

    from papa_capture_reference.economic_balance import EconomicConfig
    from papa_capture_reference.environmental_balance import EnvironmentalConfig
    from papa_capture_reference.workflow import run_case

    flue = {
        "CO2": 0.14,
        "N2": 0.698014,
        "O2": 0.04,
        "H2O": 0.11,
        "Ar": 0.0093,
        "SO2": 35.0e-6,
        "NO": 100.0e-6,
        "NO2": 46.0e-6,
        "CO": 2500.0e-6,
        "H2S": 5.0e-6,
    }
    capture_cfg = replace(capture.Config(), T_gas_raw_C=120.0)
    economic_cfg = EconomicConfig(
        cost_year=2024,
        discount_rate=0.08,
        plant_life_yr=25,
        capex_ref_MEUR=250.0,
        capex_ref_capacity_tco2_yr=1_000_000.0,
        capex_scaling_exponent=0.65,
        fixed_om_frac_capex=0.04,
        variable_om_other_per_tco2=2.0,
        steam_cost_GJ=7.0,
        elec_cost_kWh=0.165,
        mea_cost_kg=1.82,
        water_cost_kg=0.00232,
    )
    with contextlib.redirect_stdout(io.StringIO()):
        capture_result = run_case(
            flue,
            cfg=capture_cfg,
            export_path=None,
            economic_cfg=economic_cfg,
            environmental_cfg=EnvironmentalConfig(),
        )

    product = capture_result["product"]
    product_stream = {
        key: float(value)
        for key, value in product.get("stream_mol_s", product.get("stream", {})).items()
    }
    if not product_stream:
        total = float(product.get("F_total_mol_s", 0.0))
        product_stream = {
            key: total * float(value)
            for key, value in product.get("y_mol", {}).items()
        }
    feed = purification.FeedCO2(
        F_total_mol_s=sum(product_stream.values()),
        T_C=float(product.get("T_C", capture_result["cfg"].T_cond_C)),
        P_bar=float(product.get("P_bar", capture_result["cfg"].P_str_bar)),
        y_mol=_composition(product_stream),
        source="Papa capture reference run",
    )
    with contextlib.redirect_stdout(io.StringIO()):
        train_a = purification.run_purification_a(
            feed=feed,
            cfg=purification.PurificationAConfig(),
            export_path=None,
            verbose=False,
        )
        train_b = purification.run_purification_b(
            feed=feed,
            cfg=purification.PurificationBConfig(),
            export_path=None,
            verbose=False,
        )

    capture_summary = {
        "config": _plain(capture_result["cfg"]),
        "flue_y_mol": flue,
        "capture_rate": float(capture_result["R_abs"].get("eta_capture", 0.0)),
        "co2_regeneration_fraction": float(
            capture_result["R_str"].get("CO2_regen_frac", 0.0)
        ),
        "raw_product_total_mol_s": sum(product_stream.values()),
        "raw_product_y_mol": _composition(product_stream),
        "raw_product_temperature_c": feed.T_C,
        "raw_product_pressure_bar": feed.P_bar,
        "energy": _plain(capture_result["energy"]),
        "economics": _plain(capture_result["eco"]),
        "environmental": _plain(capture_result["environmental"]),
        "makeup": _plain(capture_result["R_makeup"]),
        "mass_balance": _plain(
            capture_result.get("technical_balance", capture_result.get("balance", {}))
        ),
    }

    def purification_summary(result: Any) -> dict[str, Any]:
        return {
            "feed_total_mol_s": result.feed.F_total_mol_s,
            "feed_y_mol": result.feed.y_mol,
            "final_y_mol": _composition(result.final_stream),
            "final_total_mol_s": sum(result.final_stream.values()),
            "energy": _plain(result.energy),
            "economics": _plain(result.economics),
            "environmental": _plain(result.environmental),
            "mass_balance": _plain(result.balance),
            "spec": _plain(result.spec),
            "tp": _plain(result.tp),
            "unit_metrics": {
                key: _plain(unit.metrics) for key, unit in result.units.items()
            },
        }

    return {
        "provenance": {
            "reference_root": reference_root.name,
            "capture_package": capture_dir.name,
            "purification_package": purification_dir.name,
            "note": "Reference files loaded and executed without modification.",
        },
        "capture": capture_summary,
        "purification_train_a": purification_summary(train_a),
        "purification_train_b": purification_summary(train_b),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference-root", type=Path, default=DEFAULT_REFERENCE_ROOT)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("verification/papa_reference/reference_case.json"),
    )
    args = parser.parse_args()
    result = run(args.reference_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    capture = result["capture"]
    train_a = result["purification_train_a"]
    train_b = result["purification_train_b"]
    print(f"Saved {args.output.resolve()}")
    print(
        "Capture: "
        f"eta={capture['capture_rate']:.4f}, "
        f"raw CO2={capture['raw_product_y_mol'].get('CO2', 0.0):.5f}"
    )
    print(
        "Train A/B electricity: "
        f"{train_a['energy'].get('elec_kWh_tCO2', 0.0):.2f} / "
        f"{train_b['energy'].get('elec_kWh_tCO2', 0.0):.2f} kWh/t feed CO2"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
