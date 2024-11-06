#!/usr/bin/env python
"""
These functions construct common header objects.

    Version Notes:
        1.0.0.0 - 07/29/2019 - Created file with cover and standard functions.
        1.0.0.1 - 11/05/2019 - Switched to multi-view logo.
        1.0.0.2 - 11/18/2019 - Updated logo graphics, Enlarged header logo.
        1.0.0.3 - 11/19/2019 - Updated with new graphics names/dimensions.
        1.0.0.4 - 11/24/2019 - Expanded logo to page edges, shrunk report title.
        1.0.0.5 - 11/25/2019 - Adjusted table positioning.

"""

__author__ = "John Dorian for Sai Systems Technologies"
__copyright__ = "Copyright 2019"
__version__ = "1.0.0.5"

# Built-in modules
import os

# VOCSN modules
from modules.models import vocsn_enum as ve
from modules.models.errors import ErrorManager

# ReportLab libraries
from reportlab.lib.units import inch
from reportlab.pdfgen.canvas import Canvas
from reports.elements.styles import Styles as s


def cover(c: Canvas, d: str):
    """
    Cover page header elements.
    :param c: Canvas from a template definition.
    :param d: Program execution directory.
    """

    # Main logo
    logo_path = os.path.join(d, "resources", "images", "Multi-View_Logo_Title-Page.png")
    left = 0.0 * inch
    bottom = 7.65 * inch
    width = 8.5 * inch
    height = 3.35 * inch
    # c.drawImage(logo_path, left, bottom, preserveAspectRatio=True, width=width)
    c.drawImage(logo_path, left, bottom, width=width, height=height)

    # Report title
    center = 4.25 * inch
    bottom = 8.00 * inch
    c.setFont(s.Fonts.heavy, 20)
    c.setFillColor(s.Colors.white)
    c.drawCentredString(center, bottom, "Usage Report")
    # logo_path = os.path.join(d, "resources", "images", "usage_title.png")
    # left = 0.5 * inch
    # bottom = 7.1 * inch
    # width = 7.5 * inch
    # c.drawImage(logo_path, left, bottom, preserveAspectRatio=True, width=width)


def standard(c: Canvas, d: str, em: ErrorManager):
    """
    Standard header elements.
    :param c: Canvas from a template definition.
    :param d: Program execution directory.
    :param em: Error manager.
    """

    # Logo
    logo_path = os.path.join(d, "resources", "images", "Multi-View_Logo-Header.png")
    left = 0.5 * inch
    bottom = 10.055 * inch
    width = 1.65 * inch
    height = 0.65 * inch
    c.drawImage(logo_path, left, bottom, width=width, height=height, mask="auto")

    # Colored bar
    c.setFillColor(s.Colors.dark_blue)
    c.rect(0.5 * inch, 9.9 * inch, 7.5 * inch, 0.12 * inch, stroke=0, fill=1)

    # Advisory notice
    if em.status == ve.ErrorLevel.ADVISORY:
        left = 4.5 * inch
        right = 8 * inch
        bottom = 10.125 * inch
        c.setFont(s.Fonts.heavy, 14)
        c.setFillColor(s.Colors.dark_gray)
        size = 22
        warn_path = os.path.join(d, "resources", "images", "warn.png")
        c.drawImage(warn_path, left, bottom - 0.07 * inch, width=size, height=size, mask="auto")
        c.drawRightString(right, bottom, "Some data could not be displayed.")

    # # Logo
    # logo_path = os.path.join(d, "resources", "images", "VOCSN_multi_beta_dark_small.png")
    # left = 0.5 * inch
    # bottom = 9.07 * inch
    # width = 1.25 * inch
    # c.drawImage(logo_path, left, bottom, preserveAspectRatio=True, width=width)
    #
    # # Colored bar
    # c.setFillColor(s.Colors.dark_blue)
    # c.rect(0.5 * inch, 10.1 * inch, 7.5 * inch, 0.08 * inch, stroke=0, fill=1)
