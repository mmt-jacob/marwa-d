#!/usr/bin/env python
"""
General page template. Includes header and footer only.

    Version Notes:
        1.0.0.0 - 09/12/2019 - Created from with general_template function.
        1.0.0.1 - 09/29/2019 - Fixed name to be unique.
        1.0.0.2 - 11/05/2019 - Moved things down to accommodate the multi-view logo.
        1.0.1.0 - 11/24/2019 - Added functions for a template with alarm graph at the top.
        1.0.1.1 - 12/12/2019 - Reworked section name management.
        1.0.1.2 - 12/13/2019 - Added arguments to support section linking.
        1.0.1.3 - 12/17/2019 - Added more space for section links at bottom of page.
        1.0.2.0 - 01/10/2020 - Streamlined some arguments.
        1.0.2.1 - 01/24/2020 - Adjusted usage/alarm graph on later pages of the settings section.

"""

__author__ = "John Dorian for Sai Systems Technologies"
__copyright__ = "Copyright 2019"
__version__ = "1.0.2.1"

# ReportLab libraries
from reportlab.lib import pagesizes
from reportlab.platypus import Frame
from reportlab.lib.units import inch
from reportlab.platypus import BaseDocTemplate

# VOCSN modules
from modules.models import report as r
from modules.models.report import Report
from modules.models import vocsn_enum as ve
from reports.elements import footers as foot
from modules.models.errors import ErrorManager
from modules.models.vocsn_data import VOCSNData
from reports.elements.utilization_graph import UtilizationGraph
from reports.elements.headers import standard as head
from modules.processing.resource_loader import load_fonts
from reports.elements.templates import CustomBaseDocTemplate
from reports.elements.templates import FormattedPage, SectionTemplate

# Global variables
SECTION_NAME = ""
REPORT = None
DATA = None
DIR = ""


def set_refs(data: VOCSNData, report: Report, w_dir: str):
    """
    Set memory references.
    :param data: VOCSN data container.
    :param report: Report definitions.
    :param w_dir: Working directory context.
    :return:
    """
    global DATA, REPORT, DIR
    DATA = data
    REPORT = report
    DIR = w_dir


def report_doc_setup(em: ErrorManager, data: VOCSNData, report: Report, title: str, auth: str, dir: str, filename: str):
    """
    Prepare base ReportLab document.
    :param em: Error manager.
    :param data: VOCSN data container.
    :param report: Report definitions.
    :param title: Report title.
    :param auth: Author of report.
    :param dir: Directory context.
    :param filename: Output filename.
    :return: Base doc template
    """

    # Catch errors
    try:

        load_fonts(dir)
        page_size = pagesizes.portrait(pagesizes.letter)
        doc = CustomBaseDocTemplate(filename, report, data,
                                    pagesize=page_size,
                                    leftMargin=0.5 * inch,
                                    rightMargin=0.5 * inch,
                                    topMargin=0.5 * inch,
                                    bottomMargin=0.5 * inch,
                                    title=title,
                                    author=auth,
                                    encrypt=None)

        # Return prepared doc
        return doc

    # Handle errors
    except Exception as e:
        message = "Error while preparing ReportLab document"
        em.log_error(ve.Programs.REPORTING, ve.ErrorCat.PROCESS_ERROR, ve.ErrorSubCat.INTERNAL_ERROR, message, e)
    return None


def _all_pages(c: FormattedPage, d: BaseDocTemplate, name: str, bottom_link: str = None):
    """
    First page template.
    :param c: Canvas reference passed from page constructor.
    :param d: Document reference passed from page constructor.
    :param name: Section name.
    :param bottom_link: Section destination mame for link at bottom of page.
    """
    global REPORT, DIR

    # Header
    head(c, DIR, DATA.errors)

    # Footer
    foot.section(c, REPORT, name, bottom_link)


def _alarm_pages(c: FormattedPage, d: BaseDocTemplate, name: str, bottom_link: str):
    """
    Page template with alarm graph.
    :param c: Canvas reference passed from page constructor.
    :param d: Document reference passed from page constructor.
    :param name: Section name.
    :param bottom_link: Section destination name for link at bottom of page.
    """
    global REPORT, DIR, DATA

    # Header and footer
    _all_pages(c, d, name, bottom_link)

    # Render alarm graph
    graph = UtilizationGraph(DIR, REPORT, DATA, 1 * inch, 1.139 * inch, 6.021 * inch)
    graph.wrap()
    graph.drawOn(c, 0.5835*inch, 8.75*inch)


def general_template(name: str, doc: BaseDocTemplate, bottom_link: str = None, bottom_margin: int = 0):
    """
    Create trending/calendar report section.
    :param name: Section name
    :param doc: Reference to main report document.
    :param bottom_link: Section destination name for link at bottom of page
    :param bottom_margin: Adds margin to bottom.
    """
    global SECTION_NAME, DATA, REPORT, DIR

    # Set global variables
    SECTION_NAME = name

    # Assemble page template
    template_name = SECTION_NAME.replace(' ', '') + "General"
    frames = [Frame(0.5 * inch, 0.5 * inch + bottom_margin, doc.width, doc.height - bottom_margin,
                    topPadding=0.75 * inch, bottomPadding=0.6 * inch, id=template_name)]
    return SectionTemplate(section=name, id=template_name, frames=frames, onPage=_all_pages, bottom_link=bottom_link)


def alarm_template(name: str, doc: BaseDocTemplate, bottom_link: str):
    """
    Create a general page with alarm graph at the top.
    :param name: Section name
    :param doc: Reference to main report document.
    :param bottom_link: Section destination name for link at bottom of page.
    """
    global SECTION_NAME, REPORT, DIR, DATA

    # Set global variables
    SECTION_NAME = name

    # Assemble page template
    template_name = SECTION_NAME.replace(' ', '') + "Alarm"
    frames = [Frame(0.5 * inch, 0.65 * inch, doc.width, doc.height - 0.15*inch,
                    topPadding=1.75 * inch, bottomPadding=0.6 * inch, id=template_name)]
    return SectionTemplate(id=template_name, frames=frames, onPage=_alarm_pages, section=SECTION_NAME,
                           bottom_link=bottom_link)
