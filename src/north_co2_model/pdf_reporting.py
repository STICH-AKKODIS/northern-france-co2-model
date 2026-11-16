import io

from dataclasses import dataclass

from fpdf import FPDF, FontFace
from datetime import datetime

import plotly.graph_objects as go


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
    # decision_rows: list[dict[str, str]]
    # """Executive decision gates"""
    truc = True
    # result: ScenarioResult



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
    pdf.ln(8)

    # Section description
    pdf.set_font("NotoSerif", "B", size=12)
    pdf.write(5, f"What happens here:")
    pdf.set_font("NotoSerif", "", size=12)
    pdf.write(5, f"eligible flue-gas streams are selected, CO₂ is separated using a source-specific technology, and annual plant availability is applied. Capture excludes later dehydration, polishing and compression.")
    pdf.ln(8)

    # Note : possible refactoring with app.py with have the same graph

    # Add the capture vs emissions bar-graph (each site represented)
    fig_capture = go.Figure()
    fig_capture.add_trace(go.Bar(name="Emissions basis", x=pdf_data.capture_df["ID"], y=pdf_data.capture_df["Emissions basis (kt/y)"], marker_color="#B6C4CF"))
    fig_capture.add_trace(go.Bar(name="Captured", x=pdf_data.capture_df["ID"], y=pdf_data.capture_df["Captured (kt/y)"], marker_color=PDF_COLORS["capture"]))
    fig_capture.update_layout(
        barmode="group",
        height=390,
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
    pdf.set_font("NotoSerif", size=12)
    pdf.set_draw_color(0, 0, 0)
    pdf.set_line_width(0.3)
    headings_style = FontFace(emphasis="BOLD", color=255, fill_color=(180, 180, 180))
    with pdf.table(
        # borders_layout="NO_HORIZONTAL_LINES",
        # cell_fill_color=(224, 235, 255),
        # cell_fill_mode=TableCellFillMode.ROWS,
        col_widths=(15, 30, 30, 50, 25, 25, 20, 20, 30, 30, 25, 25, 15, 20),
        headings_style=headings_style,
        line_height=6,
        # text_align=("LEFT"),
        width=190,
    ) as table:
        # Add decision table header
        headerRow = table.row()
        headerRow.min_height = 8
        headerRow.cell("ID")
        headerRow.cell("Source")
        headerRow.cell("Sector")
        headerRow.cell("Capture technology")
        headerRow.cell("Emissions basis (kt/y)")
        headerRow.cell("Captured (kt/y)")
        headerRow.cell("Capture rate")
        headerRow.cell("Availability")
        headerRow.cell("Electricity (MWh/t captured)")
        headerRow.cell("Steam (GJ/t captured)")
        headerRow.cell("CAPEX (€m)")
        headerRow.cell("Cost (€/t product)")
        headerRow.cell("TRL")
        headerRow.cell("Maturity")

        #Add decision table content
        pdf.set_font("NotoSerif", size=10)
        for data_row in pdf_data.capture_df.to_dict(orient="records"):
            row = table.row()
            row.cell(str(data_row["ID"]))
            row.cell(str(data_row["Source"]))
            row.cell(str(data_row["Sector"]))
            row.cell(str(data_row["Capture technology"]))
            row.cell(f"{data_row['Emissions basis (kt/y)']:.1f}")
            row.cell(f"{data_row['Captured (kt/y)']:.1f}")
            row.cell(f"{(data_row['Capture rate']*100):.0f}%")
            row.cell(f"{(data_row['Availability']*100):.0f}%")
            row.cell(f"{data_row['Electricity (MWh/t captured)']:.3f}")
            row.cell(f"{data_row['Steam (GJ/t captured)']:.2f}")
            row.cell(f"{data_row['CAPEX (€m)']:.1f}")
            row.cell(f"{data_row['Cost (€/t product)']:.1f}")
            row.cell(str(data_row["TRL"]))
            row.cell(str(data_row["Maturity"]))
    # st.dataframe(
    #     pdf_data.capture_df,
    #     hide_index=True,
    #     width="stretch",
    #     column_config={
    #         "Capture rate": st.column_config.ProgressColumn(format="percent", min_value=0, max_value=1),
    #         "Availability": st&.column_config.ProgressColumn(format="percent", min_value=0, max_value=1),
    #         "Emissions basis (kt/y)": st.column_config.NumberColumn(format="%.1f"),
    #         "Captured (kt/y)": st.column_config.NumberColumn(format="%.1f"),
    #         "CAPEX (€m)": st.column_config.NumberColumn(format="%.1f"),
    #         "Cost (€/t product)": st.column_config.NumberColumn(format="%.1f"),
    #         "Electricity (MWh/t captured)": st.column_config.NumberColumn(format="%.3f"),
    #         "Steam (GJ/t captured)": st.column_config.NumberColumn(format="%.2f"),
    #     },
    # )
    # with st.expander("How the capture result is calculated"):
    #     st.markdown(
    #         "**Captured CO₂ = emissions basis × capturable fraction × capture rate × annual availability.**  "
    #         "CAPEX is scaled from the reference train using a 0.67 exponent, then annualized over the selected project life. "
    #         "Electricity, steam, consumables and fixed O&M are added separately."
    #     )



def generate_pdf_report(pdf_data : PDF_REPORT_INPUT) -> None:
    """ Main function to call to generate the STICH reporting """
    print(f"[PDF] Reporting generation")
    
    
    # Instantiation of inherited class
    pdf = PDF()
    
    # Set FONT to NotoSerif to support (CO)₂ ₃ ₄ (subscripts) and ² ³ (superscripts)
    pdf.add_font(
        "NotoSerif",
        "",
        r"ressources\NotoSerif-Regular.ttf"
    )
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
    pdf.set_font("NotoSerif", size=12)

    
    # Setup meta datas & header / footer
    pdf.set_subject("Modelisation STICH")
    pdf.set_title(pdf_data.scenarioLabel)
    pdf.set_author("Akkodis Research - STICH Project")
    pdf.set_creation_date(datetime.now())
    

    # start page content
    pdf.add_page()
    pdf.set_font("NotoSerif", size=12)
    pdf.multi_cell(0, 5, f"{pdf_data.scenario['description']}", new_x="LMARGIN", new_y="NEXT")

    # ajout de text
    # pdf.set_font("Times", size=12)
    # for i in range(1, 41):
    #     pdf.multi_cell(0, 10, f"Printing line number {i}", new_x="LMARGIN", new_y="NEXT")

    
    # fig = go.Figure() # Already availlable in the app.Py file #TODO get them
    # # Convert the figure to png using kaleido
    # image_data = fig.to_image(format="png", engine="kaleido")

    # # Create an io.BytesIO object which can be used by FPDF2
    # image = io.BytesIO(image_data)
    # pdf.add_page()
    # pdf.image(image, w=pdf.epw)  # Width of the image is equal to the width of the page


    # Add decision table:
    pdf.add_page()
    pdf.set_font("NotoSerif", size=12)
    pdf.set_draw_color(0, 0, 0)
    pdf.set_line_width(0.3)
    headings_style = FontFace(emphasis="BOLD", color=255, fill_color=(180, 180, 180))
    with pdf.table(
        # borders_layout="NO_HORIZONTAL_LINES",
        # cell_fill_color=(224, 235, 255),
        # cell_fill_mode=TableCellFillMode.ROWS,
        col_widths=(30, 12, 30, 50),
        headings_style=headings_style,
        line_height=6,
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

    pdf.set_font("NotoSerif", size=12)
    pdf.set_y(pdf.get_y() + 2)  # add some vertical spacing between the table and the caption
    pdf.multi_cell(0, 5, 
                   text=f"Independent gates are shown instead of a single composite score so that a strong result cannot hide a critical weakness.", 
                   new_x="LMARGIN", new_y="NEXT")

    generate_pdf_section_capture(pdf, pdf_data)

    pdf.output("outputs//POC_STICH_report.pdf")

    print(f"[PDF] Fin reporting generation")





