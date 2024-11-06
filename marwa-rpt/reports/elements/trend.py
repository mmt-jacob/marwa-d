#!/usr/bin/env python
"""
Elements used in the Trend Summary section of the report.

    Version Notes:
        1.0.0.0 - 09/14/2019 - Created file with constructors for image headers and trend blocks.
        1.0.0.1 - 09/17/2019 - Added the CalDay class.
        1.0.1.0 - 09/30/2019 - Expanded TrendBlock to have a "Large" option that includes change values and percentage.
        1.0.1.1 - 10/04/2019 - Fixed a bug that added to many days on weeks starting on Sunday.
        1.0.1.2 - 10/10/2019 - Updated to use newly-calculated trend values.
        1.0.1.3 - 10/16/2019 - Fixed display values for no data and moved precision control here from trend_calendar.py
        1.0.1.4 - 11/01/2019 - Improved I:E display
        1.0.1.5 - 11/04/2019 - Disabled dashed lines on legend key.
        1.0.1.6 - 11/14/2019 - Disabled trend arrow for I:E display, capped precision at one decimal place.
        1.0.1.7 - 11/19/2019 - Updated with new graphics/dimensions. Suppressed percentages under 1%.
        1.0.1.8 - 11/22/2019 - Changed trend block precision logic.
        1.0.1.6 - 11/27/2019 - Changed value formatting to preserve 0. None still defaults to "---".
        1.0.2.0 - 11/28/2019 - Added calendar legend.
        1.0.2.1 - 12/05/2019 - Inserted properly sized icons into the legend.
        1.0.2.2 - 12/06/2019 - Adjusted rounding on percentages.
        1.0.3.0 - 12/12/2019 - Created TrendTable class to help implement links at the correct time.
        1.0.3.1 - 12/20/2019 - Improved display format for no data blocks.
        1.0.3.2 - 01/02/2020 - Added better null value protection.
        1.0.3.3 - 01/12/2020 - Added support to partial days.
        1.0.3.4 - 01/15/2020 - Added trend shading.
        1.0.3.5 - 01/17/2020 - Added parameter to omit trend and fit a smaller block.
        1.0.3.6 - 01/20/2020 - Created no data bars. Adapted labels for use without trends.
        1.0.4.0 - 03/11/2020 - Added a grey-out feature.
        1.0.4.1 - 03/27/2020 - Fixed legend key range strings to represent hours.

"""

__author__ = "John Dorian for Sai Systems Technologies"
__copyright__ = "Copyright 2019"
__version__ = "1.0.4.1"

# Built-in modules
import os

# ReportLab modules
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus.flowables import Flowable

# VOCSN modules
from modules.models import vocsn_enum as ve
from modules.models.errors import ErrorManager
from reports.elements.styles import Styles as s
from modules.models.vocsn_data import VOCSNData
from modules.processing.utilities import trend_img
from modules.processing.utilities import var_precision


class TrendBlock(Flowable):
    """ Draw a rounded rectangle. """

    def __init__(self, em: ErrorManager, p_dir: str, size: list, color: colors.Color, title: str, value: float,
                 precision: int, units: str, percent, trend_title: str = None, delta: float = 0, large: bool = False,
                 split: bool = False, split_val: float = None, split_unit: str = None, show_sign: bool = False,
                 ratio: bool = False, legend: bool = None, duration: [int] = None, link: str = None,
                 has_trend: bool = True, in_use: bool = True):
        """
        Create a trend block as a custom flowable.
        :param em: Error manager.
        :param p_dir: Program directory.
        :param size: List with sizes. [X, Y]
        :param color: Border color
        :param title: Block title
        :param value: Block value
        :param precision: Number of decimal places to include
        :param units: Block value units
        :param trend_title: Trend title line
        :param percent: Percent change in value over trend period
        :param delta: Change in value over trend period
        :param large: Creates an expanded block with both value and percent change
        :param split: Use a min/max value.
        :param split_val: Second value in split value.
        :param split_unit: Second units in split values.
        :param show_sign: If true, show sign for both positive and negative numbers
        :param ratio: Value is a ratio.
        :param legend: When true, renders a pre-defined legend block.
        :param duration: Number of days in report period used for legend entry.
        :param link: Link destination name.
        :param has_trend: When true, display trend percentages.
        :param in_use: When true, block is in use and white. When false, block is blank and greyed out.
        """
        Flowable.__init__(self)

        # References
        self.em = em
        self.dir = p_dir

        # Store attributes
        self.size = size
        self.color = color
        self.large = large
        self.show_sign = show_sign
        self.ratio = ratio
        self.has_trend = has_trend
        self.in_use = in_use

        # Store strings values
        self.title = title
        self.trend_title = trend_title
        self.value = value
        self.units = units
        self.delta = delta
        self.percent = percent
        self.precision = precision

        # Link info
        self.link = link
        self.table_x = None
        self.table_y = None

        # Split values
        self.split = split
        self.split_val = split_val
        self.split_unit = split_unit

        # Legend values
        self.legend = legend
        self.duration = duration
        if legend:
            self.size = [0.95*inch, 1.0*inch]
            self.title = "Parameter Name"
            self.units = "units"

    def wrap(self, *args):
        """ Make internal sizes available to build engine. """
        return self.size[0], self.size[1]

    def drawOn(self, canvas, x, y, _sW=0):
        """ Get position relative to table canvas. """

        # Call default drawOn function
        Flowable.drawOn(self, canvas, x, y, _sW)

        # Store position relative to table
        self.table_x = x
        self.table_y = y

        # Create reference for later
        if not hasattr(canvas, "blocks_with_links"):
            canvas.blocks_with_links = []
        canvas.blocks_with_links.append(self)

    def draw(self):
        """ Construct block. """

        # Prepare values
        units = str(self.units)
        split_unit = str(self.split_unit)
        val = "---"
        trend = "---"
        percent = "---"
        split_val = "---"
        use_trend = False
        try:
            if self.value is not None:
                val = "%0.*f" % (int(self.precision), self.value)
                # val = str(flex_float(self.value, self.precision))
                if self.ratio:
                    if self.value > 0:
                        val = "{}:1".format(val)
                    elif self.value < 0:
                        val = "1:{}".format(val).replace('-', '')
                    else:
                        val = "1:1"
            if self.split_val is not None:
                split_val = str(round(self.split_val))
            if self.show_sign:
                if self.value is not None and self.value > 0:
                    val = "+" + val
                if self.split_val is not None and self.split:
                    if self.split_val > 0:
                        split_val = "+" + split_val
        except Exception as e:
            self.em.log_error(ve.Programs.REPORTING, ve.ErrorCat.MID_ERROR, ve.ErrorSubCat.INTERNAL_ERROR,
                              "Average display error in Trend Summary", e)
        if units != "":
            units = " " + str(self.units)
        if split_unit not in ["", "max"]:
            split_unit = " " + str(self.split_unit)
        if self.percent is not None:
            try:
                sign = '+' if self.percent >= 0 else '-'
                if self.large:
                    precision = 0 if abs(self.delta) >= 100 else 1
                    trend = sign + "%0.*f" % (precision, abs(self.delta))
                    if self.ratio:
                        trend = "%0.*f" % (int(self.precision), abs(self.delta))
                        if self.delta > 0:
                            trend = "{}:1".format(trend)
                        elif self.value < 0:
                            trend = "1:{}".format(trend).replace('-', '')
                        else:
                            trend = "1:1"
                    if abs(self.percent) >= 0.0005:
                        percent = "{}%".format(var_precision(abs(self.percent) * 100))
                        use_trend = True
                else:
                    if abs(self.percent) >= 0.005:
                        percent = "{:.0f}%".format(abs(self.percent * 100))
                        use_trend = True

            # Value error indicates suspicious data, but may be able to continue
            except (TypeError, ValueError) as e:
                use_trend = False
                self.em.log_error(ve.Programs.REPORTING, ve.ErrorCat.MID_ERROR, ve.ErrorSubCat.INTERNAL_ERROR,
                                  "Trend display error in Trend Summary", e)

            # Other errors cause abort
            except Exception as e:
                self.em.log_error(ve.Programs.REPORTING, ve.ErrorCat.PROCESS_ERROR, ve.ErrorSubCat.INTERNAL_ERROR,
                                  "Error while processing trend values in Trend Summary", e)
        else:
            use_trend = False
        split = self.split

        # Prepare canvas
        canvas = self.canv
        canvas.setLineWidth(2)
        canvas.setStrokeColor(self.color)
        canvas.scale(1, 1)

        # Draw border shape
        m = 0.01 * inch    # margin
        r = 0.25 * inch    # radius
        x, y = self.size
        curves = [
            (x-m-r,   m), (x-m,   m+r), 270,
            (x-m, y-m-r), (x-m-r, y-m),   0,
            (m+r,   y-m), (m,   y-m-r),  90,
            (m,     m+r), (m+r,     m), 180
        ]
        p = canvas.beginPath()
        p.moveTo(m+r, m)
        ccopy = list(curves)
        while ccopy:
            [(x1, y1), (x2, y2), a] = ccopy[:3]
            p.lineTo(x1, y1)
            p.arcTo(x1, y1, x2, y2, startAng=a, extent=90)
            del ccopy[:3]
        p.close()
        fill = 0 if self.in_use else 1
        canvas.setFillColor(s.Colors.x_light_gray)
        canvas.drawPath(p, fill=fill)

        # Font color
        color = s.Colors.dark_gray if self.in_use else s.Colors.med_gray
        canvas.setFillColor(color)

        # Key lines
        if self.legend:
            canvas.setFont(s.Fonts.regular, 8)
            canvas.drawCentredString(x * 0.5, y + m + 2, "KEY")
            canvas.setFont(s.Fonts.light, 8)
            range_seconds = self.duration[0].total_seconds()
            if range_seconds >= 86400:
                canvas.drawCentredString(x * 0.5, 30, "({}-Day Average)".format(round(range_seconds / 86400)))
            else:
                canvas.drawCentredString(x * 0.5, 30, "({}-Hour Average)".format(round(range_seconds / 3600)))
            if self.has_trend:
                trend_seconds = self.duration[1].total_seconds()
                canvas.setFont(s.Fonts.light, 7)
                if trend_seconds >= 86400:
                    canvas.drawCentredString(x * 0.5, 8, "(Last {}-Day Trend)".format(round(trend_seconds / 86400)))
                else:
                    canvas.drawCentredString(x * 0.5, 8, "(Last {}-Hour Trend)".format(round(trend_seconds / 3600)))
            else:
                canvas.setFont(s.Fonts.light, 7)
                canvas.drawCentredString(x * 0.5, 8, "(Trend Unavailable)")

        # Title
        lines = self.title.splitlines()
        font_size = 8.5
        y_offset = 0.125*inch if len(lines) > 1 else 0.175*inch
        if self.legend:
            canvas.setFont(s.Fonts.regular, 8)
        else:
            canvas.setFont(s.Fonts.light, font_size)
        canvas.drawCentredString(x*0.5, y-m-y_offset, lines[0])
        if len(lines) > 1:
            canvas.drawCentredString(x * 0.5, y - m - (y_offset+font_size*1.2), lines[1])

        # Value/Units line
        if self.legend:
            val = "###"
            bottom = y - 32
            start_size = val_size = 14
        else:
            bottom = 21
            start_size = val_size = 18 if not split else 16
        unit_size = 10
        val_width = x
        unit_width = x
        if len(lines) > 1:
            bottom = 18
        first = True
        while first or val_width + unit_width > x - 8*m:
            if not first:
                val_size *= 0.95
                unit_size *= 0.95
            first = False

            # Regular line
            if not split:
                canvas.setFont(s.Fonts.heavy, val_size)
                val_width = canvas.stringWidth(val)
                canvas.setFont(s.Fonts.light, unit_size)
                unit_width = canvas.stringWidth(units)

            # Split line
            else:
                canvas.setFont(s.Fonts.heavy, val_size)
                val_width = canvas.stringWidth(val + "/" + split_val)
                unit_width = 0

        # Regular line
        if not split:
            if val == "---":
                unit_width = 0
            x_pos = 0.5*x + (val_width - 0.5 * (val_width + unit_width))
            if not self.has_trend:
                y_pos = y - 2*m - 2*font_size - val_size
            else:
                y_pos = bottom + 0.5 * (start_size - val_size)
            if self.large:
                y_pos += self.size[1] * 0.4
            canvas.setFont(s.Fonts.heavy, val_size)
            canvas.drawRightString(x_pos, y_pos, val)
            if val != "---":
                canvas.setFont(s.Fonts.light, unit_size)
                canvas.drawString(x_pos, y_pos, units)

        # Split line
        else:
            x_pos = 0.5*x - 0.5 * val_width
            y_pos = bottom + 0.5 * (start_size - val_size)
            canvas.setFont(s.Fonts.heavy, val_size)
            canvas.drawString(x_pos, y_pos, val + "/" + split_val)

        # Large block elements
        if self.large:

            # Trend title
            lines = self.trend_title.splitlines()
            font_size = 8.5
            y_offset = 0.125 * inch if len(lines) > 1 else 0.175 * inch
            y_offset += self.size[1] * 0.4
            canvas.setFont(s.Fonts.light, font_size)
            canvas.drawCentredString(x * 0.5, y - m - y_offset, lines[0])
            if len(lines) > 1:
                canvas.drawCentredString(x * 0.5, y - m - (y_offset + font_size * 1.2), lines[1])

            # Trend value
            start_size = val_size = 18
            unit_size = 10
            val_width = x
            unit_width = x
            bottom = 21
            if len(lines) > 1:
                bottom = 18
            first = True
            while first or val_width + unit_width > x - 6 * m:
                if not first:
                    val_size *= 0.95
                    unit_size *= 0.95
                canvas.setFont(s.Fonts.heavy, val_size)
                val_width = canvas.stringWidth(trend)
                canvas.setFont(s.Fonts.light, unit_size)
                unit_width = canvas.stringWidth(units)
                first = False
            if trend == "---":
                unit_width = 0
                units = ""
            x_pos = 0.5 * x + (val_width - 0.5 * (val_width + unit_width))
            y_pos = bottom + 0.5 * (start_size - val_size)
            canvas.setFont(s.Fonts.heavy, val_size)
            canvas.drawRightString(x_pos, y_pos, trend)
            canvas.setFont(s.Fonts.light, unit_size)
            canvas.drawString(x_pos, y_pos, units)

        # Legend arrows
        if self.legend:
            arr_size = 0.11 * inch
            center = 0.5 * x
            y_pos = 15
            x_pos = center - 1.7 * arr_size
            path = os.path.join(self.dir, "resources", "images", "Multi-View_Arrow-Up.png")
            canvas.drawImage(path, x_pos, y_pos, height=arr_size, width=arr_size, mask="auto")
            x_pos = center - 0.5 * arr_size
            path = os.path.join(self.dir, "resources", "images", "Multi-View_Arrow-Down.png")
            canvas.drawImage(path, x_pos, y_pos, height=arr_size, width=arr_size, mask="auto")
            x_pos = center + 0.7 * arr_size
            canvas.drawString(x_pos, y_pos, "%")

        # Trend percentage line
        elif not split:
            if self.has_trend and not self.ratio:
                if use_trend:
                    if self.percent >= 0:
                        arrow = "Multi-View_Arrow-Up.png"
                    else:
                        arrow = "Multi-View_Arrow-Down.png"
                    arr_width = 0.11 * inch
                    path = os.path.join(self.dir, "resources", "images", arrow)
                else:
                    arr_width = 0
                    path = ""
                spacer = 1.5
                bottom = 4.5
                arr_size = 12
                canvas.setFont(s.Fonts.light, arr_size)
                if self.ratio:
                    spacer = 0
                    percent = ""
                if percent == "---":
                    trend_width = canvas.stringWidth(percent)
                else:
                    trend_width = arr_width + spacer + canvas.stringWidth(percent)
                x_pos = 0.5*x - 0.5*trend_width
                if use_trend:
                    canvas.drawImage(path, x_pos, bottom - 31, preserveAspectRatio=True, width=arr_width, mask="auto")
                if percent == "---":
                    canvas.drawString(x_pos, bottom, percent)
                else:
                    canvas.drawString(x_pos + spacer + arr_width, bottom, percent)

        # Split values
        elif not self.legend:
            canvas.setFont(s.Fonts.light, unit_size)
            val_str = units
            if split_unit != "":
                val_str += "/" + split_unit
            x_pos = 0.5*x - 0.5*canvas.stringWidth(val_str)
            canvas.drawString(x_pos, 7, val_str)


class CalDay(Flowable):
    """ Draw a calendar day. """

    # Canvas properties
    size = [7.25*inch / 7, 0.55*inch]

    def __init__(self, prog_dir: str, data: VOCSNData, day: str, in_range: bool, full_day: bool):
        """
        Create a flowable canvas and fill with date and therapy usage.
        :param prog_dir: Program directory.
        :param data: VOCSN data.
        :param day: Date string ("DD/MM")
        :param in_range: Indicates the day is within the specified report range.
        :param full_day: Full days in range are white. Non-full days in range are light gray.
        """
        Flowable.__init__(self)

        # References
        self.dir = prog_dir
        self.data = data
        self.day = day
        self.in_range = in_range
        self.full_day = full_day

        # Data bar definition
        # Populated later - None is no bar
        self.bar = None

    def wrap(self, *args):
        """ Make internal sizes available to build engine. """
        return self.size[0], self.size[1]

    def draw(self):
        """ Construct block. """

        # Prepare canvas
        font_size = 9
        canvas = self.canv
        canvas.setLineWidth(0.5)
        canvas.setFont(s.Fonts.table, font_size)
        canvas.scale(1, 1)

        # Gray-out days that are outside the report range
        if not self.in_range:
            canvas.setFillColor(s.Colors.light_gray)
            canvas.setStrokeColor(s.Colors.light_gray)
            canvas.rect(-6, -3, self.size[0], self.size[1], fill=1)
        elif not self.full_day:
            canvas.setFillColor(s.Colors.x_light_gray)
            canvas.setStrokeColor(s.Colors.x_light_gray)
            canvas.rect(-6, -3, self.size[0], self.size[1], fill=1)

        # Date
        m = 3
        x = -3
        y = self.size[1] - m - font_size - 1
        color = s.Colors.black if self.in_range else s.Colors.med_gray
        canvas.setFillColor(color)
        canvas.setFont(s.Fonts.light, font_size)
        canvas.drawString(x, y, self.day)

        # Partial day note
        if self.in_range and not self.full_day:
            x = self.size[0] - 3*m
            font_size -= 1
            color = s.Colors.dark_red
            canvas.setFillColor(color)
            canvas.setFont(s.Fonts.light, font_size)
            canvas.drawRightString(x, y, "Partial Day")

        # Therapy Icons and numbers
        m = 0.0 * inch
        y = (self.size[1] - font_size - 28) * 0.5
        x = m
        inc = (self.size[0] + 3) / 6
        for therapy in ["ventilator", "oxygen", "cough", "suction", "nebulizer"]:
            self._therapy_parts(self.dir, therapy, x, y, self.in_range)
            x += inc

        # Draw no data bar
        if self.bar:
            b = self.bar
            cell_width = self.size[0]
            m = 20
            w = b.length * cell_width - m
            h = 15
            x = 0 - w + cell_width - 0.5 * m - 6
            y = 0.5 * (self.size[1] - h) - 7
            c = x + 0.5 * w
            font_size = 10
            even_offset = 4 if b.length % 2 == 0 else 0
            canvas.setStrokeColor(s.Colors.light_gray)
            canvas.setFillColor(s.Colors.light_gray)
            canvas.roundRect(x, y, w, h, 5, stroke=1, fill=1)
            canvas.setFillColor(s.Colors.med_gray)
            y = y + 0.5 * (h - font_size) + 1
            canvas.setFont(s.Fonts.heavy, font_size)
            canvas.drawCentredString(c + even_offset, y, "No Data")

    def _therapy_parts(self, prog_dir: str, therapy_name: str, x: float, y: float, in_range: bool):
        """
        Place a therapy icon and usage day count on the canvas.
        :param prog_dir: Program directory.
        :param therapy_name: Name of therapy.
        :param x: X coordinate.
        :param y: Y coordinate.
        :param in_range: Indicates the day is within the specified report range.
        """

        # References
        canvas = self.canv
        tracker = getattr(self.data.events_tracker, therapy_name)
        stats = tracker.calendar.days[self.day]

        # Draw nothing when there's no activity
        if not stats.activity:
            return

        # Draw image
        font_size = size_start = 10
        img_size = 0.15 * inch
        y_offset = -img_size - 4
        path_only = True
        initial = therapy_name[0].capitalize()
        img_path = trend_img(prog_dir, initial, ve.ImgSizes.SML, path_only)
        canvas.drawImage(img_path, x, y+y_offset, preserveAspectRatio=True, width=img_size, mask="auto")

        # Draw day count
        x_offset = img_size * 0.5
        if therapy_name in ["ventilator", "oxygen"]:
            day_count = str(round(stats.duration.total_seconds() / 3600))
        else:
            day_count = str(stats.sessions)
        shade = "_dark" if therapy_name == "oxygen" else ""
        color = getattr(s.Colors, therapy_name + shade)
        canvas.setFillColor(color)
        canvas.setFont(s.Fonts.heavy, font_size)
        while canvas.stringWidth(day_count) > img_size:
            font_size -= 0.2
            canvas.setFont(s.Fonts.heavy, font_size)
        y_offset = (size_start - font_size) * 0.45
        canvas.drawCentredString(x + x_offset, y + y_offset, day_count)


class CalLegend(Flowable):
    """ Calendar legend using medium therapy initial blocks. """

    # Canvas properties
    size = [1.55*inch, 0.5*inch]

    def __init__(self, prog_dir: str):
        """
        Create a flowable canvas and render calendar legend.
        :param prog_dir: Program directory.
        """
        Flowable.__init__(self)

        # References
        self.dir = prog_dir

    def wrap(self, *args):
        """ Make internal sizes available to build engine. """
        return self.size[0], self.size[1]

    def draw(self):
        """ Construct block. """

        # References
        c = self.canv
        w = self.size[0]
        h = self.size[1]

        # Parameters
        my = 3   # Margin 1 for vertical spacing
        mx = 2   # Margin 2 for horizontal spacing
        indent = 7.25*inch - w
        y_pos = h - my
        
        # Prepare canvas
        font_size = 9
        c.setLineWidth(0.5)
        c.setFont(s.Fonts.table, font_size)
        c.setFillColor(s.Colors.black)
        c.scale(1, 1)

        # Title
        y_pos -= font_size
        c.drawCentredString(indent + 0.5*w, y_pos, "KEY")

        # Draw therapy icons
        offset = 0
        img_size = (w - 4*mx) / 5
        y_pos -= img_size + my
        step = img_size + mx
        for initial in ['V', 'O', 'C', 'S', 'N']:
            img_path = trend_img(self.dir, initial, ve.ImgSizes.MDS, path_only=True)
            c.drawImage(img_path, indent+offset, y_pos, width=img_size, height=img_size, mask="auto")
            offset += step

        # Indicator line for V, O
        top = y_pos = y_pos - my
        bottom = y_pos = y_pos - 0.1*inch
        x_pos = indent + 0.5*img_size
        p = c.beginPath()
        p.moveTo(x_pos, top)
        p.lineTo(x_pos, bottom)
        x_pos += step
        p.lineTo(x_pos, bottom)
        p.lineTo(x_pos, top)
        c.drawPath(p)

        # Indicator line for C, S, N
        x_pos += step
        p = c.beginPath()
        p.moveTo(x_pos, top)
        p.lineTo(x_pos, bottom)
        x_pos += 2*step
        p.lineTo(x_pos, bottom)
        p.lineTo(x_pos, top)
        c.drawPath(p)

        # Legend labels
        font_size = 8
        y_pos -= font_size + my
        c.setFillColor(s.Colors.dark_gray)
        c.setFont(s.Fonts.table, font_size)
        x_pos = indent + img_size + 0.5*1
        c.drawCentredString(x_pos, y_pos, "HOURS/DAY")
        x_pos = indent + w - 0.5 * (3*img_size + 2*mx)
        c.drawCentredString(x_pos, y_pos, "SESSIONS/DAY")
