# Version 0.6 interactive technology upgrade

Version 0.6 makes capture and purification configurable source by source while keeping one integrated calculation from source emissions to CO₂ received at Dunkerque.

## New user controls

For every selected source, the Streamlit sidebar now provides:

- a sector-compatible capture-technology selector;
- an adjustable CO₂ capture efficiency bounded by that technology's configured range;
- an independent purification-technology selector;
- adjustable purification recovery, product CO₂ purity and H₂O target;
- advanced O₂, NOₓ, SOₓ and CO targets;
- visible technology-readiness and hazard categories.

`config/technologies.toml` is the shared source for both the interface and calculation engine. The interface therefore cannot offer a choice that the engine evaluates with a different assumption set.

## Dynamic propagation

On **Run selected scenario**, the model recalculates:

1. source CO₂ captured and purification losses;
2. technology- and target-dependent CAPEX, fixed O&M, variable OPEX, electricity and steam;
3. energy-related emissions, lifecycle burden and net CO₂ avoided;
4. product-quality compliance and qualitative process-safety flags;
5. flow-weighted CO₂/N₂/O₂/Ar composition for the Peng–Robinson EOS;
6. total mixture mass flow, density, velocity, pressure loss, diameter and network cost;
7. executive gates and Decision lab indicators.

Target severity is interpolated within configured ranges. The model rejects values outside those ranges rather than extrapolating silently.

## Interpretation of low-purity cases

Low-purity or high-impurity cases remain calculable to support trade-off comparison. They are explicitly marked when they miss the external six-component product benchmark or require a detailed multicomponent phase-envelope review. Their presence in a comparison is not a statement of receiver acceptance.

## Verification

The regression suite covers base-case preservation, independent technology selection, 90% versus 98% capture behavior, 95% versus 99.95% purity behavior, dynamic EOS composition/density, cost and energy propagation, quality/safety flags and rejection of out-of-range targets.
