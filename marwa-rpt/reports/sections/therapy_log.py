#!/usr/bin/env python
"""
Therapy log report section.

    Version Notes:
        1.0.0.0  - 11/29/2019 - Created from with event_log.py.
        1.0.0.1  - 12/05/2019 - Implemented patient reset, fixed font mapping. Added vent therapy entries.
        1.0.0.2  - 12/06/2019 - Rearranged cell borders. Added no therapy usage message.
        1.0.0.3  - 12/11/2019 - Set grid space to none in spanned cells.
        1.0.0.4  - 12/13/2019 - Added section linking.
        1.0.0.5  - 12/16/2019 - Renamed ventilator labels to "ventilation"
        1.0.0.6  - 12/19/2019 - Added nebulizer source to therapy start/stop lines.
        1.0.0.7  - 01/07/2020 - Added record limit.
        1.0.0.8  - 01/12/2020 - Moved data container references for general template. Added O2 flush therapy lines.
        1.0.0.9  - 01/19/2020 - Added NOSPLIT to last line when table reaches size limit.
        1.0.0.10 - 02/05/2020 - Shortened table rows.

"""

__author__ = "John Dorian for Sai Systems Technologies"
__copyright__ = "Copyright 2019"
__version__ = "1.0.0.10"

# Built-in libraries
from datetime import datetime

# ReportLab libraries
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak
from reportlab.platypus.tables import Table
from reportlab.platypus import BaseDocTemplate
from reportlab.platypus import NextPageTemplate
from reportlab.platypus import Spacer, Paragraph
from reportlab.platypus.tables import TableStyle

# VOCSN modules
from modules.models import report as r
from modules.models import vocsn_enum as ve
from modules.models import vocsn_data as vd
from reports.elements.templates import Bookmark
from reports.elements.styles import Styles as s
from reports.elements.general import general_template

# Global variables
SECTION_NAME = "Therapy Log"


def therapy_log_section(w_dir: str, doc: BaseDocTemplate, report: r.Report, data: vd.VOCSNData, story):
    """
    Create therapy log report section.
    :param w_dir: Working directory.
    :param doc: Reference to main report document.
    :param report: Report definitions.
    :param data: VOCSN data container.
    :param story: List of flowable elements.
    :return: PageTemplate class to be integrated into main DocTemplate.
    """
    global SECTION_NAME

    def dt_format(dt: datetime):
        return dt.strftime("%m/%d %H:%M:%S").lstrip("0")

    # Assemble page template
    link_name_arrive = "section_therapy_log"
    bottom_link_away = "section_trend_summary" if report.sections.trend_summary else None
    page_template = general_template(SECTION_NAME, doc, bottom_link=bottom_link_away,
                                     bottom_margin=0.25*inch)
    doc.addPageTemplates(page_template)

    # Get record limit
    line_max = report.settings["tables"]["table_row_max"]

    # Basic formats
    style_items = [
        ('GRID', (0, 0), (-1, 0), 1, colors.rgb2cmyk(0.8, 0.8, 0.8)),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, 0), 'TOP'),
        ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('FONT', (0, 0), (-1, 0), s.Fonts.heavy),
        ('FONT', (0, 1), (-1, -1), s.Fonts.regular),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('LINEBELOW', (0, 0), (-1, 0), 2, colors.rgb2cmyk(0.2, 0.2, 0.2)),
        ('BACKGROUND', (0, 0), (-1, 0), colors.rgb2cmyk(0.8, 0.8, 0.8)),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
        ('LEFTPADDING', (0, 1), (0, -1), 5)
    ]

    # Generate lines
    line = 0
    lines = []
    data.utilization_presets.sort(key=lambda x: x.start)
    for session in data.utilization_presets:

        # Only include events in report range
        r_range = report.range
        if not r_range.data_start <= session.start <= r_range.end:
            continue

        # Format label strings
        label = session.therapy.name.title() + " Therapy"
        label = label.replace("Ventilator", "Ventilation")
        if session.sub_therapy == ve.SubTherapies.NEBULIZER.value:
            label += " (Internal)"
        if session.sub_therapy == ve.SubTherapies.NEBULIZER_EXT.value:
            label += " (External)"
        if session.sub_therapy == ve.SubTherapies.OXYGEN_FLUSH.value:
            label = "Oxygen Flush Therapy"

        # Construct line
        line += 1
        first_line = line
        lines.append([label, dt_format(session.start), dt_format(session.stop), session.duration])

        # Add event lines
        for detail in session.details:
            line += 1
            lines.append([detail])
            style_items.extend([
                ('LEFTPADDING', (0, line), (0, line), 20),
                # ('SPAN', (0, line), (-1, line)),
                ('TEXTCOLOR', (0, line), (-1, line), s.Colors.med_gray)
            ])

        # Keep lines together
        if line != first_line:
            limit_line = 1 if line >= line_max else 0
            style_items.append(('NOSPLIT', (0, first_line), (-1, line + limit_line)))
        for x in range(0, 4):
            style_items.append(('BOX', (x, first_line), (x, line), 1, colors.rgb2cmyk(0.8, 0.8, 0.8)))

        # Limit table size
        if line >= line_max:
            line += 1
            lines.append(["Reached table size limit. Please narrow the report range."])
            style_items.extend([
                ('SPAN', (0, line), (-1, line)),
                ('ALIGN', (0, line), (-1, line), 'CENTER'),
                ('FONT', (0, line), (-1, line), s.Fonts.italic),
                ('TEXTCOLOR', (0, line), (-1, line), s.Colors.black),
                ('BOX', (0, line), (-1, line), 1, colors.rgb2cmyk(0.8, 0.8, 0.8))
            ])
            break

    # Final styles (top layer)
    style_items.append(('LINEBELOW', (0, 0), (-1, 0), 2, colors.rgb2cmyk(0.2, 0.2, 0.2)))

    # Construct table style
    table_style = TableStyle(style_items)
    widths = [2.5*inch, 1.7*inch, 1.7*inch, 1.35*inch]

    # Create combined list of data rows
    headers = [["Therapy", "Start", "End", "Duration"]]
    data = headers + lines

    # Assemble page template
    page_template = general_template(SECTION_NAME, doc)
    doc.addPageTemplates(page_template)

    # Add flowable elements
    story.append(NextPageTemplate(page_template.id))
    story.append(PageBreak())

    # Section title
    story.extend(s.section_title_flow(SECTION_NAME))

    # Add bookmark destination
    story.append(Bookmark(link_name_arrive))

    # Generate table if there are data
    if len(lines) > 0:
        story.append(Spacer(1, 0.5*inch))
        heights = [0.227 * inch] * len(data)
        t = Table(data, colWidths=widths, rowHeights=heights, style=table_style, repeatRows=1)
        story.append(t)

    # No data message
    else:
        story.append(Spacer(1, 0.5 * inch))
        story.append(Paragraph("No Therapy Usage", s.subtitle))
