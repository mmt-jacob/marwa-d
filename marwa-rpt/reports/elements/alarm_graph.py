#!/usr/bin/env python
"""
Creates a flowable bar graph for alarm statistics.

    Version Notes:
        1.0.0.0 - 01/24/2020 - Created file with AlarmGraph class.

"""

__author__ = "John Dorian for Sai Systems Technologies"
__copyright__ = "Copyright 2019"
__version__ = "1.0.0.0"

# ReportLab modules
from reportlab.lib.units import inch
from reportlab.pdfgen.canvas import Canvas

# VOCSN modules
from reports.elements.styles import Styles as s
from modules.processing.graph_range import auto_calc_graph_ticks


def alarm_graph(canvas: Canvas, size: list, x_corner: float, y_corner: float, x_vals, y_vals, color,
                zero_on_left: bool):
    """
    Prepare individual alarm graph area.
    :param canvas: Parent canvas.
    :param size: Graph Area dimensions.
    :param x_corner: X coordinate for lower left corner.
    :param y_corner: Y coordinate for lower left corner.
    :param x_vals: X-axis values
    :param y_vals: Y-axis values.
    :param color: Bar color.
    :param zero_on_left: Choose horizontal graph orientation.
    """

    def t_to_x(v: float):
        """ Get x coordinate on graph from x value. """
        return h_start + direction * (v / x_max) * h_range

    def t_to_y(v: float):
        """ Get y coordinate on graph from y label. """
        v += 0.5
        return v_start + (v / y_max) * v_range

    # ----- Setup ----- #

    # References
    w = size[0]
    h = size[1]
    c = canvas

    # Set axis scaling
    x_max = 0
    for val in x_vals:
        x_max = max(x_max, val)
    n = None if x_max else 0
    x_max *= 0.95
    min_ticks = 4 if x_max >= 1000 else 5
    ticks = auto_calc_graph_ticks(n, n, n, n, n, fill_max=x_max, min_ticks=min_ticks)

    # Settings
    margin = 8
    font_size = 10
    x_font_size = 10
    top_margin = 0
    c.setLineWidth(1)
    label_margin = 0.8 * inch

    # Coordinate space conversion variables
    zol = zero_on_left
    direction = 1 if zol else -1
    y_max = len(y_vals)
    x_max = float(ticks[-1])
    if zol:
        h_start = x_corner + label_margin
        h_end = x_corner + w - margin
    else:
        h_start = x_corner + w - label_margin
        h_end = x_corner + margin
    h_range = abs(h_end - h_start)
    v_start = y_corner + font_size + 0.5*margin
    v_end = y_corner + h - top_margin
    v_range = abs(v_end - v_start)

    # Set x-axis font size
    max_tick_width = h_range / len(x_vals) - 5
    c.setFont(s.Fonts.light, x_font_size)
    while c.stringWidth(str(x_vals[-1])) > max_tick_width and x_font_size > 3:
        x_font_size -= 0.1

    # ----- Render ----- #

    # Draw graph lines
    c.setFillColor(s.Colors.dark_gray)
    c.setStrokeColor(s.Colors.med_light_gray)
    for tick in ticks:
        c.setStrokeColor(s.Colors.med_light_gray)
        x = t_to_x(float(tick))
        c.drawCentredString(x, 0, tick)
        c.setStrokeColor(s.Colors.light_gray)
        p = c.beginPath()
        p.moveTo(x, v_start)
        p.lineTo(x, v_end)
        p.close()
        c.drawPath(p)

    # Draw Y-axis labels
    c.setFont(s.Fonts.light, font_size)
    x_pos = label_margin - margin if zol else x_corner + w - label_margin + margin
    for y, label in enumerate(y_vals):
        y_pos = t_to_y(y) - 0.4*font_size
        if zol:
            c.drawRightString(x_pos, y_pos, label)
        else:
            c.drawString(x_pos, y_pos, label)

    # Draw bars and value labels
    font_size = 12
    c.setFont(s.Fonts.heavy, font_size)
    bar_thickness = v_range / len(y_vals) * 0.7
    base = 0.6 * bar_thickness
    for idx in range(0, len(y_vals)):

        # Values
        label = str(x_vals[idx])
        x = t_to_x(x_vals[idx])
        y = t_to_y(idx)

        # Ignore 0 value
        if label == "0":
            continue

        # Bar
        bar_width = abs(h_start - x)
        c.setFillColor(color)
        if zol:
            c.rect(h_start + 0.5, y-base, bar_width - 0.5, bar_thickness, stroke=False, fill=True)
        else:
            c.rect(x, y - base, bar_width - 0.5, bar_thickness, stroke=False, fill=True)

        # Value labels
        str_width = c.stringWidth(label)
        y_pos = y - 0.5 * font_size
        if str_width < bar_width - margin:
            c.setFillColor(s.Colors.white)
            x_pos = x - direction * (0.5 * str_width + 0.5*margin)
            c.drawCentredString(x_pos, y_pos, label)
        else:
            c.setFillColor(s.Colors.dark_gray)
            x_pos = x + direction * (0.5 * str_width + 0.5*margin)
            c.drawCentredString(x_pos, y_pos, label)
