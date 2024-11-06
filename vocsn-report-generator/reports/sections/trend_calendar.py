#!/usr/bin/env python
"""
Trending summary and usage calendar report section.

    Version Notes:
        1.0.0.0 - 09/07/2019 - Created from with TrendCalendar function.
        1.0.0.1 - 09/09/2019 - Experimented with flowables.
        1.0.0.2 - 09/12/2019 - Laid out "element" table.
        1.0.0.3 - 10/10/2019 - Updated to use newly-calculated trend values.
        1.0.1.0 - 10/24/2019 - Added O2-specific blocks
        1.0.1.1 - 10/27/2019 - Restructured special blocks at end of table.
        1.0.1.2 - 11/01/2019 - Pulling precision from metadata.
        1.0.1.3 - 11/02/2019 - Updated trend calculation field names.
        1.0.1.4 - 11/03/2019 - Added bleed-in values, legend block.
        1.0.1.5 - 11/05/2019 - Moved things down to accommodate the multi-view logo.
        1.0.1.6 - 11/14/2019 - Updated some values based on report feedback.
        1.0.1.7 - 11/19/2019 - Updated for new graphics names.
        1.0.1.8 - 11/20/2019 - Updated flush units.
        1.0.1.9 - 11/22/2019 - Darkened oxygen color.
        1.0.2.0 - 11/28/2019 - Added calendar legend.
        1.0.2.1 - 12/11/2019 - Renamed to Trend Summary.
        1.0.2.2 - 12/12/2019 - Reworked section name management.
        1.0.2.3 - 12/13/2019 - Added section linking.
        1.0.2.4 - 12/18/2019 - Changed nebulizer duration calculations.
        1.0.2.5 - 12/20/2019 - Range days was changed to float. Rounded for display in title.
        1.0.2.6 - 12/21/2019 - Integrated error management.
        1.0.2.7 - 01/12/2020 - Moved data container references for general template.
        1.0.2.8 - 01/16/2020 - Added an "Insufficient Data" message when both trend and preceding ranges aren't used.
        1.0.2.9 - 01/17/2020 - Shrank top blocks and removed their trends. Changed neb units to minutes.
        1.0.3.0 - 01/19/2020 - Added no data bars to graph.
        1.0.3.1 - 01/20/2020 - Adapted labels for use without trends.
        1.0.3.2 - 02/04/2020 - Changed trend label for cough flow.
        1.0.3.3 - 02/09/2020 - Fixed PDF links for cough blocks.
        1.0.3.4 - 03/10/2020 - Added missing period to trend range description.
        1.0.4.0 - 03/11/2020 - Disabled day-based averages in reports under a day.
        1.0.4.1 - 03/27/2020 - Changed precision on flush sessions block, changed source data for legend trend range.

"""

__author__ = "John Dorian for Sai Systems Technologies"
__copyright__ = "Copyright 2019"
__version__ = "1.0.4.1"

# Built-in modules
import os
import math
from datetime import timedelta

# ReportLab libraries
from reportlab.lib import colors
from reportlab.platypus import Frame
from reportlab.lib.units import inch
from reportlab.platypus import Spacer
from reportlab.platypus import Paragraph
from reportlab.platypus import PageBreak
from reportlab.platypus.tables import Table
from reportlab.platypus import KeepTogether
from reportlab.platypus import BaseDocTemplate
from reportlab.platypus import NextPageTemplate

# VOCSN modules
from modules.models import report as r
from modules.models import vocsn_enum as ve
from modules.models import vocsn_data as vd
from reports.elements import footers as foot
from modules.models.errors import ErrorManager
from reports.elements.styles import Styles as s
from reports.elements.templates import TrendTable
from modules.processing.utilities import flex_float
from reports.elements.general import general_template
from reports.elements.headers import standard as header
from reports.elements.trend import trend_img, TrendBlock, CalDay, CalLegend
from reports.elements.templates import FormattedPage, SectionTemplate, Bookmark

# Global variables
SECTION_NAME = "Trend Summary"
REPORT = None
DATA = None
DIR = ""


def _first_page(c: FormattedPage, _: BaseDocTemplate, name: str, bottom_link: str = None):
    """
    First page template.
    :param c: Canvas reference passed from page constructor.
    :param _: Document reference passed from page constructor.
    :param name: Section name.
    :param bottom_link: Section destination name for link at bottom of page.
    """
    global REPORT, DATA, DIR

    # Header
    header(c, DIR, DATA.errors)

    # Trend average period message
    day_close_enough = timedelta(minutes=1435)
    use_days = REPORT.range.data_duration >= day_close_enough
    day = timedelta(days=1)
    r = REPORT.range
    if r.use_trend:
        units = r.trend_units if r.trend_period > 1 else r.trend_units[:-1]
        text = "Values are a {}-day average with      or      trended based on the last {} {}.".format(
            round(r.average_days),
            r.trend_period,
            units
        )
    else:
        avg_units = "day" if r.duration > day else "hour"
        avg_duration = round(r.days) if r.duration > day else round(r.duration.total_seconds() / 3600)
        if use_days:
            text = "Values are a {}-{} average. Insufficient data to calculate trends.".format(avg_duration, avg_units)
        else:
            text = "Values are a {}-{} average. Insufficient data to calculate trends or daily counts."\
                .format(avg_duration, avg_units)
    bottom = 9.25 * inch
    c.setFont(s.Fonts.light, 14)
    c.setFillColor(s.Colors.black)
    c.drawString(0.6 * inch, bottom, text)

    # Draw trend arrow images
    if REPORT.range.use_trend:
        bottom -= 0.43 * inch
        range_offset = 0 if REPORT.range.average_days < 10 else 0.1 * inch
        path = os.path.join(DIR, "resources", "images", "Multi-View_Arrow-Up.png")
        c.drawImage(path, 3.36*inch + range_offset, bottom, preserveAspectRatio=True, width=0.2 * inch, mask="auto")
        path = os.path.join(DIR, "resources", "images", "Multi-View_Arrow-Down.png")
        c.drawImage(path, 3.85*inch + range_offset, bottom, preserveAspectRatio=True, width=0.2 * inch, mask="auto")

    # Footer
    foot.section(c, REPORT, name, bottom_link)


def trend_table(em: ErrorManager):
    """ Create the trend table to manage the blocks for each monitor trend block. """
    global DIR, DATA, REPORT

    def check_for_monitor(param: str):
        """ Check if parameter ID is displayed as a monitor graph. """
        for graph in REPORT.settings["display"]["monitor_graphs"]:
            if graph == param:
                return True
        return False

    # Settings
    data = []
    off = None
    day_close_enough = timedelta(minutes=1435)
    use_days = REPORT.range.data_duration >= day_close_enough
    short = [0.95 * inch, 0.65 * inch]
    size = [0.95*inch, 0.75*inch]
    img_size = ve.ImgSizes.LRG

    # Start data with row of icon blocks
    data.append([
        trend_img(DIR, 'V', img_size),
        "",
        trend_img(DIR, 'O', img_size),
        "",
        trend_img(DIR, 'C', img_size),
        trend_img(DIR, 'S', img_size),
        trend_img(DIR, 'N', img_size)
    ])
    
    # Gather ventilation values
    vent_track = DATA.events_tracker.ventilator
    vent_use_hours_all = vent_track.hours_per_all_day if use_days else off
    vent_use_hours_used = vent_track.hours_per_used_day if use_days else off
    vent_use_hours_all_perc = vent_track.hours_per_all_day_trend_percent if use_days else off
    vent_use_hours_used_perc = vent_track.hours_per_used_day_trend_percent if use_days else off

    # Gather O2 values
    o2_track = DATA.events_tracker.oxygen if use_days else off
    fio2_hours = o2_track.fio2_hours_per_day if use_days else off
    flow_hours = o2_track.flow_hours_per_day if use_days else off
    bleed_hours = o2_track.bleed_hours_per_day if use_days else off
    flush_per_day = o2_track.o2_flush_sessions_per_day if use_days else off
    fio2_percent = o2_track.fio2_percent if use_days else off
    flow_percent = o2_track.flow_percent if use_days else off
    bleed_percent = o2_track.bleed_percent if use_days else off
    flush_per_day_perc = o2_track.o2_flush_sessions_percent if use_days else off

    # Gather cough values
    cough_track = DATA.events_tracker.cough
    c_per_day = cough_track.sessions_per_day_all if use_days else off
    c_per_day_perc = cough_track.sessions_per_day_percent if use_days else off

    # Gather suction values
    suc_track = DATA.events_tracker.suction
    s_per_day = suc_track.sessions_per_day_all if use_days else off
    s_per_day_perc = suc_track.sessions_per_day_percent if use_days else off
    s_min_per_day = suc_track.calendar.min_sess_per_day if use_days else off
    s_max_per_day = suc_track.calendar.max_sess_per_day if use_days else off

    # Gather nebulizer values
    neb_track = DATA.events_tracker.nebulizer
    n_per_day = neb_track.sessions_per_day_all if use_days else off
    n_per_day_perc = neb_track.sessions_per_day_percent if use_days else off
    n_min_per_day = neb_track.calendar.min_sess_per_day if use_days else off
    n_max_per_day = neb_track.calendar.max_sess_per_day if use_days else off

    # First block row - Usage 1
    track = DATA.events_tracker
    data.append([
        TrendBlock(em, DIR, short, s.Colors.ventilator_light, "Days Used", track.ventilator.active_days, 0, "",
                   track.ventilator.trend_percent, has_trend=False),
        "",
        TrendBlock(em, DIR, short, s.Colors.oxygen_light, "Days Used", track.oxygen.active_days, 0, "",
                   track.oxygen.trend_percent, has_trend=False),
        "",
        TrendBlock(em, DIR, short, s.Colors.cough_light, "Days Used", track.cough.active_days, 0, "",
                   track.cough.trend_percent, has_trend=False),
        TrendBlock(em, DIR, short, s.Colors.suction_light, "Days Used", track.suction.active_days, 0, "",
                   track.suction.trend_percent, has_trend=False),
        TrendBlock(em, DIR, short, s.Colors.nebulizer_light, "Days Used", track.nebulizer.active_days, 0, "",
                   track.nebulizer.trend_percent, has_trend=False)
    ])

    # Second block row - Usage 2
    data.append([
        TrendBlock(em, DIR, size, s.Colors.ventilator_light, "Use Hours\n(of days used)",
                   flex_float(vent_use_hours_used, 0), 0, "/Day", vent_use_hours_used_perc, in_use=use_days),
        TrendBlock(em, DIR, size, s.Colors.ventilator_light, "Use Hours\n(of all days)",
                   flex_float(vent_use_hours_all, 0), 0, "/Day", vent_use_hours_all_perc, in_use=use_days),
        TrendBlock(em, DIR, size, s.Colors.oxygen_light, "Use Hours\n(of Pulse Dose)", flow_hours, 0, "/Day",
                   flow_percent, in_use=use_days),
        TrendBlock(em, DIR, size, s.Colors.oxygen_light, "Use Hours\n(of FiO2)", fio2_hours, 0, "/Day", fio2_percent,
                   in_use=use_days),
        TrendBlock(em, DIR, size, s.Colors.cough_light, "Cough\nSessions", flex_float(c_per_day, 2), 1, "/Day",
                   c_per_day_perc, in_use=use_days),
        TrendBlock(em, DIR, size, s.Colors.suction_light, "Suction\nSessions", flex_float(s_per_day, 2), 1, "/Day",
                   s_per_day_perc, in_use=use_days),
        TrendBlock(em, DIR, size, s.Colors.nebulizer_light, "Nebulizer\nSessions", flex_float(n_per_day, 2), 1, "/Day",
                   n_per_day_perc, in_use=use_days)
    ])

    # ---- Parameterized rows ---- #

    # Placeholders for end-of-table blocks
    placeholders = [0, 2, 4, 1, 1]

    # Check number of additional rows needed
    block_defs = REPORT.settings["display"]["trend_table"]
    row_count = 0
    p_idx = 0
    for key, therapy in block_defs.items():
        rows = len(therapy) + placeholders[p_idx]
        if key in ["ventilator", "oxygen"]:
            rows = math.ceil(rows / 2)
        elif key == "nebulizer":    # Reserve space for legend
            rows += 2
        row_count = max(row_count, rows)
        p_idx += 1

    # Add blocks one row at a time
    cols = ["ventilator", "ventilator", "oxygen", "oxygen", "cough", "suction", "nebulizer"]
    for row in range(0, row_count):
        row_data = []

        # Add cell for each column/therapy
        for col in range(0, 7):
            therapy = cols[col]
            vo_idx = 2*row + ((col % 2) != 0)
            idx = vo_idx if col < 4 else row
            block_def = block_defs[therapy]

            # End of parameterized list
            if idx >= len(block_def):

                # Add special O2 blocks
                if col in [2, 3] and vo_idx == len(block_def):
                    row_data.append(TrendBlock(em, DIR, size, s.Colors.oxygen_light, "Use Hours\n(of Bleed In)",
                                               bleed_hours, 0, "/Day", bleed_percent, in_use=use_days))
                elif col in [2, 3] and vo_idx == len(block_def) + 1:
                    row_data.append(TrendBlock(em, DIR, size, s.Colors.oxygen_light, "O2 Flush\nSessions",
                                               flex_float(flush_per_day, 2), 1, "/Day", flush_per_day_perc,
                                               in_use=use_days))

                # Add special Cough blocks
                elif col in [4] and idx >= len(block_def):
                    do_link = REPORT.sections.monitor_details
                    source = track.cough
                    if idx == 0:
                        link = "monitor_12026" if do_link else None
                        row_data.append(TrendBlock(em, DIR, size, s.Colors.cough_light, "Cycles/Session",
                                                   source.cough_avg_cycles, 0, "", source.cough_percent_cycles,
                                                   link=link))
                    elif idx == 1:
                        link = "monitor_12024" if do_link else None
                        row_data.append(TrendBlock(em, DIR, size, s.Colors.cough_light, "Peak Cough\nFlow",
                                                   source.cough_avg_peak_flow, 0, "L/min",
                                                   source.cough_percent_peak_flow, link=link))
                    elif idx == 2:
                        link = "monitor_12025" if do_link else None
                        row_data.append(TrendBlock(em, DIR, size, s.Colors.cough_light, "Cough Volume",
                                                   source.cough_avg_volume, 0, "mL",
                                                   source.cough_percent_volume, link=link))
                    elif idx == 3:
                        row_data.append(TrendBlock(em, DIR, size, s.Colors.cough_light, "Peak +/- Pres.",
                                                   source.cough_avg_in_press, 0, "cmH2O", None, split=True,
                                                   split_val=source.cough_avg_ex_press,
                                                   split_unit="", show_sign=True))

                # Add special Suction blocks
                elif col in [5] and idx == len(block_def):
                    row_data.append(TrendBlock(em, DIR, size, s.Colors.suction_light, "Sessions/Day", s_min_per_day,
                                               0, "min", None, split=True, split_val=s_max_per_day, split_unit="max",
                                               in_use=use_days))

                # Add special Nebulizer blocks
                elif col in [6] and idx == len(block_def):
                    row_data.append(TrendBlock(em, DIR, size, s.Colors.nebulizer_light, "Sessions/Day", n_min_per_day,
                                               0, "min", None, split=True, split_val=n_max_per_day, split_unit="max",
                                               in_use=use_days))

                # Add legend
                elif col in [6] and row == row_count - 1:
                    row_data.append(TrendBlock(em, DIR, size, s.Colors.med_gray, "", 0, 0, "", None, legend=True,
                                               duration=[REPORT.range.duration, REPORT.range.raw_trend_duration],
                                               has_trend=REPORT.range.use_trend))

                # Add blank cell
                else:
                    row_data.append(None)

            # Fill with a block
            else:

                # Read block definition
                key = list(block_def)[idx]
                source_def = block_def[key]
                color = getattr(s.Colors, therapy + "_light")

                # Set link name if applicable
                link_name = None
                if REPORT.sections.monitor_details and check_for_monitor(key):
                    link_name = "monitor_" + key

                # Build with monitor value types
                if source_def["source"] == "monitor":
                    monitor = DATA.monitors_all[key]
                    label = source_def["label"]
                    value = monitor.average
                    units = monitor.display_units
                    trend = monitor.trend_percent
                    delta = monitor.trend_delta
                    precision = monitor.precision
                    row_data.append(TrendBlock(em, DIR, size, color, label, value, precision, units, trend, delta=delta,
                                               link=link_name))

                # Build with settings value types
                elif source_def["source"] == "setting":
                    setting = DATA.settings_all[key]
                    label = source_def["label"]
                    value = setting.average_value
                    units = setting.definition["displayUnits"]
                    trend = setting.trend_percent
                    delta = setting.trend_delta
                    precision = setting.definition["precision"]
                    row_data.append(TrendBlock(em, DIR, size, color, label, value, precision, units, trend, delta=delta,
                                               link=link_name))

                # Build with therapy start/stop value types
                elif source_def["source"] == "stop_value":
                    t = getattr(DATA.events_tracker, therapy)
                    if key == "neb-duration":   # Override units to minutes
                        label = source_def["label"]
                        value = (t.neb_average_duration / 60) if t.neb_average_duration else None
                        units = "min"
                        trend = t.neb_trend_percentage if t.neb_trend_percentage else 0
                        delta = t.neb_trend_delta if t.neb_trend_delta else 0
                        precision = 0
                    else:
                        if key == "55":
                            stop_val = t.session_vals[key]
                        else:
                            stop_val = t.session_vals[key]
                        label = source_def["label"]
                        value = stop_val.average
                        units = stop_val.units
                        trend = stop_val.trend_percent
                        delta = stop_val.trend_delta
                        precision = stop_val.precision
                    row_data.append(TrendBlock(em, DIR, size, color, label, value, precision, units, trend, delta=delta,
                                               link=link_name))

        # Add row to data
        data.append(row_data)

    # ---- Formatting ---- #

    # Basic formats
    table_style = [('SPAN', (0, 0), (1, 0)),
                   ('SPAN', (2, 0), (3, 0)),
                   ('SPAN', (0, 1), (1, 1)),
                   ('SPAN', (2, 1), (3, 1)),
                   # ('GRID', (0, 0), (-1, -1), 1, colors.rgb2cmyk(0.8, 0.8, 0.8)),
                   ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                   ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                   ('VALIGN', (-1, -1), (-1, -1), 'BOTTOM'),
                   ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                   ('FONT', (0, 0), (-1, -1), "Helvetica"),
                   ('FONTSIZE', (0, 0), (-1, -1), 12)]

    # ---- Formatting ---- #

    # Place trend arrows in average period message
    widths = [1.037*inch for _ in range(0, len(data[0]))]
    heights = [0.9*inch, 0.72*inch] + (len(data) - 2) * [0.82*inch]
    return TrendTable(data=data, colWidths=widths, rowHeights=heights, style=table_style, repeatRows=1)


class NoDataBar:
    """ Tracking for no data bar on calendar. """

    def __init__(self, week: int, day: int):
        """ Store the start day and duration of a no-data bar. """
        self.week = week
        self.day = day
        self.length = 1

    def add_day(self):
        """ Count another day to bar length. """
        self.length += 1
        self.day += 1


def trend_calendar(data: vd.VOCSNData):
    """
    Draw a calendar showing therapy usage for all days in the report range, expanded to round out full weeks.
    :param data: VOCSN data.
    :return: Completed usage calendar wrapped in a KeepTogether flowable.
    """
    global DIR, REPORT

    # References
    usage = data.events_tracker

    # Title
    style = s.subtitle
    title = Paragraph("Compliance Calendar", style)

    # Prepare no-data bar tracking
    start_dt = REPORT.range.data_start
    if data.events_all:
        start_dt = data.events_all[0].syn_time
    data_started = False
    data_bars = []
    bar = None

    # Setup table data
    day_list = usage.ventilator.calendar.days
    cal_data = [[None] * 7]
    week = 0
    week_day = 0
    day_count = 0
    for day, stats in day_list.items():

        # Manage no data bars
        if stats.end > start_dt:
            data_started = True
        if not data_started and stats.in_range:
            if bar:
                bar.add_day()
            else:
                bar = NoDataBar(week, week_day)
        if week_day >= 6 and bar:
            data_bars.append(bar)
            bar = None

        # Prepare calendar days
        cal_data[week][week_day] = CalDay(DIR, data, day, stats.in_range, stats.complete)
        week_day += 1
        day_count += 1
        if week_day >= 7 and day_count < len(day_list):
            cal_data.append([None] * 7)
            week += 1
            week_day = 0

    # Apply bars
    for bar in data_bars:
        cal_data[bar.week][bar.day].bar = bar

    # Basic formats
    table_style = [('GRID', (0, 0), (-1, -1), 0.5, colors.black)]
    
    # Assemble table
    widths = [CalDay.size[0]] * 7
    heights = [CalDay.size[1]] * len(cal_data)
    cal_grid = Table(data=cal_data, colWidths=widths, rowHeights=heights, style=table_style, spaceBefore=0.3*inch,
                     repeatRows=0)

    # Create legend
    legend = CalLegend(DIR)

    # Return completed calendar
    calendar_stack = KeepTogether([title, Spacer(1, 0.01 * inch), cal_grid, legend])
    return calendar_stack


def trend_calendar_section(em: ErrorManager, w_dir: str, doc: BaseDocTemplate, report: r.Report, data: vd.VOCSNData,
                           story: list):
    """
    Create trending/calendar report section.
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
    link_name_arrive = "section_trend_summary"
    bottom_link_away = "section_monitor_details" if report.sections.monitor_details else None
    frames = [Frame(0.5 * inch, 0.5 * inch, doc.width, doc.height,
                    topPadding=0.65 * inch, bottomPadding=0.6 * inch, id='TrendCalendar')]
    first_template = SectionTemplate(id="TrendCalendar", frames=frames, onPage=_first_page, section=SECTION_NAME,
                                     bottom_link=bottom_link_away)
    later_template = general_template(SECTION_NAME, doc, bottom_link=bottom_link_away)
    doc.addPageTemplates(first_template)
    doc.addPageTemplates(later_template)

    # Add flowable elements
    story.append(NextPageTemplate("TrendCalendar"))
    story.append(PageBreak())
    story.append(NextPageTemplate(later_template.id))

    # Section title
    story.extend(s.section_title_flow(SECTION_NAME))

    # Add bookmark destination
    story.append(Bookmark(link_name_arrive))

    # Create trend table
    story.append(Spacer(1, 0.78 * inch))
    story.append(trend_table(em))

    # Create calendar
    story.append(Spacer(1, 0.2 * inch))
    story.append(trend_calendar(data))
