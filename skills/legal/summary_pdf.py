"""
Summary PDF generator for the /legal skill.

Produces a counterparty-facing landscape-letter summary table:
  - Columns: # | Section | <Counterparty> Version | <User-org> Version | Discussion
  - Grouped by topic with section header bars
  - 9pt cells, navy header, light-gray banding

Usage:
    from summary_pdf import build_summary_pdf

    groups = [
        ("1. Commercial structure", [
            ("Schedule X pricing", "Their version...", "Our version...", "One-line discussion."),
            ("§28 Partnership Discount", "(none)", "Our addition...", "Core deal."),
        ]),
        ("2. Risk allocation", [
            ("§13 Liability cap", "Their version...", "Our version...", "Industry standard."),
            ...
        ]),
    ]

    build_summary_pdf(
        groups=groups,
        output_path="/path/to/output.pdf",
        title="Counterparty × Us — PO Redline Summary",
        intro="Brief intro paragraph for the counterparty...",
        signoff="Looking forward to talking through this. — Name",
        counterparty_label="Counterparty Version",
        user_label="Our Version",
    )
"""

from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_LEFT


def build_summary_pdf(
    groups,
    output_path,
    *,
    title="Contract Redline Summary",
    intro=None,
    signoff=None,
    counterparty_label="Counterparty Version",
    user_label="Our Version",
):
    """
    Build the standard summary table PDF.

    groups: list of (group_label, [(section, counterparty_version, our_version, discussion), ...])
    """
    doc = SimpleDocTemplate(
        output_path,
        pagesize=landscape(letter),
        leftMargin=0.4 * inch,
        rightMargin=0.4 * inch,
        topMargin=0.4 * inch,
        bottomMargin=0.4 * inch,
        title=title,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "Title", parent=styles["Title"], fontSize=16, spaceAfter=6
    )
    intro_style = ParagraphStyle(
        "Intro", parent=styles["Normal"], fontSize=10, leading=13,
        spaceAfter=10, textColor=colors.HexColor("#444444"),
    )
    cell_style = ParagraphStyle(
        "Cell", parent=styles["Normal"], fontSize=9, leading=11.5,
        textColor=colors.HexColor("#222222"),
    )
    cell_bold = ParagraphStyle("CellBold", parent=cell_style, fontName="Helvetica-Bold")
    header_style = ParagraphStyle(
        "Header", parent=styles["Normal"], fontSize=9, leading=11,
        fontName="Helvetica-Bold", textColor=colors.white, alignment=TA_LEFT,
    )
    group_style = ParagraphStyle(
        "Group", parent=styles["Normal"], fontSize=10, leading=12,
        fontName="Helvetica-Bold", textColor=colors.HexColor("#1F3A5F"),
    )
    closing_style = ParagraphStyle(
        "Close", parent=styles["Normal"], fontSize=10, leading=13,
    )

    story = []
    story.append(Paragraph(title, title_style))
    if intro:
        story.append(Paragraph(intro, intro_style))

    P = lambda t, s=cell_style: Paragraph(t, s)
    header = [
        P("#", header_style),
        P("Section", header_style),
        P(counterparty_label, header_style),
        P(user_label, header_style),
        P("Discussion", header_style),
    ]

    table_data = [header]
    group_header_indices = []
    row_counter = 1
    for group_label, items in groups:
        table_data.append([Paragraph(group_label, group_style), "", "", "", ""])
        group_header_indices.append(len(table_data) - 1)
        for section_label, counterparty_v, user_v, discussion in items:
            table_data.append([
                P(str(row_counter), cell_bold),
                P(section_label, cell_bold),
                P(counterparty_v, cell_style),
                P(user_v, cell_style),
                P(discussion, cell_style),
            ])
            row_counter += 1

    col_widths = [0.3 * inch, 1.7 * inch, 2.4 * inch, 3.0 * inch, 3.0 * inch]
    t = Table(table_data, colWidths=col_widths, repeatRows=1)

    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F3A5F")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#999999")),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    for gi in group_header_indices:
        style_cmds.append(("SPAN", (0, gi), (-1, gi)))
        style_cmds.append(("BACKGROUND", (0, gi), (-1, gi), colors.HexColor("#D9E2EC")))
        style_cmds.append(("TOPPADDING", (0, gi), (-1, gi), 8))
        style_cmds.append(("BOTTOMPADDING", (0, gi), (-1, gi), 6))

    data_row_indices = [
        i for i in range(1, len(table_data)) if i not in group_header_indices
    ]
    for k, di in enumerate(data_row_indices):
        if k % 2 == 1:
            style_cmds.append(("BACKGROUND", (0, di), (-1, di), colors.HexColor("#F4F6FA")))

    t.setStyle(TableStyle(style_cmds))
    story.append(t)

    if signoff:
        story.append(Spacer(1, 12))
        story.append(Paragraph(signoff, closing_style))

    doc.build(story)
    return output_path
