# Process-linked capture, purification and transport methods

## 1. Calculation modes and boundary

Version 0.8.0 contains two selectable calculation paths:

- `process_linked` is the default. It calculates a wet capture product, transmits its CO₂ flow, component composition, temperature and pressure to purification, and transmits the achieved purified composition and flow to pipeline transport.
- `screening` preserves the v0.7.3 reference-coefficient calculation for regression and sensitivity comparison.

The system boundary is capture → purification and compression to 110 bar → pipeline transport to the Port of Dunkerque receiving site. Liquefaction, shipping, injection and geological storage are excluded. Capture does not contain product compression. Purification contains the only source-to-pipeline compression duty. Pipeline transport starts at the configured inlet pressure and therefore does not duplicate compression CAPEX, power or emissions.

## 2. Source and technology mapping

The defaults are source-specific and remain independently selectable in the interface.

| Source | Default capture family | Default purification family |
|---|---|---|
| S1 · Réty lime | Cryocap FG cryogenic flue-gas separation | Dehydration, molecular-sieve polishing and compression |
| S2 · Auneuil gypsum/plaster | 30 wt-% MEA post-combustion absorption | Knockout, dehydration, polishing, deoxygenation and compression |
| S3 · Lumbres cement | Oxyfuel with Cryocap Oxy | Deep dehydration, cryogenic polishing and compression |
| S4 · Aluminium Dunkerque | Dilute-gas MEA absorption | Enhanced dehydration, impurity polishing and compression |
| S5 · ArcelorMittal Dunkerque | DMX demixing-solvent absorption on the capturable stream | Dehydration, non-condensable removal and compression |

`config/process_sources.toml` contains the source-side gas defaults. These entries are explicitly labelled engineering screening proxies, not plant assays. The Streamlit controls allow CO₂, H₂O, O₂, SOₓ, NOₓ and CO to be changed per source. The model rejects a composition whose specified components reach or exceed 100 mol-%.

## 3. Capture mass balance

For source \(s\), annual captured CO₂ is

\[
M_{cap,s}=M_{basis,s}\,f_{capturable,s}\,\eta_{cap,s}\,A_s
\]

where \(M_{basis}\) is the selected emissions basis, \(f_{capturable}\) is the fraction of total site emissions in an eligible process stream, \(\eta_{cap}\) is separation efficiency and \(A\) is availability. This distinction explains, for example, why S5 can have a 90% separation efficiency while capturing much less than 90% of total steelworks emissions: only 35% of the site inventory is assigned to the selected capturable stream.

### 3.1 MEA-family energy and consumables

MEA equations are used only for `mea_absorption`. The solvent flow per tonne captured follows the cyclic loading balance

\[
m_{solution}=\frac{(1000/MW_{CO_2})MW_{MEA}}{w_{MEA}\,\Delta\alpha}
\]

with 30 wt-% MEA by default. The reboiler duty is

\[
Q_{reb}=Q_{reaction}+m_{solution}C_{p,sol}\Delta T(1-\varepsilon_{HX})+Q_{water}
\]

followed by a configurable heat-loss allowance. The reference heat of absorption is 84 kJ/mol CO₂ and rich/lean exchanger effectiveness is 0.78. Cyclic capacity is reduced at very high capture efficiency, increasing solvent circulation and heat duty.

Blower work is calculated from the wet flue-gas molar flow, absorber pressure drop and blower efficiency:

\[
W_{blower}=\frac{nRT\ln(P_2/P_1)}{\eta_b}
\]

and solvent pump work is calculated from solvent volume, pressure rise and pump efficiency. Solvent degradation is

\[
m_{MEA,makeup}=1.5+0.30\,y_{O_2,vol\%}+0.002\,C_{SOx,ppmv}
\quad \mathrm{kg/tCO_2}.
\]

This reproduces Papa's reference order of magnitude while remaining responsive to each source composition. DMX, Cryocap and oxyfuel technologies do not use the MEA circulation, reboiler or degradation equations.

### 3.2 Non-MEA families

Cryogenic, oxyfuel, DMX and other non-MEA families retain technology-specific reference duties. Capture-efficiency response follows a reversible-separation severity based on \(-\ln(1-\eta)\), with a configurable fixed-energy share for loads that do not scale strongly with recovery. Feed concentration affects gas-handling energy and CAPEX through transparent exponents. These are screening-level technology-family equations, not detailed vendor simulations.

### 3.3 Wet capture product

For absorption families, each dry impurity accompanying regenerated CO₂ is calculated from its inlet molar ratio, a species-specific transfer/desorption factor and capture efficiency. Water is set by the condenser approach to saturation at the capture-product temperature and pressure. The resulting stream contains CO₂, H₂O, N₂, O₂, Ar, NOₓ, SOₓ, CO and, for MEA, a trace solvent concentration. Non-absorption technologies use configurable raw-product compositions. The wet product is not replaced by the final pipeline target before purification.

## 4. Purification model

### 4.1 Connected component balance

Captured CO₂ enters purification without an intermediate rescaling. Product CO₂ is

\[
M_{CO_2,out}=M_{CO_2,in}\,\eta_{pur}.
\]

For every modelled impurity, output moles cannot exceed inlet moles. Removed material is assigned to condensate, off-gas or spent-treatment side streams. The reported balance is

\[
\epsilon=\frac{n_{feed}-n_{product}-n_{side}}{n_{feed}}.
\]

If a user selects 95 mol-% CO₂ together with 20 ppmv H₂O and very low trace limits, the specified components may not sum to a physically attainable product using the available feed. The model does not create N₂ to fill the gap: it reports the achievable, purer composition and flags the selected target as infeasible.

### 4.2 Knockout and dehydration

Bulk water is condensed before deep dehydration. The water reaching TEG or molecular sieve is limited by saturation at the configured dryer inlet temperature and pressure:

\[
y_{H_2O,sat}=P_{sat,H_2O}(T)/P.
\]

Only water remaining after cooling/interstage knockout receives the adsorption or solvent-regeneration duty. The method prevents the common error of applying molecular-sieve regeneration heat to all water present in the wet capture product.

### 4.3 Multistage compression

Compression from the capture outlet to the 110 bar pipeline inlet is calculated once, in purification. For \(N\) equal-pressure-ratio stages with intercooling,

\[
w=\frac{N}{\eta_s}\frac{k}{k-1}R_{mix}T_{in}
\left[r_s^{(k-1)/k}-1\right],
\qquad r_s=(P_{out}/P_{in})^{1/N}.
\]

Mixture molecular weight and CO₂ mass fraction convert mixture work to kWh per tonne of product CO₂. Default efficiency is 0.78. Cryogenic trains add refrigeration; membrane and non-condensable-removal trains add technology-family separation power.

### 4.4 Thermal, cooling and consumables

Thermal demand includes residual dryer regeneration, bed/solvent inventory heating where configured, and catalytic deoxygenation preheat. Cooling includes capture-feed cooling, compression intercooling and train-specific heat rejection. Deoxygenation consumes stoichiometric hydrogen for removed O₂. Adsorbent or guard replacement is calculated separately from utilities.

## 5. Cost model

Each stage uses a reference installed CAPEX and capacity:

\[
C=C_{ref}\left(\frac{Q}{Q_{ref}}\right)^n F_{process}.
\]

Capture includes a gas-handling factor based on source CO₂ concentration and capture efficiency. Purification separates the treatment and compression shares so pressure ratio and feed dilution affect the appropriate equipment. Annualized CAPEX uses

\[
CRF=\frac{i(1+i)^N}{(1+i)^N-1}.
\]

Annual cost is annualized CAPEX + fixed O&M + electricity + steam/thermal energy + cooling + solvent/water/hydrogen/sorbent costs + other variable O&M. Specific capture cost is reported per tonne captured and per tonne of purified product; purification and full-chain costs are reported per tonne of CO₂ product or received at the sink. The user can change energy prices, discount rate and project life.

## 6. Environmental calculation

Utility emissions use the configured French electricity and steam factors. Process-linked mode additionally includes screening burdens for solvent, water, hydrogen, sorbent replacement and annualized equipment. Pipeline leakage, use-phase tonne-kilometres, construction and material-sensitive embodied carbon remain separate. The environmental total avoids double counting baseline pipeline construction and material deltas.

## 7. Transport handoff and EOS

The achieved purification products are mixed on a dry molar basis. H₂O is removed from the EOS mixture; dry trace species not explicitly present in the four-component transport property package are conservatively represented in the N₂ pseudo-component. The Peng–Robinson EOS calculates mixture compressibility and density with classical mixing and \(k_{ij}=0\). Darcy–Weisbach hydraulics, elevation effects, diameter selection, user-imported QGIS trajectories, existing-pipeline cost exclusion and material screens are unchanged from v0.7.3.

## 8. Reference sources used in the implementation

The equations and default ranges were traced through Papa's preserved local packages, including their reference registers. Principal sources include:

- Jou, Otto & Mather (1994), aqueous MEA/MDEA CO₂ VLE: <https://www.osti.gov/biblio/6905095>
- Kim, Hoff & Mejdell (2014), heat of absorption in MEA: <https://www.sciencedirect.com/science/article/pii/S1876610214019699>
- Abu-Zahra et al. (2007), MEA capture process study: <https://doi.org/10.1016/S1750-5836(06)00007-7>
- IEAGHG 2014-04, CO₂ dehydration units: <https://ieaghg.org/publications/evaluation-and-analysis-of-the-performance-of-dehydration-units-for-co2-capture/>
- IEAGHG 2016-01, CO₂ impurities: <https://ieaghg.org/publications/co2-impurities/>
- Abbas et al. (2013), deep-removal technology selection: <https://doi.org/10.1016/j.ijggc.2013.01.053>
- Chen et al. (2021), TEG dehydration for pipeline transport: <https://doi.org/10.1016/j.cjche.2020.12.025>
- Carvalho et al., fixed-bed dehydration with 4A molecular sieve: <https://doi.org/10.4025/actascitechnol.v45i1.58764>
- Berstad et al. (2013), low-temperature CO₂ capture: <https://doi.org/10.1016/j.ijrefrig.2013.03.017>
- NETL QGESS capital-cost scaling: <https://www.osti.gov/biblio/1893821>
- RTE annual electricity review 2024: <https://analysesetdonnees.rte-france.com/en/annual-review-2024/keyfindings>
- ADEME Base Carbone V23: <https://data.ademe.fr/datasets/base-carboner>

## 9. Appropriate use

This is a transparent process-linked engineering and pre-FEED model. It is suitable for internally consistent scenario comparison, sensitivity analysis, source ranking and identification of data that materially change the cluster result. Source assays, dynamic operation, detailed column design, full phase envelopes with validated binary-interaction parameters, corrosion/fracture assessment, vendor quotations and receiver contractual specifications remain external engineering inputs.
