#!/usr/bin/env python
"""
Report cover sheet section.

    Version Notes:
        1.0.0.0 - 07/22/2019 - Created from with CoverSection function.
        1.0.0.1 - 07/28/2019 - Added Avenir font, improved spacing, and added report section field.
        1.0.0.2 - 09/12/2019 - Create PHI and No-PHI variant with tedt field inputs.
        1.0.0.3 - 09/28/2019 - Change report date label to "creation" date.
        1.0.0.4 - 11/24/2019 - Changed AcroField procedure to ensure proper tab order, changed disclaimer color/font.
        1.0.0.5 - 12/20/2019 - Added filter to omit requested sections that were unavailable.
        1.0.0.6 - 01/01/2020 - Sourced report creation date from input to allow for localization.

"""

__author__ = "John Dorian for Sai Systems Technologies"
__copyright__ = "Copyright 2019"
__version__ = "1.0.0.6"

# ReportLab libraries
from reportlab.lib import colors
from reportlab.platypus import Frame
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph
from reportlab.platypus.tables import Table
from reportlab.platypus import PageTemplate
from reportlab.platypus import BaseDocTemplate
from reportlab.platypus import NextPageTemplate

# VOCSN modules
from modules.models import report as r
from modules.models import vocsn_data as vd
from reports.elements.styles import Styles as s
from reports.elements.headers import cover as header
from reports.elements.templates import FormattedPage

# Global variables
REPORT = None
DATA = None
DIR = ""

# Settings
USE_LABEL = False


def _cover_page(c: FormattedPage, _: BaseDocTemplate):
    """
    First page template.
    :param c: Canvas reference passed from page constructor.
    :param _: Document reference passed from page constructor.
    """
    global REPORT, DIR, y_offset, USE_LABEL

    # Input field generator
    if USE_LABEL:
        single_height = 20.5
        multi_height = 40
    else:
        single_height = 22.5
        multi_height = 40
    y_offset = 0.5 - single_height

    def text_field(name: str, multi: bool = False):
        global y_offset
        field_flags = "multiline" if multi else ""
        x = 204
        y = 300 if USE_LABEL else 257
        width = 368.5
        height = multi_height if multi else single_height   # Auto-increment vertical placement
        y_offset += height + 5.5                       # Account for notes to be taller
        max_chars = 88 if multi else 36
        c.acroForm.textfield(
            value="",
            maxlen=max_chars,
            x=x,
            y=y-y_offset,
            width=width,
            height=height,
            fontName='Helvetica',
            fontSize=12,
            textColor=s.Colors.dark_gray,
            borderWidth=0,
            fillColor=s.Colors.white,
            # borderColor=s.Colors.dark_gray,
            tooltip=name,
            fieldFlags=field_flags,
            annotationFlags='print'
        )
        return ""

    # Main logo
    header(c, DIR)

    # Section Title
    c.setFont(s.Fonts.title, 24)
    c.setFillColor(s.Colors.dark_blue)
    c.drawString(0.59 * inch, 7.245 * inch, "Report Information")

    # Section List
    section_list = REPORT.sections.section_list()
    style = [('FONT', (0, 0), (-1, -1), s.Fonts.table),
             ('FONTSIZE', (0, 0), (-1, -1), 12),
             ('TEXTCOLOR', (0, 0), (-1, -1), s.Colors.dark_gray)]
    widths = 3 * [1.75 * inch]
    section_table = Table(data=section_list, colWidths=widths, style=style)

    # Prepare data
    if REPORT.settings["system"]["store_phi"]:
        patient = REPORT.patient.full_name()
        patient_id = REPORT.patient.ref_num
        patient_dob = REPORT.patient.dob_string()
        equipment = ""  # TODO: Determine source?
        physician = REPORT.physician.full_name()
        institution = REPORT.institute.name
        notes = Paragraph(REPORT.notes, s.cover_wrap)
    else:
        # Populated in reverse order
        multi_line = True
        patient = text_field("Enter the patient's name.")
        patient_id = text_field("Enter an identification number for the patient.")
        patient_dob = text_field("Enter the patient's date of birth.")
        equipment = text_field("Enter a description of equipment used.")
        physician = text_field("Enter the physician's name.")
        institution = text_field("Enter the affiliation or institution name.")
        notes = text_field("Enter any notes regarding patient care.", multi_line)
    disclaimer = "Note: The dates and times shown in this report are relative to the most recent VOCSN\n" \
                 "Date and Time setting. Reports that span daylight savings, time zone, or other VOCSN Date and\n" \
                 "Time changes will contain event timestamps calculated backwards from the most recent setting."

    # Field table
    widths = [2.25 * inch, 5.25 * inch]
    # sh = 0.388 * inch     # Standard row height

    if USE_LABEL:
        sh = 0.362 * inch  # Standard row height
        heights = [sh, sh, sh, sh, sh, sh, 2.6 * sh, sh, sh, sh, sh, sh, sh, sh, 1.5 * sh]
    else:
        sh = 0.388 * inch  # Standard row height
        heights = [sh, sh, sh, sh, sh, sh, 2.4 * sh, sh, sh, sh, sh, sh, sh, 1.5 * sh]
    t_height = sum(heights)
    ver = DATA.version
    if ver and ver[-1] in ["R", "D"]:
        ver = ver[:-1]
    v = "v" if ver else ""
    data = [["Serial Number", DATA.sn],
            ["Configuration", "{}  {}{}".format(DATA.configuration, v, ver)],
            ["Report Creation Date", REPORT.created_string()],
            ["Report Duration", REPORT.range.duration_string()],
            ["Report Date Range", REPORT.range.range_string()],
            ["", disclaimer],
            ["Report Sections", section_table]]
    if USE_LABEL:
        data.append(["Report Label", REPORT.label])
    data.extend([
        ["Patient", patient],
        ["Patient Reference ID", patient_id],
        ["Date of Birth", patient_dob],
        ["Equipment Used", equipment],
        ["Physician", physician],
        ["Affiliation or Institution", institution],
        ["Comments", notes]])
    style = [("FONT", (0, 0), (0, -1), s.Fonts.heavy),
             ("FONT", (1, 0), (1, -1), s.Fonts.table),
             ('FONTSIZE', (0, 0), (-1, -1), 12),
             ("FONTSIZE", (1, 5), (1, 5), 8),
             ('TEXTCOLOR', (0, 0), (-1, -1), s.Colors.dark_gray),
             ('VALIGN', (0, 0), (-1, -1), "TOP"),
             ('TOPPADDING', (0, 0), (-1, -1), 6),
             ('TOPPADDING', (0, 5), (-1, 5), -5),
             ('LEADING', (0, 5), (-1, 5), 10),
             ('LEFTPADDING', (0, 0), (-1, -1), 7),
             ('LEFTPADDING', (1, 6), (1, 6), 1),
             # ("INNERGRID", (0, 0), (-1, -1), 0.5, s.Colors.dark_gray),
             ("BOX", (0, 0), (-1, -1), 0.6, colors.white),
             ("LINEABOVE", (0, 0), (-1, 4), 0.5, s.Colors.dark_gray),
             ("LINEABOVE", (0, 6), (-1, -1), 0.5, s.Colors.dark_gray)]
    table = Table(data=data, style=style, colWidths=widths, rowHeights=heights)
    table.wrapOn(c, 7.5 * inch, t_height)
    table.drawOn(c, 0.5 * inch, 0.925 * inch)

    # Vertical line
    pt = c.beginPath()
    pt.moveTo(200, 511)
    pt.lineTo(200, 65)
    c.drawPath(pt, stroke=1, fill=0)

    # Disclaimer
    disc_line_1 = "This report is for informational purposes only. Clinical decisions should be "
    disc_line_2 = "made based on observations of the patient, not solely this report."
    c.setFont(s.Fonts.italic, 12)
    c.setFillColor(s.Colors.dark_gray)
    c.drawCentredString(4.25 * inch, 0.7 * inch, disc_line_1)
    c.drawCentredString(4.25 * inch, 0.5 * inch, disc_line_2)

    # Footer
    # foot.section(c, REPORT)


def cover_section(w_dir: str, doc: BaseDocTemplate, report: r.Report, data: vd.VOCSNData, story: list):
    """
    Create report cover section.
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
    frames = [Frame(0.5 * inch, 0.5 * inch, doc.width, doc.height, id='Cover')]
    page_template = PageTemplate(id="Cover", frames=frames, onPage=_cover_page)
    doc.addPageTemplates(page_template)

    # Add flowable elements - First page template is assumed, not declared
    story.append(NextPageTemplate("Cover"))
