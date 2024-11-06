#!/usr/bin/env python
"""
Monitor data graph.

    Version Notes:
        1.0.0.0  - 09/29/2019 - Created with MonitorGraph flowable class.
        1.0.0.1  - 10/02/2019 - Added graph dots.
        1.0.0.2  - 10/16/2019 - Improved y-axis scaling.
        1.0.0.3  - 10/17/2019 - Updated alarm attributes to work with new data files.
        1.0.0.4  - 10/31/2019 - Segmented monitor graphs and changed stop values to plot points.
        1.0.0.5  - 11/01/2019 - Take in precision from metadata, updated pass-through values for I:E ratios
        1.0.0.6  - 11/03/2019 - Updated field names to accommodate scale logic fix in graph_ranges, cleaned up y-axis
                                alignment, fixed a notch in the percentile tick marks.
        1.0.0.7  - 11/06/2019 - Added proper ratio support with accurate number space around value 1:1. Added usage
                                timer/counter summary table
        1.0.0.8  - 11/14/2019 - Changed Usage Timer table labels and arrangement based on feedback.
        1.0.0.9  - 11/22/2019 - Added therapy colors and icons to graphs.
        1.0.0.10 - 12/05/2019 - Modified display logic for monitor graphs.
        1.0.0.11 - 12/14/2019 - Fixed minute bug that could have split stop value lines in short reports.
        1.0.0.12 - 12/20/2019 - Changed period label to make sense in sub-day report ranges.
        1.0.0.13 - 12/21/2019 - Implemented error management.
        1.0.0.14 - 12/31/2019 - Bug fix: no data values were invalid for maintenance records.
        1.0.0.15 - 01/09/2020 - Bug fix: I:E ratio could fail to display at a certain range.
        1.0.0.16 - 01/12/2020 - Added support for partial days.
        1.0.0.17 - 01/15/2020 - Expanded single samples to half sample resolution. Added thickness to cough dots.
        1.0.1.0  - 02/04/2020 - Added alternate Usage Timer section for VC models.
        1.0.1.1  - 02/09/2020 - Corrected cough trend value routing.

"""

__author__ = "John Dorian for Sai Systems Technologies"
__copyright__ = "Copyright 2019"
__version__ = "1.0.1.1"

# Built-in
from enum import Enum
from datetime import datetime

# ReportLab modules
from reportlab.lib.units import inch
from reportlab.platypus.tables import Table
from reportlab.platypus.flowables import Flowable

# VOCSN data modules
from modules.models import vocsn_enum as ve
from reports.elements.trend import TrendBlock
from modules.models.errors import ErrorManager
from reports.elements.styles import Styles as s
from modules.models.vocsn_data import VOCSNData
from modules.processing.values import read_ratio
from modules.processing.utilities import trend_img
from modules.models.vocsn_data import MonitorChannel
from modules.models.report import Report, ReportRange
from modules.models.vocsn_enum import MonitorTherapies, ImgSizes


class MonitorGraph(Flowable):
    """ Create a single monitor data graph. """

    def __init__(self, em: ErrorManager, path: str, report: Report, monitor, label: str, legend: bool):
        """
        Initialize.
        :param em: Error manager.
        :param path: Program execution path.
        :param report: Report reference.
        :param monitor: Monitor channel data container, or therapy session value
        :param label: Graph title.
        :param legend: Show Graph point legend.
        """
        Flowable.__init__(self)

        # Reference
        self.em = em
        self.path = path
        self.report = report
        self.monitor = monitor

        # Properties
        self.label = label
        self.width = 7.25 * inch
        self.height = 1.75 * inch
        self.legend = legend

    def wrap(self, *args):
        """ Make internal sizes available to build engine. """
        return self.width, self.height

    def draw(self):
        from modules.processing.sessions import SessionValTracker
        """ Construct block. """

        # Blank - return blank canvas
        if not self.monitor:
            return

        # References
        c = self.canv
        r = self.report
        m = self.monitor
        h = self.height
        w = self.width

        # Lookup therapy name
        therapy_name = "system"
        m_id = self.monitor.id
        for therapy in MonitorTherapies:
            if m_id in therapy.value:
                therapy_name = therapy.name

        # Draw image
        img_size = 14
        initial = therapy_name[0].capitalize()
        img_path = trend_img(self.path, initial, ImgSizes.MED, path_only=True)
        c.drawImage(img_path, 0, 1.075*inch, preserveAspectRatio=True, width=img_size, mask="auto")

        # Title
        font_size = 14
        c.setFont(s.Fonts.title, font_size)
        c.setFillColor(s.Colors.dark_blue)
        c.drawString(0.25*inch, h-font_size+1, self.label)

        # Set colors based on therapy
        color = getattr(s.Colors, therapy_name)
        if therapy_name == "oxygen":
            color = s.Colors.oxygen_dark
        color_l = getattr(s.Colors, therapy_name + "_light")
        color_xl = getattr(s.Colors, therapy_name + "_x_light")

        # Large trend block
        size = [1.125 * inch, 1.25 * inch]
        y_offset = 0.5 * (h-font_size-size[1]) + 4
        long_avg_msg = "{} Average".format(r.range.name)
        trend_days = r.range.trend_period
        trend_units = r.range.trend_units
        plural = 's' if trend_days == 1 and trend_units == 'Day' else ''
        short_avg_msg = "{}-{}{} Trend".format(trend_days, trend_units, plural) if r.range.use_trend else "No Trend"

        # Monitor Blocks
        if type(m) == MonitorChannel:
            is_ratio = m.display_type == "ratioMonitor"
            if is_ratio:
                short_avg_msg = short_avg_msg.replace("Trend", "Average")
            trend = m.trend if is_ratio else m.trend_delta
            block = TrendBlock(self.em, self.path, size, color_l, long_avg_msg, m.average, m.precision,
                               m.display_units, m.trend_percent, short_avg_msg, trend, large=True, ratio=is_ratio)

        # Session Blocks
        elif type(m) == SessionValTracker:
            track = m.tracker
            if m.id == "12024":
                avg = track.cough_avg_peak_flow
                t_perc = track.cough_percent_peak_flow
                delta = track.cough_trend_peak_flow
            elif m.id == "12025":
                avg = track.cough_avg_volume
                t_perc = track.cough_percent_volume
                delta = track.cough_trend_volume
            elif m.id == "12026":
                avg = track.cough_avg_cycles
                t_perc = track.cough_percent_cycles
                delta = track.cough_trend_cycles
            else:
                avg = m.average
                t_perc = m.trend_percent
                delta = m.trend_delta
            block = TrendBlock(self.em, self.path, size, color_l, long_avg_msg, avg, m.precision,
                               m.units, t_perc, short_avg_msg, delta, large=True)

        # Settings Blocks
        else:
            block = TrendBlock(self.em, self.path, size, color_l, long_avg_msg, m.average, m.precision,
                               m.units, m.trend_percent, short_avg_msg, m.delta, large=True)
        block.wrap()
        block.drawOn(c, 0, y_offset)

        # Monitor graph
        x_offset = size[0] + 0.125*inch
        size = [w - x_offset, size[1]]
        graph = GraphArea(size, self.monitor, r.range, self.legend, color, color_xl)
        graph.wrap()
        graph.drawOn(c, x_offset, y_offset)


class GraphArea(Flowable):
    """" Monitor graph components. """

    def __init__(self, size: list, monitor, r_range: ReportRange, legend: bool, color_1, color_2):
        """
        Prepare individual monitor graph area.
        :param size: Graph Area dimensions.
        :param monitor: Monitor channel data container, or therapy session value
        :param r_range: Report range definitions.
        :param legend: Show legend.
        :param color_1: Darker color.
        :param color_2: Lighter color.
        """
        Flowable.__init__(self)

        # References
        self.monitor = monitor
        self.range = r_range

        # Check for ratio
        self.ratio = False
        if hasattr(monitor, "display_type"):
            self.ratio = monitor.display_type == "ratioMonitor"

        # Properties
        self.size = size
        self.legend = legend
        self.color_1 = color_1
        self.color_2 = color_2

    def wrap(self, *args):
        """ Make internal sizes available to build engine. """
        return self.width, self.height

    def draw(self):
        from modules.processing.sessions import SessionValTracker
        """ Construct block. """

        class Datum:
            """ Graph data point. """
            def __init__(self, time: datetime, val: float):
                self.time = time
                self.val = val

        def tv_to_xy(time: datetime, val: float, ratio):
            """ Get xy coordinates on graph from date/time and value. """
            if ratio:
                if val <= -1:
                    val += 1
                elif val >= 1:
                    val -= 1
                else:
                    val = 0
            vertical_range = ratio_range if ratio else v_range
            x = x_start + x_range * ((time - t_start) / t_range)
            y = y_start + y_range * ((val - v_start) / vertical_range)
            return x, y

        class Points(Enum):
            P_95 = 3
            MEAN = 2
            P_05 = 1

        def point(x, y, p_type: Points, diameter=2):
            """ Draw a point on the graph. """

            # Save style state
            c.saveState()

            # 95th percentile
            d = diameter
            if p_type == Points.P_95:
                c.setFillColor(line_color)
                c.setStrokeColor(line_color)
                pt = c.beginPath()
                pt.moveTo(x, y-d)
                pt.lineTo(x+d, y)
                pt.lineTo(x, y+d)
                pt.lineTo(x-d, y)
                pt.lineTo(x, y - d)
                pt.lineTo(x, y - 2*d)
                c.drawPath(pt, stroke=1, fill=1)

            # Mean average line
            elif p_type == Points.MEAN:
                c.setFillColor(line_color)
                c.setStrokeColor(line_color)
                c.circle(x, y, d, stroke=1, fill=1)

            # 5th percentile
            elif p_type == Points.P_05:
                c.setFillColor(s.Colors.white)
                c.setStrokeColor(line_color)
                pt = c.beginPath()
                pt.moveTo(x, y+d)
                pt.lineTo(x+d, y)
                pt.lineTo(x, y-d)
                pt.lineTo(x-d, y)
                pt.lineTo(x, y + d)
                pt.lineTo(x, y + 2*d)
                c.drawPath(pt, stroke=1, fill=1)

            # Restore previous style state
            c.restoreState()

        # ----- Setup ----- #

        # References
        w = self.size[0]
        h = self.size[1]
        c = self.canv
        r = self.range
        m = self.monitor
        ty = m.ticks

        # Create margin bellow title
        h -= 10

        # Settings
        x_indent = 20
        line_color = self.color_1
        fill_color = self.color_2
        font_size = 8
        margin = font_size * 0.5

        # Coordinate space conversion variables
        have_data = ty[0] != "---"
        if hasattr(m.tracker, "has_data") and not m.tracker.has_data:
            have_data = False
        t_start = r.start
        t_range = r.duration
        v_start = 0
        v_end = 3
        v_range = 3
        ratio_range = 3
        if have_data:
            v_start = float(ty[0])
            v_end = float(ty[-1])
            v_range = ratio_range = v_end - v_start
            if self.ratio:
                if '0' in ty:
                    if ty[0] == '0' or ty[-1] == '0':
                        ratio_range -= 1
                    else:
                        ratio_range -= 2
                if v_start < 0:
                    v_start += 1
                elif v_start > 0:
                    v_start -= 1
        x_start = x_indent
        x_range = w - x_start
        y_start = margin
        y_range = h

        # Measure X tick width
        sample_width = self.range.graph_sample_size
        x1, _ = tv_to_xy(r.start, 0, self.ratio)
        x2, _ = tv_to_xy(r.start + sample_width, 0, self.ratio)
        min_width = (x2 - x1) / 2

        # Draw trend area
        if r.use_trend:
            c.setFillColor(s.Colors.trend)
            x1, _ = tv_to_xy(r.trend_start, 0, ratio=False)
            x2, _ = tv_to_xy(r.end, 0, ratio=False)
            p = c.beginPath()
            p.moveTo(x1, 0+margin)
            p.lineTo(x1, h+margin)
            p.lineTo(x2, h+margin)
            p.lineTo(x2, 0+margin)
            p.close()
            c.drawPath(p, stroke=0, fill=1)

        # Legend
        if self.legend:
            font_size = 8
            c.setFillColor(s.Colors.dark_gray)
            c.setFont(s.Fonts.light, font_size)
            y_pos_dot = h + 10 + margin
            y_pos = y_pos_dot - 0.5*font_size - 2.5 + margin
            point(w - 2.4*inch, y_pos_dot, Points.P_05)
            c.drawCentredString(w - 2.0*inch, y_pos, "5th Percentile")
            point(w - 1.5*inch, y_pos_dot, Points.MEAN)
            c.drawCentredString(w - 1.2*inch, y_pos, "Median")
            point(w - 0.85*inch, y_pos_dot, Points.P_95)
            c.drawCentredString(w - 0.4*inch, y_pos, "95th Percentile")

        # Draw Y-axis labels and grid lines
        # Adjusts tick increments around "0" for ratios
        inc_norm = h / (len(ty) - 1)
        c.setFillColor(s.Colors.dark_gray)
        c.setFont(s.Fonts.light, font_size)
        c.setStrokeColor(s.Colors.med_light_gray)
        c.setLineWidth(1)
        x_pos = x_indent
        labels = ty if "---" not in ty else [0, 1, 2, 3]
        for idx, t in enumerate(labels):
            # if self.ratio and have_data:
            _, y_pos = tv_to_xy(r.start, float(t), self.ratio)
            y_pos -= y_start
            label = read_ratio(t) if self.ratio else t
            if not have_data:
                label = "---"
            c.drawRightString(14, y_pos+2, label)
            p = c.beginPath()
            p.moveTo(x_pos, y_pos+margin)
            p.lineTo(w, y_pos+margin)
            p.close()
            c.drawPath(p)
            y_pos += inc_norm

        # Draw X-axis labels
        tx = self.range.tick_times
        tx_label = self.range.tick_labels
        y_max = y_start + y_range
        y_pos = -font_size
        for idx, tick in enumerate(tx):

            # Labeled tick
            x_pos, _ = tv_to_xy(tick, 0, False)
            if tx_label[idx] is not None:
                color = s.Colors.med_gray if idx == 0 else s.Colors.light_gray
                c.setStrokeColor(color)
                c.drawCentredString(x_pos, y_pos, tx_label[idx])

            # Sub-tick
            else:
                color = s.Colors.med_gray if idx == 0 else s.Colors.x_light_gray
                c.setStrokeColor(color)

            # # Draw tick
            # p = c.beginPath()
            # p.moveTo(x_pos, y_max)
            # p.lineTo(x_pos, y_start)
            # p.close()
            # c.drawPath(p)

        # Exit with no data
        if v_end is None:
            return

        # ----- Data processing ----- #

        # Prepare graph values
        is_stop_val = type(m) == SessionValTracker
        line_segments = []
        area_segments = []

        # Monitor data
        if type(m) == MonitorChannel:

            # Filter out no-data points and divide into contiguous segments
            use_percentile = m.uses_percentiles
            sample_segments = []
            sample_segment = []
            for sample in m.graph_samples:
                if sample.has_data:
                    sample_segment.append(sample)
                elif len(sample_segment) > 0:
                    sample_segments.append(sample_segment)
                    sample_segment = []
            if len(sample_segment) > 0:
                sample_segments.append(sample_segment)

            # Convert samples to graph data
            for sample_segment in sample_segments:
                line_segment = []
                area_segment = []

                # First pass
                for sample in sample_segment:
                    if not use_percentile:
                        line_segment.append(Datum(sample.time, sample.val1))
                    else:
                        line_segment.append(Datum(sample.time, sample.val2))
                        area_segment.append(Datum(sample.time, sample.val1))
                line_segments.append(line_segment)

                # Loop back to complete line ring around shaded area
                if use_percentile:
                    for sample in reversed(sample_segment):
                        area_segment.append(Datum(sample.time, sample.val3))
                    area_segments.append(area_segment)

        # Therapy session stop/start data
        else:
            segment = []
            for idx, sample in enumerate(m.graph_samples):
                segment.append(Datum(sample.time, sample.val))
                if sample.is_last or idx == len(m.graph_samples)-1:
                    line_segments.append(segment)
                    segment = []

        # ----- Render graph data ----- #

        # Draw percentile graph area for monitor data
        if type(m) == MonitorChannel:
            c.setFillColor(fill_color)
            for segment in area_segments:

                # Multiple samples
                short_sample = len(segment) <= 2
                p = c.beginPath()
                for idx, datum in enumerate(segment):
                    x_pos, y_pos = tv_to_xy(datum.time, datum.val, self.ratio)
                    if idx == 0:
                        p.moveTo(x_pos, y_pos)
                        if short_sample:
                            p.lineTo(x_pos + min_width, y_pos)
                    else:
                        if short_sample:
                            p.lineTo(x_pos + min_width, y_pos)
                        p.lineTo(x_pos, y_pos)
                c.drawPath(p, stroke=0, fill=1)
                for idx, datum in enumerate(segment):
                    last_idx = len(segment) / 2
                    x_pos, y_pos = tv_to_xy(datum.time, datum.val, self.ratio)
                    if r.is_tick(datum.time) and not is_stop_val:
                        if idx < last_idx:
                            point(x_pos, y_pos, Points.P_05)
                        else:
                            point(x_pos, y_pos, Points.P_95)

        # Draw average graph line
        c.setStrokeColor(line_color)
        for segment in line_segments:
            p = c.beginPath()
            short_sample = len(segment) == 1
            for idx, datum in enumerate(segment):
                x_pos, y_pos = tv_to_xy(datum.time, datum.val, self.ratio)
                if idx == 0:
                    p.moveTo(x_pos, y_pos)
                    if short_sample:
                        p.lineTo(x_pos + min_width, y_pos)
                else:
                    p.lineTo(x_pos, y_pos)
                if len(segment) == 1:
                    p.lineTo(x_pos, y_pos)
                if is_stop_val:
                    point(x_pos, y_pos, Points.MEAN, 2)
                if r.is_tick(datum.time) and not is_stop_val:
                    point(x_pos, y_pos, Points.MEAN)
            c.drawPath(p, stroke=1, fill=0)

            # Connect session dots with thick line
            if is_stop_val and len(segment) >= 2:
                c.setFillColor(line_color)
                c.setStrokeColor(line_color)
                start = segment[0]
                x1, y1 = tv_to_xy(start.time, start.val, ratio=False)
                end = segment[1]
                x2, y2 = tv_to_xy(end.time, end.val, ratio=False)
                p = c.beginPath()
                half_thickness = 2.5
                p.moveTo(x1, y1 - half_thickness)
                p.lineTo(x1, y1 + half_thickness)
                p.lineTo(x2, y2 + half_thickness)
                p.lineTo(x2, y2 - half_thickness)
                c.drawPath(p, stroke=0, fill=1)


class UsageTimerGraph(Flowable):
    """ Create a single monitor data graph. """

    def __init__(self, path: str, report: Report, data: VOCSNData, ):
        """
        Initialize.
        :param path: Program execution path.
        :param report: Report reference.
        :param data: VOCSN data container.
        """
        Flowable.__init__(self)

        # Reference
        self.path = path
        self.report = report
        self.data = data

        # Properties
        self.width = 7.25 * inch
        self.height = 1.75 * inch

    def wrap(self, *args):
        """ Make internal sizes available to build engine. """
        return self.width, self.height

    def draw(self):
        """ Construct block. """

        # References
        c = self.canv
        d = self.data

        # Collect last usage timer event
        sys_pm_due = ["---", "---"]
        sys_usage = ["---", "---"]
        pump_use = ["---", "---"]
        # o2_pm_due = ["---", "---"]
        o2_therapy = ["---", "---"]
        vpsa = ["---", "---"]
        for event in d.events_all:
            if event.id == "6022":
                for val in event.values:
                    if val.key == "12004":
                        sys_pm_due = val.str.split(' ')
                    elif val.key == "12001":
                        sys_usage = val.str.split(' ')
                    elif val.key == "12003":
                        pump_use = val.str.split(' ')
                    # elif val.key == "12005":
                    #     o2_pm_due = val.str.split(' ')
                    elif val.key == "14506":
                        o2_therapy = val.str.split(' ')
                    elif val.key == "12002":
                        vpsa = val.str.split(' ')

        # Title
        c.setFont(s.Fonts.title, 14)
        c.setFillColor(s.Colors.dark_blue)
        c.drawCentredString(3.75 * inch, 1.25 * inch, "Usage Timers")

        # Override PM due label for emergency models
        if "mergency" in d.model:
            pm_label = "Hours to Expiration:"
        else:
            pm_label = "System PM Due In:"

        # System usage only
        if d.model_id in [ve.Models.VC_PRO, ve.Models.V_PRO, ve.Models.VC]:

            # Styles
            styles = [
                ('ALIGN', (0, 0), (1, -1), "RIGHT"),
                ('FONT', (0, 0), (0, -1), s.Fonts.heavy),
                ('LEFTPADDING', (0, 0), (-1, -1), 2),
                ('RIGHTPADDING', (0, 0), (-1, -1), 2)
            ]

            # Populate table data
            data = [
                [pm_label, sys_pm_due[0], sys_pm_due[1]],
                ["System Usage:", sys_usage[0], sys_usage[1]],
            ]

            # Build table
            widths = [1.5 * inch, 0.5 * inch, 0.5 * inch]
            heights = [0.1 * inch, 0.25 * inch]
            table = Table(data=data, colWidths=widths, rowHeights=heights, style=styles, spaceBefore=0.5 * inch)
            table.wrapOn(c, 0, 0)
            table.drawOn(c, 2.45 * inch, 0.6 * inch)

        # System monitors plus pump
        elif d.model_id in [ve.Models.VCSN_PRO]:

            # Styles
            styles = [
                ('ALIGN', (0, 0), (1, -1), "RIGHT"),
                ('FONT', (0, 0), (0, -1), s.Fonts.heavy),
                ('LEFTPADDING', (0, 0), (-1, -1), 2),
                ('RIGHTPADDING', (0, 0), (-1, -1), 2)
            ]

            # Populate table data
            data = [
                [pm_label, sys_pm_due[0], sys_pm_due[1]],
                ["System Usage:", sys_usage[0], sys_usage[1]],
                ["Pump Usage:", pump_use[0], pump_use[1]],

            ]

            # Build table
            widths = [1.5 * inch, 0.5 * inch, 0.5 * inch]
            heights = [0.1 * inch, 0.25 * inch, 0.25 * inch]
            table = Table(data=data, colWidths=widths, rowHeights=heights, style=styles, spaceBefore=0.5 * inch)
            table.wrapOn(c, 0, 0)
            table.drawOn(c, 2.45 * inch, 0.35 * inch)

        # All usage monitors
        else:

            # Styles
            styles = [
                ('ALIGN', (0, 0), (1, -1), "RIGHT"),
                ('ALIGN', (3, 0), (4, -1), "RIGHT"),
                ('FONT', (0, 0), (0, -1), s.Fonts.heavy),
                ('FONT', (3, 0), (3, -1), s.Fonts.heavy),
                ('LEFTPADDING', (0, 0), (-1, -1), 2),
                ('RIGHTPADDING', (0, 0), (-1, -1), 2)
            ]

            # Populate table data
            data = [
                [pm_label, sys_pm_due[0], sys_pm_due[1], "Pump Usage:", pump_use[0], pump_use[1]],
                ["System Usage:", sys_usage[0], sys_usage[1], "VPSA Usage:", vpsa[0], vpsa[1]],
                ["O2 Concentrator Usage:", o2_therapy[0], o2_therapy[1], "", "", ""]
            ]

            # Build table
            widths = [1.5 * inch, 0.5 * inch, 0.5 * inch] * 2
            heights = [0.1 * inch, 0.25 * inch, 0.25 * inch]
            table = Table(data=data, colWidths=widths, rowHeights=heights, style=styles, spaceBefore=0.5 * inch)
            table.wrapOn(c, 0, 0)
            table.drawOn(c, 1.25 * inch, 0.35 * inch)
