#!/usr/bin/env python
"""
Event log report section.

    Version Notes:
        1.0.0.0  - 07/29/2019 - Created from with EventLogSection function.
        1.0.0.1  - 09/12/2019 - Restructured to match requirements of other templates.
        1.0.0.2  - 10/04/2019 - Filtered events, increased top margin to allow for mulit-view logo.
        1.0.0.2  - 10/05/2019 - Filtered strings labels to look more natural.
        1.0.0.3  - 10/14/2019 - Changed name for therapy and alarm events and suppressed alarm detail.
        1.0.0.4  - 12/01/2019 - Updated formatting to match recent marketing example.
        1.0.0.5  - 12/05/2019 - Implemented patient reset, fixed font mapping.
        1.0.0.6  - 12/06/2019 - Rearranged cell borders. Added no-event message.
        1.0.0.7  - 12/11/2019 - Set grid space to none in spanned cells. Removed detail header label.
        1.0.0.8  - 12/12/2019 - Added strings label filtering.
        1.0.0.9  - 12/13/2019 - Added section linking.
        1.0.0.10 - 12/14/2019 - Added applicability filter.
        1.0.0.11 - 12/17/2019 - Applied label definitions.
        1.0.1.0  - 12/18/2019 - Reworked label and detail determination to draw from definition file, then filter tabs
                                as backup if needed.
        1.0.1.1  - 12/19/2019 - Added nebulizer source to therapy start/stop lines. Changed preset label change format.
        1.0.1.2  - 12/21/2019 - Implemented error management. Added preset labels to therapy starts.
        1.0.1.3  - 01/07/2020 - Added record limit.
        1.0.1.4  - 01/09/2020 - Changed display values for access code used events. Restored presets on settings change.
        1.0.1.5  - 01/10/2020 - Reversed record order.
        1.0.1.6  - 01/12/2020 - Moved data container references for general template.
        1.0.1.7  - 01/18/2020 - Fixed formatting for flush sessions.
        1.0.1.8  - 01/19/2020 - Added NOSPLIT to last line when table size limit reached. Updated time change label.
        1.0.1.9  - 02/04/2020 - Fixed a capitalization error that prevented processing of on/off states. Added filter
                                to remove "Changed" from "Unlock Required?" label
        1.0.1.10 - 02/05/2020 - Added "Change" back to unlock required events. Shortened table rows.
        1.0.1.11 - 02/17/2020 - Switched from dict conditions to sets for performance.
        1.0.1.12 - 02/28/2020 - Added support for alternate labels for "spontaneous" override.
        1.0.1.13 - 03/11/2020 - Standardized use of label filters.
        1.0.1.14 - 04/06/2020 - Added handling for insp. hold events.
        1.0.2.0  - 04/10/2020 - Removed handling for insp. hold events. (data type changed)

"""

__author__ = "John Dorian for Sai Systems Technologies"
__copyright__ = "Copyright 2019"
__version__ = "1.0.2.0"

# Built-in libraries
from datetime import datetime, timedelta

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
from modules.models.vocsn_enum import EventIDs as eID, Therapies, SubTherapies

# Global variables
SECTION_NAME = "Event Log"


def event_log_section(em: ErrorManager, w_dir: str, doc: BaseDocTemplate, report: r.Report, data: vd.VOCSNData, story):
    """
    Create event log report section.
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

    def applicable_value(default, evnt, dtl):
        if evnt.id in {eID.THERAPY_START, eID.THERAPY_END} and not dtl.applicable:
            default = "n/a"
        return default

    # Assemble page template
    link_name_arrive = "section_event_log"
    bottom_link = "section_trend_summary" if report.sections.trend_summary else None
    page_template = general_template(SECTION_NAME, doc, bottom_link=bottom_link, bottom_margin=0.25*inch)
    doc.addPageTemplates(page_template)

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
        ('LINEBELOW', (0, 0), (-1, 0), 2, colors.rgb2cmyk(0.2, 0.2, 0.2)),
        ('BACKGROUND', (0, 0), (-1, 0), colors.rgb2cmyk(0.8, 0.8, 0.8)),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
        ('LEFTPADDING', (0, 1), (0, -1), 5)
    ]

    # Generate lines
    line = 0
    lines = []
    for event in data.events_all:

        # Skip unwanted events
        synthetic = "-" in event.id
        no_display = (not synthetic) and (int(event.id) < 6000 or int(event.id) > 6999)
        if no_display or event.id == "6022":
            continue

        # Only include events in report range and sequence restrictions
        r_range = report.range
        if not r_range.data_start <= event.syn_time <= r_range.end:
            continue
        if r_range.data_sequence and 0 < int(event.sequence) < int(r_range.data_sequence) and \
                (event.id not in {eID.VENT_START, eID.THERAPY_START}):
            continue

        # Lookup settings change label
        if event.id == eID.SETTINGS_CHANGE:
            label = label_lookup(em, data, event.control) or event.label
            label += " Change"

            # Format label strings as backup
            if not label:
                if event.id == eID.SETTINGS_CHANGE and "Change" not in event.id:
                    label = event.control_name + " Change"
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

        # Lookup other types
        else:
            if event.id in [eID.ALARM_START, eID.ALARM_END]:
                label = None
                if event.control:
                    label = label_lookup(em, data, event.control)
                if not label:
                    label = filter_label(event.param_label.title())
                if event.id == eID.ALARM_START:
                    label = label + " Alarm Triggered"
                elif event.id == eID.ALARM_END:
                    label = label + " Alarm Resolved"
            elif event.id in {eID.THERAPY_START, eID.VENT_START}:
                label = event.sub_therapy.name.title() + " Therapy Start"
            elif event.id in {eID.THERAPY_END, eID.VENT_END}:
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

            # Add nebulizer source
            if event.id in {eID.THERAPY_START, eID.THERAPY_END}:
                if event.therapy_id == "2825":
                    label += " (Internal)"
                if event.therapy_id == "2831":
                    label += " (External)"

            # Filters
            if "Nebulizer" in label:
                label = label.replace("_Ext", "")
            label = label.replace("Ventilator", "Ventilation")
            label = label.replace("_", "")
            label = label.replace("OxygenFlush", "Oxygen Flush")

        # Preset label change number addition
        is_label_change = event.control in {"14502", "14503", "14504"}
        if is_label_change:
            label = label.replace("Preset ", "Preset {} ".format(event.preset))

        # Add event lines
        line += 1
        first_line = line
        time_record = False
        lines.append([label, "", dt_format(event.syn_time)])
        style_items.append(('LEFTPADDING', (0, line), (0, line), 5))
        style_items.append(('SPAN', (0, line), (1, line)))
        if event.values and event.id not in {eID.ALARM_START, eID.ALARM_END, eID.ACCESS_CODE_USED}:
            for idx, detail in enumerate(event.values):
                label = detail.name.title()

                # Skip blacklisted lines
                if detail.key == "SuctionUnits":
                    continue

                # Format label strings
                if label in {"Was-Value", "Is-Value", "Was-Epoch-Time-Value", "Is-Epoch-Time-Value"}:

                    # Format label strings
                    label = detail.name.title()
                    label = label.replace('Was-Value', 'Previous Value')
                    label = label.replace('Is-Value', 'Updated Value')
                    label = label.replace('Was-Epoch-Time-Value', 'Previous Value')
                    label = label.replace('Is-Epoch-Time-Value', 'Updated Value')
                    label = label.replace('value', ' Value')

                    # Detail line
                    if event.control in {"91", "92"}:
                        time_record = True
                        label = label.replace('Was-Epoch-Time-Value', 'Previous Value')
                        label = label.replace('Is-Epoch-Time-Value', 'Updated Value')
                        info = datetime.utcfromtimestamp(detail.num)
                    else:
                        info = applicable_value((detail.alt_str if detail.alt_str else detail.str), event, detail)

                    # Add preset after last line
                    if is_label_change:
                        preset_label = detail.str
                        info = "\"{}\"".format(preset_label)

                    # Ventilation preset change
                    elif event.control == "22":
                        preset = info.split(" ")[-1]
                        if "Previous" in label:
                            preset_label = event.old_preset_label
                        else:
                            preset_label = event.new_preset_label
                        info = "Preset {}: \"{}\"".format(preset, preset_label)

                    # Add line
                    line += 1
                    label = filter_label(label)
                    lines.append([label, info, ""])

                # Override previous lines with "Off" if state is False
                elif label in {"Was-Onoffstate", "Is-Onoffstate"} or "_state" in detail.key:
                    if detail.str.lower() == "off":
                        lines[-1][1] = applicable_value("Off", event, detail)

                # Special format for therapy duration
                elif label == "Therapy-Duration-Seconds":
                    line += 1
                    label = "Duration"
                    seconds = int(detail.str.split(" ")[0].split(".")[0])
                    info = timedelta(seconds=seconds)
                    lines.append([label, info, ""])

                # Nebulizer start duration setting
                elif detail.key == "57":
                    line += 1
                    label = "Set Duration"
                    seconds = int(detail.num * 60)
                    info = timedelta(seconds=seconds)
                    lines.append([label, info, ""])

                # Catch remainders
                else:
                    line += 1
                    label = filter_label(label)
                    info = applicable_value(detail.alt_str if detail.alt_str else detail.str, event, detail)
                    lines.append([label, info, ""])

                # Add preset after last line
                if idx == len(event.values) - 1 and event.id in {eID.SETTINGS_CHANGE}:

                    # Capture preset label if provided
                    if event.therapy in {Therapies.VENTILATOR, Therapies.OXYGEN, Therapies.COUGH}:

                        # Construct preset line
                        if not is_label_change:
                            preset_val = "{}: \"{}\"".format(event.preset, event.preset_label)
                            lines.append(["Preset", preset_val, ""])
                            line += 1

            # Add preset line after label change
            if is_label_change:
                label.replace("Preset ", "Preset {} ".format(event.preset))

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
                    ('TOPPADDING', (0, line), (-1, line), 0)
                ])

        # Add preset to therapy starts
        if event.id in {eID.THERAPY_START, eID.VENT_START} and \
                (event.therapy in {Therapies.VENTILATOR, Therapies.OXYGEN, Therapies.COUGH} and
                 (event.sub_therapy != SubTherapies.OXYGEN_FLUSH)):
            lines.append(["Preset", "{}: \"{}\"".format(event.preset, event.preset_label), ""])
            line += 1

        # Keep lines together
        if line != first_line:
            limit_line = 1 if line >= line_max else 0
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

    # Construct table style
    table_style = TableStyle(style_items)

    # Create combined list of data rows
    headers = [["Event", "", "Time"]]
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
        t = Table(data, colWidths=[2.4 * inch, 2.45 * inch, 2.4 * inch], rowHeights=heights, style=table_style,
                  repeatRows=1)
        story.append(t)

    # No data message
    else:
        story.append(Spacer(1, 0.5 * inch))
        story.append(Paragraph("No Events", s.subtitle))
