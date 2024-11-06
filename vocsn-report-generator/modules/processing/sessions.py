#!/usr/bin/env python
"""
Elements used in the Trend Summary section of the report.

    Version Notes:
        1.0.0.0 - 10/21/2019 - Created file with tracking for therapy start/stop attributes.
        1.0.0.1 - 10/30/2019 - Added values to divide graphs into segments.
        1.0.0.2 - 10/31/2019 - Modified value storage to allow for line segmentation on graphs, fixed some calculations.
        1.0.0.3 - 11/01/2019 - Fixed suction precision value.
        1.0.0.4 - 11/02/2019 - Added session value active time tracking to track O2 mode.
        1.0.0.5 - 11/07/2019 - Filter sessions by report range.
        1.0.0.6 - 11/14/2019 - Updated session value tracking to use settings as backup data source.
        1.0.0.7 - 11/19/2019 - Disabled trend calculations for 1 day report.
        1.0.0.8 - 11/22/2019 - Multiple changes to support proper settings average calculations. Renamed trackers.
        1.0.1.0 - 11/29/2019 - Added function to create log detail lines for therapy sessions.
        1.0.1.1 - 12/05/2019 - Implemented patient reset.
        1.0.1.2 - 12/10/2019 - Moved therapy start/stop definition lookup to metadata reader.
        1.0.1.3 - 12/11/2019 - Corrected preset label formatting.
        1.0.1.4 - 12/14/2019 - Fixed bug that broke session values displaying in monitor graphs.
        1.0.1.5 - 12/18/2019 - Improved suction detail lines.
        1.0.1.6 - 12/21/2019 - Implemented error management.
        1.0.1.7 - 01/09/2020 - Changed suction precision to 0.
        1.0.2.0 - 01/18/2020 - Implemented pre-trend average calculations.
        1.0.2.1 - 01/19/2020 - Centralized trend logic.
        1.0.2.2 - 02/04/2020 - Improved handling of a partial 7203 event.
        1.0.2.3 - 02/26/2020 - Added provision to properly capture oxygen mode value from 5004 settings message.
        1.0.2.4 - 02/29/2020 - Added oxygen preset to synthetic events depicting preset changes.
        1.1.0.0 - 04/10/2020 - Added non-session event tracking for insp. hold events.

"""

__author__ = "John Dorian for Sai Systems Technologies"
__copyright__ = "Copyright 2019"
__version__ = "1.1.0.0"

# Built-in modules
import sys
from enum import Enum, auto
from datetime import datetime, timedelta

# VOCSN modules
from modules.processing.events import Event
from modules.models.vocsn_data import VOCSNData
from modules.processing.values import EventValue
from modules.processing.utilities import calc_trend
from modules.models.vocsn_enum import Therapies, SubTherapies
from modules.processing.graph_range import calc_session_graph_y_ticks
from modules.models.vocsn_enum import PresetMIDs, PressureUnits, EventIDs as eID


class SessionVal:
    """ Record settings and measurements from therapy start and stop events. """

    def __init__(self, active: bool, time: datetime, num: float, string: str):
        """ Initialize. """

        # Attributes
        self.active = active
        self.time = time
        self.num = num
        self.str = string


class SessionGraphSample:
    """ Data for monitor-style graph. """

    def __init__(self, time: datetime, val: float, is_last: bool):
        self.time = time
        self.val = val
        self.is_last = is_last


class SessionValType(Enum):
    """ Session start/stop event source type. """
    SINGLE = auto()
    START = auto()
    BOTH = auto()
    END = auto()


class SessionValTracker:
    """ Track settings and measurements from therapy start/stop records. Only applies to 6014/6015 events, not vent."""

    def __init__(self, tracker, key: str, start_def: dict, end_def: dict, track_unique_vals: bool = False):
        """
        Initialize.
        Note that at this stage numbers have already been scaled according to parameter definitions.
        :param tracker: Therapy tracker reference.
        :param key: session value name/key.
        :param start_def: Start record metadata definition
        :param end_def: End record metadata definition.
        :param track_unique_vals: Track active duration for each unique value.
        """

        # Reference
        self.em = tracker.em
        self.tracker = tracker

        # Identifiers
        self.id = key

        # Determine type
        in_start = start_def and start_def["attributes"] and key in start_def["attributes"]
        in_end = end_def and end_def["attributes"] and key in end_def["attributes"]
        if in_start:
            if in_end:
                self.type = SessionValType.BOTH
            else:
                self.type = SessionValType.START
        else:
            if in_end:
                self.type = SessionValType.END
            else:
                self.type = SessionValType.SINGLE

        # Current values
        self.active = False
        self.last_value = None
        self.last_time = None

        # Average values
        self.val_time_product = 0
        self.duration = timedelta(seconds=0)
        self.sessions = 0
        self.average = None

        # Trend average values
        self.use_trend = tracker.range.use_trend
        self.val_time_product_pre_trend = 0
        self.val_time_product_trend = 0
        self.trend_percent = None
        self.duration_pre_trend = timedelta(seconds=0)
        self.duration_trend = timedelta(seconds=0)
        self.sessions_pre_trend = 0
        self.sessions_trend = 0
        self.average_pre_trend = None
        self.average_trend = None
        self.trend_delta = None

        # Cough values
        self.total_coughs = None
        self.trend_coughs = None
        self.pre_trend_coughs = None
        self.total_val_cough_prod = None
        self.trend_val_cough_prod = None
        self.pre_trend_val_cough_prod = None

        # Units
        if key in ["is-preset-change-only", "suction-pressure"]:
            self.units = None
            self.precision = None
        elif key == "therapy-duration-seconds":
            self.units = "secs"
            self.precision = 1
        else:
            param_def = tracker.data.metadata_parameters[key]
            self.units = param_def["displayUnits"]
            self.precision = param_def["precision"]

        # Session records
        self.records = []
        self.graph_samples = []
        self.unique_value_time = {}
        self.unique_value_trend_time = {}
        self.unique_value_pre_trend_time = {}
        self.track_unique_vals = track_unique_vals

        # Range values
        self.min = sys.maxsize
        self.max = -sys.maxsize
        self.ticks = None

    def add_event(self, event: Event, val: EventValue, active: bool = None):
        """
        Add to session statistics from therapy start/stop event.
        :param event: Therapy start/stop event.
        :param val: Therapy start/stop event.
        :param active: Explicitly declare on/off state.
        """

        # Determine prior state
        was_active = self.active
        non_session = self.type == SessionValType.SINGLE

        # BACKUP DATA SOURCE - Use current settings in absence of valid start/stop data.
        if val.num is None and val.str is None:

            # Check if value is available as a setting
            settings = self.tracker.data.settings_all
            if self.id in settings:
                setting = settings[self.id]
                set_val = setting.current_value()
                val.str = str(set_val) if set_val is not None else None
                if set_val and type(set_val) is not str:
                    val.num = float(set_val)

        # Detect change_only
        change_only = False
        if hasattr(event, "is_preset_change_only"):
            change_only = event.is_preset_change_only

        # Therapy start
        if event.id == eID.THERAPY_START and not change_only:
            start_val = val.num if val.num is not None else val.str
            end_val = None
            is_active = True

        # Therapy stop
        elif event.id == eID.THERAPY_END or change_only:
            start_val = self.last_value
            end_val = val.num if val.num is not None else val.str
            is_active = change_only

            # O2 Mode accepts updates from 5004 settings update
            if self.id == "87" and event.id == eID.SETTINGS_PRESETS:
                is_active = self.tracker.data.events_tracker.oxygen.calendar.active

        # Non-session event types
        elif non_session:
            start_val = val.num
            end_val = val.num
            is_active = True

        # Unexpected value
        else:
            raise Exception("Unexpected event in session tracker: {}".format(event.id))

        # Use explicit activity state
        if active is not None:
            is_active = active

        # Update average statistics at end of active period
        have_values = False
        graph_start = None
        graph_end = None

        # Variables
        avg_val = 0

        # Start only
        if (self.type == SessionValType.START and start_val is not None) or \
                (change_only and start_val is not None) or \
                (self.type == SessionValType.BOTH and start_val is not None and end_val is None):
            avg_val = start_val
            calc_numbers = type(avg_val) != str
            have_values = True
            graph_start = graph_end = start_val

        # End only
        elif (self.type == SessionValType.END and end_val is not None) or \
                (self.type == SessionValType.BOTH and start_val is None and end_val is not None):
            avg_val = end_val
            calc_numbers = type(avg_val) != str
            have_values = True
            graph_start = graph_end = end_val

        # Both start and end
        elif self.type == SessionValType.BOTH and start_val is not None and end_val is not None:
            calc_numbers = type(end_val) != str
            if calc_numbers:
                avg_val = (end_val + start_val) / 2
            have_values = True
            graph_start = start_val
            graph_end = end_val

        # Non-Session value
        elif non_session and start_val is not None:
            calc_numbers = type(end_val) != str
            self.last_time = event.syn_time
            avg_val = start_val
            have_values = True
            graph_start = avg_val
            graph_end = avg_val

        # No value available
        else:
            avg_val = None
            calc_numbers = False

        # Some values available to process
        if have_values:

            # Process completed session if in range
            r_range = self.tracker.range
            if (was_active and not (self.last_time > r_range.data_end or event.syn_time < r_range.data_start)) or \
                    (non_session and r_range.data_start <= event.syn_time <= r_range.data_end):

                # Update averages
                self.sessions += 1
                session_start = max(self.last_time, r_range.data_start)
                session_end = min(event.syn_time, r_range.data_end)
                sess_duration = timedelta(seconds=5) if non_session else session_end - session_start

                # Value calculations
                if calc_numbers:
                    self.val_time_product += avg_val * sess_duration.total_seconds()
                    self.duration += sess_duration
                    self.records.append(SessionVal(is_active, session_start, graph_end, val.str))
                    self.graph_samples.append(SessionGraphSample(session_start, graph_start, False))
                    self.graph_samples.append(SessionGraphSample(session_end, graph_end, True))

                # Trend values
                if self.use_trend:
                    non_session_dur = timedelta(seconds=1)
                    if not (self.last_time >= r_range.trend_start or event.syn_time < r_range.data_start):
                        self.sessions_pre_trend += 1
                        pre_trend_duration = non_session_dur if non_session else \
                            min(r_range.trend_start, event.syn_time) - max(r_range.data_start, self.last_time)
                        if calc_numbers:
                            self.val_time_product_pre_trend += avg_val * pre_trend_duration.total_seconds()
                            self.duration_pre_trend += non_session_dur if non_session else pre_trend_duration
                    if not (self.last_time > r_range.data_end or event.syn_time < r_range.trend_start):
                        self.sessions_trend += 1
                        trend_duration = non_session_dur if non_session else min(r_range.data_end, event.syn_time) - \
                            max(r_range.trend_start, self.last_time)
                        if calc_numbers:
                            self.val_time_product_trend += avg_val * trend_duration.total_seconds()
                            self.duration_trend += non_session_dur if non_session else trend_duration

                # Track active time for unique values
                if self.track_unique_vals:
                    items = self.unique_value_time
                    t_items = self.unique_value_trend_time
                    pt_items = self.unique_value_pre_trend_time
                    if avg_val in items:
                        items[avg_val] += sess_duration
                    else:
                        items[avg_val] = sess_duration
                        t_items[avg_val] = timedelta(seconds=0)
                        pt_items[avg_val] = timedelta(seconds=0)

                    # Track active trend time for unique values
                    r = self.tracker.range
                    if r.use_trend:
                        session_pre_trend_start = min(max(session_start, r.data_start), r.trend_start)
                        session_pre_trend_end = min(max(session_end, r.data_start), r.trend_start)
                        pre_trend_duration = session_pre_trend_end - session_pre_trend_start
                        if pre_trend_duration != timedelta(hours=0):
                            if avg_val in t_items:
                                pt_items[avg_val] += pre_trend_duration
                            else:
                                pt_items[avg_val] = pre_trend_duration
                        session_trend_start = min(max(session_start, r.trend_start), r.trend_end)
                        session_trend_end = min(max(session_end, r.trend_start), r.trend_end)
                        trend_duration = session_trend_end - session_trend_start
                        if trend_duration != timedelta(hours=0):
                            if avg_val in t_items:
                                t_items[avg_val] += trend_duration
                            else:
                                t_items[avg_val] = trend_duration

        # Capture last value
        if not (val.num is None and val.str is None):
            self.last_value = val.num if val.num is not None else val.str

        # Update range
        if type(val.num) in [int, float]:
            self.max = max(self.max, val.num)
            self.min = min(self.min, val.num)

        # Update current values
        self.active = is_active
        self.last_time = event.syn_time

        # Reset
        if event.id == eID.THERAPY_END:
            self.last_value = None

    def calc_avg(self):
        """ Calculate average value, corrected for session activity and unit scale. """

        # Calculate averages
        seconds = self.duration.total_seconds()
        seconds_trend = self.duration_trend.total_seconds()
        seconds_pre_trend = self.duration_pre_trend.total_seconds()
        has_data = False
        if self.sessions > 0:
            self.average = self.val_time_product / seconds if seconds > 0 else 0
            if self.sessions_trend > 0 and self.sessions_pre_trend > 0:
                self.average_pre_trend = self.val_time_product_pre_trend / seconds_pre_trend \
                    if seconds_pre_trend > 0 else 0
                self.average_trend = self.val_time_product_trend / seconds_trend if seconds_trend > 0 else 0
                self.trend_delta, self.trend_percent = calc_trend(self.average_pre_trend, self.average_trend)
            has_data = True

        # Set y-scale for monitor graphs
        graph_def = None
        graph_defs = self.tracker.report.settings["display"]["monitor_graphs"]
        if self.id in graph_defs:
            graph_def = graph_defs[self.id]
        calc_session_graph_y_ticks(self, self.min, self.max, has_data, graph_def)


class SessionValTrackerSuction:
    """ Wrapper for SessionTracker to handle special suction value with two inputs and variable units. """

    def __init__(self, tracker, start_def: dict, end_def: dict):

        # References
        self.em = tracker.em
        self.event_tracker = tracker
        data = self.event_tracker.data
        start_defs = data.metadata_t_start
        self.unit_enum = start_defs[Therapies.SUCTION.value[0]]["enum_ref"]["SuctionUnits"]

        # Identifiers
        self.id = "suction-pressure"

        # Last units
        self.last_units = "Pa"

        # Base tracker
        self.tracker = SessionValTracker(tracker, self.id, start_def, end_def)

        # Reference properties
        self.precision = 0

        # Placeholders
        self.average = None
        self.units = None
        self.trend_percent = None
        self.trend_delta = None

    def add_event(self, event: Event, val: EventValue, units: EventValue):
        """
        Add to session statistics from therapy start/stop event.
        Units are always stored in pascals, then converted to last used units on retrieval.
        :param event: Therapy start/stop event.
        :param val: Suction value.
        :param units: Suction units.
        """

        # Lookup values if not provided
        if val.num is None:
            val.num = self.event_tracker.data.settings_all["suction-pressure"].current_value()
        if units.str is None:
            units.str = self.event_tracker.data.settings_all["SuctionUnits"].current_value()

        # Current units
        self.last_units = self.units
        self.units = self.tracker.units = self.unit_enum[units.str]

        # Convert to pascals for averaging
        value = val.num
        if self.units == "mmHg":
            value = value * PressureUnits.mmHg_to_Pa

        # Update tracker
        new_units = EventValue(val.key, val.name, value, "{:.0f} {}".format(val.num, self.units))

        self.tracker.add_event(event, new_units)

    def calc_avg(self):
        """ Calculate average, convert to correct units. """

        # Calculate average
        track = self.tracker
        track.calc_avg()

        # Convert units
        if track.average and self.last_units == "mmHg":
            track.average *= PressureUnits.Pa_to_mmHg
            if track.average_trend:
                track.average_trend *= PressureUnits.Pa_to_mmHg
        self.average = track.average
        self.trend_percent = track.trend_percent


def init_session_vals(tracker, data: VOCSNData, therapy):
    """ Initialize a list of session values for a given therapy. """

    # Reference definitions
    m_id = therapy.value
    if type(m_id) is list:
        m_id = m_id[0]

    # Read key IDs
    start_def = data.metadata_t_start[m_id]
    stop_def = data.metadata_t_stop[m_id]

    # Gather list of all attributes
    attr_list = []
    start_attrs = start_def["attributes"]
    if start_attrs:
        for attribute in start_attrs:
            attr_list.append(attribute)
    stop_attrs = stop_def["attributes"]
    if stop_attrs:
        for attribute in stop_attrs:
            if attribute not in attr_list:
                attr_list.append(attribute)

    # Create and return a dict of session value trackers
    trackers = {}
    for attribute in attr_list:
        if attribute in ["suction-pressure"]:
            trackers[attribute] = init_suction_val(tracker, data)
        else:
            track = True if attribute == "87" else False
            trackers[attribute] = SessionValTracker(tracker, attribute, start_def, stop_def, track)
    return trackers


def init_suction_val(tracker, data: VOCSNData):
    """ Initialize an O2 flush session value. """
    therapy = Therapies.SUCTION
    m_id = therapy.value
    if type(m_id) is list:
        m_id = m_id[0]
    start_def = data.metadata_t_start[m_id]
    stop_def = data.metadata_t_stop[m_id]
    return SessionValTrackerSuction(tracker, start_def, stop_def)


def session_details(d: VOCSNData, start_e: Event = None, stop_e: Event = None, therapy=None):
    """
    Construct detail lins to show in Therapy Log.
    :param d: VOCSN data container reference.
    :param start_e: Therapy start event.
    :param stop_e: Therapy Stop event.
    :param therapy: Provide therapy instead of event.
    :return: List of detail strings.
    """

    def lookup_preset(name):
        p_id = getattr(PresetMIDs, name).value[0]
        setting = d.settings_presets[p_id]
        p_num = setting["current_preset"]
        return setting, p_num

    # Variables and references
    from modules.processing.utilities import current_preset_label
    lines = []
    if start_e:
        therapy = start_e.therapy

    # Ventilator
    if therapy == Therapies.VENTILATOR:
        settings, preset_num = lookup_preset("VENTILATOR")
        preset_label = current_preset_label(d, therapy, preset_num)
        lines.append("Preset {} - \"{}\"".format(preset_num, preset_label))

    # Oxygen
    if therapy == Therapies.OXYGEN:
        settings, preset_num = lookup_preset("OXYGEN")
        mode = settings["87"].current_value()
        if not start_e or start_e.sub_therapy != SubTherapies.OXYGEN_FLUSH:
            preset_label = current_preset_label(d, therapy, preset_num)
            lines.append("Preset {} - \"{}\"".format(preset_num, preset_label))
        lines.append("Delivery Mode: {}".format(mode))

    # Cough
    elif therapy == Therapies.COUGH:
        settings, preset_num = lookup_preset("COUGH")
        preset_label = current_preset_label(d, therapy, preset_num)
        if not preset_label:
            preset_label = "(no label)"
        lines.append("Preset {} - \"{}\"".format(preset_num, preset_label))

    # Suction
    elif therapy == Therapies.SUCTION:

        # Get start value
        start_val = None
        if start_e:
            for info in start_e.values:
                if info.key == "suction-pressure":
                    start_val = info.num

        # Get stop value
        stop_val = None
        if stop_e:
            for info in stop_e.values:
                if info.key == "suction-pressure":
                    stop_val = info.num

        # Construct value
        if start_val is not None:
            vacuum = None
            if start_val is not None and stop_val is not None:
                vacuum = (start_val + stop_val) * 0.5
            elif start_val is not None:
                vacuum = start_val
            elif stop_val is not None:
                vacuum = stop_val
            settings, preset_num = lookup_preset("NEB_SUC_SYS")
            s = settings["suction-pressure"]
            units = s.tracker.session_vals["suction-pressure"].units
            lines.append("Suction: {:.0f} {}".format(vacuum, units))

    # Return detail lines
    return lines
