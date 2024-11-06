#!/usr/bin/env python
"""
Style definitions to standardize element appearance across reports and sections.

    Version Notes:
        1.0.0.0  - 07/21/2019 - Created file with Styles class.
        1.0.0.1  - 07/29/2019 - Added colors and fonts.
        1.0.0.2  - 09/09/2019 - Restructured to place section titles in flowable story.
        1.0.0.3  - 09/12/2019 - Added black.
        1.0.0.4  - 09/29/2019 - Added some colors and renamed some fonts.
        1.0.0.5  - 10/04/2019 - Added notification dot color and alarm colors.
        1.0.0.7  - 10/10/2019 - Tweaked x-light colors.
        1.0.0.8  - 10/17/2019 - Added dark therapy colors.
        1.0.0.9  - 11/05/2019 - Darkened system colors.
        1.0.0.10 - 11/20/2019 - Added orange color.
        1.0.0.11 - 11/24/2019 - Added blue-white for AcroForm inputs and italics for disclaimer.
        1.0.0.12 - 12/17/2019 - Added dark yellow.
        1.0.0.13 - 01/15/2020 - Added more gray colors.
        1.0.0.14 - 04/06/2020 - Added lighter colors.

"""

__author__ = "John Dorian for Sai Systems Technologies"
__copyright__ = "Copyright 2019"
__version__ = "1.0.0.14"

# Built-in modules
import os

# ReportLab libraries
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import Spacer
from reportlab.platypus import Paragraph
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.styles import ParagraphStyle


class Styles:
    """ ReportLab style definitions """

    class Colors:
        """ Common color definitions """

        # Gray tones
        white = colors.Color(1.0, 1.0, 1.0)
        xx_light_gray = colors.Color(0.965, 0.965, 0.965)
        x_light_gray = colors.Color(0.95, 0.95, 0.95)
        light_gray = colors.Color(0.863, 0.867, 0.871)
        med_light_light_gray = colors.Color(0.741, 0.749, 0.757)
        med_light_gray = colors.Color(0.655, 0.663, 0.675)
        med_gray = colors.Color(0.485, 0.489, 0.497)
        dark_gray = colors.Color(0.345, 0.349, 0.357)
        black = colors.Color(0.0, 0.0, 0.0)

        # Therapy color associations
        system_x_light = x_light_gray
        system_light = light_gray
        system = med_gray
        system_dark = dark_gray
        ventilator_dark = colors.Color(0.0, 0.53, 0.83)
        oxygen_dark = colors.Color(0.40, 0.65, 0.22)
        cough_dark = colors.Color(0.05, 0.28, 0.45)
        suction_dark = colors.Color(0.40, 0.18, 0.42)
        nebulizer_dark = colors.Color(1.0, 0.40, 0.12)
        ventilator = colors.Color(0.0, 0.71, 0.89)
        oxygen = colors.Color(0.59, 0.84, 0.0)
        cough = colors.Color(0.06, 0.32, 0.52)
        suction = colors.Color(0.58, 0.15, 0.56)
        nebulizer = colors.Color(0.95, 0.66, 0.0)
        ventilator_light = colors.Color(0.50, 0.85, 0.94)
        oxygen_light = colors.Color(0.69, 0.83, 0.63)
        cough_light = colors.Color(0.53, 0.66, 0.76)
        suction_light = colors.Color(0.79, 0.58, 0.78)
        nebulizer_light = colors.Color(1.0, 0.70, 0.56)
        ventilator_x_light = colors.Color(0.70, 0.94, 1.0, alpha=0.5)
        oxygen_x_light = colors.Color(0.82, 0.91, 0.80, alpha=0.5)
        cough_x_light = colors.Color(0.73, 0.98, 0.97, alpha=0.5)
        suction_x_light = colors.Color(0.94, 0.76, 0.56, alpha=0.5)
        nebulizer_x_light = colors.Color(1.0, 0.80, 0.70, alpha=0.5)
        ventilator_xx_light = colors.Color(0.70, 0.94, 1.0, alpha=0.15)
        oxygen_xx_light = colors.Color(0.82, 0.91, 0.80, alpha=0.15)
        cough_xx_light = colors.Color(0.76, 0.81, 0.97, alpha=0.15)
        suction_xx_light = colors.Color(0.99, 0.61, 0.81, alpha=0.15)
        nebulizer_xx_light = colors.Color(1.0, 0.80, 0.70, alpha=0.15)

        # Additional colors
        dark_blue = colors.Color(0.07, 0.29, 0.52)
        blue_white = colors.Color(0.9451, 0.9569, 1.00)
        orange = colors.Color(0.95, 0.66, 0.00)
        dark_orange = colors.Color(1.00, 0.40, 0.12)
        red = colors.Color(0.78, 0.13, 0.18)
        dark_red = colors.Color(0.65, 0.10, 0.18)
        dark_yellow = colors.Color(0.88, 0.78, 0.14)

        # Functional colors
        alarm_high = red
        alarm_med = dark_yellow
        alarm_low = ventilator
        trend = xx_light_gray

        # Data notifications
        data_warn = colors.Color(1.0, 0.75, 0.1)
        data_error = colors.Color(1.0, 0.1, 0.1)

    class Fonts:
        """ Common font definitions. """

        title = "Avenir-Heavy"
        table = "Avenir-Regular"
        light = "Avenir-Light"
        regular = "Avenir-Regular"
        heavy = "Avenir-Heavy"
        italic = "Avenir-RegLight-I"

    # Color type converter
    @staticmethod
    def col_to_attr_str(color: colors.Color) -> str:
        """ Convert a ReportLab Color object to a ReportLab attribute color string. """
        return "rgba" + str(color.bitmap_rgba())

    # Title creation
    @staticmethod
    def section_title_fixed(c: Canvas, text: str):
        """ Section title paragraph drawn on canvas. """
        c.saveState()
        c.setFont(Styles.Fonts.title, 24)
        c.setFillColor(Styles.Colors.dark_blue)
        c.drawString(0.5 * inch, 9.7 * inch, text)
        c.restoreState()

    @staticmethod
    def section_title_flow(text: str):
        """ Section title paragraph as flowable. """
        # Use extend to add to story, since this returns a list.
        return [Spacer(1, -0.05 * inch), Paragraph(text, Styles.title)]

    # Paragraph style definitions
    title = ParagraphStyle(name="title",
                           fontName=Fonts.title,
                           fontSize=24,
                           textColor=Colors.dark_blue,
                           wordWrap="LTR",
                           leading=0)
    subtitle = ParagraphStyle(name="subtitle",
                              fontName=Fonts.title,
                              fontSize=14,
                              textColor=Colors.dark_blue,
                              wordWrap="LTR",
                              leading=0)
    cover_wrap = ParagraphStyle(name="cover_wrap",
                                fontName=Fonts.table,
                                fontSize=12,
                                textColor=Colors.dark_gray,
                                wordWrap="LTR",
                                leading=15)

    # Centered two-line value strings
    @staticmethod
    def centered_2line_val(c: Canvas, center: float, top: float, max_width: float, val: str, units: str, label: str):
        """ Section title paragraph drawn on canvas. """

        # Properties
        big_font = 36
        small_font = 14
        c.setFillColor(Styles.Colors.dark_gray)
        units = " " + units

        # Shrink to fit
        first = False
        big_width = 0
        small_width = 0
        temp_small = small_font
        val_width = max_width + 1
        while val_width > max_width:
            c.setFont(Styles.Fonts.title, big_font)
            big_width = c.stringWidth(val)
            c.setFont(Styles.Fonts.title, temp_small)
            small_width = c.stringWidth(units)
            val_width = big_width + small_width
            if not first:
                big_font -= 0.2
                temp_small -= 0.2
            first = False

        # Value strings
        c.saveState()
        c.setFont(Styles.Fonts.title, big_font)
        position = center - 0.5 * (val_width - big_width)
        c.drawCentredString(position, top - big_font, val)
        c.setFont(Styles.Fonts.title, temp_small)
        position = center + 0.5 * (val_width - small_width)
        c.drawCentredString(position, top - big_font, units)
        c.restoreState()

        # Shrink to fit
        first = False
        val_width = max_width + 1
        while val_width > max_width:
            c.setFont(Styles.Fonts.title, small_font)
            val_width = c.stringWidth(label)
            if not first:
                small_font -= 0.2
            first = False

        # Label strings
        c.saveState()
        c.setFont(Styles.Fonts.title, small_font)
        c.drawCentredString(center, top - big_font - small_font - 0.125*inch, label)
        c.restoreState()
