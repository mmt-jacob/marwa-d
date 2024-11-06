#!/usr/bin/env python
"""
Creates a flowable report object with alarm statistics including bar graphs and summary averages.

    Version Notes:
        1.0.0.0 - 09/29/2019 - Created file with AlarmStats report element.
        1.0.0.1 - 10/04/2019 - Renamed timestamp fields.
        1.0.0.2 - 11/20/2019 - Changed graph color.
        1.0.0.3 - 11/22/2019 - Added trend blocks.
        1.0.0.4 - 12/12/2019 - Changed graph label to dark blue.
        1.0.0.5 - 12/21/2019 - Implemented error management.
        1.0.0.6 - 01/25/2020 - Created custom alarm graphs.
        1.0.0.7 - 03/29/2020 - Disabled average occurrences block with less than a day of data.

"""

__author__ = "John Dorian for Sai Systems Technologies"
__copyright__ = "Copyright 2019"
__version__ = "1.0.0.7"

# Built-in modules
from datetime import timedelta

# ReportLab modules
from reportlab.lib.units import inch
from reportlab.platypus.flowables import Flowable

# VOCSN modules
from modules.models.report import Report
from reports.elements.trend import TrendBlock
from modules.models.errors import ErrorManager
from reports.elements.styles import Styles as s
from modules.models.vocsn_data import VOCSNData
from reports.elements.alarm_graph import alarm_graph


class AlarmStats(Flowable):
    """ Create an extension of a ReportLab Flowable report object containing alarm statistics graphs and averages. """

    def __init__(self, em: ErrorManager, report: Report, data: VOCSNData, w_dir: str):
        """
        Initialize.
        :param em: Error manager.
        :param report: Report definition object.
        :param data: VOCSN data container.
        :param w_dir: Working directory.
        :return: AlarmState flowable.
        """
        Flowable.__init__(self)

        # References
        self.em = em
        self.dir = w_dir
        self.data = data
        self.report = report

        # Properties
        self.width = 7.5 * inch
        self.height = 3 * inch
        self.graph_width = 2.65 * inch
        self.graph_height = self.height - 0.4*inch

    def wrap(self, *args):
        """ Make internal sizes available to build engine. """
        return self.width, self.height

    def draw(self):
        """ Construct flowable canvas. """

        # References
        data = self.data
        canvas = self.canv

        # Properties
        w = self.width
        h = self.height
        gw = self.graph_width
        gh = self.graph_height
        graph_margin_offset = 10
        pad = 0.125 * inch

        # Check if day values should be used
        day_close_enough = timedelta(minutes=1435)
        use_days = self.report.range.data_duration >= day_close_enough

        # Graph Titles
        canvas.setFont(s.Fonts.heavy, 14)
        canvas.setFillColor(s.Colors.dark_blue)
        canvas.drawCentredString(gw * 0.5 + pad, gh + pad, "Avg. Alarms by Day")
        canvas.drawCentredString(w - gw*0.5 - graph_margin_offset - pad, gh + pad, "Avg. Alarms by Hour")

        # Weekday alarm graph
        pos_x = 0
        pos_y = 0
        val_x = []
        val_y = []
        for idx in [5, 4, 3, 2, 1, 0, 6]:
            day = data.alarms_tracker.calendar.days[idx]
            val_x.append(day.count)
            val_y.append(day.name)
        color = s.Colors.orange
        alarm_graph(canvas, [gw, gh], pos_x, pos_y, val_x, val_y, color, zero_on_left=True)

        # Time of day alarm graph
        pos_x = w - gw - graph_margin_offset
        pos_y = 0
        val_x = []
        val_y = []
        buckets = data.alarms_tracker.calendar.times
        for idx in range(len(buckets)-1, -1, -1):
            bucket = buckets[idx]
            val_x.append(bucket.count)
            val_y.append(bucket.name)
        color = s.Colors.orange
        alarm_graph(canvas, [gw, gh], pos_x, pos_y, val_x, val_y, color, zero_on_left=False)

        # Total alarms
        max_width = 1.5 * inch
        x_pos = 0.5 * (w - graph_margin_offset)
        t_count = data.alarms_tracker.stats.total_count
        val = str(t_count) if t_count is not None else None
        units = ""
        label = "Total Alarms"
        s.centered_2line_val(canvas, x_pos, h - 0.1*inch, max_width, val, units, label)

        # Average duration block
        size = [1.1 * inch, 0.8 * inch]
        x_offset = 0.5*self.width - 0.5*size[0] - 0.075*inch
        stats = data.alarms_tracker.stats
        val = stats.avg_duration
        if val:
            val = val.total_seconds()
        percentage = stats.trend_duration_percentage
        block = TrendBlock(self.em, self.dir, size, s.Colors.ventilator_light, "Average\nDuration",
                           val, 0, "sec.", percentage)
        block.wrap()
        block.drawOn(canvas, x_offset, 1.15 * inch)

        # Average occurrence block
        off = None
        val = stats.avg_occurrence if use_days else off
        percentage = stats.trend_occurrence_percentage if use_days else off
        block = TrendBlock(self.em, self.dir, size, s.Colors.ventilator_light, "Average\nOccurrences",
                           val, 0, "/Day", percentage, in_use=use_days)
        block.wrap()
        block.drawOn(canvas, x_offset, 0.25 * inch)

        # Add note explaining disabled block
        if not use_days:
            canvas.setFont(s.Fonts.italic, 9)
            canvas.setFillColor(s.Colors.med_light_gray)
            canvas.drawCentredString(3.675 * inch, 6, "Insufficient data")
