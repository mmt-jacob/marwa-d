#!/usr/bin/env python
"""
Functions used to calculate graph range and tick values.

    Version Notes:
        1.0.0.0 - 10/01/2019 - Created first pass at file with functions needed to calculate monitor graph Y-axis ticks.
        1.0.0.1 - 10/02/2019 - Added some fields to support positioning graph dots.
        1.0.0.2 - 10/16/2019 - Improved y-axis ranging logic
        1.0.0.3 - 10/17/2019 - Fixed x-scale range to include all days.
        1.0.0.4 - 11/03/2019 - Fixed bug scaling values with 0 min value.
        1.0.1.0 - 11/06/2019 - Added minimum range to y-axis from settings.
        1.0.1.1 - 11/27/2019 - Added lower bound to y-axis from settings.
        1.0.1.2 - 12/20/2019 - Changed tick calculations to support sub-day report ranges. Fixed min. range calculation.
        1.0.1.3 - 01/09/2020 - Fixed the negative range protection.
        1.0.2.0 - 01/11/2020 - Changed to allow misalignment from calendar. Improved I:E ration tick generation.
        1.0.2.1 - 01/13/2020 - Fixed calculation bug in last change.
        1.0.2.2 - 01/25/2020 - Generalized for use with alarm graphs.
        1.0.2.3 - 02/24/2020 - Changed Y-scaling to expand under all circumstances to include outlier values.

"""

__author__ = "John Dorian for Sai Systems Technologies"
__copyright__ = "Copyright 2019"
__version__ = "1.0.2.3"

# Built-in modules
import math
from datetime import datetime, timedelta

# VOCSN modules
from modules.models.vocsn_data import MonitorChannel


class XTick:
    """ X axis ticks """

    def __init__(self, dt: datetime, label: str = None):
        self.dt = dt
        self.label = label


def calc_monitor_graph_x_ticks(r_range):
    """
    Set the monitor graph x-axis tick values.
    :param r_range: Report range definition
    """

    # Variables
    day = timedelta(days=1)
    r_range.tick_labels = tick_labels = []
    r_range.tick_times = tick_times = []
    start = r_range.start
    end = r_range.end
    start_of_day = datetime(year=start.year, month=start.month, day=start.day)
    sub_tick_count = r_range.graph_sub_ticks
    sub_tick_length = r_range.graph_tick_duration / sub_tick_count
    use_hours = r_range.graph_tick_units in ["hours", "minutes"]

    # Align to Sunday if ticks are a week
    if r_range.graph_tick_duration in [timedelta(days=7), timedelta(days=14)]:
        while start_of_day.weekday() != 6:
            start_of_day -= day

    # Generate ticks and store the ones in range
    tick = start_of_day
    tick_count = sub_tick_count
    while tick <= end:
        if start <= tick <= end:

            # Labeled tick
            if tick_count == sub_tick_count:
                if use_hours:
                    label = "{:02d}:{:02d}".format(tick.hour, tick.minute)
                    if label == "00:00":
                        label = "{}/{}".format(tick.month, tick.day)
                else:
                    label = "{}/{}".format(tick.month, tick.day)

            # Sub-tick
            else:
                label = None

            # Store tick
            tick_labels.append(label)
            tick_times.append(tick)

        # Next tick
        if tick_count == sub_tick_count:
            tick_count = 0
        tick_count += 1
        tick += sub_tick_length

    # Ensure limit lines
    if tick_times[0] != start:
        tick_times.insert(0, start)
        tick_labels.insert(0, "")
    if tick_times[-1] != end:
        tick_times.append(end)
        tick_labels.append("")


def auto_calc_graph_ticks(channel: MonitorChannel, avg_5th_min: float, avg_5th: float, avg_95th: float,
                          avg_95th_max: float, graph_def: dict = None, fill_max: float = None,
                          min_ticks: int = None):
    """
    Calculate the Y-axis range for a monitor graph, generate a list of tick values, and store the values with the 
    monitor channel data container.
    :param channel: Monitor data container. 
    :param avg_5th_min: Lowest Y-value data point on graph.
    :param avg_5th: Average 5th percentile Y-axis value.
    :param avg_95th: Average 95th percentile Y-axis value.
    :param avg_95th_max: Upper Y-value data point on graph.
    :param graph_def: If applicable, definitions for the corresponding monitor graph
    :param fill_max: Fill graph up to this maximum
    :param min_ticks: Minimum number of ticks.
    """

    # Handle no data
    if (avg_5th_min is None or avg_95th_max is None) and fill_max is None:
        channel.ticks = ['---', '---', '---', '---', '---']
        return

    # Get settings parameters
    if fill_max is None:
        negative_data = avg_5th < 0
        y_range_min = None
        y_range_max = None
        y_range = None
        y_bound_low = None
        y_bound_high = None
        if graph_def:
            if "range" in graph_def:
                set_range = graph_def["range"]
                y_range_min = set_range[0]
                y_range_max = set_range[1]
            if "min_range" in graph_def:
                y_range = graph_def["min_range"]
            if "min_bound" in graph_def:
                y_bound_low = min(graph_def["min_bound"], avg_5th_min)
            if "max_bound" in graph_def:
                y_bound_high = max(graph_def["max_bound"], avg_95th_max)
        fixed = y_range_min is not None

        # Fixed range
        if fixed:
            y_min = min(y_range_min, avg_5th_min)
            y_max = max(y_range_max, avg_95th_max)

        # Dynamic range
        else:

            # Calculate final monitor graph Y-axis range
            val_range = avg_95th - avg_5th
            margin = val_range * 0.3
            avg_min = avg_5th - val_range - margin
            avg_max = avg_95th + val_range + margin
            outer_min = avg_5th_min if avg_5th_min is not None else avg_min
            outer_max = avg_95th_max if avg_95th_max is not None else avg_max
            center = (avg_min + avg_max) * 0.5
            if not negative_data and y_range:
                center = max(center, y_range * 0.5)
            setting_min = center - 0.5*y_range if y_range else avg_min
            setting_max = center + 0.5*y_range if y_range else avg_max
            y_min = min(avg_min, outer_min, setting_min)
            y_max = max(avg_max, outer_max, setting_max)
            if y_bound_low is not None:
                y_min = max(y_bound_low, y_min)
                if y_range:
                    y_max = max(y_min + y_range, y_max)
            if y_bound_high is not None:
                y_max = max(y_bound_high, y_max)

    # Full-range scaling when percentiles not specified
    else:

        # Default 0 value
        if fill_max == 0:
            return ["0", "1", "2", "3", "4"]

        # Set ranges to extremes
        y_min = 0
        y_max = fill_max
        avg_5th_min = 0
        y_bound_low = 0
        y_bound_high = None
        negative_data = y_min < 0

    # Calculate monitor graph Y-axis tick values
    most_significant = max(abs(y_min), abs(y_max))
    decade = get_decade(most_significant)

    # Determine appropriate graph ticks
    ticks = []
    min_ticks = min_ticks if min_ticks else 4
    tick_scale_count = 0
    ratio = channel.ratio if channel else False
    while len(ticks) < min_ticks:
        for factor in [5, 2.5, 2, 1]:
            interval = factor * decade
            if y_bound_low is not None:
                tick_bottom = min(y_bound_low, avg_5th_min) if avg_5th_min else y_bound_low
            else:
                tick_bottom = closest_tick(y_min, interval, top=False)
            if y_bound_high is not None:
                tick_top = max(y_bound_high, avg_95th_max) if avg_95th_max else y_bound_high
            else:
                tick_top = closest_tick(y_max, interval, top=True)
            ticks = get_ticks(tick_bottom, tick_top, interval, negative_data, y_bound_low, y_bound_high, ratio=ratio)
            if len(ticks) >= min_ticks:
                break
        decade /= 10
        tick_scale_count += 1

        # Very small range set to default
        if tick_scale_count > 20:
            ticks = []
            close_int = round(y_min) - 2
            for _ in range(0, 5):
                ticks.append(str(close_int))
                close_int += 1
            break

    # Save ticks
    if channel:
        channel.ticks = ticks
    else:
        return ticks


def calc_session_graph_y_ticks(session, y_min: float, y_max: float, has_data: bool, graph_def: dict = None):
    """
    Calculate the Y-axis range for a session data graph, generate a list of tick values, and store the values with the
    monitor channel data container.
    :param session: Therapy session start/stop data tracker.
    :param y_min: Lowest Y-value data point on graph.
    :param y_max: Upper Y-value data point on graph.
    :param has_data: Session data available.
    :param graph_def: If applicable, definitions for the corresponding monitor graph
    """

    # Handle no data
    if not has_data:
        session.ticks = ['---', '---', '---', '---', '---']
        return

    # Get settings parameters
    negative_data = y_min < 0
    y_range_min = None
    y_range_max = None
    y_range = None
    if graph_def:
        if "range" in graph_def:
            set_range = graph_def["range"]
            y_range_min = set_range[0]
            y_range_max = set_range[1]
        if "min_range" in graph_def:
            y_range = graph_def["min_range"]
    fixed = y_range_min is not None

    # Fixed range
    if fixed:
        y_min = min(y_range_min, y_min)
        y_max = max(y_range_max, y_max)

    # Dynamic range
    else:

        # Calculate final monitor graph Y-axis range
        val_range = y_max - y_min
        margin = val_range * 0.2
        avg_min = y_min - val_range - margin
        avg_max = y_max + val_range + margin
        center = (avg_min + avg_max) * 0.5
        if not negative_data and y_range:
            center = max(center, y_range * 0.5)
        setting_min = center - 0.5*y_range if y_range else avg_min
        setting_max = center + 0.5*y_range if y_range else avg_max
        y_min = min(avg_min, setting_min)
        y_max = max(avg_max, setting_max)

    # Calculate monitor graph Y-axis tick values
    most_significant = max(abs(y_min), abs(y_max))
    decade = get_decade(most_significant)

    # Determine appropriate graph ticks
    ticks = []
    min_ticks = 4
    tick_scale_count = 0
    while len(ticks) < min_ticks:
        for factor in [5, 2.5, 2, 1]:
            interval = factor * decade
            tick_bottom = closest_tick(y_min, interval, top=False)
            tick_top = closest_tick(y_max, interval, top=True)
            ticks = get_ticks(tick_bottom, tick_top, interval, negative_data)
            if len(ticks) >= min_ticks:
                break
        decade /= 10
        tick_scale_count += 1

        # Very small range set to default
        if tick_scale_count > 20:
            ticks = []
            close_int = round(y_min) - 2
            for _ in range(0, 5):
                ticks.append(str(close_int))
                close_int += 1
            break

    # Save ticks
    session.ticks = ticks


def get_decade(val: float):
    """
    Determine the decade of the most significant digit.
    :param val: Value to check.
    :return: Value decade
    """

    # Variables
    n = 0

    # Value greater/equal to than 1
    if val >= 1:
        while val >= 10:
            n += 1
            val //= 10

    # Value less than 1
    elif val <= -1:
        while val <= 1:
            n -= 1
            val *= 10

    # Return the decade
    return 10 ** n


def closest_tick(val: float, interval: float, top: bool = False):
    """
    Determine the closest tick to the provided value. Rounds up for top value, down for bottom value, with a provision
    to exceed bounds by a little bit.
    :param val: Target value.
    :param interval: Interval between ticks.
    :param top: Tick increment interval.
    :return: Closest tick value
    """

    # Settings
    oversample = 0.2

    # Set direction
    direction = 1 if top else -1

    # Get closest inclusive tick
    if top:
        tick = math.ceil(val / interval)
    else:
        tick = math.floor(val / interval)
    round_tick = interval * tick

    # Step back to center one interval if it's still close on the top
    if top:
        gap = round_tick - val
        if gap > (1 - oversample) * interval:
            round_tick -= direction * interval
    return round_tick


def round_to_base(val: float, base: float):
    """
    Round to specified base.
    :param val: Value to round.
    :param base: Base to round to.
    :return: Rounded number
    """
    return base * round(val/base)


def get_ticks(bottom: float, top: float, interval: float, use_negative: bool, low_bound: float = None,
              high_bound: float = None, ratio: bool = None):
    """
    List all the ticks from bottom to top at the provided interval.
    :param bottom: Lowest tick
    :param top: Highest tick
    :param interval: Interval between ticks.
    :param use_negative: Allows graph to extend into negative values.
    :param low_bound: Constrain lower y values.
    :param high_bound: Constrain upper y values.
    :param ratio: True when data represents a ratio.
    :return: List of tick labels as strings.
    """

    # Variables
    ticks = []
    tick = bottom

    # Protect against miniscule increments (shouldn't happen)
    interval = max(interval, 0.0001)

    # List ticks in range
    tick_min = 0
    while tick <= top:

        # Correct small rounding error
        tick = round_to_base(tick, 0.0000001)
        tick_min = max(tick_min, tick)

        # Number conversion
        label = str(tick)
        if label[-2:] == '.0':
            label = label[:-2]

        # Add to list
        ticks.append(label)
        tick += interval

    # Avoid displaying negative values unless necessary
    if not use_negative:
        while (len(ticks) > 0) and (float(ticks[0]) < 0):
            del ticks[0]

    # Constrain lower y values
    if low_bound is not None:
        while (len(ticks) > 0) and (float(ticks[0]) < low_bound):
            del ticks[0]

    # Constrain upper y values
    if high_bound is not None:
        while (len(ticks) > 0) and (float(ticks[-1]) > high_bound):
            del ticks[-1]

    # Prevent 0 in ratio values
    if ratio:
        delete = 0
        while len(ticks) > 0 and delete is not None:
            first = None
            delete = None
            for x, tick in enumerate(ticks):
                if -1 <= float(tick) <= 1:
                    if first is None:
                        ticks[x] = '0'
                        first = x
                    else:
                        delete = x
                        break
            if delete is not None:
                del ticks[delete]

    # Return completed list
    return ticks
