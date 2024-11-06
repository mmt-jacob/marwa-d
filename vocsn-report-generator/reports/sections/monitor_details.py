#!/usr/bin/env python
"""
Monitoring Details section, showing trend graphs for each monitored data stream.

    Version Notes:
        1.0.0.0 - 09/30/2019 - Created from with monitoring_details_section function.
        1.0.0.1 - 12/06/2019 - Moved usage/alarm graphs to top of page.
        1.0.0.2 - 12/11/2019 - Renamed to Monitor Details.
        1.0.0.3 - 12/13/2019 - Added section linking.
        1.0.0.4 - 01/12/2020 - Moved data container references for general template.
        1.0.0.5 - 01/25/2020 - Functions renamed.
        1.0.0.6 - 04/06/2020 - Corrected missing legends.

"""

__author__ = "John Dorian for Sai Systems Technologies"
__copyright__ = "Copyright 2019"
__version__ = "1.0.0.6"

# ReportLab libraries
from reportlab.lib.units import inch
from reportlab.platypus import Spacer
from reportlab.platypus import PageBreak
from reportlab.platypus import BaseDocTemplate
from reportlab.platypus import NextPageTemplate

# VOCSN modules
from modules.models import report as r
from modules.models import vocsn_data as vd
from reports.elements import footers as foot
from modules.models.errors import ErrorManager
from reports.elements.styles import Styles as s
from reports.elements.utilization_graph import UtilizationGraph
from reports.elements.general import general_template
from reports.elements.headers import standard as header
from reports.elements.monitor_graph import MonitorGraph
from reports.elements.templates import FormattedPage, Bookmark

# Global variables
SECTION_NAME = "Monitor Details"
REPORT = None
DATA = None
DIR = ""


def _first_page(c: FormattedPage, d: BaseDocTemplate):
    """
    First page template.
    :param c: Canvas reference passed from page constructor.
    :param d: Document reference passed from page constructor.
    """
    global REPORT, DATA, DIR

    # Header
    header(c, DIR, DATA.errors)

    # Footer
    foot.section(c, REPORT, SECTION_NAME)


def populate_graphs(em: ErrorManager):
    """ Adds graphs for each channel of monitored data, with alarm graph at end of page. """
    from reports.elements.monitor_graph import UsageTimerGraph
    global REPORT, DATA, DIR

    # Variables
    story = []

    # Process each monitored data channel
    first_page = True
    first = True
    graph_count = 0
    page_graph_count = 0
    graph_defs = REPORT.settings["display"]["monitor_graphs"].items()
    for key, graph_def in graph_defs:

        # Add alarm graph at end of page
        # Add more spacing on later pages that don't have a title
        if page_graph_count == 0:
            first = True
            if not first_page:
                gap = 0.25 * inch
                story.append(Spacer(1, 0.1 * inch))
            else:
                gap = 0.15 * inch
            story.append(UtilizationGraph(DIR, REPORT, DATA, 1 * inch))
            story.append(Spacer(1, gap))

        # Blank
        if "blank" in key:
            story.append(MonitorGraph(em, DIR, REPORT, None, "", False))

        # Usage table
        elif "usage" in key:
            story.append(UsageTimerGraph(DIR, REPORT, DATA))

        # Data graph
        else:

            # Lookup source
            source = graph_def["source"]
            label = graph_def["label"]

            # Create link destination
            mark = Bookmark("monitor_" + key)
            y_offset = -3*inch - page_graph_count*1.75*inch
            mark.offset = y_offset
            story.append(mark)

            # Graph from monitor data
            if source == "monitor":

                # Reference monitor channel
                monitor = DATA.monitors_all[key]

                # Add graph to story
                legend = first
                story.append(MonitorGraph(em, DIR, REPORT, monitor, label, legend))

            # Graph from therapy stop data
            elif source == "stop_value":

                # Reference therapy stop data
                therapy_name = graph_def["therapy"]
                tracker = getattr(DATA.events_tracker, therapy_name)
                session_values = tracker.session_vals[key]
                session_values.display_label = label

                # Add graph to story
                legend = first
                story.append(MonitorGraph(em, DIR, REPORT, session_values, label, legend))

        # Graph spacing
        if not first_page and graph_count < 4:
            story.append(Spacer(1, 0.08 * inch))

        # Account for graph space
        graph_count += 1
        page_graph_count += 1
        first = False

        # Move to next page
        if page_graph_count >= 4:
            page_graph_count = 0
            first_page = False
            first = True
            if graph_count < len(graph_defs):
                story.append(PageBreak())

    # Return story extensions
    return story


def monitor_details_section(em: ErrorManager, w_dir: str, doc: BaseDocTemplate, report: r.Report, data: vd.VOCSNData,
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
    link_name_arrive = "section_monitor_details"
    bottom_link_away = "section_trend_summary" if report.sections.trend_summary else None
    page_template = general_template(SECTION_NAME, doc, bottom_link=bottom_link_away)
    doc.addPageTemplates(page_template)

    # Add flowable elements
    story.append(NextPageTemplate(page_template.id))
    story.append(PageBreak())

    # Section title
    story.extend(s.section_title_flow(SECTION_NAME))

    # Add bookmark destination
    story.append(Bookmark(link_name_arrive))

    # Populate monitor graphs
    story.append(Spacer(1, 0.5 * inch))
    story.extend(populate_graphs(em))
