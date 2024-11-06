#!/usr/bin/env python
"""
Configuration log report section.

    Version Notes:
        1.0.0.0  - 12/01/2019 - Created from with therapy_log.py.
        1.0.0.1  - 12/05/2019 - Fixed font mapping.
        1.0.0.2  - 12/06/2019 - Rearranged cell borders. Added no therapy usage message.
        1.0.1.0  - 12/10/2019 - Modified a copy of the ReportLab Table class to include a title that can't be orphaned at
                               the end of the page and won't push the table to the next page.
        1.0.1.1  - 12/11/2019 - Set grid space to none in spanned cells.
        1.0.1.2  - 12/12/2019 - Improved line display formatting and strings filtering.
        1.0.1.3  - 12/13/2019 - Added section linking.
        1.0.1.4  - 12/14/2019 - Added applicability filter.
        1.0.1.5  - 12/16/2019 - Renamed "ventilator" to "ventilation", removed "detail" header.
        1.0.1.6  - 12/17/2019 - Applied label definitions.
        1.0.1.7  - 12/19/2019 - Changed format for preset label change lines.
        1.0.1.8  - 12/21/2019 - Added patient reset sequence filter.
        1.0.1.9  - 01/07/2020 - Added record limit.
        1.0.1.10 - 01/09/2020 - Restored presets on settings change.
        1.0.1.11 - 01/12/2020 - Moved data container references for general template.
        1.0.1.12 - 01/19/2020 - Created a section-global line count to further limit table sizes. Updated time
                                change label.
        1.0.1.13 - 02/05/2020 - Shortened table rows.
        1.0.1.14 - 02/12/2020 - Corrected spacing for no data message.
        1.0.1.15 - 02/14/2020 - Corrected configuration column header.
        1.0.1.16 - 02/17/2020 - Switched from dict conditions to sets for performance.
        1.0.1.17 - 02/28/2020 - Added support for alternate labels needed for "spontaneoud" override.
        1.0.1.18 - 03/11/2020 - Applied label filter more consistently.

"""

__author__ = "John Dorian for Sai Systems Technologies"
__copyright__ = "Copyright 2019"
__version__ = "1.0.1.18"

# Built-in libraries
from datetime import datetime

# ReportLab libraries
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak
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
from reports.elements.title_table import TitleTable
from reports.elements.general import general_template
from modules.processing.utilities import filter_label
from modules.processing.utilities import label_lookup
from modules.models.vocsn_enum import EventIDs as eID, Therapies

# Global variables
SECTION_NAME = "Configuration Log"

# Title values
DOC = None
DATA = None
TITLE = None
LINES = 0


def create_log_table(em: ErrorManager, report: r.Report, story: list, title: str, event_list: list,
                     no_space: bool = False):
    """
    Create a log table section
    :param em: Error manager.
    :param report: Report definitions.
    :param story: List of flowable elements.
    :param title: Table section title.
    :param event_list: List of events to form table lines.
    :param no_space: Do not add space before the table title.
    :return: PageTemplate class to be integrated into main DocTemplate.
    """
    global DOC, TITLE, DATA, LINES

    def dt_format(dt: datetime):
        return dt.strftime("%m/%d %H:%M:%S").lstrip("0")

    # Skip table without data
    if not event_list:
        return

    # Get record limit
    line_max = report.settings["tables"]["table_row_max"]

    # Basic formats
    style_items = [
        ('GRID', (0, 0), (-1, 0), 1, colors.rgb2cmyk(0.8, 0.8, 0.8)),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 1), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, 0), 'TOP'),
        ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('FONT', (0, 0), (-1, 0), s.Fonts.heavy),
        ('FONT', (0, 1), (-1, -1), s.Fonts.regular),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BACKGROUND', (0, 0), (-1, 0), colors.rgb2cmyk(0.8, 0.8, 0.8)),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
        ('LEFTPADDING', (0, 1), (0, -1), 5)
    ]

    # Generate lines
    line = 0
    lines = []
    for event in event_list:

        # Only include events in report range
        r_range = report.range
        if not r_range.data_start <= event.syn_time <= r_range.end and not event.force_display:
            continue

        # Only include events in usable sequence of data, excluding synthetic events
        if 0 < int(event.sequence) < int(r_range.data_sequence):
            continue

        # Lookup settings change label
        is_label_change = event.control in {"14502", "14503", "14504"}
        if event.id == eID.SETTINGS_CHANGE:
            label = label_lookup(em, DATA, event.control)

            # Format label strings as backup
            if not label:
                if event.id == eID.SETTINGS_CHANGE and "Change" not in event.id:
                    label = event.control_name
                else:
                    label = event.name
                if label[:2] == "CA":
                    label = label[2:]
                c = 1
                while c < len(label):
                    if label[c].istitle() and not label[c - 1].istitle() and label[c - 1] != ' ':
                        label = label[:c] + ' ' + label[c:]
                    c += 1
                label = label.title()
                label = filter_label(label)

            # Add "Change"
            label += " Change"

        # Lookup other types
        else:
            if event.id == eID.ALARM_START:
                label = event.param_label.title() + " Alarm Triggered"
            elif event.id == eID.ALARM_END:
                label = event.param_label.title() + " Alarm Resolved"
            elif event.id in {eID.THERAPY_START, eID.VENT_START}:
                label = event.sub_therapy.name.title() + " Therapy Start"
            elif event.id in {eID.THERAPY_END, eID.VENT_START}:
                label = event.sub_therapy.name.title() + " Therapy Stop"
            elif event.id in {eID.ACCESS_CODE_USED} and len(event.values) > 0:
                granted = event.values[0].str
                if granted == "Yes":
                    label = "Clinician Access Unlocked"
                else:
                    label = "Clinician Access Locked"
            else:
                label = event.label.title()
                label = filter_label(label)

            # Filter
            if "Ventilator" in label:
                label = label.replace("Ventilator", "Ventilation")

        # Preset label change number addition
        if is_label_change:
            label = label.replace("Preset ", "Preset {} ".format(event.preset))

        # Add event lines
        line += 1
        first_line = line
        time_record = False
        vent_preset_change = event.control == "22"
        lines.append([label, "", dt_format(event.syn_time)])
        style_items.append(('LEFTPADDING', (0, line), (0, line), 5))
        style_items.append(('SPAN', (0, line), (1, line)))
        if event.values and event.id not in {eID.ALARM_START, eID.ALARM_END}:
            for idx, detail in enumerate(event.values):

                # Skip blacklisted lines
                if detail.key == "SuctionUnits":
                    continue

                # Format label strings
                label = detail.name.title()
                if label in {"Was-Value", "Is-Value"}:
                    label = label.replace('Was-Value', 'Previous Value')
                    label = label.replace('Is-Value', 'Updated Value')

                    # Format detail information
                    info = detail.alt_str if detail.alt_str else detail.str
                    if is_label_change:
                        info = "\"{}\"".format(info)
                    if vent_preset_change:
                        preset = info.split(" ")[-1]
                        if "Previous" in label:
                            preset_label = event.old_preset_label
                        else:
                            preset_label = event.new_preset_label
                        info = "Preset {}: \"{}\"".format(preset, preset_label)

                    # Mask non-applicable values
                    if not detail.applicable:
                        info = "n/a"

                    # Add line
                    line += 1
                    lines.append([label, info, ""])

                # Handle times
                elif event.control in {"91", "92"}:
                    time_record = True
                    label = label.replace('Was-Epoch-Time-Value', 'Previous Value')
                    label = label.replace('Is-Epoch-Time-Value', 'Updated Value')
                    info = datetime.utcfromtimestamp(detail.num)

                    # Add line
                    line += 1
                    lines.append([label, info, ""])

                # Override previous lines with "Off" if state is False
                elif label in {"Was-Onoffstate", "Is-Onoffstate"}:
                    if detail.str.lower() == "off":
                        lines[-1][1] = "Off"

                # Add preset after last line
                if idx == len(event.values)-1 and event.id == eID.SETTINGS_CHANGE:

                    # Capture preset label if provided
                    if event.therapy in {Therapies.VENTILATOR, Therapies.OXYGEN, Therapies.COUGH}:

                        # Construct preset line
                        if not is_label_change:
                            preset_val = "{}: \"{}\"".format(event.preset, event.preset_label)
                            lines.append(["Preset", preset_val, ""])
                            line += 1

            # Add note to time record
            if time_record:
                lines.append(["Note: All event times in this report are calculated backwards from the", "", ""])
                lines.append(["most recent VOCSN Date and Time setting.", "", ""])
                line += 2
                style_items.extend([
                    # ('SPAN', (0, line), (1, line)),
                    ('VALIGN', (0, line-1), (1, line-1), 'BOTTOM'),
                    ('VALIGN', (0, line), (1, line), 'TOP'),
                    ('FONTSIZE', (0, line - 1), (-1, line), 8),
                    ('BOTTOMPADDING', (0, line-1), (-1, line-1), 0),
                    ('TOPPADDING', (0, line), (-1, line), 0),
                    ('LEFTPADDING', (0, line), (-1, line), 40)
                ])

            # Keep lines together
            if line != first_line:
                limit_line = 1 if line >= line_max else 0
                # limit_line = 1 if ((line + LINES) >= line_max and line > 25) else 0   # Share limit for all tables
                style_items.extend([
                    ('TEXTCOLOR', (0, first_line+1), (-1, line), s.Colors.med_gray),
                    ('LEFTPADDING', (0, first_line+1), (0, line), 20),
                    ('NOSPLIT', (0, first_line), (-1, line + limit_line))
                ])

        # Fill in grid
        style_items.extend([
            ('BOX', (0, first_line), (1, line), 1, colors.rgb2cmyk(0.8, 0.8, 0.8)),
            ('BOX', (2, first_line), (2, line), 1, colors.rgb2cmyk(0.8, 0.8, 0.8)),
        ])

        # Limit table size
        # if (line + LINES) >= line_max and line > 25:      # Share limit for all tables
        if line >= line_max:
            line += 1
            lines.append(["Reached section table size limit. Please narrow the report range."])
            style_items.extend([
                ('SPAN', (0, line), (-1, line)),
                ('ALIGN', (0, line), (-1, line), 'CENTER'),
                ('FONT', (0, line), (-1, line), s.Fonts.italic),
                ('TEXTCOLOR', (0, line), (-1, line), s.Colors.black),
                ('BOX', (0, line), (-1, line), 1, colors.rgb2cmyk(0.8, 0.8, 0.8))
            ])
            break

    # Update total line count
    LINES += line

    # Don't generate a table with no events
    if len(lines) == 0:
        return

    # Final styles (top layer)
    style_items.append(('LINEBELOW', (0, 0), (-1, 0), 2, colors.rgb2cmyk(0.2, 0.2, 0.2)))

    # Construct table style
    table_style = TableStyle(style_items)
    widths = [2.4 * inch, 2.45 * inch, 2.4 * inch]

    # Create combined list of data rows
    headers = [["Configuration", "", "Time"]]
    data = headers + lines

    # Generate table if there are data
    if len(lines) > 0:
        # story.append(Spacer(1, 0.25*inch))
        TITLE = title
        space = 0.25*inch
        heights = [0.227 * inch] * len(data)
        t = TitleTable(data=data, colWidths=widths, rowHeights=heights, style=table_style, repeatRows=1, title=title,
                       spaceBefore=space)
        t.no_space = no_space
        story.append(t)


def config_log_section(em: ErrorManager, w_dir: str, doc: BaseDocTemplate, report: r.Report, data: vd.VOCSNData, story):
    """
    Create configuration log report section.
    :param em: Error manager.
    :param w_dir: Working directory.
    :param doc: Reference to main report document.
    :param report: Report definitions.
    :param data: VOCSN data container.
    :param story: List of flowable elements.
    :return: PageTemplate class to be integrated into main DocTemplate.
    """
    global SECTION_NAME, DOC, TITLE, DATA

    # Assemble page template
    DOC = doc
    DATA = data
    link_name_arrive = "section_configuration_log"
    bottom_link_away = "section_settings_summary" if report.sections.settings_summary else None
    page_template = general_template(SECTION_NAME, doc, bottom_link=bottom_link_away, bottom_margin=0.25*inch)
    doc.addPageTemplates(page_template)

    # Add flowable elements
    story.append(NextPageTemplate(page_template.id))
    story.append(PageBreak())

    # Section title
    story.extend(s.section_title_flow(SECTION_NAME))
    story.append(Spacer(1, -0.25 * inch))

    # Add bookmark destination
    story.append(Bookmark(link_name_arrive))

    # Add tables for system and each therapy
    story.append(Spacer(1, 0.5 * inch))
    base_length = len(story)
    create_log_table(em, report, story, "System Configuration", data.events_system, no_space=True)
    create_log_table(em, report, story, "Ventilation Configuration", data.events_tracker.ventilator.settings_events)
    create_log_table(em, report, story, "Oxygen Configuration", data.events_tracker.oxygen.settings_events)
    create_log_table(em, report, story, "Cough Configuration", data.events_tracker.cough.settings_events)
    create_log_table(em, report, story, "Suction Configuration", data.events_tracker.suction.settings_events)
    create_log_table(em, report, story, "Nebulizer Configuration", data.events_tracker.nebulizer.settings_events)
    TITLE = None

    # No data message
    if len(story) == base_length:
        story.append(Spacer(1, 0.25 * inch))
        story.append(Paragraph("No Configuration Changes", s.subtitle))
