#!/usr/bin/env python
"""
Alarm summary report section, including alarm statistics and durations by alarm type.

    Version Notes:
        1.0.0.0  - 09/28/2019 - Created from with alarm_summary function.
        1.0.0.1  - 10/18/2019 - Adapted to new data file format, some formatting still needed.
        1.0.0.2  - 10/19/2019 - Fixed no-value formatting in alarm table.
        1.0.0.3  - 10/31/2019 - Set alarm strings color based on alarm severity.
        1.0.0.4  - 11/05/2019 - Moved elements down to make space for the multi-view logo.
        1.0.0.5  - 11/14/2019 - Changed alarm table sort order to priority, then count.
        1.0.0.6  - 11/22/2019 - Pass path to alarm graph.
        1.0.0.7  - 12/12/2019 - Reworked section name management.
        1.0.0.8  - 12/13/2019 - Added section links and label filter.
        1.0.0.9  - 12/18/2019 - Added label lookup from definition file.
        1.0.0.10 - 12/20/2019 - Changed alarm coloring.
        1.0.0.11 - 12/21/2019 - Implemented error management.
        1.0.0.12 - 01/12/2020 - Moved data container references for general template.
        1.0.0.13 - 01/19/2020 - Changed later page templates to include alarm log link.

"""

__author__ = "John Dorian for Sai Systems Technologies"
__copyright__ = "Copyright 2019"
__version__ = "1.0.0.13"

# ReportLab libraries
from reportlab.lib import colors
from reportlab.platypus import Frame
from reportlab.lib.units import inch
from reportlab.platypus import Spacer
from reportlab.platypus import PageBreak
from reportlab.platypus.tables import Table
from reportlab.platypus import BaseDocTemplate
from reportlab.platypus import NextPageTemplate

# VOCSN modules
from modules.models import report as r
from modules.models import vocsn_data as vd
from reports.elements import footers as foot
from modules.models.errors import ErrorManager
from reports.elements.styles import Styles as s
from reports.elements.alarm_stats import AlarmStats
from reports.elements.headers import standard as header
from modules.processing.utilities import filter_label, label_lookup
from reports.elements.templates import FormattedPage, SectionTemplate, Bookmark

# Global variables
SECTION_NAME = "Alarm Summary"
REPORT = None
DATA = None
DIR = ""


def _first_page(c: FormattedPage, _: BaseDocTemplate, name: str, bottom_link: str = None):
    """
    First page template.
    :param c: Canvas reference passed from page constructor.
    :param _: Document reference passed from page constructor.
    :param name: Section name.
    """
    global REPORT, DATA, DIR

    # Header
    header(c, DIR, DATA.errors)

    # Footer
    foot.section(c, REPORT, name, bottom_link)


def alarm_table(em: ErrorManager):
    """ Create the alarm duration-bucket table. """
    global REPORT, DATA, DIR

    # Settings
    splits = REPORT.settings["tables"]["alarm_duration_splits"]
    bucket_count = len(splits)

    # Table formatting
    table_style = [
        # ('GRID', (0, 0), (-1, 1), 1.5, s.Colors.light_gray),
        ('GRID', (0, 2), (-1, -1), 1.5, s.Colors.med_light_gray),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 2), (0, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TEXTCOLOR', (0, 0), (-1, 1), s.Colors.dark_blue),
        ('FONT', (0, 0), (-1, 1), s.Fonts.title),
        ('FONT', (1, 2), (-1, -1), s.Fonts.table),
        ('FONT', (0, 2), (0, -1), s.Fonts.heavy),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, -1), 12),
        ('LINEBELOW', (0, 1), (-1, 1), 2, s.Colors.dark_gray),
        ('BACKGROUND', (1, 2), (1, -1), s.Colors.light_gray),
        ('SPAN', (2, 0), (bucket_count+1, 0))
    ]

    # Headers
    data = [["", "", "Duration (sec.)"],
            ["Alarm", "Total"]]
    first = True
    for split in splits:
        if not first:
            data[0].append("")
        if split["high"]:
            data[1].append("{}-{}".format(split["low"], split["high"]))
        else:
            data[1].append("{}+".format(split["low"]))
        first = False

    # Prepare alarm type references
    alarms = []
    therapies = DATA.alarms_tracker.therapy_man.therapies
    for t_name, therapy in therapies.items():
        for at_id, alarm_type in therapy.alarm_types.items():
            alarms.append(alarm_type)
    severity_order = {"High": 0, "Medium": 1, "Low": 2}
    alarms.sort(key=lambda i: (severity_order[i.severity], -i.count))

    # Fill cell values
    row = 1
    for alarm_type in alarms:

        # Set strings color based on alarm severity
        if alarm_type.severity == "High":
            color = s.Colors.alarm_high
        elif alarm_type.severity == "Medium":
            color = s.Colors.alarm_med
        else:
            color = s.Colors.alarm_low

        # Clean label
        label = label_lookup(em, DATA, alarm_type.id)
        if not label:
            label = alarm_type.name.title()
            label = filter_label(label)

        row += 1
        col = 2
        last_val = 1
        text_color = s.Colors.black if alarm_type.severity == "Medium" else s.Colors.white
        table_style.append(('BACKGROUND', (0, row), (0, row), color))
        table_style.append(('TEXTCOLOR', (0, row), (0, row), text_color))

        line = [label, alarm_type.count]
        for bucket in alarm_type.buckets:
            val = str(bucket.count) if bucket.count is not None else None
            if val != "0":
                table_style.append(('BACKGROUND', (col, row), (col, row), s.Colors.x_light_gray))
                last_val = col
            line.append(val)
            col += 1

        # Format empty cells
        if last_val > 1:
            table_style.append(('BACKGROUND', (2, row), (last_val, row), s.Colors.x_light_gray))
        for x in range(0, (len(alarm_type.buckets)+1) - last_val):
            idx = -(x+1)
            line[idx] = ""
        data.append(line)

    # Handle no alarms
    small_cells = len(data[0]) - 1
    if len(data) == 2:
        line = ["No Alarms"]
        for _ in range(0, small_cells):
            line.append("")
        data.append(line)
        table_style.extend([('BACKGROUND', (0, 2), (-1, 2), colors.white)]),
        table_style.extend([('ALIGN', (0, 2), (-1, 2), "CENTER")])
        table_style.extend([('SPAN', (0, 2), (-1, 2))])

    # Cell sizes
    widths = [3*inch]
    for _ in range(0, small_cells):
        widths.append((4.5 / small_cells) * inch)
    heights = [0.2*inch, 0.3*inch]
    for _ in range(0, len(data) - 2):
        heights.append(0.3*inch)

    # Create and return table
    return Table(data=data, colWidths=widths, rowHeights=heights, style=table_style, repeatRows=2)


def alarm_summary_section(em: ErrorManager, w_dir: str, doc: BaseDocTemplate, report: r.Report, data: vd.VOCSNData,
                          story: list):
    """
    Create alarm summary report section.
    :param em: Error manager.
    :param w_dir: Working directory.
    :param doc: Reference to main report document.
    :param report: Report definitions.
    :param data: VOCSN data container.
    :param story: List of flowable elements.
    :return: PageTemplate class to be integrated into main DocTemplate.
    """

    # Set global variables
    global REPORT, DATA, DIR
    REPORT = report
    DATA = data
    DIR = w_dir

    # Assemble page template
    link_name_arrive = "section_alarm_summary"
    bottom_link_away = "section_alarm_log" if report.sections.alarm_log else None
    frames = [Frame(0.5 * inch, 0.5 * inch, doc.width, doc.height,
                    topPadding=0.65 * inch, bottomPadding=0.6 * inch, id='AlarmSummary')]
    first_template = SectionTemplate(id="AlarmSummary", frames=frames, onPage=_first_page, section=SECTION_NAME,
                                     bottom_link=bottom_link_away)
    doc.addPageTemplates(first_template)

    # Add flowable elements
    story.append(NextPageTemplate("AlarmSummary"))
    story.append(PageBreak())

    # Section title
    story.extend(s.section_title_flow(SECTION_NAME))

    # Add bookmark destination
    story.append(Bookmark(link_name_arrive))

    # Create alarm graphs
    story.append(Spacer(1, 0.4 * inch))
    story.append(AlarmStats(em, report, data, DIR))

    # Create alarm duration bucket table
    story.append(Spacer(1, 0.2 * inch))
    story.append(alarm_table(em))
