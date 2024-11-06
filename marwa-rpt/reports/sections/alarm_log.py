#!/usr/bin/env python
"""
Alarm log report section.

    Version Notes:
        1.0.0.0 - 11/29/2019 - Created from with therapy_log.py.
        1.0.0.1 - 12/05/2019 - Implemented patient reset, fixed font mapping.
        1.0.0.2 - 12/06/2019 - Added no alarm message.
        1.0.0.3 - 12/13/2019 - Added section linking.
        1.0.0.4 - 12/17/2019 - Applied label definitions.
        1.0.0.5 - 01/07/2020 - Added record limit.
        1.0.0.6 - 01/12/2020 - Moved data container references for general template.
        1.0.0.7 - 01/19/2020 - Added NOSPLIT to last line when table reaches size limit.
        1.0.0.8 - 02/05/2020 - Shortened table rows.
        1.0.0.9 - 03/11/2020 - Standardized label filtering with Alarm Summary.

"""

__author__ = "John Dorian for Sai Systems Technologies"
__copyright__ = "Copyright 2019"
__version__ = "1.0.0.9"

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
from modules.models import vocsn_data as vd
from modules.models.errors import ErrorManager
from reports.elements.styles import Styles as s
from reports.elements.templates import Bookmark
from reports.elements.general import general_template
from modules.processing.utilities import filter_label, label_lookup

# Global variables
SECTION_NAME = "Alarm Log"


def alarm_log_section(em: ErrorManager, w_dir: str, doc: BaseDocTemplate, report: r.Report, data: vd.VOCSNData, story):
    """
    Create alarm log report section.
    :param em: Error manager.
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
    link_name_arrive = "section_alarm_log"
    bottom_link_away = "section_alarm_summary" if report.sections.alarm_summary else None
    page_template = general_template(SECTION_NAME, doc, bottom_link=bottom_link_away, bottom_margin=0.25*inch)
    doc.addPageTemplates(page_template)

    # Get record limit
    line_max = report.settings["tables"]["table_row_max"]

    # Basic formats
    style_items = [
        ('GRID', (0, 0), (-1, -1), 1, colors.rgb2cmyk(0.8, 0.8, 0.8)),
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
    data.alarms_all.sort(key=lambda x: x.start_syn)
    for alarm in data.alarms_all:

        # Only include events in report range
        r_range = report.range
        if not r_range.data_start <= alarm.start_syn <= r_range.end:
            continue

        # Lookup alarm label
        label = label_lookup(em, data, alarm.alarm_id)

        # Format label strings
        if not label:
            label = "{}".format(alarm.label).title()
            label = filter_label(label)

        # Construct line
        line += 1
        lines.append([label, dt_format(alarm.start_syn), dt_format(alarm.end_raw), alarm.duration])

        # Limit table size
        if line >= line_max:
            line += 1
            lines.append(["Reached table size limit. Please narrow the report range."])
            style_items.extend([
                ('SPAN', (0, line), (-1, line)),
                ('ALIGN', (0, line), (-1, line), 'CENTER'),
                ('FONT', (0, line), (-1, line), s.Fonts.italic),
                ('TEXTCOLOR', (0, line), (-1, line), s.Colors.black),
                ('NOSPLIT', (0, -2), (-1, -1)),
            ])
            break

    # Construct table style
    table_style = TableStyle(style_items)
    widths = [2.5*inch, 1.7*inch, 1.7*inch, 1.35*inch]

    # Assemble page template
    page_template = general_template(SECTION_NAME, doc)
    doc.addPageTemplates(page_template)

    # Create combined list of data rows
    headers = [["Alarm", "Start", "End", "Duration"]]
    data = headers + lines

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
        story.append(Paragraph("No Alarms", s.subtitle))
