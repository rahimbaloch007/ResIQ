from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
import datetime


def generate_well_report(output_path, well_name, field_name,
                          pvt_results=None, mb_results=None,
                          dca_results=None, prepared_by="Rahim Ullah"):
    """
    Generate a professional ResIQ well report PDF.

    Input:
      output_path  : file path to save PDF
      well_name    : name of well being analyzed
      field_name   : name of field
      pvt_results  : dict from PVTEngine (optional)
      mb_results   : dict from MaterialBalanceEngine (optional)
      dca_results  : dict from DeclineCurveEngine (optional)
      prepared_by  : engineer name
    """
    doc = SimpleDocTemplate(
        output_path, pagesize=letter,
        topMargin=0.6 * inch, bottomMargin=0.6 * inch,
        leftMargin=0.7 * inch, rightMargin=0.7 * inch
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'ResIQTitle', parent=styles['Heading1'],
        fontSize=22, textColor=colors.HexColor('#0A1628'),
        spaceAfter=4, alignment=TA_CENTER
    )
    subtitle_style = ParagraphStyle(
        'ResIQSubtitle', parent=styles['Normal'],
        fontSize=11, textColor=colors.HexColor('#00897B'),
        spaceAfter=20, alignment=TA_CENTER
    )
    section_style = ParagraphStyle(
        'SectionHeader', parent=styles['Heading2'],
        fontSize=14, textColor=colors.HexColor('#0A1628'),
        spaceBefore=18, spaceAfter=8,
        borderColor=colors.HexColor('#00D4AA'),
        borderWidth=0, borderPadding=0,
    )
    body_style = ParagraphStyle(
        'Body', parent=styles['Normal'], fontSize=10, spaceAfter=6
    )

    elements = []

    # ── HEADER ──────────────────────────────────────────
    elements.append(Paragraph("ResIQ", title_style))
    elements.append(Paragraph("Reservoir Intelligence Platform", subtitle_style))

    today = datetime.date.today().strftime("%B %d, %Y")
    header_data = [
        ["Well Name:", well_name, "Field:", field_name],
        ["Date:", today, "Prepared By:", prepared_by],
    ]
    header_table = Table(header_data, colWidths=[1.1*inch, 2.2*inch, 1.1*inch, 2.0*inch])
    header_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LINEBELOW', (0, -1), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 12))

    # ── PVT SECTION ─────────────────────────────────────
    if pvt_results:
        elements.append(Paragraph("PVT Analysis", section_style))
        ref_p = pvt_results.get('reference_pressure', 'N/A')
        pvt_data = [
            ["Parameter", "Value", "Unit"],
            [f"Z-Factor (at {ref_p} psia)", f"{pvt_results.get('Z_factor', 'N/A')}", "—"],
            [f"Gas FVF (at {ref_p} psia)", f"{pvt_results.get('Bg', 'N/A')}", "res ft³/scf"],
            [f"Gas Viscosity (at {ref_p} psia)", f"{pvt_results.get('viscosity', 'N/A')}", "cp"],
            ["Pseudocritical Temp", f"{pvt_results.get('Tpc', 'N/A')}", "°R"],
            ["Pseudocritical Pressure", f"{pvt_results.get('Ppc', 'N/A')}", "psia"],
        ]
        pvt_table = Table(pvt_data, colWidths=[2.5*inch, 2*inch, 1.5*inch])
        pvt_table.setStyle(_table_style())
        elements.append(pvt_table)
        elements.append(Spacer(1, 10))

    # ── MATERIAL BALANCE SECTION ─────────────────────────
    if mb_results:
        elements.append(Paragraph("Material Balance & P/Z Analysis", section_style))
        mb_data = [
            ["Parameter", "Value", "Unit"],
            ["OGIP", f"{mb_results.get('OGIP_Bscf', 'N/A')}", "Bscf"],
            ["R-squared", f"{mb_results.get('r_squared', 'N/A')}", "—"],
            ["Drive Mechanism", f"{mb_results.get('drive', 'N/A')}", "—"],
        ]
        mb_table = Table(mb_data, colWidths=[2.5*inch, 2*inch, 1.5*inch])
        mb_table.setStyle(_table_style())
        elements.append(mb_table)
        elements.append(Spacer(1, 10))

    # ── DCA SECTION ───────────────────────────────────────
    if dca_results:
        elements.append(Paragraph("Decline Curve Analysis", section_style))
        dca_data = [
            ["Parameter", "Value", "Unit"],
            ["Initial Rate (qi)", f"{dca_results.get('qi', 'N/A')}", "MMscfd"],
            ["Decline Type", f"{dca_results.get('decline_type', 'N/A')}", "—"],
            ["b-factor", f"{dca_results.get('b', 'N/A')}", "—"],
            ["Annual Decline", f"{dca_results.get('Di_annual_pct', 'N/A')}", "%"],
            ["EUR", f"{dca_results.get('EUR', 'N/A')}", "MMscf"],
        ]
        dca_table = Table(dca_data, colWidths=[2.5*inch, 2*inch, 1.5*inch])
        dca_table.setStyle(_table_style())
        elements.append(dca_table)
        elements.append(Spacer(1, 10))

    # ── FOOTER NOTE ───────────────────────────────────────
    elements.append(Spacer(1, 20))
    footer_style = ParagraphStyle(
        'Footer', parent=styles['Normal'], fontSize=8,
        textColor=colors.HexColor('#888888')
    )
    elements.append(Paragraph(
        "Generated by ResIQ — Reservoir Intelligence Platform. "
        "Results based on industry-standard correlations "
        "(Hall-Yarborough, Sutton, Arps, Havlena-Odeh). "
        "This report is intended to support, not replace, "
        "engineering judgment.", footer_style
    ))

    doc.build(elements)
    return output_path


def _table_style():
    """Reusable professional table styling."""
    return TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0A1628')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#DDDDDD')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1),
         [colors.white, colors.HexColor('#F5F5F5')]),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
    ])


if __name__ == "__main__":
    # Self-test with sample data
    print("Testing PDF report generation...")

    sample_pvt = {
        'Z_factor': 0.9278, 'Bg': 0.00504, 'viscosity': 0.0208,
        'Tpc': 365.11, 'Ppc': 670.13
    }
    sample_mb = {
        'OGIP_Bscf': 25.096, 'r_squared': 0.9997,
        'drive': 'Volumetric depletion'
    }
    sample_dca = {
        'qi': 41.797, 'decline_type': 'Hyperbolic', 'b': 0.5,
        'Di_annual_pct': 36.26, 'EUR': 1773.23
    }

    path = generate_well_report(
        "test_report.pdf",
        well_name="Qadirpur-12",
        field_name="Qadirpur Gas Field",
        pvt_results=sample_pvt,
        mb_results=sample_mb,
        dca_results=sample_dca,
    )

    print(f"PDF generated at: {path}")
    print("PDF generator module working correctly.")