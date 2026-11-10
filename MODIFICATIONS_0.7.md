# Version 0.7 — pipeline trajectory implementation

## Interface workflow (updated v0.7.2)

1. Open **3 Pipeline trajectory** and upload one or more QGIS vertex CSVs.
2. Check the automatically detected route IDs, names, order and multipart parts.
3. Associate each active model source with one imported route. Sources close to route ends are suggested automatically.
4. Preview the route geometry. Optionally set downstream connections and existing/new cost status.
5. Review source/end connectors and multipart gaps; confirm those screening assumptions.
6. Click **Apply imported trajectories and run**. Use **Use automatic network** to revert.

The manual coordinate editor and per-point Z-entry controls have been removed. A QGIS Z column or an accepted elevation field is imported automatically;
missing Z values default to 0 m. Long direct
connectors to source or sink are explicitly shown and require user acknowledgement.
You can export the processed route configuration as JSON.

## Calculation propagation

- Source-to-route dependencies are checked for missing points, invalid Lambert-93 coordinates, duplicate points and cycles.
- A source connected to another route continues through that route to the sink.
- Shared segment flow is the sum of all source paths that use the segment.
- Segment length is calculated in three dimensions from `X/Y/Z`.
- The Peng–Robinson EOS provides density and compressibility for the selected product blend.
- Darcy–Weisbach friction and hydrostatic elevation head are combined in the net pressure change.
- Standard diameters are selected against maximum velocity, minimum pressure anywhere in the network and maximum design pressure.
- Updated segment length and flow propagate into CAPEX, O&M, steel mass, leakage, tonne-kilometres, construction burden, lifecycle indicators, maps and downloads.

## Existing-pipeline switch

Unchecking a route's cost box does not delete it from the model. The route still carries flow and contributes to:

- physical length and shared-flow aggregation;
- velocity, friction, elevation head and pressure limits;
- pipeline leakage;
- operating tonne-kilometres and use-phase environmental burden.

The route is excluded from:

- construction CAPEX and annualized capital;
- fixed pipeline O&M in the project case;
- the source connection allowance;
- new-project steel and material embodied carbon;
- pipeline construction LCA.

This represents an available sunk asset with no tariff. If an owner charges a transport tariff or refurbishment is required, that commercial cost must be entered in a later extension.

## Compatibility

The v0.6 automatic least-cost network remains the default. Selecting **Use automatic network** restores the original topology enumeration and route-factor method without deleting imported trajectory data.
