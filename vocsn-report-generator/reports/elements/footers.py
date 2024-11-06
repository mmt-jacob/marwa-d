#!/usr/bin/env python
"""
These functions construct common footer objects.

    Version Notes:
        1.0.0.0 - 07/29/2019 - Created file with name, section and page functions.
        1.0.0.1 - 09/09/2019 - Uses ReportLab overrides.
        1.0.0.2 - 09/12/2019 - Replaced patient name with report name when not storing PHI.
        1.0.0.3 - 11/01/2019 - Swapped report name for device serial number in lower left corner with PHI disabled.
        1.0.0.4 - 12/12/2019 - Reworked section name management.
        1.0.1.0 - 12/13/2019 - Added section links.

"""

__author__ = "John Dorian for Sai Systems Technologies"
__copyright__ = "Copyright 2019"
__version__ = "1.0.1.0"

# ReportLab libraries
from reportlab.lib.units import inch
from reportlab.pdfgen.canvas import Canvas
from reports.elements.styles import Styles as s

# VOCSN modules
from modules.models.report import Report
from modules.models.vocsn_data import VOCSNData


def name(c: Canvas, r: Report):
    """
    Patient name.
    :param c: Canvas from a template definition.
    :param r: Report definitions.
    """

    # Name is replaced with report name
    if r.settings["system"]["store_phi"]:
        text = "{}, {}".format(r.patient.name_lst, r.patient.name_fst)
    else:
        text = r.name

    # Show serial number and date range in lower-left corner of page
    c.saveState()
    c.setFont(s.Fonts.light, 13)
    c.setFillColor(s.Colors.med_gray)
    c.drawString(0.5 * inch, 0.5 * inch, text)
    c.restoreState()


def name_sn(c: Canvas, d: VOCSNData,  r: Report):
    """
    Patient name or serial number.
    :param c: Canvas from a template definition.
    :param d: VOCSN Data container reference.
    :param r: Report definitions.
    """

    # Name is replaced with serial number when PHI is disabled
    if r.settings["system"]["store_phi"]:
        text = "{}, {}".format(r.patient.name_lst, r.patient.name_fst)
    else:
        text = d.sn

    # Show serial number and date range in lower-left corner of page
    c.saveState()
    c.setFont(s.Fonts.light, 13)
    c.setFillColor(s.Colors.med_gray)
    c.drawString(0.5 * inch, 0.5 * inch, text)
    c.restoreState()


def section(c: Canvas, r: Report, section_name: str = None, bottom_link: str = None):
    """
    Section name footer.
    :param c: Canvas from a template definition.
    :param section_name: Section name.
    :param r: Report definitions.
    :param bottom_link: Section destination name for link at bottom of page.
    """

    # Show section name in bottom center of page
    c.saveState()
    c.setFont(s.Fonts.light, 13)
    c.setFillColor(s.Colors.med_gray)
    disp_str = ""
    if section_name:
        disp_str = "{}  |  ".format(section_name)
    disp_str += r.range.range_string()
    c.drawCentredString(4.25 * inch, 0.5 * inch, disp_str)

    # Link button
    if bottom_link:

        # Create display name
        font_size = 16
        bottom = 0.75 * inch
        link_name = bottom_link.replace("section_", "")
        link_name = link_name.replace("_", " ").title()
        c.setFont(s.Fonts.heavy, font_size)
        text_width = c.stringWidth(link_name)
        width = text_width + 20
        height = font_size + 5
        radius = 0.5 * height
        x = 4.25*inch - 0.5 * width
        y = bottom
        c.setFillColor(s.Colors.orange)
        c.roundRect(x, y, width, height, radius, stroke=0, fill=1)
        x = 4.25*inch
        y = bottom + 5
        c.setFillColor(s.Colors.white)
        c.drawCentredString(x, y, link_name)
        x1 = 4.25*inch - 0.5*width
        x2 = 4.25*inch + 0.5*width
        y1 = bottom
        y2 = bottom + height
        c.linkAbsolute(link_name, bottom_link, (x1, y1, x2, y2))
    c.restoreState()


def page(c: Canvas, this_page: int, total_pages: int):
    """
    Page number footer.
    :param c: Canvas from a template definition.
    :param this_page: Current page number.
    :param total_pages: Total page count.
    """

    # Show page number in lower-right corner of page
    c.saveState()
    c.setFont(s.Fonts.light, 13)
    c.setFillColor(s.Colors.med_gray)
    c.drawRightString(8 * inch, 0.5 * inch, "Page {} of {}".format(this_page, total_pages))
    c.restoreState()
