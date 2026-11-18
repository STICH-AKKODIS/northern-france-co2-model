import io

from dataclasses import dataclass

from fpdf import FPDF, FontFace
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
from streamlit import pdf


from north_co2_model.model import ScenarioResult




PDF_COLORS = {
    "ink": "#102235",
    "muted": "#64748B",
    "capture": "#176B87",
    "purification": "#17A398",
    "transport": "#E59A31",
    "inactive": "#CBD5E1",
}



@dataclass
class PDF_REPORT_INPUT:
    truc = True # TODO Rework class definition



class PDF(FPDF):
    def header(self):
        # Rendering logo:
        self.image("docs/STICH_Logo.png", 10, 8, 33)
        self.image("docs/AKKODIS_Logo.png", 170, 8, 33)
        # Setting font: Times bold 15
        self.set_font("Times", style="B", size=15)

        # Printing title:
        self.set_font("Times", style="B", size=15)
        width = self.get_string_width(self.title) + 6
        self.set_x((210 - width) / 2)
        self.cell(
            width,
            9,
            self.title,
            border=1,
            new_x="LMARGIN",
            new_y="NEXT",
            align="C",
        )
        # Performing a line break:
        self.ln(20)

    def footer(self):
        # Position cursor at 1.5 cm from bottom:
        self.set_y(-15)
        # Setting font: Times italic 8
        self.set_font("Times", style="I", size=8)
        # Printing creation date:
        self.cell(0, 10, f"Created on {self.creation_date.strftime('%d/%m/%Y %H:%M:%S')}", align="L")
        # Printing page number:
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="R")

    
def generate_pdf_section_capture(pdf : PDF, pdf_data : PDF_REPORT_INPUT) -> None:
    """ Function to generate the capture part of the STICH reporting """
    print(f"[PDF] Capture generation section")

    pdf.add_page()
    pdf.set_font("NotoSerif", size=18)
    # Section title
    pdf.multi_cell(0, 5, f"Capture section", 
                   new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    # Section description
    pdf.set_font("NotoSerif", "", size=11)
    pdf.write_html(
        """
        <p align="justify">
        <b>What happen here:</b>
        eligible flue-gas streams are selected, CO₂ is separated using a
        source-specific technology, and annual plant availability is applied.
        Capture excludes later dehydration, polishing and compression.
        </p>
        """
    )    
    pdf.ln(8)

    # Note : possible refactoring with app.py with have the same graph

    # Add the capture vs emissions bar-graph (each site represented)
    fig_capture = go.Figure()
    fig_capture.add_trace(go.Bar(name="Emissions basis", x=pdf_data.capture_df["ID"], y=pdf_data.capture_df["Emissions basis (kt/y)"], marker_color="#B6C4CF"))
    fig_capture.add_trace(go.Bar(name="Captured", x=pdf_data.capture_df["ID"], y=pdf_data.capture_df["Captured (kt/y)"], marker_color=PDF_COLORS["capture"]))
    fig_capture.update_layout(
        barmode="group",
        height=335,
        margin={"l": 50, "r": 20, "t": 35, "b": 40},
        paper_bgcolor="white",
        plot_bgcolor="white",
        yaxis={"title": "kt CO₂/year", "gridcolor": "#E2E8F0"},
        legend={"orientation": "h", "y": 1.12},
    )
    # Convert the figure to png using kaleido
    image_data_capture = fig_capture.to_image(format="png", engine="kaleido")
    # Create an io.BytesIO object which can be used by FPDF2
    image = io.BytesIO(image_data_capture)
    pdf.image(image, w=pdf.epw)  # Width of the image is equal to the width of the page

    
    pdf.multi_cell(0, 5, f"Cost position", 
                   new_x="LMARGIN", new_y="NEXT")
    # Add the cost position bar-graph (capture-purification-transport)
    fig_cost = pdf_data.cost_figure
    fig_cost.update_layout(    #Already defined in creating fonction but may need changes between web page & pdf
        height=335,
        margin={"l": 50, "r": 20, "t": 30, "b": 40},
        paper_bgcolor="white",
        plot_bgcolor="white",
        yaxis={"title": "€/t received at sink", "gridcolor": "#E2E8F0", "rangemode": "tozero"},
        xaxis={"title": None},
        showlegend=False,
    )
    # Convert the figure to png using kaleido
    image_data_cost = fig_cost.to_image(format="png", engine="kaleido")
    # Create an io.BytesIO object which can be used by FPDF2
    image = io.BytesIO(image_data_cost)
    pdf.image(image, w=pdf.epw)  # Width of the image is equal to the width of the page


    # Detailed datas
    pdf.add_page()
    pdf.set_draw_color(0, 0, 0)
    pdf.set_line_width(0.3)
    headings_style = FontFace(emphasis="BOLD", color=255, fill_color=(180, 180, 180))
    # TODO : PDF Split the table in at least two table for lisibility
    
    with pdf.table(
        # borders_layout="NO_HORIZONTAL_LINES",
        # cell_fill_color=(224, 235, 255),
        # cell_fill_mode=TableCellFillMode.ROWS,
        col_widths=(8, 40, 15, 30, 20),
        headings_style=headings_style,
        line_height=6,
        # text_align=("LEFT"),
        width=190,
    ) as table:
        # Add table header
        pdf.set_font("NotoSerif", size=11)
        headerRow = table.row()
        headerRow.min_height = 8
        headerRow.cell("ID")
        headerRow.cell("Source")
        headerRow.cell("Sector")
        headerRow.cell("Capture technology")
        headerRow.cell("Maturity")

        
        #Add table content
        pdf.set_font("NotoSerif", size=10)
        for data_row in pdf_data.capture_df.to_dict(orient="records"):
            row = table.row()
            row.cell(str(data_row["ID"]))
            row.cell(str(data_row["Source"]))
            row.cell(str(data_row["Sector"]))
            row.cell(str(data_row["Capture technology"]))
            row.cell(str(data_row["Maturity"]))

    pdf.ln(8)   # vertical space between tables

    with pdf.table(
        # borders_layout="NO_HORIZONTAL_LINES",
        # cell_fill_color=(224, 235, 255),
        # cell_fill_mode=TableCellFillMode.ROWS,
        col_widths=(9, 26, 22, 20, 26, 24, 22, 22, 20, 20, 16, 20, 6),
        headings_style=headings_style,
        line_height=6,
        # text_align=("LEFT"),
        width=190,
    ) as table:
        # Add table header
        pdf.set_font("NotoSerif", size=8)
        headerRow = table.row()
        headerRow.min_height = 8
        headerRow.cell("ID")
        headerRow.cell("Emissions basis (kt/y)")
        headerRow.cell("Captured (kt/y)")
        headerRow.cell("Capture rate")
        headerRow.cell("Availability")
        headerRow.cell("Electricity (MWh/t captured)")
        headerRow.cell("Steam (GJ/t captured)")
        headerRow.cell("Cooling (GJ/t captured)")
        headerRow.cell("Solvent makeup (kg/t)")
        headerRow.cell("Wet product CO₂ (mol-%)")
        headerRow.cell("CAPEX (€m)")
        headerRow.cell("Cost (€/t product)")
        headerRow.cell("TRL")

        #Add table content
        pdf.set_font("NotoSerif", size=10)
        for data_row in pdf_data.capture_df.to_dict(orient="records"):
            row = table.row()
            row.cell(str(data_row["ID"]))
            row.cell(f"{data_row['Emissions basis (kt/y)']:.1f}")
            row.cell(f"{data_row['Captured (kt/y)']:.1f}")
            row.cell(f"{(data_row['Capture rate']*100):.0f}%")
            row.cell(f"{(data_row['Availability']*100):.0f}%")
            row.cell(f"{data_row['Electricity (MWh/t captured)']:.3f}")
            row.cell(f"{data_row['Steam (GJ/t captured)']:.2f}")
            row.cell(f"{data_row['Cooling (GJ/t captured)']:.2f}")
            row.cell(f"{data_row['Solvent makeup (kg/t)']:.2f}")
            row.cell(f"{data_row['Wet product CO₂ (mol-%)']:.3f}")
            row.cell(f"{data_row['CAPEX (€m)']:.1f}")
            row.cell(f"{data_row['Cost (€/t product)']:.1f}")
            row.cell(str(data_row["TRL"]))

    
    # Table results description and precisions
    pdf.set_font("NotoSerif", "", size=11)
    with pdf.offset_rendering() as dummy:
        my_html = """
            <p align="justify">
            <u><font size="12">How the capture result is calculated:</font></u>
            </p>

            <p align="justify">
            <b>Captured CO₂ = emissions basis × capturable fraction × capture rate × annual availability.</b>
            </p>
            
            <p align="justify">
            For MEA, the reboiler duty is the sum of reaction heat, residual sensible heat after the rich/lean exchanger,
            water vaporisation and heat loss.
            </p>

            <p align="justify">
            Blower and pump work are calculated from gas/solvent flow. Solvent degradation responds to O₂ and SOₓ.
            </p>

            <p align="justify">
            Cryogenic, oxyfuel and DMX routes use their own configured process families; MEA equations are not applied to them.
            </p>
            """
        dummy.write_html(my_html)

        if dummy.page_break_triggered:
            pdf.add_page()

        pdf.write_html(my_html)


def generate_pdf_section_purification(pdf : PDF, pdf_data : PDF_REPORT_INPUT) -> None:
    """ Function to generate the purification part of the STICH reporting """
    print(f"[PDF] Purification generation section")

    pdf.add_page()
    pdf.set_font("NotoSerif", size=18)
    # Section title
    pdf.multi_cell(0, 5, f"Purification section", 
                   new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    # Section description
    pdf.set_font("NotoSerif", "", size=11)
    pdf.write_html(
        """
        <p align="justify">
        <b>What happen here::</b>
        captured gas is dehydrated, polished for key impurities and compressed to the 110 bar pipeline inlet. Recovery losses, power, CAPEX and OPEX are accounted independently from capture.
        </p>
        """
    )    
    pdf.ln(8)

    # TODO add general metrics (purification)


    pdf.set_draw_color(0, 0, 0)
    pdf.set_line_width(0.3)
    headings_style = FontFace(emphasis="BOLD", color=255, fill_color=(180, 180, 180))
    
    # ==========================================================
    # Table 1 : General purification information
    # ==========================================================
    with pdf.table(
        col_widths=(8, 30, 40, 30, 35, 35, 20),
        headings_style=headings_style,
        line_height=4.5,
        width=190,
    ) as table:

        pdf.set_font("NotoSerif", size=9)

        headerRow = table.row()
        headerRow.min_height = 8
        headerRow.cell("ID")
        headerRow.cell("Source")
        headerRow.cell("Purification technology")
        headerRow.cell("Method")
        headerRow.cell("Selected target benchmark")
        headerRow.cell("Achieved-product benchmark")
        headerRow.cell("Safety screen")

        pdf.set_font("NotoSerif", size=10)

        for data_row in pdf_data.purification_df.to_dict(orient="records"):
            row = table.row()
            row.cell(str(data_row["ID"]))
            row.cell(str(data_row["Source"]))
            row.cell(str(data_row["Purification technology"]))
            row.cell(str(data_row["Method"]))
            row.cell(str(data_row["Selected-target benchmark"]))
            row.cell(str(data_row["Achieved-product benchmark"]))
            row.cell(str(data_row["Safety screen"]))

    pdf.ln(8)

    # ==========================================================
    # Table 2 : Product quality and safety
    # ==========================================================
    with pdf.table(
        col_widths=(10, 26, 24, 24, 21, 25, 21, 25, 19, 19, 19, 19),
        headings_style=headings_style,
        line_height=4.5,
        width=190,
    ) as table:

        pdf.set_font("NotoSerif", size=9)

        headerRow = table.row()
        headerRow.min_height = 10
        headerRow.cell("ID")
        headerRow.cell("Captured feed (kt/y)")
        headerRow.cell("Product (kt/y)")
        headerRow.cell("Recovery")
        headerRow.cell("Target CO₂ (mol-%)")
        headerRow.cell("Achieved CO₂ (mol-%)")
        headerRow.cell("Target H₂O (ppmv)")
        headerRow.cell("Achieved H₂O (ppmv)")
        headerRow.cell("O₂ (ppmv)")
        headerRow.cell("NOₓ (ppmv)")
        headerRow.cell("SOₓ (ppmv)")
        headerRow.cell("CO (ppmv)")

        pdf.set_font("NotoSerif", size=9)

        for data_row in pdf_data.purification_df.to_dict(orient="records"):
            row = table.row()
            row.cell(str(data_row["ID"]))
            row.cell(f'{data_row["Captured feed (kt/y)"]:.1f}')
            row.cell(f'{data_row["Product (kt/y)"]:.1f}')
            row.cell(f'{data_row["Recovery"]:.1%}')
            row.cell(f'{data_row["Target CO₂ (mol-%)"]:.3f}')
            row.cell(f'{data_row["Achieved CO₂ (mol-%)"]:.3f}')
            row.cell(f'{data_row["Target H₂O (ppmv)"]:.1f}')
            row.cell(f'{data_row["Achieved H₂O (ppmv)"]:.1f}')
            row.cell(f'{data_row["O₂ (ppmv)"]:.1f}')
            row.cell(f'{data_row["NOₓ (ppmv)"]:.1f}')
            row.cell(f'{data_row["SOₓ (ppmv)"]:.1f}')
            row.cell(f'{data_row["CO (ppmv)"]:.1f}')

    pdf.ln(8)


    # ==========================================================
    # Table 3 : Product quality and safety flags
    # ==========================================================
    with pdf.table(
        col_widths=(8, 30, 150),
        headings_style=headings_style,
        line_height=4.5,
        width=190,
    ) as table:

        pdf.set_font("NotoSerif", size=9)

        headerRow = table.row()
        headerRow.min_height = 10
        headerRow.cell("ID")
        headerRow.cell("Safety screen")
        headerRow.cell("Safety / quality flags")

        pdf.set_font("NotoSerif", size=9)

        for data_row in pdf_data.purification_df.to_dict(orient="records"):
            row = table.row()
            row.cell(str(data_row["ID"]))
            row.cell(str(data_row["Safety screen"]))
            row.cell(str(data_row["Safety / quality flags"]))

    pdf.ln(8)

    # ==========================================================
    # Table 4 : Energy and economics
    # ==========================================================
    with pdf.table(
        col_widths=(8, 35, 28, 34, 22, 24, 20, 20),
        headings_style=headings_style,
        line_height=4.5,
        width=190,
    ) as table:

        pdf.set_font("NotoSerif", size=9)

        headerRow = table.row()
        headerRow.min_height = 10
        headerRow.cell("ID")
        headerRow.cell("Source")
        headerRow.cell("Electricity (MWh/t product)")
        headerRow.cell("Compression elec. (MWh/t)")
        headerRow.cell("Thermal (MWh/t product)")
        headerRow.cell("Cooling (MWh/t product)")
        headerRow.cell("Cost (€/t product)")
        headerRow.cell("CAPEX (€m)")

        pdf.set_font("NotoSerif", size=9)

        for data_row in pdf_data.purification_df.to_dict(orient="records"):
            row = table.row()
            row.cell(str(data_row["ID"]))
            row.cell(str(data_row["Source"]))
            row.cell(f'{data_row["Electricity (MWh/t product)"]:.3f}')
            row.cell(f'{data_row["Compression electricity (MWh/t)"]:.3f}')
            row.cell(f'{data_row["Thermal (MWh/t product)"]:.3f}')
            row.cell(f'{data_row["Cooling (MWh/t product)"]:.3f}')
            row.cell(f'{data_row["Cost (€/t product)"]:.1f}')
            row.cell(f'{data_row["CAPEX (€m)"]:.1f}')

    pdf.ln(8)

def generate_pdf_section_ProductQualityScreen(pdf : PDF, pdf_data : PDF_REPORT_INPUT) -> None:
    """ Function to generate the product quality screen part of the STICH reporting """
    print(f"[PDF] Product quality screen generation section")

    pdf.add_page()
    pdf.set_font("NotoSerif", size=18)
    # Section title
    pdf.multi_cell(0, 5, f"Product quality screen", 
                   new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    # Section description
    pdf.set_font("NotoSerif", "", size=11)
    pdf.multi_cell(0, 5, f"The dashboard checks 6 of 27 components in the selected public cargo benchmark (22% coverage). Passing this screen is not a substitute for a complete compositional assay, a Dunkerque pipeline specification or a shipper agreement.", 
                   new_x="LMARGIN", new_y="NEXT")

    pdf.ln(8)

    # TODO Product quality screen
    # full_limit_df = pd.DataFrame(
    #     [
    #         {
    #             "Component": limit.component,
    #             "Requirement": "Minimum" if limit.limit_type == "minimum" else "Maximum",
    #             "Limit": limit.limit_value,
    #             "Unit": limit.unit,
    #             "Model status": "Screened" if limit.screened_in_model else "Assay required",
    #             "Validation": limit.validation_status,
    #         }
    #         for limit in pdf_data.input.reference_product_limits
    #     ]
    # )



def generate_pdf_section_transport(pdf : PDF, pdf_data : PDF_REPORT_INPUT) -> None:
    """ Function to generate the transport part of the STICH reporting """
    print(f"[PDF] Transport generation section")

    pdf.add_page()
    pdf.set_font("NotoSerif", size=18)
    # Section title
    pdf.multi_cell(0, 5, f"Transport section", 
                   new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    # Section description
    pdf.set_font("NotoSerif", "", size=11)
    pdf.write_html(
        """
        <p align="justify">
        <b>What happen here:</b>
        pipeline-quality CO₂ enters the collection network at 110 bar. The model evaluates every feasible source/sink tree without free junction nodes, aggregates branch flows and retains the least-annualized-cost feasible screening network. Density and compressibility are calculated with the Peng-Robinson equation of state from pressure, temperature and mixture composition.
        </p>
        """
    )    
    pdf.ln(8)


    fig_pipeline = pdf_data.pipeline_figure
    fig_pipeline.update_layout(    #Already defined in creating fonction but may need changes between web page & pdf
        margin={"l": 50, "r": 20, "t": 30, "b": 40},
    )
    # Convert the figure to png using kaleido
    image_data_cost = fig_pipeline.to_image(format="png", engine="kaleido")
    # Create an io.BytesIO object which can be used by FPDF2
    image = io.BytesIO(image_data_cost)
    pdf.image(image, w=pdf.epw)  # Width of the image is equal to the width of the page

    
    pdf.set_font("NotoSerif", "", size=11)
    route_basis_text = (
        "The route geometry is imported from GIS CSVs with straight connectors where necessary. "
        "Supplied QGIS Z values are used; missing Z values default to zero, "
        "and gaps use straight connectors. No unprovided terrain profile is inferred."
        if pdf_data.summary["transport_network_mode"] == "user_defined_trajectory"
        else "The path is an optimized screening topology, not a surveyed right-of-way."
    )
    pdf.write_html(
        f"""
        <p align="justify">
        <b>Precision boundary:</b>
        {route_basis_text} Land ownership, protected areas, road/rail/water crossings, geotechnics, transient operation, fracture control and material compatibility require project engineering. The endpoint is the supplied Port of Dunkerque site; downstream terminal and storage activities are excluded.
        </p>
        """
    )    

    pdf.add_page()


    # ==========================================================
    # Pipeline transport KPIs
    # ==========================================================

    diameters = [row["nominal_diameter_mm"] for row in pdf_data.result.pipeline_segments]
    max_velocity = max(
        (row["velocity_m_per_s"] for row in pdf_data.result.pipeline_segments),
        default=0.0,
    )

    min_diameter = min(diameters) if diameters else None
    max_diameter = max(diameters) if diameters else None

    pressure_margin = (pdf_data.summary["minimum_network_pressure_bar"] - pdf_data.inputs.config["transport"]["minimum_arrival_pressure_bar"])

    kpis = [
        (
            "Physical route",
            f"{pdf_data.summary['pipeline_route_length_km']:.1f} km",
        ),
        (
            "Costed / existing",
            f"{pdf_data.summary['pipeline_costed_route_length_km']:.1f} / "
            f"{pdf_data.summary['pipeline_existing_route_length_km']:.1f} km",
        ),
        (
            "Pipe sizes",
            f"DN{min_diameter:.0f}-DN{max_diameter:.0f}" if diameters else "—",
        ),
        (
            "Maximum velocity",
            f"{max_velocity:.2f} m/s",
        ),
        (
            "Minimum network pressure",
            f"{pdf_data.summary['minimum_network_pressure_bar']:.1f} bar",
        ),
        (
            "Pressure margin",
            f"{pressure_margin:+.1f} bar",
        ),
        (
            "Screened wall thickness",
            f"{pdf_data.summary['pipeline_wall_thickness_min_mm']:.1f}"
            f"-{pdf_data.summary['pipeline_wall_thickness_max_mm']:.1f} mm",
        ),
        (
            "New-project steel",
            f"{pdf_data.summary['pipeline_steel_mass_t'] / 1000:.1f} kt",
        ),
    ]

    # Transport KPI title
    pdf.set_font("NotoSerif", "B", 14)
    pdf.cell(0, 8, "Pipeline transport KPIs", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(2)

    headings_style = FontFace(
        emphasis="BOLD",
        color=255,
        fill_color=(180, 180, 180),
    )

    with pdf.table(
        col_widths=(85, 45),
        width=130,
        line_height=5,
        text_align=("LEFT", "CENTER"),
        headings_style=headings_style,
    ) as table:

        header = table.row()
        header.cell("Indicator")
        header.cell("Value")

        pdf.set_font("NotoSerif", "", 11)
        for label, value in kpis:
            row = table.row()
            row.cell(label)
            row.cell(value)

    pdf.ln(5)


    
    # ==========================================================
    # Table 1 : Pipeline Route & geometry
    # ==========================================================
    with pdf.unbreakable() as pdf_table1:
        pdf_table1.set_font("NotoSerif", "", 11)
        pdf_table1.multi_cell(0, 5, f"Pipeline Route & geometry", 
                        new_x="LMARGIN", new_y="NEXT")
        pdf_table1.ln(2)


        with pdf_table1.table(
            col_widths=(20, 12, 28, 28, 25, 22, 22, 20),
            headings_style=headings_style,
            line_height=4.5,
            width=190,
        ) as table:

            headerRow = table.row()
            headerRow.min_height = 10
            headerRow.cell("Owner route")
            headerRow.cell("Seg.")
            headerRow.cell("From")
            headerRow.cell("To")
            headerRow.cell("Asset basis")
            headerRow.cell("3D route\n(km)")
            headerRow.cell("Plan route\n(km)")
            headerRow.cell("Elev. ΔZ\n(m)")

            pdf_table1.set_font("NotoSerif", size=9)
            for data_row in pdf_data.transport_df.to_dict(orient="records"):
                row = table.row()
                row.cell(str(data_row["Owner route"]))
                row.cell(str(data_row["Segment"]))
                row.cell(str(data_row["From"]))
                row.cell(str(data_row["To"]))
                row.cell(str(data_row["Asset basis"]))
                row.cell(f'{data_row["3D route (km)"]:.3f}')
                row.cell(f'{data_row["Plan route (km)"]:.3f}')
                row.cell(f'{data_row["Elevation ΔZ (m)"]:+.1f}')

    pdf.ln(8)

    
    # ==========================================================
    # Table 2 : Flow rate & stream composition
    # ==========================================================
    with pdf.unbreakable() as pdf_table2:
        pdf_table2.set_font("NotoSerif", "", 11)
        pdf_table2.multi_cell(0, 5, f"Flow rate & stream composition", 
                        new_x="LMARGIN", new_y="NEXT")
        pdf_table2.ln(2)

        with pdf_table2.table(
            col_widths=(28, 25, 25, 28, 30, 25, 25),
            headings_style=headings_style,
            line_height=4.5,
            width=190,
        ) as table:

            headerRow = table.row()
            headerRow.min_height = 10
            headerRow.cell("Owner route")
            headerRow.cell("CO₂ flow\n(Mt/y)")
            headerRow.cell("Total stream\n(Mt/y)")
            headerRow.cell("CO₂ fraction\n(%)")
            headerRow.cell("PR density\n(kg/m³)")
            headerRow.cell("PR Z\n(-)")
            headerRow.cell("EOS P-ref\n(bar)")

            for data_row in pdf_data.transport_df.to_dict(orient="records"):
                row = table.row()
                row.cell(str(data_row["Owner route"]))
                row.cell(f'{data_row["CO₂ flow (Mt/y)"]:.3f}')
                row.cell(f'{data_row["Total stream (Mt/y)"]:.3f}')
                row.cell(f'{100 * data_row["CO₂ mass fraction"]:.1f}%')
                row.cell(f'{data_row["PR density (kg/m³)"]:.1f}')
                row.cell(f'{data_row["PR Z (-)"]:.4f}')
                row.cell(f'{data_row["EOS P-ref (bar)"]:.1f}')

    pdf.ln(8)


    # ==========================================================
    # Table 3 : Pipeline sizing
    # ==========================================================
    with pdf.unbreakable() as pdf_table3:
        pdf_table3.set_font("NotoSerif", "", 11)
        pdf_table3.multi_cell(0, 5, f"Pipeline sizing", 
                        new_x="LMARGIN", new_y="NEXT")
        pdf_table3.ln(2)

        with pdf_table3.table(
            col_widths=(30, 25, 35, 25, 30, 30),
            headings_style=headings_style,
            line_height=4.5,
            width=190,
        ) as table:

            headerRow = table.row()
            headerRow.min_height = 10
            headerRow.cell("Owner route")
            headerRow.cell("Diameter")
            headerRow.cell("Material")
            headerRow.cell("Wall\n(mm)")
            headerRow.cell("Steel\n(t)")
            headerRow.cell("Velocity\n(m/s)")

            for data_row in pdf_data.transport_df.to_dict(orient="records"):
                row = table.row()
                row.cell(str(data_row["Owner route"]))
                row.cell(str(data_row["Diameter"]))
                row.cell(str(data_row["Material"]))
                row.cell(f'{data_row["Wall (mm)"]:.1f}')
                row.cell(f'{data_row["Steel (t)"]:.0f}')
                row.cell(f'{data_row["Velocity (m/s)"]:.2f}')

    pdf.ln(8)

    
    # ==========================================================
    # Table 4 : Pipeline hydraulics and cost
    # ==========================================================
    with pdf.unbreakable() as pdf_table4:
        pdf_table4.set_font("NotoSerif", "", 11)
        pdf_table4.multi_cell(0, 5, f"Pipeline hydraulics and cost", 
                        new_x="LMARGIN", new_y="NEXT")
        pdf_table4.ln(2)

        with pdf_table4.table(
            col_widths=(28, 25, 25, 25, 25, 25, 25),
            headings_style=headings_style,
            line_height=4.5,
            width=190,
        ) as table:

            headerRow = table.row()
            headerRow.min_height = 10
            headerRow.cell("Owner route")
            headerRow.cell("Friction ΔP\n(bar)")
            headerRow.cell("Elevation ΔP\n(bar)")
            headerRow.cell("Net ΔP\n(bar)")
            headerRow.cell("Minimum P\n(bar)")
            headerRow.cell("CAPEX\n(€m)")

            for data_row in pdf_data.transport_df.to_dict(orient="records"):
                row = table.row()
                row.cell(str(data_row["Owner route"]))
                row.cell(f'{data_row["Friction ΔP (bar)"]:.2f}')
                row.cell(f'{data_row["Elevation ΔP (bar)"]:+.2f}')
                row.cell(f'{data_row["Net ΔP (bar)"]:+.2f}')
                
                min_p = data_row["Minimum P (bar)"]
                row.cell("N/A" if pd.isna(min_p) else f"{min_p:.2f}")
                
                row.cell(f'{data_row["CAPEX (€m)"]:.1f}')

    pdf.ln(8)


    pdf.set_font("NotoSerif", "", size=11)
    # Use this to check if we can have all the precision in one texte group, tu avoid page break in the middle of the text
    with pdf.offset_rendering() as dummy:
        if pdf_data.summary["transport_network_mode"] == "user_defined_trajectory":
            my_html= f"""
                <p align="justify">
                <b>How the network is selected:</b>
                The imported topology is fixed: the model does not shorten or reroute it. 
                Segment length is calculated from the imported X/Y/Z coordinates (Z = 0 m 
                when absent); connected 
                source flows are summed on every shared downstream segment. Diameters 
                are increased until the 2.5 m/s velocity ceiling, 85 bar minimum network 
                pressure and 120 bar design-pressure screen are satisfied.
                </p>
                """
        else:
            my_html= f"""
                <p align="justify">
                <b>How the network is selected:</b>
                The model evaluated **{pdf_data.summary['candidate_pipeline_trees_evaluated']:,} feasible network trees** for this case. 
                For every segment it uses source-specific route uplifts, Peng–Robinson density/compressibility, Darcy–Weisbach pressure loss with a Swamee–Jain friction factor, 
                standard nominal diameters, a 2.5 m/s velocity ceiling and an 85 bar minimum arrival pressure. The least annualized-cost feasible tree is retained.
                </p>
                """

        my_html2 = f"""
            <p align="justify">
            <b>Material screen:</b>
            Wall thickness uses the Barlow pressure relation at the configured 120 bar design pressure, 
            with material SMYS, a 0.72 design factor, corrosion allowance, and a 6.4 mm minimum wall. 
            The hydraulic diameter is held fixed; 35% of route CAPEX is treated as material-sensitive. 
            Fracture control, decompression, toughness, weldability, impurity corrosion, fatigue, fittings, and code-class location factors require FEED.
            </p>
            """

        # Check if we have the space to add the text, if not we add a page break before trully adding the text
        dummy.write_html(my_html)
        dummy.write_html(my_html2)

    if dummy.page_break_triggered:
        pdf.add_page()

    pdf.write_html(my_html)
    pdf.write_html(my_html2)

    







def generate_pdf_report(pdf_data : PDF_REPORT_INPUT) -> None:
    """ Main function to call to generate the STICH reporting """
    print(f"[PDF] Reporting generation")
    
    
    # Instantiation of inherited class
    pdf = PDF()
    
    # Set FONT to NotoSerif to support (CO)₂ ₃ ₄ (subscripts) and ² ³ (superscripts)
    pdf.add_font(
        family="NotoSerif",
        style="",
        fname=r"ressources\NotoSerif-Regular.ttf"
    )

    pdf.add_font(
        family="NotoSerif",
        style="B",
        fname=r"ressources\NotoSerif-Bold.ttf"
    )

    pdf.add_font(
        family="NotoSerif",
        style="I",
        fname=r"ressources\NotoSerif-Italic.ttf"
    )

    pdf.add_font(
        family="NotoSerif",
        style="BI",
        fname=r"ressources\NotoSerif-BoldItalic.ttf"
    )
    pdf.set_font("NotoSerif", size=11)

    
    # Setup meta datas & header / footer
    pdf.set_subject("Modelisation STICH")
    pdf.set_title(pdf_data.scenarioLabel)
    pdf.set_author("Akkodis Research - STICH Project")
    pdf.set_creation_date(datetime.now())
    

    # start page content
    pdf.add_page()
    pdf.set_font("NotoSerif", size=11)
    pdf.multi_cell(0, 5, f"{pdf_data.scenario['description']}", new_x="LMARGIN", new_y="NEXT")

    # TODO add general metrics - Overall


    # Add decision table:
    pdf.add_page()
    pdf.set_font("NotoSerif", size=11)
    pdf.set_draw_color(0, 0, 0)
    pdf.set_line_width(0.3)
    headings_style = FontFace(emphasis="BOLD", color=255, fill_color=(180, 180, 180))
    with pdf.table(
        # borders_layout="NO_HORIZONTAL_LINES",
        # cell_fill_color=(224, 235, 255),
        # cell_fill_mode=TableCellFillMode.ROWS,
        col_widths=(30, 12, 30, 50),
        headings_style=headings_style,
        line_height=4.5,
        text_align=("LEFT", "LEFT", "LEFT", "LEFT"),
        width=190,
    ) as table:
        # Add decision table header
        headerRow = table.row()
        headerRow.min_height = 8
        headerRow.cell("Decision gate")
        headerRow.cell("Status")
        headerRow.cell("Result")
        headerRow.cell("Management meaning")

        #Add decision table content
        pdf.set_font("NotoSerif", size=10)
        for data_row in pdf_data.decision_rows:
            row = table.row()
            row.cell(data_row["Decision gate"])
            row.cell(data_row["Status"])
            row.cell(data_row["Result"])
            row.cell(data_row["Management meaning"])

    pdf.set_font("NotoSerif", size=11)
    pdf.set_y(pdf.get_y() + 2)  # add some vertical spacing between the table and the caption
    pdf.multi_cell(0, 5, 
                   text=f"Independent gates are shown instead of a single composite score so that a strong result cannot hide a critical weakness.", 
                   new_x="LMARGIN", new_y="NEXT")

    # Generation of each sub-part of the report (capture, purification, transport, etc.)
    generate_pdf_section_capture(pdf, pdf_data)
    generate_pdf_section_purification(pdf, pdf_data)
    generate_pdf_section_ProductQualityScreen(pdf, pdf_data)
    generate_pdf_section_transport(pdf, pdf_data)


    # Generate the final PDF file
    pdf.output("outputs//POC_STICH_report.pdf")

    print(f"[PDF] Fin reporting generation")





