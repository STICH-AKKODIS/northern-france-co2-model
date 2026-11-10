"""CSV parser regression tests; no Streamlit dependency."""

import unittest
from pathlib import Path

from north_co2_model.trajectory_import import (
    distance_to_source,
    parse_route_csv,
    oriented_xyz_vertices,
    via_points_for_source,
)


HEADER = "X,Y,id,Rety_Lumbr,vertex_index,vertex_part,vertex_part_index,distance,angle\n"


class TrajectoryCSVImportTests(unittest.TestCase):
    def test_multi_route_multipart_and_unsorted_csv(self) -> None:
        rows = (
            "636000,7071000,3,GOCO2,1,0,1,100,5\n"
            "613500,7079000,1,dartagnan,0,0,0,0,0\n"
            "637000,7070000,3,GOCO2,0,0,0,0,5\n"
            "615000,7080000,1,dartagnan,1,0,1,100,20\n"
            "615100,7080100,1,dartagnan,2,1,0,150,25\n"
            "616000,7081000,1,dartagnan,3,1,1,300,30\n"
        )
        routes = parse_route_csv((HEADER + rows).encode(), "routes.csv")
        self.assertEqual([r.csv_id for r in routes], ["3", "1"])
        self.assertEqual(routes[0].vertices[0], (637000.0, 7070000.0))
        self.assertEqual(routes[1].name, "dartagnan")
        self.assertEqual(len(routes[1].parts), 2)
        self.assertAlmostEqual(routes[1].part_gaps_km[0], 0.1414213562, places=7)

    def test_reverses_route_to_nearest_source_and_strips_exact_sink(self) -> None:
        csv = (HEADER +
            "636000,7105000,2,R,0,0,0,0,0\n"
            "637000,7100000,2,R,1,0,1,0,0\n"
            "637500,7099000,2,R,2,0,2,0,0\n"
        )
        route = parse_route_csv(csv.encode(), "test.csv")[0]
        via, source_gap, sink_gap, reversed_route = via_points_for_source(
            route, (637500, 7099000), destination_xy=(636000, 7105000)
        )
        self.assertTrue(reversed_route)
        self.assertAlmostEqual(source_gap, 0.0)
        self.assertAlmostEqual(sink_gap, 0.0)
        self.assertEqual(len(via), 1)
        self.assertEqual((via[0]["x_l93_m"], via[0]["y_l93_m"]), (637000, 7100000))
        self.assertEqual(via[0]["z_m"], 0.0)
        self.assertEqual(distance_to_source(route, 637500, 7099000), 0.0)

    def test_qgis_xyz_elevations_are_preserved_when_sorted_and_reversed(self) -> None:
        # QGIS AS_XYZ places Z alongside X/Y; vertex indexing overrides row order.
        xyz_header = HEADER.replace("X,Y,id,", "X,Y,Z,id,")
        csv = (xyz_header +
            "636000,7105000,5,2,threeD,2,0,2,0,0\n"
            "637000,7103000,65,2,threeD,0,0,0,0,0\n"
            "636500,7104000,125,2,threeD,1,0,1,0,0\n"
        )
        route = parse_route_csv(csv.encode(), "qgis_3d.csv")[0]
        self.assertEqual(route.elevation_column, "Z")
        self.assertTrue(route.has_elevation)
        self.assertEqual(route.observed_z_count, 3)
        self.assertEqual([p[2] for p in route.xyz_vertices], [65, 125, 5])
        oriented, reversed_route = oriented_xyz_vertices(route, (636000, 7105000))
        self.assertTrue(reversed_route)
        self.assertEqual([p[2] for p in oriented], [5, 125, 65])
        via, source_gap, _, _ = via_points_for_source(
            route, (636000, 7105000), destination_xy=(637000, 7103000)
        )
        self.assertEqual(source_gap, 0.0)
        self.assertEqual(len(via), 1)
        self.assertEqual(via[0]["z_m"], 125)
        self.assertGreater(route.length_km, sum(
            __import__('math').dist(a, b)
            for a, b in zip(route.vertices, route.vertices[1:])
        ) / 1000)

    def test_2d_csv_and_null_elevations_default_to_zero(self) -> None:
        plain = parse_route_csv((HEADER +
            "637000,7100000,7,a,0,0,0,0,0\n"
            "636000,7105000,7,a,1,0,1,0,0\n"
        ).encode(), "2d.csv")[0]
        self.assertFalse(plain.has_elevation)
        self.assertEqual([p[2] for p in plain.xyz_vertices], [0.0, 0.0])
        xyz = parse_route_csv((HEADER.replace("X,Y,id,", "X,Y,z_m,id,") +
            "637000,7100000,80,7,a,0,0,0,0,0\n"
            "636000,7105000,NULL,7,a,1,0,1,0,0\n"
        ).encode(), "mixed.csv")[0]
        self.assertTrue(xyz.has_elevation)
        self.assertEqual(xyz.missing_z_count, 1)
        self.assertEqual([p[2] for p in xyz.xyz_vertices], [80, 0])

    def test_bad_elevation_is_rejected_instead_of_ignored(self) -> None:
        header = HEADER.replace("X,Y,id,", "X,Y,Z,id,")
        malformed = (header +
            "637000,7100000,200,7,a,0,0,0,0,0\n"
            "636000,7105000,not_a_number,7,a,1,0,1,0,0\n"
        )
        with self.assertRaisesRegex(ValueError, "invalid Z"):
            parse_route_csv(malformed.encode(), "invalid_z.csv")
        high = malformed.replace("not_a_number", "6000")
        with self.assertRaisesRegex(ValueError, "between -500 and 5,000"):
            parse_route_csv(high.encode(), "impossible.csv")

    def test_xyz_multipart_respects_part_indices(self) -> None:
        xyz_header = HEADER.replace("X,Y,id,", "X,Y,Z,id,")
        csv = (xyz_header +
            "637000,7100000,10,7,multi,0,0,0,0,0\n"
            "637100,7100100,15,7,multi,1,0,1,0,0\n"
            "637200,7100200,20,7,multi,2,1,0,0,0\n"
            "637300,7100300,25,7,multi,3,1,1,0,0\n"
        )
        route = parse_route_csv(csv.encode(), "multi_xyz.csv")[0]
        self.assertEqual([p[2] for p in route.xyz_vertices], [10, 15, 20, 25])
        self.assertEqual(len(route.parts), 2)
        self.assertGreater(route.part_gaps_km[0], 0)
        via, _, _, _ = via_points_for_source(
            route, (637000, 7100000), destination_xy=(637300, 7100300)
        )
        self.assertEqual([point["z_m"] for point in via], [15.0, 20.0])

    def test_qgis_elevation_reaches_actual_hydraulic_solver(self) -> None:
        from north_co2_model.model import load_model_inputs, run_custom_scenario

        inputs = load_model_inputs(Path(__file__).resolve().parents[1])
        source = next(s for s in inputs.sources if s.source_id == "S1")
        sink = inputs.config["sink"]
        coordinates = [
            (source.x_l93_m, source.y_l93_m, 100.0),
            (625000.0, 7090000.0, 190.0),
            (sink["x_l93_m"], sink["y_l93_m"], 5.0),
        ]
        csv = ("X,Y,Z,id,Rety_Lumbr,vertex_index,vertex_part,vertex_part_index,distance,angle\n"
            + "".join(
                f"{x},{y},{z},1,Test,{i},0,{i},0,0\n"
                for i, (x, y, z) in enumerate(coordinates)
            )
        )
        route = parse_route_csv(csv.encode(), "integration_xyz.csv")[0]
        oriented, _ = oriented_xyz_vertices(route, (source.x_l93_m, source.y_l93_m))
        via, _, _, _ = via_points_for_source(
            route, (source.x_l93_m, source.y_l93_m),
            destination_xy=(sink["x_l93_m"], sink["y_l93_m"]),
        )
        self.assertEqual([p["z_m"] for p in via], [190.0])
        payload = {
            "enabled": True,
            "sink_z_m": oriented[-1][2],
            "routes": {"S1": {
                "source_z_m": oriented[0][2],
                "destination": "SINK",
                "via_points": via,
            }},
        }
        three_d = run_custom_scenario(
            inputs, active_source_ids=["S1"], flow_basis="irep_2024_total",
            sink_capacity_tpy=1_500_000, trajectory_overrides=payload,
        )
        self.assertEqual(three_d.summary["transport_network_mode"], "user_defined_trajectory")
        self.assertEqual([s["elevation_change_m"] for s in three_d.pipeline_segments], [90, -185])
        self.assertTrue(any(
            abs(s["elevation_pressure_change_bar"]) > 0.1
            for s in three_d.pipeline_segments
        ))
        payload["sink_z_m"] = 0
        payload["routes"]["S1"]["source_z_m"] = 0
        payload["routes"]["S1"]["via_points"][0]["z_m"] = 0
        flat = run_custom_scenario(
            inputs, active_source_ids=["S1"], flow_basis="irep_2024_total",
            sink_capacity_tpy=1_500_000, trajectory_overrides=payload,
        )
        self.assertTrue(all(
            abs(s["elevation_pressure_change_bar"]) < 1e-6
            for s in flat.pipeline_segments
        ))

    def test_rejects_wrong_crs_and_missing_columns(self) -> None:
        csv = (HEADER +
            "2.3,51.0,1,route,0,0,0,0,0\n"
            "2.4,51.1,1,route,1,0,1,0,0\n"
        )
        with self.assertRaisesRegex(ValueError, "Lambert-93"):
            parse_route_csv(csv.encode(), "degrees.csv")
        with self.assertRaisesRegex(ValueError, "missing required columns"):
            parse_route_csv(b"X,Y,id\n1,2,3\n", "invalid.csv")

    def test_rejects_duplicate_vertices_and_parts(self) -> None:
        csv = (HEADER +
            "636000,7071000,1,r,0,0,0,0,0\n"
            "637000,7072000,1,r,1,0,0,0,0\n"
        )
        with self.assertRaisesRegex(ValueError, "duplicate vertex_part_index"):
            parse_route_csv(csv.encode(), "dup.csv")


if __name__ == "__main__":
    unittest.main()
