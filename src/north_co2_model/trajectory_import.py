"""Read QGIS vertex CSVs for fixed 2D/3D pipeline trajectories.

The import recognizes XYZ exports produced by QGIS (or an explicit elevation
attribute). Missing elevation data defaults to zero metres; routes and their
geometry part ordering remain unchanged for review.
"""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
import math
from typing import Any

import pandas as pd


REQUIRED_COLUMNS = (
    "X", "Y", "id", "vertex_index", "vertex_part", "vertex_part_index"
)
# QGIS CSV export with AS_XYZ writes a 'Z' column. Other variants are accepted
# when the elevation was added as a QGIS field instead of a geometry coordinate.
ELEVATION_COLUMNS = (
    "z", "z_m", "elevation", "elevation_m", "altitude", "altitude_m", "vertex_z"
)
EMPTY_ELEVATIONS = {"", "null", "none", "nan", "na", "n/a", "<null>"}


@dataclass(frozen=True)
class ImportedRoute:
    key: str
    filename: str
    csv_id: str
    name: str
    parts: tuple[tuple[tuple[float, float], ...], ...]
    z_parts: tuple[tuple[float, ...], ...]
    elevation_column: str | None = None
    missing_z_count: int = 0
    observed_z_count: int = 0

    @property
    def vertices(self) -> tuple[tuple[float, float], ...]:
        """Plan-view coordinates for source matching and route preview."""
        return tuple(point for part in self.parts for point in part)

    @property
    def xyz_vertices(self) -> tuple[tuple[float, float, float], ...]:
        return tuple(
            (x, y, z)
            for part, elevations in zip(self.parts, self.z_parts)
            for (x, y), z in zip(part, elevations)
        )

    @property
    def has_elevation(self) -> bool:
        return self.observed_z_count > 0

    @property
    def length_km(self) -> float:
        # Include straight connectors between multipart line parts because
        # the hydraulic model treats this as one continuous 3D path.
        return sum(
            math.dist(a, b)
            for a, b in zip(self.xyz_vertices, self.xyz_vertices[1:])
        ) / 1000

    @property
    def part_gaps_km(self) -> tuple[float, ...]:
        parts = tuple(
            tuple((x, y, z) for (x, y), z in zip(part, elevations))
            for part, elevations in zip(self.parts, self.z_parts)
        )
        return tuple(
            math.dist(a[-1], b[0]) / 1000
            for a, b in zip(parts, parts[1:])
        )


def parse_route_csv(data: bytes, filename: str) -> list[ImportedRoute]:
    """Parse one QGIS vertex CSV; distinct `id` values are separate routes."""
    try:
        frame = pd.read_csv(BytesIO(data), encoding="utf-8-sig", dtype={"id": str})
    except (UnicodeError, pd.errors.ParserError, pd.errors.EmptyDataError, ValueError) as exc:
        raise ValueError(f"{filename}: cannot read CSV ({exc}).") from exc
    frame.columns = frame.columns.str.strip()
    missing = sorted(set(REQUIRED_COLUMNS) - set(frame.columns))
    if missing:
        raise ValueError(f"{filename}: missing required columns: {', '.join(missing)}.")
    if frame.empty:
        raise ValueError(f"{filename}: no route vertices were found.")
    frame["id"] = frame["id"].str.strip()
    if frame["id"].isna().any() or frame["id"].eq("").any():
        raise ValueError(f"{filename}: every row must have a route id.")

    numeric = ["X", "Y", "vertex_index", "vertex_part", "vertex_part_index"]
    for column in numeric:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
        if not frame[column].map(math.isfinite).all():
            raise ValueError(f"{filename}: column {column} contains missing or invalid numbers.")
    if not frame["X"].between(0, 1_300_000).all() or not frame["Y"].between(5_900_000, 7_400_000).all():
        raise ValueError(
            f"{filename}: X/Y outside Lambert-93 bounds. Expected EPSG:2154 coordinates in metres."
        )
    if (frame[["vertex_index", "vertex_part", "vertex_part_index"]] < 0).any().any():
        raise ValueError(f"{filename}: vertex indices and part numbers must not be negative.")
    for column in ("vertex_index", "vertex_part", "vertex_part_index"):
        if not (frame[column] % 1 == 0).all():
            raise ValueError(f"{filename}: {column} must contain integers.")
    if frame.duplicated(subset=["id", "vertex_part", "vertex_part_index"]).any():
        raise ValueError(f"{filename}: duplicate vertex_part_index in a route part.")

    # Case-insensitive exact-name lookup (QGIS writes upper-case X/Y/Z for XYZ).
    available = {column.lower(): column for column in frame.columns}
    elevation_col = next((available[key] for key in ELEVATION_COLUMNS if key in available), None)
    if elevation_col is None:
        frame["_imported_z_m"] = 0.0
        frame["_imported_z_missing"] = True
    else:
        original = frame[elevation_col].astype("string").str.strip()
        absent = original.isna() | original.str.lower().isin(EMPTY_ELEVATIONS).fillna(True)
        converted = pd.to_numeric(original.where(~absent), errors="coerce")
        bad = ~absent & (~converted.map(math.isfinite).fillna(False))
        if bad.any():
            raise ValueError(
                f"{filename}: elevation column '{elevation_col}' contains invalid Z values "
                "(expected numeric metres or blank/NULL)."
            )
        frame["_imported_z_m"] = converted.fillna(0.0).astype(float)
        frame["_imported_z_missing"] = absent.astype(bool)
    if not frame["_imported_z_m"].between(-500, 5000).all():
        raise ValueError(f"{filename}: elevation Z must be between -500 and 5,000 metres.")

    routes: list[ImportedRoute] = []
    for csv_id, group in frame.groupby("id", sort=False):
        parts: list[tuple[tuple[float, float], ...]] = []
        z_parts: list[tuple[float, ...]] = []
        # Sort by the geometry part and local part-index, not arbitrary CSV row order.
        for _, part in group.groupby("vertex_part", sort=True):
            ordered = part.sort_values(["vertex_part_index", "vertex_index"], kind="stable")
            vertices = tuple((float(row.X), float(row.Y)) for row in ordered.itertuples())
            if len(vertices) < 2:
                raise ValueError(f"{filename}: route {csv_id} has a part with fewer than two vertices.")
            if any(math.dist(a, b) <= 0.001 for a, b in zip(vertices, vertices[1:])):
                raise ValueError(f"{filename}: route {csv_id} contains consecutive duplicate coordinates.")
            parts.append(vertices)
            z_parts.append(tuple(float(z) for z in ordered["_imported_z_m"]))
        name = ""
        if "Rety_Lumbr" in group.columns:
            names = group["Rety_Lumbr"].dropna().astype(str).str.strip()
            names = names[names.ne("")]
            if not names.empty:
                name = names.iloc[0]
        routes.append(
            ImportedRoute(
                key=f"{filename}::{csv_id}",
                filename=filename,
                csv_id=str(csv_id),
                name=name or f"Route {csv_id}",
                parts=tuple(parts),
                z_parts=tuple(z_parts),
                elevation_column=elevation_col,
                missing_z_count=int(group["_imported_z_missing"].sum()),
                observed_z_count=int((~group["_imported_z_missing"]).sum()),
            )
        )
    return routes


def distance_to_source(route: ImportedRoute, x: float, y: float) -> float:
    """Plan-view distance in metres to nearer route endpoint."""
    return min(math.dist(route.vertices[0], (x, y)), math.dist(route.vertices[-1], (x, y)))


def oriented_xyz_vertices(
    route: ImportedRoute, source_xy: tuple[float, float]
) -> tuple[list[tuple[float, float, float]], bool]:
    """Orient the full 3D vertex sequence from the endpoint nearest the source."""
    xyz = list(route.xyz_vertices)
    reverse = math.dist(route.vertices[-1], source_xy) < math.dist(route.vertices[0], source_xy)
    if reverse:
        xyz.reverse()
    return xyz, reverse


def via_points_for_source(
    route: ImportedRoute,
    source_xy: tuple[float, float],
    *,
    destination_xy: tuple[float, float] | None = None,
) -> tuple[list[dict[str, Any]], float, float, bool]:
    """Carry QGIS Z values into the hydraulic points, preserving route direction.

    Exact source/target XY duplicates are omitted because the solver adds those
    nodes itself. Callers should use the corresponding imported endpoint Z for
    their source/sink nodes, when available; otherwise elevations default to 0.
    """
    vertices, reversed_route = oriented_xyz_vertices(route, source_xy)
    source_gap_m = math.dist(source_xy, vertices[0][:2])
    destination_gap_m = math.dist(vertices[-1][:2], destination_xy) if destination_xy else float("nan")
    if source_gap_m <= 0.001:
        vertices.pop(0)
    if destination_xy is not None and vertices and math.dist(vertices[-1][:2], destination_xy) <= 0.001:
        vertices.pop()
    vertices = [
        point for idx, point in enumerate(vertices)
        if idx == 0 or math.dist(point[:2], vertices[idx - 1][:2]) > 0.001
    ]
    via = [
        {
            "order": index,
            "label": f"CSV {route.csv_id} · {index}",
            "x_l93_m": x,
            "y_l93_m": y,
            "z_m": z,
        }
        for index, (x, y, z) in enumerate(vertices, 1)
    ]
    return via, source_gap_m, destination_gap_m, reversed_route
