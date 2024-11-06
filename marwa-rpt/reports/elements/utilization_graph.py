#!/usr/bin/env python
"""
Alarm graph.

    Version Notes:
        1.0.0.0  - 09/29/2019 - Created with AlarmGraph flowable class.
        1.0.0.1  - 10/02/2019 - Finished legend.
        1.0.0.2  - 10/04/2019 - Completed graph bars.
        1.0.0.3  - 10/17/2019 - Updated alarm property types to match new data files.
        1.0.0.4  - 10/31/2019 - Colored alarm bars based on alarm severity.
        1.0.0.5  - 11/01/2019 - Re-ordered alarm bar layers with high always on top. Adjusted min. thickness.
        1.0.0.6  - 11/02/2019 - Disabled warning notification when events exceed report range.
        1.0.0.7  - 11/19/2019 - Updated for new graphics names.
        1.0.0.8  - 11/24/2019 - Parameterized some dimensions to allow for precision alignment with settings chart.
        1.0.0.9  - 12/12/2019 - Removed corner radius from bars.
        1.0.0.10 - 12/19/2019 - Changed tick references to support sub-day report durations.
        1.0.0.11 - 01/11/2020 - Adapted to align independently from calendar days.
        1.0.0.12 - 01/15/2020 - Added shading to trend region.
        1.0.0.13 - 01/24/2020 - Renamed to utilization graph.
        1.0.1.0  - 02/29/2020 - Consolidated bars within minimum bar width.
        1.0.1.1  - 04/04/2020 - Changed "Alarm" label to the alarm icon.

"""

__author__ = "John Dorian for Sai Systems Technologies"
__copyright__ = "Copyright 2019"
__version__ = "1.0.1.1"

# Built-in
from datetime import datetime

# ReportLab modules
from reportlab.lib.units import inch
from reportlab.platypus.flowables import Flowable

# VOCSN data modules
from reports.elements.styles import Styles as s
from modules.models.vocsn_data import VOCSNData
from modules.processing.utilities import trend_img
from modules.models.report import Report, ReportRange
from modules.models.vocsn_enum import Therapies, ImgSizes, RecordCompleteState as rState


class UtilizationGraph(Flowable):
    """ Create a single alarm graph. """

    def __init__(self, prog_dir: str, report: Report, data: VOCSNData, height: float,
                 left_width: int = None, right_width: int = None):
        """
        Initialize.
        :param prog_dir: Program execution directory.
        :param report: Report reference.
        :param data: VOCSN data container reference.
        :param height: graph height.
        :return: UtilizationGraph, extending ReportLab flowable.
        """
        Flowable.__init__(self)

        # Reference
        self.dir = prog_dir
        self.report = report
        self.data = data

        # Properties
        self.width = 7.25 * inch
        self.height = height
        self.left_width = left_width
        self.right_width = right_width

    def wrap(self, *args):
        """ Make internal sizes available to build engine. """
        return self.width, self.height

    def draw(self):
        """ Construct block. """

        # References
        c = self.canv
        r = self.report
        d = self.data
        h = self.height
        w = self.width

        # Title
        font_size = 14
        c.setFont(s.Fonts.title, font_size)

        # Utilization/alarm graph
        # x_offset = 1.25 * inch
        x_offset = self.left_width if self.left_width else 1.25*inch
        size = [w - x_offset, h]
        if self.right_width:
            size[0] = self.right_width
        graph = AlarmArea(d, self.dir, size, r.range)
        graph.wrap()
        graph.drawOn(c, x_offset, 0)

        # Legend
        font_size = 12
        y_margin = 5
        y_header = font_size - y_margin
        yh_graph = (h - y_header) * 0.9
        row_1 = yh_graph * (5/6) + 1
        row_2 = yh_graph * (3/6) + 1
        row_3 = yh_graph * (1/6) + 1
        x_pos = 1.05 * x_offset
        icon_size_ltr = ImgSizes.SML
        icon_size = 14
        half_icon = 0.5 * icon_size
        path_only = True
        c.setFillColor(s.Colors.dark_blue)
        c.setFont(s.Fonts.heavy, font_size)
        c.setStrokeColor(s.Colors.med_gray)
        img = trend_img(self.dir, 'V', icon_size_ltr, path_only)
        c.drawImage(img, x_pos - half_icon - 30, row_1 - 0.6*icon_size, preserveAspectRatio=True,
                    width=icon_size, height=icon_size, mask="auto")
        c.drawCentredString(x_pos - 15, row_1 - 0.5*font_size, '+')
        img = trend_img(self.dir, 'C', icon_size_ltr, path_only)
        c.drawImage(img, x_pos - half_icon, row_1 - 0.6*icon_size, preserveAspectRatio=True,
                    width=icon_size, height=icon_size, mask="auto")
        img = trend_img(self.dir, 'O', icon_size_ltr, path_only)
        c.drawImage(img, x_pos - half_icon - 60, row_2 - 0.6*icon_size, preserveAspectRatio=True,
                    width=icon_size, height=icon_size, mask="auto")
        c.drawCentredString(x_pos - 45, row_2 - 0.5*font_size, '+')
        img = trend_img(self.dir, 'S', icon_size_ltr, path_only)
        c.drawImage(img, x_pos - half_icon - 30, row_2 - 0.6*icon_size, preserveAspectRatio=True,
                    width=icon_size, height=icon_size, mask="auto")
        c.drawCentredString(x_pos - 15, row_2 - 0.5*font_size, '+')
        img = trend_img(self.dir, 'N', icon_size_ltr, path_only)
        c.drawImage(img, x_pos - half_icon, row_2 - 0.6*icon_size, preserveAspectRatio=True,
                    width=icon_size, height=icon_size, mask="auto")
        img = trend_img(self.dir, 'A', icon_size_ltr, path_only)
        c.drawImage(img, x_pos - half_icon, row_3 - 0.6*icon_size, preserveAspectRatio=True,
                    width=icon_size, height=icon_size, mask="auto")
        # c.drawCentredString(x_pos, row_3 - 0.5*font_size, 'Alarms')

        # Notification dot legend
        dot_legend = NotificationLegend(d.persistent_event_out_of_range, d.persistent_event_incomplete,
                                        "Event extends beyond report range.", "Partial data, may be inaccurate.")
        l_width, l_height = dot_legend.wrap()

        dot_legend.drawOn(c, 0.5*w - 0.5*l_width, -l_height)


class AlarmArea(Flowable):
    """" Utilization/alarm graph components. """

    # Expose minimum bar width
    min_bar_width = 0.5

    def __init__(self, data: VOCSNData, prog_dir: str, size: list, r_range: ReportRange):
        """
        Prepare individual alarm graph area.
        :param data: VOCSN data container reference.
        :param prog_dir: Program execution directory.
        :param size: Graph Area dimensions.
        :param r_range: Report range definitions.
        """
        Flowable.__init__(self)

        # References
        self.dir = prog_dir
        self.data = data
        self.range = r_range

        # Properties
        self.size = size

    def wrap(self, *args):
        """ Make internal sizes available to build engine. """
        return self.width, self.height

    def draw(self):
        """ Construct block. """

        def t_to_x(time: datetime):
            """ Get x coordinates on graph from date/time. """
            x = x_start + x_range * ((time - t_start) / t_range)
            return x

        def bar(s_start: float, s_end: float, y: float, height: float, offset, complete: rState, truncated: rState):
            """ Draw a utilization/alarm bar on the graph. """
            width = max(self.min_bar_width, s_end - s_start)
            # radius = min(2.0, 0.5*width)      Radius disabled
            # radius = 0
            height *= 0.9
            dot_y = bar_y = y - 0.5*height
            if offset is not None:
                height *= 1 - bar_offset
                if offset:
                    bar_y += bar_offset * height
            c.rect(s_start, bar_y, width, 0.9 * height, stroke=0, fill=1)
            # c.roundRect(s_start, bar_y, width, 0.9*height, radius, stroke=0, fill=1)
            if complete is not rState.COMPLETE:
                x = s_start if complete is rState.MISSING_START else s_end
                errors.append([x, dot_y])
            # Warnings for events exceeding report range are disabled
            # elif truncated is not rState.COMPLETE:
            #     x = s_start if complete is rState.MISSING_START else s_end
            #     warns.append([x, dot_y])

        def dot(dot_xy: list):
            """ Draw a notification dot on a problematic record. """
            radius = 0.5 * notification_size
            x = dot_xy[0]
            y = dot_xy[1] + radius
            c.circle(x, y, radius, stroke=1, fill=1)

        # References
        w = self.size[0]
        h = self.size[1]
        c = self.canv
        r = self.range
        d = self.data
        tx = r.tick_times
        tx_label = r.tick_labels

        # Properties
        font_size = 8
        x_indent = 20
        y_margin = 5
        y_header = font_size + y_margin
        yh_graph = h - y_header
        bar_height = (yh_graph / 3) * 0.9
        bar_offset = 0
        bar_up = True
        bar_down = False
        no_offset = None
        row_1 = yh_graph * (5/6)
        row_2 = yh_graph * (3/6)
        row_3 = yh_graph * (1/6)

        # Coordinate space conversion variables
        t_start = r.start
        t_range = r.duration
        x_start = x_indent
        x_range = w - x_start

        # Draw trend area
        if r.use_trend:
            title_ext = 23
            title_size = 7
            c.setFillColor(s.Colors.trend)
            x1 = t_to_x(r.trend_start)
            x2 = t_to_x(r.end)
            p = c.beginPath()
            p.moveTo(x1, 0)
            p.lineTo(x1, yh_graph + title_ext)
            p.lineTo(x2, yh_graph + title_ext)
            p.lineTo(x2, 0)
            p.close()
            c.drawPath(p, stroke=0, fill=1)
            c.setFillColor(s.Colors.dark_gray)
            c.setFont(s.Fonts.light, title_size)
            text_x = x1 + 0.5 * (x2 - x1)
            text_y = yh_graph + title_ext - title_size - 0.5
            c.drawCentredString(text_x, text_y, "Trend Period")

        # Draw grid lines
        c.setFillColor(s.Colors.dark_gray)
        c.setFont(s.Fonts.light, font_size)
        c.setStrokeColor(s.Colors.med_light_gray)
        c.setLineWidth(0.25)
        x_pos = x_indent
        y_pos = yh_graph
        p = c.beginPath()
        p.moveTo(x_pos, y_pos)
        p.lineTo(w, y_pos)
        p.close()
        c.drawPath(p)

        # Notification lists
        notification_size = 5
        warns = []
        errors = []

        # X-axis labels
        for idx, tick in enumerate(tx):

            # Labeled tick
            x_pos = t_to_x(tick)
            if tx_label[idx] is not None:
                c.setStrokeColor(s.Colors.med_light_gray)
                c.drawCentredString(x_pos, yh_graph + y_margin, tx_label[idx])
                if not r.use_trend or tick < r.trend_start:
                    color = s.Colors.med_light_gray if idx == 0 else s.Colors.light_gray
                else:
                    color = s.Colors.med_light_light_gray
                c.setStrokeColor(color)

            # Sub-tick
            else:
                if not r.use_trend or tick < r.trend_start:
                    color = s.Colors.med_light_gray if idx == 0 else s.Colors.x_light_gray
                else:
                    color = s.Colors.light_gray
                c.setStrokeColor(color)

            # Draw tick
            p = c.beginPath()
            p.moveTo(x_pos, yh_graph)
            p.lineTo(x_pos, 0)
            p.close()
            c.drawPath(p)

        # Determine minimum time width for bar
        min_time = r.duration / (x_range / self.min_bar_width)

        # Bar consolidation function
        def consolidate(item_list: list, filter_key, filter_val, is_alarm: bool = False):
            result = []
            for item in item_list:
                if hasattr(item, filter_key) and getattr(item, filter_key) == filter_val:
                    if is_alarm:
                        entry = BarDef(item.start_syn, item.end_syn, item.complete, item.truncated)
                    else:
                        entry = BarDef(item.start, item.stop, item.complete, item.truncated)
                    if len(result) == 0:
                        result.append(entry)
                    elif entry.start <= max(result[-1].stop, result[-1].start + min_time):
                        result[-1].stop = max(result[-1].stop, entry.stop)
                    else:
                        result.append(entry)
            return result

        # Iterate over bar items and send to render
        def render(item_list: list, row, b_height, offset):
            for item in item_list:
                bar(t_to_x(item.start), t_to_x(item.stop), row, b_height, offset, item.complete, item.truncated)

        # Ventilator bars
        c.setFillColor(s.Colors.ventilator)
        c.setStrokeColor(s.Colors.ventilator)
        sessions = consolidate(d.utilization_all, "therapy", Therapies.VENTILATOR)
        render(sessions, row_1, bar_height, bar_up)

        # Cough bars
        c.setFillColor(s.Colors.cough)
        c.setStrokeColor(s.Colors.cough)
        sessions = consolidate(d.utilization_all, "therapy", Therapies.COUGH)
        render(sessions, row_1, bar_height, bar_down)

        # Oxygen bars
        c.setFillColor(s.Colors.oxygen_dark)
        c.setStrokeColor(s.Colors.oxygen_dark)
        sessions = consolidate(d.utilization_all, "therapy", Therapies.OXYGEN)
        render(sessions, row_2, bar_height, bar_up)

        # Suction bars
        c.setFillColor(s.Colors.suction)
        c.setStrokeColor(s.Colors.suction)
        sessions = consolidate(d.utilization_all, "therapy", Therapies.SUCTION)
        render(sessions, row_2, bar_height, bar_down)

        # Nebulizer bars
        c.setFillColor(s.Colors.nebulizer)
        c.setStrokeColor(s.Colors.nebulizer)
        sessions = consolidate(d.utilization_all, "therapy", Therapies.NEBULIZER)
        render(sessions, row_2, bar_height, bar_down)

        # Low severity alarms
        c.setFillColor(s.Colors.alarm_low)
        c.setStrokeColor(s.Colors.alarm_low)
        alarms = consolidate(d.alarms_all, "severity", "Low", is_alarm=True)
        render(alarms, row_3, bar_height, no_offset)

        # Medium severity alarms
        c.setFillColor(s.Colors.alarm_med)
        c.setStrokeColor(s.Colors.alarm_med)
        alarms = consolidate(d.alarms_all, "severity", "Medium", is_alarm=True)
        render(alarms, row_3, bar_height, no_offset)

        # High severity alarms
        c.setFillColor(s.Colors.alarm_high)
        c.setStrokeColor(s.Colors.alarm_high)
        alarms = consolidate(d.alarms_all, "severity", "High", is_alarm=True)
        render(alarms, row_3, bar_height, no_offset)

        # # Warning notifications
        # c.setFillColor(s.Colors.data_warn)
        # c.setStrokeColor(s.Colors.dark_gray)
        # for warn in warns:
        #     dot(warn)
        #
        # # Error notifications
        # c.setFillColor(s.Colors.data_error)
        # c.setStrokeColor(s.Colors.dark_gray)
        # for error in errors:
        #     dot(error)

        # # Store notification status
        # d.persistent_event_out_of_range = len(warns) > 0
        # d.persistent_event_incomplete = len(errors) > 0


class NotificationLegend(Flowable):
    """ Create a legend for warning and error notifications that only only appear when needed. """

    def __init__(self, warns: bool, errors: bool, warn_message: str, error_message: str):
        """
        Prepare individual alarm graph area.
        :param warns: List of data warnings.
        :param errors: List of error warnings..
        :param warn_message: Legend message for warning dots.
        :param error_message: Legend message for error dots.
        """
        Flowable.__init__(self)

        # Store values
        self.show_warns = warns
        self.show_errors = errors
        self.warn_message = warn_message
        self.error_message = error_message

        # Properties
        self.radius = 2.5
        self.font_size = 9
        self.width = 0
        self.height = 0.25 * inch
        self.message_width = 2.15 * inch

    def wrap(self, *args):
        """ Make internal sizes available to build engine. """
        width = 0
        if self.show_warns:
            width += self.message_width
        if self.show_errors:
            width += self.message_width
        self.width = width
        return width, self.height

    def draw(self):
        """ Construct block. """

        # References
        c = self.canv
        r = self.radius
        h = self.height
        w = self.width
        f = self.font_size

        # Properties
        c.setFont(s.Fonts.light, f)
        # center = 0.5 * self.height
        x_pos = 0.5 * h
        y_pos = 0.5*h - 0.5*f

        # Error message
        if self.show_errors:
            c.setFillColor(s.Colors.data_error)
            c.setStrokeColor(s.Colors.dark_gray)
            c.circle(x_pos, y_pos+r, r, stroke=1, fill=1)
            x_pos += 2 * r
            c.setFillColor(s.Colors.black)
            c.drawString(x_pos, y_pos, "= " + self.error_message)
            x_pos = 0.5*w + 0.5 * h

        # Warning message
        if self.show_warns:
            c.setFillColor(s.Colors.data_warn)
            c.setStrokeColor(s.Colors.dark_gray)
            c.circle(x_pos, y_pos+r, r, stroke=1, fill=1)
            x_pos += 2 * r
            c.setFillColor(s.Colors.black)
            c.drawString(x_pos, y_pos, "= " + self.warn_message)


class BarDef:
    """ Bar definition. """

    def __init__(self, start: datetime, stop: datetime, complete, truncated):
        self.start = start
        self.stop = stop
        self.complete = complete
        self.truncated = truncated
