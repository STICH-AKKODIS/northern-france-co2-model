# Three-stage scenario report: `announced_2030`

Project-backed CalCC and K6 flows delivered to the Port of Dunkerque receiving site.

| Headline metric | Result |
|---|---:|
| CO₂ captured | 1.417 Mt/y |
| CO₂ purified to pipeline specification | 1.410 Mt/y |
| CO₂ received at Port of Dunkerque | 1.410 Mt/y |
| Net CO₂ avoided within model boundary | 1.383 Mt/y |
| Three-stage CAPEX | €618.0 m |
| Base levelized cost | €82.2/t received |
| Screening cost range | €59.8–104.5/t received |

## 1. Capture

Capture CAPEX: **€400.0 m**. Annualized capture cost: **€53.7/t received**.

| ID | Source | Emissions basis (kt/y) | Captured (kt/y) | Technology | Capture rate | Availability |
|---|---|---:|---:|---|---:|---:|
| S1 | Chaux et Dolomies du Boulonnais | 693.2 | 613.1 | Cryocap FG cryogenic separation | 95.0% | 95.0% |
| S2 | ETEX France Building Performance | 0.0 | 0.0 | Post-combustion amine absorption | 90.0% | 90.0% |
| S3 | EQIOM Lumbres cement plant | 989.2 | 804.0 | Oxyfuel process with Cryocap Oxy separation | 92.0% | 93.0% |
| S4 | Aluminium Dunkerque | 0.0 | 0.0 | Low-concentration flue-gas amine capture | 85.0% | 85.0% |
| S5 | ArcelorMittal Dunkerque steelworks | 0.0 | 0.0 | DMX demixing-solvent absorption | 90.0% | 90.0% |

## 2. Purification

Purification CAPEX: **€98.4 m**. Annualized purification cost: **€20.2/t received**.

| ID | Captured feed (kt/y) | Product (kt/y) | Recovery | CO₂ purity | H₂O | Screened specification |
|---|---:|---:|---:|---:|---:|---|
| S1 | 613.1 | 610.0 | 99.5% | 99.99 mol-% | 20 ppmv | Pass |
| S2 | 0.0 | 0.0 | 99.5% | 99.90 mol-% | 20 ppmv | Pass |
| S3 | 804.0 | 800.0 | 99.5% | 99.95 mol-% | 20 ppmv | Pass |
| S4 | 0.0 | 0.0 | 99.5% | 99.90 mol-% | 20 ppmv | Pass |
| S5 | 0.0 | 0.0 | 99.5% | 99.90 mol-% | 20 ppmv | Pass |

## 3. Transport to the sink site

Pipeline CAPEX: **€119.5 m**. Annualized transport cost: **€8.3/t received**.

The optimized screening network contains 2 segments, totals 93.8 km, starts at 110 bar and reaches Dunkerque at no less than 90.3 bar.

Transport properties are calculated with the **Peng-Robinson equation of state** at 35.0 °C. PR density and compressibility are evaluated iteratively at the representative mean pressure of each segment.

Selected material screen: **Carbon steel X65 · reference**; calculated pipe steel **3.2 kt**; wall range **6.7–6.7 mm**.

| From | To | Route (km) | Flow (Mt/y) | Diameter | Wall (mm) | Density (kg/m³) | Z | Velocity (m/s) | ΔP (bar) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| S3 | Sink | 45.3 | 0.800 | DN 200 | 6.7 | 651.3 | 0.2640 | 1.36 | 19.74 |
| S1 | Sink | 48.5 | 0.610 | DN 200 | 6.7 | 668.4 | 0.2671 | 1.01 | 12.06 |

## 4. Environmental study

Assessment year: **2030**. The screening layer combines capture/purification energy emissions, direct pipeline leakage, and lifecycle transport factors based on annual tonne-kilometres.

| Environmental metric | Result |
|---|---:|
| Total electricity demand | 544.7 GWh/y |
| Capture steam demand | 0.0 TJ/y |
| Direct pipeline leakage | 131.6 t CO₂/y |
| Pipeline use-phase climate burden | 197.4 t CO₂-eq/y |
| Pipeline construction climate burden | 79.0 t CO₂-eq/y |
| Selected pipe-material embodied carbon | 7,004.4 t CO₂-eq total inventory |
| Annualized material delta versus X65 | 0.0 t CO₂-eq/y |
| Total modeled climate burden | 27,641.9 t CO₂-eq/y |
| Lifecycle net CO₂ avoided | 1.382 Mt/y |
| Climate burden intensity | 19.6 kg CO₂-eq/t received |
| Net avoidance efficiency | 98.0% |

### Transport climate benchmark

| Alternative mode | Mode intensity (g CO₂-eq/tkm) | Pipeline incl. construction | Pipeline reduction |
|---|---:|---:|---:|
| Truck (diesel) | 148.5 | 4.2 | 97.2% |
| Truck (electric) | 139.5 | 4.2 | 97.0% |
| Truck (H2) | 144.0 | 4.2 | 97.1% |
| Barge (diesel) | 88.2 | 4.2 | 95.2% |
| Train (electric) | 64.8 | 4.2 | 93.5% |

**Environmental scope note.** This is a screening climate/energy study, not an ISO-compliant project LCA. A routed corridor is required before quantifying biodiversity, land occupation, water, crossings, construction disturbance, noise or local air-quality impacts.

---

**Model boundary.** The calculation ends when pipeline-quality CO₂ reaches the Port of Dunkerque coordinates supplied for this study. Liquefaction, buffer storage, ship loading, shipping, geological injection and storage are excluded.

**Precision statement.** Results are deterministic screening estimates in 2026 euros. The displayed range applies maturity-based uncertainty to capture/purification costs and ±35% to routed pipeline cost; it is not a statistical confidence interval. Six product components are screened, but a complete vendor assay and receiving specification are required before FEED.
