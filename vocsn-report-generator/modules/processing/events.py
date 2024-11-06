#!/usr/bin/env python
"""
Classes and functions used for processing statistics from monitored data channels.

    Version Notes:
        1.0.0.0  - 09/15/2019 - Created with calc_usage function.
        1.0.0.1  - 09/27/2019 - Added recognition of ventilator start/stop events.
        1.0.0.2  - 10/02/2019 - Updated handling for incomplete or truncated events to use report icons.
        1.0.0.3  - 10/04/2019 - Added therapy session tracking.
        1.0.1.0  - 10/10/2019 - Changed to compare trend values with entire report range.
        1.0.1.1  - 10/17/2019 - Started switching to new data definitions.
        1.0.1.2  - 10/18/2019 - Return events back to calling function.
        1.0.1.3  - 10/19/2019 - Started adapting to new event types.
        1.0.1.4  - 10/20/2019 - Completed adaptation. It will run with some undesired results.
        1.0.2.0  - 10/27/2019 - Rerouted settings event handlers.
        1.0.2.1  - 11/01/2019 - Added config event router.
        1.0.2.2  - 11/02/2019 - Forced ventilator to start on first found event. Moved trend calculations from methods
                                to attributes and added trend calculations for hours/day.
        1.0.2.3  - 11/03/2019 - Moved oxygen mode tracking calculations here from trend report section.
        1.0.2.4  - 11/04/2019 - Added handling for pre-use test, fixed hole in code that didn't update tracker vars.
        1.0.2.5  - 11/05/2019 - Changed arguments for EventTracker, routed pre-use tests.
        1.0.2.6  - 11/07/2019 - Fixed some attribute names.
        1.0.2.7  - 11/14/2019 - Added hours/day fields for FiO2 and Pulse Dose.
        1.0.2.8  - 11/22/2019 - Updated session tracker field names.
        1.0.2.9  - 11/24/2019 - Disabled trends for short report ranges.
        1.0.2.10 - 11/27/2019 - Changed min/max sessions to count 0.
        1.0.2.11 - 11/28/2019 - Fixed bug where the last day could disappear on the calendar for long report periods.
        1.0.2.12 - 11/29/2019 - Added improved tracking for preset labels.
        1.0.2.13 - 12/01/2019 - Added settings event list.
        1.0.3.0  - 12/05/2019 - Implemented patient reset. Fixed a bug where preset labels were not always updated.
                                Added function to log session details for Therapy Log.
        1.0.3.1  - 12/10/2019 - Improved preset label lookup.
        1.0.3.2  - 12/11/2019 - Corrected range constraint in log preset period function.
        1.0.3.3  - 12/13/2019 - Fixed a bug that could cause an error on reports that don't compute trend values.
        1.0.3.4  - 12/15/2019 - Moved applicability stack population here. Generalized some therapy event indexes.
                                Changed nebulizer duration calculation.
        1.0.3.5  - 12/19/2019 - Added therapy ID value to preset period function. Changed some range references.
        1.0.3.6  - 12/20/2019 - Fixed logic that prevented therapies exceeding both ends of report range from showing.
        1.0.3.7  - 12/21/2019 - Implemented error management.
        1.0.3.8  - 01/11/2020 - Added partial days. Applied force stop on device power down.
        1.0.3.9  - 01/18/2020 - Added flush sessions to Therapy Log.
        1.0.3.10 - 01/19/2020 - Centralized trend logic in utilities.
        1.0.3.11 - 01/26/2020 - Added range filter to cough track cough values.
        1.0.3.12 - 02/01/2020 - Updated to new log format.
        1.0.3.13 - 02/04/2020 - Fixed flaw in Flush handling - used wrong event type.
        1.0.3.14 - 02/09/2020 - Corrected cough calculations.
        1.0.3.15 - 02/14/2020 - Changed the default source for therapy start/stop preset numbers to fix a bug.
        1.0.3.16 - 02/17/2020 - Switched from dict conditions to sets for performance.
        1.0.3.17 - 02/20/2020 - Adjusted behavior of the Cough force stop. Improved force-stop behavior.
        1.0.4.0  - 02/25/2020 - Added function to update oxygen mode session value durations.
        1.0.4.1  - 02/26/2020 - Disabled session value tracking for oxygen Flush.
        1.0.4.2  - 02/28/2020 - Misc. fixes in performance and preset label tracking.
        1.0.4.3  - 03/27/2020 - Corrected data type reference. Update start event reference on O2 preset change prior to
                                report start.
        1.0.4.4  - 04/02/2020 - Fixed the formatting of a synthetic vent start record to include fault condition.
        1.0.4.5  - 04/06/2020 - Added handling for insp. hold events.
        1.0.4.6  - 04/10/2020 - Removed handling for insp. hold events. (data type changed) Added routing for
                                INST_HOLD events to session tracker with new non-session event handling.
        1.0.4.7  - 04/13/2020 - Added filename tracking.

"""

__author__ = "John Dorian for Sai Systems Technologies"
__copyright__ = "Copyright 2019"
__version__ = "1.0.4.7"

# Built-in
from datetime import datetime, timedelta

# VOCSN data modules
from modules.models import vocsn_data as vd
from modules.models import vocsn_enum as ve
from modules.models import event_types as et
from modules.models.event_types import Event
from modules.models.errors import ErrorManager
from modules.processing import sessions as sess
from modules.processing.values import EventValue
from modules.processing.utilities import dt_to_ts
from modules.models import event_types as e_types
from modules.processing.utilities import calc_trend
from modules.models.report import Report, ReportRange
from modules.models.vocsn_enum import EventIDs as eID
from modules.models.vocsn_data import Session, VOCSNData
from modules.models.vocsn_enum import RecordCompleteState as rState
from modules.processing.sessions import session_details, SessionValTracker


class Calendar:
    """ Track usage by calendar day. """

    def __init__(self, tracker, data: VOCSNData, therapy: ve.Therapies, r_range: ReportRange):
        """
        Initialize: calculate days to track and display on calendar.
        :param tracker: Parent therapy tracker.
        :param data: VOCSN data container.
        :param therapy: Therapy identifier.
        :param r_range: Report range.
        """

        # References
        self.data = data
        self.range = r_range
        self.em = tracker.em
        self.tracker = tracker

        # Calendar values
        self.active_days = 0
        self.active_time = timedelta(hours=0)
        self.first_day = r_range.start
        self.sessions = 0
        self.sessions_trend = 0
        self.sessions_pre_trend = 0
        self.days = {}
        self._generate_days()
        self.min_sess_per_day = 0
        self.max_sess_per_day = 0

        # Trend values
        self.all_days = 0
        self.trend_days = 0
        self.trend_active_time = timedelta(hours=0)
        self.pre_trend_active_time = timedelta(hours=0)

        # Therapy status
        self.therapy = therapy
        self.utilization = data.utilization_all
        self.util_preset = data.utilization_presets
        self.start_event = None
        self.last_start = None
        self.preset_start = None
        self.active = False
        self.ever_active = False
        self.complete = rState.COMPLETE
        self.truncated = rState.COMPLETE

    def track_therapy(self, event, start: int, end: int):
        """
        Track a therapy start/stop event.
        :param event: VOCSN event record.
        :param start: Therapy start event ID.
        :param end: Therapy end event ID.
        :return: Therapy activity duration.
        """

        # Handle starts
        if event.id == start:

            # Preset change only
            if hasattr(event, "is_preset_change_only") and event.is_preset_change_only:

                # Disregard

                # Therapy should be running but isn't. Force start.
                if not self.active:
                    self.force_start(event)

                # Update settings value trackers
                else:

                    # Update settings and session values
                    self._track_session_vals(event)

                    # Update first record in Event log if
                    if event.syn_time <= self.range.data_start:
                        self.start_event = event

            # Regular therapy start
            else:

                # Therapy should be running but isn't. Force start.
                skip = False
                if self.active:
                    if event.syn_time - self.last_start > timedelta(seconds=2):
                        new_e = self.force_end(event)
                        self.stop_therapy(new_e)
                    else:
                        skip = True

                # Start new therapy
                if not skip:
                    self.complete = rState.COMPLETE
                    self.start_therapy(event)

        # Handle stops
        elif event.id == end:

            # Session missing start record
            if not self.active:

                # A therapy start record is missing. Create a synthetic event to start the therapy.
                self.force_start(event)

            # End therapy session
            self.stop_therapy(event)

        # Non-session events
        else:

            # Process event like a stop value
            self.stop_therapy(event, non_session=True)

        self._update_tracker()

    def _update_tracker(self):
        """ Updates parent tracker with duplicated information."""
        t = self.tracker
        t.sessions = self.sessions
        t.sessions_trend = self.sessions_trend
        t.sessions_pre_trend = self.sessions_pre_trend
        t.active_days = self.active_days
        t.active_time = self.active_time
        t.trend_active_time = self.trend_active_time
        t.pre_trend_active_time = self.pre_trend_active_time

    def start_therapy(self, start_e):
        """ Start a new therapy. """

        # Start therapy
        self.start_event = start_e
        self.last_start = start_e.syn_time
        self.preset_start = start_e.syn_time
        self.active = True
        self.ever_active = True

        # Track start values
        self._track_session_vals(start_e)

    def stop_therapy(self, end_e, last: bool = False, non_session: bool = False):
        """ End a therapy. """

        # Variables
        r = self.range
        start_e = self.start_event
        start_dt = self.last_start
        end_dt = end_e.syn_time
        if non_session:
            start_e = end_e
            start_dt = end_dt
            self.preset_start = end_dt
        day = timedelta(days=1)
        truncated = rState.COMPLETE
        is_cough = self.tracker.therapy == ve.Therapies.COUGH
        check_day = datetime(year=start_dt.year, month=start_dt.month, day=start_dt.day)

        # Constrain to report range
        preset_in_range = self.range.data_start <= self.preset_start <= self.range.data_end
        start_in_range = self.range.data_start <= start_dt <= self.range.data_end
        end_in_range = self.range.data_start <= end_dt <= self.range.data_end
        within_range = start_dt < self.range.data_start and end_dt > self.range.data_end

        # Session at least partially overlaps report range
        if start_in_range or end_in_range or within_range:

            # Session is completely contained within report period
            if start_in_range and end_in_range:
                truncated = rState.COMPLETE

            # Session is partially contained within report period - adjust times.
            else:

                # Set truncated type
                if not start_in_range:
                    start_dt = min(max(start_dt, r.data_start), r.data_end)
                    start_e.syn_time = start_dt
                    truncated = rState.MISSING_START
                if not end_in_range:
                    end_dt = max(min(end_dt, r.data_start), r.data_end)
                    end_e.syn_time = end_dt
                    truncated = rState.MISSING_END

            # Mark calendar days as active and count active days
            while check_day < end_dt:
                if check_day > start_dt - day:
                    day_key = "{}/{}".format(check_day.month, check_day.day)

                    # Day should already exists. If so, mark as active and add to active day count.
                    new_day = False
                    if day_key in self.days.keys():
                        if not self.days[day_key].activity:
                            new_day = True

                    # Something went wrong. Mark as active and add to active day count.
                    else:
                        in_range = True
                        range_duration = min(check_day+day, r.data_end) - max(check_day, r.data_start)
                        self.days[day_key] = CalDay(check_day, in_range, range_duration)
                        new_day = True

                    # Count all active time
                    duration = min(end_dt, (check_day + day), r.data_end) - \
                        max(start_dt, check_day, r.data_start)
                    self.days[day_key].add_activity(duration)

                    # Count all active days
                    if new_day:
                        self.active_days += 1

                        # Add to trend statistics
                        self.all_days += 1
                        if r.use_trend and r.trend_start <= check_day < r.data_end:
                            self.trend_days += 1

                # Next day
                check_day += day

            # Get duration
            self.active_time += timedelta(seconds=5) if non_session else end_dt - start_dt

            # Count active time for trend period
            if r.use_trend:
                self.trend_active_time += max(min(end_dt, r.data_end), r.trend_start) - \
                    min(max(start_dt, r.trend_start), r.data_end)
                self.pre_trend_active_time += max(min(end_dt, r.trend_start), r.data_start) - \
                    min(max(start_dt, r.data_start), r.trend_start)

            # Count sessions
            self.sessions += 1
            if r.use_trend:
                if r.data_start <= start_dt <= r.trend_start:
                    self.sessions_pre_trend += 1
                if r.trend_start <= start_dt <= r.data_end:
                    self.sessions_trend += 1

        # Reset
        preset_start = self.preset_start
        self.preset_start = None
        self.last_start = None
        self.active = False

        # Terminate other therapies if this is vent
        if self.therapy == ve.Therapies.VENTILATOR:
            for tracker in [
                self.data.events_tracker.oxygen,
                self.data.events_tracker.cough,
                self.data.events_tracker.suction,
                self.data.events_tracker.nebulizer,
            ]:
                if tracker.calendar.active:
                    sub_therapy = ve.SubTherapies[tracker.therapy.name.upper()]
                    new_e = tracker.calendar.force_end(end_e, sub_therapy=sub_therapy, exact=True)
                    tracker.calendar.stop_therapy(new_e)
                # if tracker.therapy == ve.Therapies.OXYGEN and tracker.o2_flush_active:
                #     tracker.force_flush_stop(end_e, exact=True)
                self.data.alarms_tracker.stop_all(end_e)

        # Track start values
        if is_cough and (start_in_range or end_in_range or within_range):
            self._track_cough(start_e, end_e)
        self._track_session_vals(end_e, last=last, non_session=non_session)

        # Create utilization record
        if not non_session:
            t_id = end_e.therapy_id if hasattr(end_e, "therapy_id") else "2829"
            if start_in_range or end_in_range or within_range:
                details = session_details(self.data, start_e, end_e)
                self.utilization.append(Session(self.therapy, t_id, start_dt, end_dt,
                                                self.complete, truncated, details))
            if preset_in_range or end_in_range:
                therapy = self.therapy
                details = session_details(self.data, start_e, end_e, therapy)
                preset_start = max(preset_start, self.range.data_start)
                self.util_preset.append(Session(therapy, t_id, preset_start, end_dt,
                                                self.complete, truncated, details))

    def force_start(self, e: Event, exact_time: bool = False):
        """
        Artificially force a therapy to start when an end is found while not already active.
        :param e: Current end event, used to make up a start time.
        :param exact_time: If true, match time to incoming event, otherwise estimate previous start time.
        """

        # References
        data = self.data
        is_vent = e.therapy == ve.Therapies.VENTILATOR

        # Reconstruct start time from duration record if available
        duration = timedelta(minutes=1)
        if exact_time:
            duration = timedelta(seconds=0)
        else:
            for value in e.values:
                if value.key == "therapy-duration-seconds":
                    duration = int(value.num)
                    duration = timedelta(seconds=duration)

        # Set start time
        raw_time = e.raw_time - duration
        syn_time = e.syn_time - duration

        # Simulate a CSV line record and create event
        if is_vent:
            line = ["-1", dt_to_ts(raw_time), dt_to_ts(syn_time), 'E', eID.VENT_START, "0", "0"]
            new_e = et.EventValParam(self.em, data, line)
        else:
            sub_therapy = e.sub_therapy
            # sub_therapy = ve.SubTherapies.OXYGEN if e.sub_therapy == ve.SubTherapies.OXYGEN_FLUSH else e.sub_therapy
            line = ["-1", dt_to_ts(raw_time), dt_to_ts(syn_time), 'E', eID.THERAPY_START, '', sub_therapy.value]
            attributes = data.metadata_t_start[sub_therapy.value]["attributes"]
            for _ in range(0, len(attributes)):
                line.append("")
            line.append("0")
            new_e = et.EventTherapy(self.em, data, line)
        new_e.name = "Therapy Start - Partial Record"
        e.name = "Therapy End - Partial Record"
        new_e.complete = rState.MISSING_START

        # Log a missing record
        self.em.log_warning("Encountered therapy stop without a start")

        # Process event
        self.start_therapy(new_e)

    def force_end(self, e: Event, last: bool = False, sub_therapy: ve.SubTherapies = None, exact: bool = None,
                  original_start=None):
        """
        Artificially force a therapy to end when a start is found while already active.
        :param e: Last start event, used to make up an end time.
        :param last: If last, extend long-running therapies to end of report range.
        :param sub_therapy: Override with specific sub-therapy
        :param exact: Use exact time from reference event.
        :param original_start: Original start event.
        """

        # References
        data = self.data
        is_vent = self.therapy == ve.Therapies.VENTILATOR
        if not sub_therapy:
            sub_therapy = e.sub_therapy

        # Create an artificial stop record. Mark record as incomplete
        if last and self.therapy in [ve.Therapies.VENTILATOR, ve.Therapies.OXYGEN]:
            raw_time = self.range.data_end
            syn_time = self.range.data_end
        elif exact:
            raw_time = e.raw_time
            syn_time = e.syn_time
        else:
            if self.therapy in [ve.Therapies.VENTILATOR, ve.Therapies.OXYGEN]:
                raw_time = e.raw_time
                syn_time = e.syn_time
            else:
                if original_start:
                    raw_time = min(original_start.raw_time + timedelta(minutes=1), e.raw_time)
                    syn_time = min(original_start.syn_time + timedelta(minutes=1), e.syn_time)
                else:
                    raw_time = e.raw_time
                    syn_time = e.syn_time
            therapy = "-unknown-" if not self.therapy else self.therapy.value[0].lower()
            message = "Had to force-stop the {} therapy".format(therapy)
            error = Exception("Missing {} therapy stop message".format(therapy))
            self.em.log_error(ve.Programs.REPORTING, ve.ErrorCat.MID_ERROR, ve.ErrorSubCat.DATA_IRREGULARITY, message,
                              error)

        # Simulate a CSV line record and create event
        if is_vent:
            line = ["-1", dt_to_ts(raw_time), dt_to_ts(syn_time), 'E', eID.VENT_END, "0"]
            new_e = et.EventValParam(self.em, data, line)
        else:
            # sub_therapy = ve.SubTherapies.OXYGEN if e.sub_therapy == ve.SubTherapies.OXYGEN_FLUSH else e.sub_therapy
            line = ["-1", dt_to_ts(raw_time), dt_to_ts(syn_time), 'E', eID.THERAPY_END, "", sub_therapy.value]
            attributes = data.metadata_t_stop[sub_therapy.value]["attributes"] or []
            if self.therapy == ve.Therapies.COUGH:
                # cycles = self.data.settings_all["52"].current_value()
                cycles = "0"
                volume = "0"
                peak_flow = "0"
                line += [cycles, volume, peak_flow]
                for _ in range(3, len(attributes)):
                    line.append("")
            else:
                for _ in range(0, len(attributes)):
                    line.append("")
            line.append("0")
            new_e = et.EventTherapy(self.em, data, line)
        self.start_event.name = "Therapy Start - Partial Record"
        new_e.name = "Therapy Stop - Partial Record"
        new_e.complete = rState.MISSING_END

        # Log a missing record
        if not last:
            self.em.log_warning("Encountered therapy start without an end")

        # Return completed event
        return new_e

    def _track_cough(self, start_e: Event, end_e: Event):
        """ Track special cycle-weighted cough values. """
        
        def lookup_setting(settings: dict, p_id: str):
            """ Lookup current value for a setting. """
            val = settings[p_id].current_value()
            return int(val) if val is not None else None

        # Vars and references
        cycles = 0
        peak_flow = None
        volume = None
        in_press = None
        ex_press = None
        r = self.range
        t = self.tracker
        s = t.data.settings_all

        # Lookup cough values
        values = []
        if start_e:
            values = start_e.values
        if end_e:
            values = values + end_e.values
        for item in values:
            if item.key == "12026":
                cycles = item.num
            if item.key == "12024":
                peak_flow = item.num
            if item.key == "12025":
                volume = item.num
            if item.key == "46":
                in_press = item.num
            if item.key == "47":
                ex_press = item.num

        # Backup - get values from settings
        if in_press is None:
            in_press = lookup_setting(s, "46")
        if ex_press is None:
            ex_press = lookup_setting(s, "47")

        # Add to totals
        if cycles:
            
            # Full range totals
            t.total_cough_cycles += cycles
            t.valid_cough_sessions += 1
            if volume:
                t.cough_volume_cycle_prod += volume * cycles
            if in_press:
                t.cough_in_press_cycle_prod += in_press * cycles
            if ex_press:
                t.cough_ex_press_cycle_prod += ex_press * cycles
            if peak_flow:
                t.cough_peak_flow_cycle_prod += peak_flow * cycles
                
            # Trend totals
            if r.use_trend:

                # Pre-trend range totals
                if start_e and r.data_start <= start_e.syn_time < r.trend_start:
                    t.total_cough_cycles_pre_trend += cycles
                    t.valid_cough_sessions_pre_trend += 1
                    if volume:
                        t.cough_pre_trend_volume_cycle_prod += volume * cycles
                    if in_press:
                        t.cough_pre_trend_in_press_cycle_prod += in_press * cycles
                    if ex_press:
                        t.cough_pre_trend_ex_press_cycle_prod += ex_press * cycles
                    if peak_flow:
                        t.cough_pre_trend_peak_flow_cycle_prod += peak_flow * cycles

                # Trend range totals
                if start_e and r.trend_start <= start_e.syn_time < r.data_end:
                    t.total_cough_cycles_trend += cycles
                    t.valid_cough_sessions_trend += 1
                    if volume:
                        t.cough_trend_volume_cycle_prod += volume * cycles
                    if in_press:
                        t.cough_trend_in_press_cycle_prod += in_press * cycles
                    if ex_press:
                        t.cough_trend_ex_press_cycle_prod += ex_press * cycles
                    if peak_flow:
                        t.cough_trend_peak_flow_cycle_prod += peak_flow * cycles

    def _track_session_vals(self, event: e_types.EventTherapy, last: bool = False, non_session: bool = False):
        """ Track therapy session start/stop values. """

        # Variables
        preset = event.preset
        old_preset = None
        updated_settings = []
        r = self.tracker.range

        # Attempt to determine correct preset group and index from label
        # Note: Preset selection for ventilation is defined by parameter 22 in 5002 messages, not here
        preset_group_name = event.therapy.name
        is_therapy_start = event.id == eID.THERAPY_START
        if is_therapy_start:
            if event.therapy in {ve.Therapies.SUCTION, ve.Therapies.NEBULIZER, ve.Therapies.SYSTEM}:
                preset_group_name = "NEB_SUC_SYS"
            preset_id = ve.PresetMIDs[preset_group_name].value[0]
            preset_group = self.data.settings_presets[preset_id]

            # First method to check preset
            for idx, label in preset_group["9100"].current.items():
                if label.str == event.preset_label:     # This attribute exists for EventTherapy type only
                    preset = idx
            old_preset = preset_group["current_preset"]

            # No match with current labels - use default preset labels
            if preset is None:
                label_parts = event.preset_label.strip('"').split(' ')
                if len(label_parts) > 1:
                    preset = label_parts[1]

            # Capture preset label if provided
            if event.therapy in {ve.Therapies.OXYGEN, ve.Therapies.COUGH}:
                from modules.processing.utilities import current_preset_id
                preset_label = event.preset_label
                preset_label_id = current_preset_id(event.therapy)
                preset_val = EventValue(preset_label_id, "Preset Label", None, preset_label)
                preset_group[preset_label_id].current[preset] = preset_val

        # Nebulizer duration
        elif event.therapy == ve.Therapies.NEBULIZER:
            start = self.start_event
            duration = None
            for detail in event.values:
                duration = detail.num
            if duration and duration > 0:
                self.tracker.neb_session_seconds.append(duration)
                if r.use_trend:
                    if r.data_start <= start.syn_time < r.trend_start:
                        self.tracker.neb_trend_session_seconds.append(duration)
                    if r.trend_start <= start.syn_time < r.data_end:
                        self.tracker.neb_pre_trend_session_seconds.append(duration)

        # Ensure session values exists for non-session events
        if non_session:
            for val in event.values:
                if val.key not in self.tracker.session_vals:
                    self.tracker.session_vals[val.key] = SessionValTracker(self.tracker, val.key, {}, {}, False)

        # Always update each value with start and stop records
        for name, session in self.tracker.session_vals.items():

            # Avoid blacklist
            if session.id in {"SuctionUnits", "is-preset-change-only"} or "state" in name:
                continue
            if session.id == "therapy-duration-seconds" and event.therapy not in \
                    [ve.Therapies.NEBULIZER, ve.Therapies.SUCTION]:
                continue

            # Lookup setting
            try:
                setting = self.data.settings_all[name]

            # Lookup monitors
            except KeyError:
                setting = self.data.monitors_all[name]

            # Update suction records
            found = False
            if name == "suction-pressure":
                value = units = None
                for val in event.values:
                    if val.str and val.key == "suction-pressure":
                        value = val
                        units = val.str.split(' ')[1]
                        enum = None
                        md = self.tracker.data.metadata_t_stop
                        for e_id, e_def in md[ve.Therapies.SUCTION.value[0]]["enum_ref"]["SuctionUnits"].items():
                            if units == e_def:
                                enum = e_id
                        units = EventValue("SuctionUnits", "SuctionUnits", None, enum, enum)
                if value is not None and units is not None:
                    session.add_event(event, value, units)
                    setting.update(preset, value, event.syn_time, new_state=True, update_preset=is_therapy_start,
                                   old_preset=old_preset, force=last)
                    updated_settings.append(name)

            # Update all other values
            else:
                for idx, val in enumerate(event.values):
                    if session.id == val.key:
                        found = True
                        active = None
                        if setting.display_type in ve.DataTypes.ON_OFF_VAL_TYPES:
                            state = event.values[idx+1]
                            active = state.str in ve.DataTypes.ACTIVE
                        session.add_event(event, val, active=active)
                        if hasattr(setting, "update"):
                            setting.update(preset, val, event.syn_time, new_state=active,
                                           update_preset=is_therapy_start, old_preset=old_preset, force=last)
                            updated_settings.append(name)
                        break

                # If no data provided, update with blank to capture time
                if not found:
                    val = EventValue(name, name, None, None)
                    session.add_event(event, val)

    def _generate_days(self):
        """ Generate dictionary of days to track in calendar. """

        # Setup range values
        r = self.range
        start_dt = self.range.start
        end_dt = self.range.end
        start_days = self.range.days_start
        end_days = self.range.days_end

        # Find starting day (move back to find a Sunday)
        day = timedelta(days=1)
        start_day = check_day = datetime(year=start_dt.year, month=start_dt.month, day=start_dt.day)
        day_steps = 0
        while check_day.weekday() != 6:
            check_day -= day
            day_steps += 1

            # Something isn't working. Fall back on original day
            if day_steps >= 7:
                check_day = start_day
                break

        # Save first day
        self.first_day = check_day

        # Populate days in report range
        while check_day < end_dt:
            day_key = "{}/{}".format(check_day.month, check_day.day)
            in_range = start_day <= check_day < end_dt
            full_day = start_days <= check_day < end_days
            range_duration = min(check_day+day, r.data_end) - max(check_day, r.data_start)
            self.days[day_key] = CalDay(check_day, in_range, range_duration, full_day)
            check_day += day

        # Continue to end of week
        # day_steps = 0
        while check_day.weekday() != 6:
            day_key = "{}/{}".format(check_day.month, check_day.day)
            in_range = False
            full_day = start_days <= check_day < end_days
            range_duration = min(check_day+day, r.data_end) - max(check_day, r.data_start)
            self.days[day_key] = CalDay(check_day, in_range, range_duration, full_day)
            check_day += day
            day_steps += 1

            # Something isn't working. Stop adding days
            if day_steps >= 12:
                break

    def finish(self):
        """ End currently active therapies at end of report range. """

        # Update values
        self._update_tracker()

        # End active therapies
        if self.active:
            last = True
            new_e = self.force_end(self.start_event, last)
            self.stop_therapy(new_e, last=True)
            self._update_tracker()
            
        # Calculate min/max sessions per day
        if self.sessions > 0:
            self.min_sess_per_day = 999999
            for _, day in self.days.items():
                self.min_sess_per_day = min(self.min_sess_per_day, day.sessions)
                self.max_sess_per_day = max(self.max_sess_per_day, day.sessions)

        # Calculate nebulizer duration
        if self.therapy == ve.Therapies.NEBULIZER:
            t = self.tracker
            if len(t.neb_session_seconds) > 0:
                sessions = len(t.neb_session_seconds)
                t.neb_average_duration = (sum(t.neb_session_seconds) / sessions) if sessions > 0 else 0
                if t.range.use_trend:
                    pt_sessions = len(t.neb_pre_trend_session_seconds)
                    pt_duration = t.neb_pre_trend_avg_duration = (sum(t.neb_pre_trend_session_seconds) / pt_sessions) \
                        if pt_sessions > 0 else None
                    t_sessions = len(t.neb_trend_session_seconds)
                    t_duration = t.neb_trend_avg_duration = (sum(t.neb_trend_session_seconds) / t_sessions) \
                        if t_sessions > 0 else None
                    t.neb_trend_delta, t.neb_trend_percent = calc_trend(pt_duration, t_duration)


class CalDay:
    """ Calendar day statistics. """

    def __init__(self, dt: datetime, in_range: bool, range_duration: datetime, complete: bool = False):
        """ Initialize. """
        self.start = dt
        self.end = dt + timedelta(days=1)
        self.activity = False
        self.sessions = 0
        self.duration = timedelta(hours=0)
        self.in_range = in_range
        self.complete = complete
        self.range_duration = range_duration

    def add_activity(self, time: timedelta):
        """ Add activity to the day. """
        self.activity = True
        self.duration += time
        self.sessions += 1


class TherapyTracker:
    """ Track usage of an individual therapy. """

    def __init__(self, em: ErrorManager, data: VOCSNData, therapy: ve.Therapies, report: Report, is_vent: bool = False):
        """ Initialize. """

        # References
        self.em = em
        self.data = data
        self.report = report
        self.settings_events = []

        # IDs
        self.therapy = therapy
        self.start = eID.VENT_START if is_vent else eID.THERAPY_START
        self.end = eID.VENT_END if is_vent else eID.THERAPY_END

        # Usage statistics
        self.active_days = 0
        self.active_time = timedelta(seconds=0)
        self.sessions = 0
        self.sessions_trend = 0
        self.sessions_pre_trend = 0
        self.sessions_per_day_all = None
        self.sessions_per_day_trend = None
        self.sessions_per_day_percent = None
        self.sessions_per_day_pre_trend = None

        # Trend statistics
        self.trend_delta = 0
        self.trend_percent = None
        self.trend_active_time = timedelta(hours=0)
        self.pre_trend_active_time = timedelta(hours=0)

        # Calendar day tracker
        self.range = report.range
        self.calendar = Calendar(self, data, therapy, self.range)

        # Session values
        self.session_vals = {}
        self.session_flush_vals = {}
        if not is_vent:
            self.session_vals = sess.init_session_vals(self, data, therapy)
        if therapy == ve.Therapies.OXYGEN:
            self.session_flush_vals = sess.init_session_vals(self, data, ve.SubTherapies.OXYGEN_FLUSH)
        
        # Statistics values
        self.hours_per_all_day = None
        self.hours_per_used_day = None
        self.hours_per_all_day_trend = None
        self.hours_per_used_day_trend = None
        self.hours_per_all_day_pre_trend = None
        self.hours_per_used_day_pre_trend = None
        self.hours_per_all_day_trend_delta = None
        self.hours_per_all_day_trend_percent = None
        self.hours_per_used_day_trend_delta = None
        self.hours_per_used_day_trend_percent = None

        # ----- Ventilator-specific values ----- #

        self.base_mode = None
        self.override_mode = None
        self.override_active = False

        # ----- Nebulizer-specific values ----- #

        # Nebulizer duration - calculated differently
        self.neb_session_seconds = []
        self.neb_trend_session_seconds = []
        self.neb_pre_trend_session_seconds = []
        self.neb_average_duration = None
        self.neb_pre_trend_avg_duration = None
        self.neb_trend_avg_duration = None
        self.neb_trend_percentage = None
        self.neb_trend_delta = None

        # ----- Oxygen-specific values ----- #
        
        # Flush tracking
        self.o2_flush_active = False
        self.o2_flush_last_event = None
        self.o2_flush_ever_active = None
        self.o2_flush_sessions_all = None
        self.o2_flush_sessions_trend = 0
        self.o2_flush_sessions_pre_trend = 0
        self.o2_flush_sessions_percent = None
        self.o2_flush_sessions_per_day = None

        # Mode tracking
        self.fio2_hours = None
        self.flow_hours = None
        self.bleed_hours = None
        self.fio2_percent = None
        self.flow_percent = None
        self.bleed_percent = None
        self.fio2_hours_per_day = None
        self.flow_hours_per_day = None
        self.bleed_hours_per_day = None

        # ----- Cough-specific values ----- #

        # Cough and session values
        self.total_cough_cycles = 0
        self.total_cough_cycles_trend = 0
        self.total_cough_cycles_pre_trend = 0
        self.valid_cough_sessions = 0
        self.valid_cough_sessions_trend = 0
        self.valid_cough_sessions_pre_trend = 0
        self.cough_volume_cycle_prod = 0
        self.cough_in_press_cycle_prod = 0
        self.cough_ex_press_cycle_prod = 0
        self.cough_peak_flow_cycle_prod = 0
        self.cough_trend_volume_cycle_prod = 0
        self.cough_trend_in_press_cycle_prod = 0
        self.cough_trend_ex_press_cycle_prod = 0
        self.cough_trend_peak_flow_cycle_prod = 0
        self.cough_pre_trend_volume_cycle_prod = 0
        self.cough_pre_trend_in_press_cycle_prod = 0
        self.cough_pre_trend_ex_press_cycle_prod = 0
        self.cough_pre_trend_peak_flow_cycle_prod = 0
        
        # Full averages
        self.cough_avg_cycles = None
        self.cough_avg_volume = None
        self.cough_avg_in_press = None
        self.cough_avg_ex_press = None
        self.cough_avg_peak_flow = None
        
        # Trend values
        self.cough_trend_cycles = None
        self.cough_trend_volume = None
        self.cough_trend_peak_flow = None

        # Trend percentages
        self.cough_percent_cycles = None
        self.cough_percent_volume = None
        self.cough_percent_peak_flow = None

    def track_event(self, event: Event):
        """ Track activity duration and add activity to calendar. """

        # Handle O2 flush events because they're special
        if event.sub_therapy == ve.SubTherapies.OXYGEN_FLUSH:
            self.flush_event(event)

        # All other therapy sessions
        else:
            self.calendar.track_therapy(event, self.start, self.end)

    def count_event_as_session(self, event: Event):
        """
        Count parameters from an event as session values.
        :param event: Event with parameter values.
        """

        # Process each value
        for param in event.values:

            # Initialize session tracking if needed
            if param.key not in self.session_vals:
                self.session_vals[param.key] = SessionValTracker(self, param.key, {}, {}, False)

            # Track value
            self.session_vals[param.key].add_event(event, param)

    def flush_event(self, event: Event):
        """
        Handle O2 Flush session start/stop events.
        :param event: O2 flush event.
        """

        # Handle starts
        if event.id == eID.THERAPY_START:

            # O2 flush already running - Flush stop is missing
            if self.o2_flush_active:
                self.force_flush_stop()

            # Start flush session
            self.start_flush(event)

        # Handle stops
        elif event.id == eID.THERAPY_END:

            # O2 flush not running - Flush start is missing
            if not self.o2_flush_active:
                self.force_flush_start(event)

            # Start flush session
            self.stop_flush(event)

        # Unexpected event
        else:
            raise Exception("Did not expect ID as therapy record: {}".format(event.id))

    def start_flush(self, event: Event):
        """ Start the O2 flush therapy. """

        # Mark O2 flush as active
        self.o2_flush_active = True
        self.o2_flush_ever_active = True
        self.o2_flush_last_event = event

        # Track flush values - Skip to avoid affecting 2828 oxygen session values
        # self._track_flush_session_vals(event)

    def stop_flush(self, event: Event):
        """ Stop the O2 flush therapy. """

        # Constrain to report range
        r = self.range
        start = self.o2_flush_last_event
        if not (start.syn_time < r.data_end and r.data_start < event.syn_time):
            return
        start.syn_time = min(max(start.syn_time, r.data_start), r.data_end)
        event.syn_time = max(min(event.syn_time, r.data_end), r.data_start)

        # Count trend range
        if r.use_trend:
            if r.data_start <= start.syn_time < r.trend_start:
                self.o2_flush_sessions_pre_trend += 1
            if r.trend_start <= start.syn_time <= r.data_end:
                self.o2_flush_sessions_trend += 1

        # Count and reset
        self.o2_flush_active = False
        self.o2_flush_last_event = None
        if self.o2_flush_sessions_all is None:
            self.o2_flush_sessions_all = 1
        else:
            self.o2_flush_sessions_all += 1

        # Track flush values - Skip to avoid affecting 2828 oxygen session values
        # self._track_flush_session_vals(event)

        # Track session
        therapy = ve.Therapies.OXYGEN
        details = session_details(self.data, start, event, therapy)
        self.data.utilization_presets.append(Session(therapy, ve.SubTherapies.OXYGEN_FLUSH.value, start.syn_time,
                                                     event.syn_time, ve.RecordCompleteState.COMPLETE,
                                                     ve.RecordCompleteState.COMPLETE, details))

    def force_flush_start(self, e: Event):
        """ Force a flush session to start when the start event is missing. """

        # Create an artificial start record. Mark record as incomplete
        first = self.o2_flush_active is None

        # First session - start at beginning of report range
        if first:
            raw_time = self.range.data_start - timedelta(minutes=1)
            syn_time = self.range.data_start - timedelta(minutes=1)

        # Later session - start a bit earlier.
        else:
            raw_time = e.raw_time - timedelta(minutes=1)
            syn_time = e.syn_time - timedelta(minutes=1)

        # Create and process new event
        line = ["-1", dt_to_ts(raw_time), dt_to_ts(syn_time), 'E', eID.THERAPY_START, "",
                ve.SubTherapies.OXYGEN_FLUSH.value, "", "0"]
        new_e = et.EventTherapy(self.em, self.data, line)
        self.start_flush(new_e)

        # Log a missing record
        self.em.log_warning("Encountered O2 flush start without a stop")

    def force_flush_stop(self, ref_e: Event = None, last: bool = False, exact: bool = False):
        """ Force a flush session to stop when the stop event is missing. """

        # Create an artificial start record. Mark record as incomplete
        # First session - start at beginning of report range
        e = self.o2_flush_last_event
        if last:
            raw_time = self.range.end + timedelta(minutes=1)
            syn_time = self.range.end + timedelta(minutes=1)
        elif exact:
            raw_time = ref_e.raw_time
            syn_time = ref_e.syn_time
        # Later session - start a bit earlier.
        else:
            raw_time = e.raw_time + timedelta(minutes=1)
            syn_time = e.syn_time + timedelta(minutes=1)

        # Create and process new event
        line = ["-1", dt_to_ts(raw_time), dt_to_ts(syn_time), 'E', eID.THERAPY_END, "",
                ve.SubTherapies.OXYGEN_FLUSH.value, "", "0"]
        new_e = et.EventTherapy(self.em, self.data, line)
        self.stop_flush(new_e)

        # Log a missing record
        self.em.log_warning("Encountered O2 flush stop without a start")

    def _track_flush_session_vals(self, event: Event):
        """ Track therapy session start/stop values. """

        # Always update each value with start and stop records
        for name, session in self.session_flush_vals.items():
            found = False

            # Update all other values
            for val in event.values:
                if session.id == val.key:
                    found = True
                    session.add_event(event, val)

            # If no data provided, update with blank to capture time
            if not found:
                val = EventValue(name, name, None, None)
                session.add_event(event, val)

    def track_o2_mode(self, time: datetime, val: EventValue):
        """
        Specifically update O2 therapy mode.
        :param time: Synthetic timestamp
        :param val: Event value.
        """

        # Lookup value
        session = self.session_vals["87"]

        # Create a synthetic preset-only therapy start record
        timestamp = dt_to_ts(time)
        line = ["-1", timestamp, timestamp, "E", "6014"]
        event = Event(self.em, self.data, line)
        event.is_preset_change_only = True

        # Update session value tracker
        session.add_event(event, val, self.calendar.active)

    def finish_therapy(self):
        """ Finish statistics calculations after all events are entered. """

        # Terminate O2 Flush session
        if self.o2_flush_active:
            last = True
            self.force_flush_stop(last=last)

        # Terminate sessions at end of range
        self.calendar.finish()

        # Calculate day trends - discontinued
        r = self.range
        # trend_period = r_range.trend_end - r_range.trend_start if r_range.use_trend else None
        # average_usage = self.calendar.all_days / r_range.average_days
        # trend_usage = self.calendar.trend_days / r_range.trend_days if r_range.use_trend else None
        # trend_delta = self.trend_delta = trend_usage - average_usage if r_range.use_trend else None

        # No calculations for invalid times
        if self.active_time.total_seconds() > 0:

            # Determine used days, adjusted for partial days
            zero = timedelta(seconds=0)
            used_days = zero
            used_trend_days = zero
            used_pre_trend_days = zero
            for _, day in self.calendar.days.items():
                if day.activity:
                    used_days += day.range_duration
                    if r.use_trend:
                        used_trend_days += max(min(day.end, r.data_end), r.trend_start) - \
                            min(max(day.start, r.trend_start), r.data_end)
                        used_pre_trend_days += max(min(day.end, r.trend_start), r.data_start) - \
                            min(max(day.start, r.data_start), r.trend_start)
            used_days = used_days.total_seconds() / 86400
            used_trend_days = used_trend_days.total_seconds() / 86400
            used_pre_trend_days = used_pre_trend_days.total_seconds() / 86400

            # Calculate hours/day for report range
            self.hours_per_all_day = ((self.active_time.total_seconds() / 3600) / r.data_days) if r.data_days else 0
            self.hours_per_used_day = ((self.active_time.total_seconds() / 3600) / used_days) if used_days else 0

            # Calculate hours/day for trend period
            if r.use_trend:

                # Hours per all days
                self.hours_per_all_day_trend = ((self.trend_active_time.total_seconds() / 3600) /
                                                r.trend_days) if r.trend_days else 0
                self.hours_per_all_day_pre_trend = ((self.pre_trend_active_time.total_seconds() / 3600) /
                                                    r.pre_trend_days) if r.pre_trend_days else 0

                # Hours per days used
                self.hours_per_used_day_trend = ((self.trend_active_time.total_seconds() / 3600) /
                                                 used_trend_days) if used_trend_days else 0
                self.hours_per_used_day_pre_trend = ((self.pre_trend_active_time.total_seconds() / 3600) /
                                                     used_pre_trend_days) if used_pre_trend_days else 0

                # Calculate hour/day trends
                self.hours_per_all_day_trend_delta, self.hours_per_all_day_trend_percent = \
                    calc_trend(self.hours_per_all_day_pre_trend, self.hours_per_all_day_trend)
                self.hours_per_used_day_trend_delta, self.hours_per_used_day_trend_percent = \
                    calc_trend(self.hours_per_used_day_pre_trend, self.hours_per_used_day_trend)

        # Calculate therapy session start/stop values
        for _, session in self.session_vals.items():
            session.calc_avg()
        for _, session in self.session_flush_vals.items():
            session.calc_avg()

        # Calculate session statistics if in valid range
        if self.sessions > 0 and r.data_days > 0:
            self.sessions_per_day_all = self.sessions / r.data_days

            # Calculate trend values
            if self.range.use_trend:
                self.sessions_per_day_pre_trend = self.sessions_pre_trend / r.pre_trend_days
                self.sessions_per_day_trend = self.sessions_trend / r.trend_days
                _, self.sessions_per_day_percent = calc_trend(self.sessions_per_day_pre_trend,
                                                              self.sessions_per_day_trend)

            # Calculate O2 Flush statistics
            if self.o2_flush_sessions_all is not None:
                self.o2_flush_sessions_per_day = self.o2_flush_sessions_all / r.data_days

                # Calculate O2 flush trend values
                if r.use_trend:
                    flush_spd_pre_trend = self.o2_flush_sessions_pre_trend / r.pre_trend_days
                    flush_spd_trend = self.o2_flush_sessions_trend / r.trend_days
                    _, self.o2_flush_sessions_percent = calc_trend(flush_spd_pre_trend, flush_spd_trend)

            # Oxygen mode tracking
            if self.therapy == ve.Therapies.OXYGEN:
                if "87" in self.session_vals:
                    o2_vals = self.session_vals["87"]
                    if "FiO2" in o2_vals.unique_value_time:
                        self.fio2_hours = o2_vals.unique_value_time["FiO2"].total_seconds() / 3600
                        if self.fio2_hours > 0:
                            self.fio2_hours_per_day = self.fio2_hours / self.range.data_days
                            if self.range.use_trend:
                                fio2_hours_pre_trend = o2_vals.unique_value_pre_trend_time["FiO2"]\
                                                           .total_seconds() / 3600
                                fio2_hours_trend = o2_vals.unique_value_trend_time["FiO2"].total_seconds() / 3600
                                fio2_hr_per_day_pre_trend = fio2_hours_pre_trend / self.range.pre_trend_days
                                fio2_hr_per_day_trend = fio2_hours_trend / self.range.trend_days
                                _, self.fio2_percent = calc_trend(fio2_hr_per_day_pre_trend, fio2_hr_per_day_trend)
                    if "Pulse Dose" in o2_vals.unique_value_time:
                        self.flow_hours = o2_vals.unique_value_time["Pulse Dose"].total_seconds() / 3600
                        if self.flow_hours > 0:
                            self.flow_hours_per_day = self.flow_hours / self.range.data_days
                            if self.range.use_trend:
                                flow_hours_pre_trend = o2_vals.unique_value_pre_trend_time["Pulse Dose"]\
                                                           .total_seconds() / 3600
                                flow_hours_trend = o2_vals.unique_value_trend_time["Pulse Dose"].total_seconds() / 3600
                                flow_hr_per_day_pre_trend = flow_hours_pre_trend / self.range.pre_trend_days
                                flow_hr_per_day_trend = flow_hours_trend / self.range.trend_days
                                _, self.flow_percent = calc_trend(flow_hr_per_day_pre_trend, flow_hr_per_day_trend)
                    if "O2 Bleed In" in o2_vals.unique_value_time:
                        self.bleed_hours = o2_vals.unique_value_time["O2 Bleed In"].total_seconds() / 3600
                        if self.bleed_hours > 0:
                            self.bleed_hours_per_day = self.bleed_hours / self.range.data_days
                            if self.range.use_trend:
                                bleed_hours_pre_trend = o2_vals.unique_value_pre_trend_time["O2 Bleed In"]\
                                                            .total_seconds() / 3600
                                bleed_hours_trend = o2_vals.unique_value_trend_time["O2 Bleed In"]\
                                                           .total_seconds() / 3600
                                bleed_hr_per_day_pre_trend = bleed_hours_pre_trend / self.range.pre_trend_days
                                bleed_hr_per_day_trend = bleed_hours_trend / self.range.trend_days
                                _, self.bleed_percent = calc_trend(bleed_hr_per_day_pre_trend, bleed_hr_per_day_trend)

        # Cough values
        if self.therapy == ve.Therapies.COUGH:
            cycles = self.total_cough_cycles
            pre_trend_cycles = self.total_cough_cycles_pre_trend
            trend_cycles = self.total_cough_cycles_trend
            if cycles > 0:
                self.cough_avg_cycles = cycles / self.valid_cough_sessions
                self.cough_avg_volume = self.cough_volume_cycle_prod / cycles
                self.cough_avg_in_press = self.cough_in_press_cycle_prod / cycles
                self.cough_avg_ex_press = self.cough_ex_press_cycle_prod / cycles
                self.cough_avg_peak_flow = self.cough_peak_flow_cycle_prod / cycles
            if r.use_trend and pre_trend_cycles > 0 and trend_cycles > 0:
                cough_avg_pre_trend_cycles = pre_trend_cycles / self.valid_cough_sessions_pre_trend
                cough_avg_pre_trend_volume = self.cough_pre_trend_volume_cycle_prod / pre_trend_cycles
                cough_avg_pre_trend_peak_flow = self.cough_pre_trend_peak_flow_cycle_prod / pre_trend_cycles
                cough_avg_trend_cycles = trend_cycles / self.valid_cough_sessions_trend
                cough_avg_trend_volume = self.cough_trend_volume_cycle_prod / trend_cycles
                cough_avg_trend_peak_flow = self.cough_trend_peak_flow_cycle_prod / trend_cycles
                self.cough_trend_cycles = cough_avg_trend_cycles - cough_avg_pre_trend_cycles
                self.cough_trend_volume = cough_avg_trend_volume - cough_avg_pre_trend_volume
                self.cough_trend_peak_flow = cough_avg_trend_peak_flow - cough_avg_pre_trend_peak_flow
                _, self.cough_percent_cycles = calc_trend(cough_avg_pre_trend_cycles, cough_avg_trend_cycles)
                _, self.cough_percent_volume = calc_trend(cough_avg_pre_trend_volume, cough_avg_trend_volume)
                _, self.cough_percent_peak_flow = calc_trend(cough_avg_pre_trend_peak_flow, cough_avg_trend_peak_flow)


class EventTracker:
    """ Track usage of all therapies. """

    def __init__(self, em: ErrorManager, data: VOCSNData, report: Report):
        """ Initialize. """

        # References
        self.em = em
        self.data = data
        self.range = report.range

        # Create trackers for all therapies
        is_vent = True
        self.ventilator = TherapyTracker(em, data, ve.Therapies.VENTILATOR, report, is_vent)
        self.oxygen = TherapyTracker(em, data, ve.Therapies.OXYGEN, report)
        self.cough = TherapyTracker(em, data, ve.Therapies.COUGH, report)
        self.suction = TherapyTracker(em, data, ve.Therapies.SUCTION, report)
        self.nebulizer = TherapyTracker(em, data, ve.Therapies.NEBULIZER, report)

        # Global values
        self.first = True

    def add_event(self, event: e_types.EventTherapy):
        """ Track activity duration and add activity to calendar for all therapies."""

        # Route to corresponding therapy tracker
        therapy = event.therapy
        if therapy == ve.Therapies.OXYGEN:
            self.oxygen.track_event(event)
        elif therapy == ve.Therapies.COUGH:
            self.cough.track_event(event)
        elif therapy == ve.Therapies.SUCTION:
            self.suction.track_event(event)
        elif therapy == ve.Therapies.NEBULIZER:
            self.nebulizer.track_event(event)
        else:   # Ventilation
            self.ventilator.track_event(event)

    def force_start_therapy(self, raw_time, syn_time, therapy: ve.Therapies):
        """ Force a therapy to activate until there is a better source of truth. """
        is_vent = therapy == ve.Therapies.VENTILATOR
        t_name = therapy.name.lower()
        e_id = eID.VENT_START if is_vent else eID.THERAPY_START
        line = ["-1", dt_to_ts(raw_time), dt_to_ts(syn_time), 'E', e_id, "", therapy.value[0], ""]
        if is_vent:
            line.extend(["0"])
            new_e = et.EventValParam(self.em, self.data, line)
        else:
            therapy_defs = self.data.metadata_messages[e_id]
            for _ in therapy_defs["KeyID"][2]["TherapyStartTypes"][therapy.value[0]]["attributes"]:
                line.append("")
            line.append("0")
            new_e = et.EventTherapy(self.em, self.data, line)
        tracker = getattr(self, t_name)
        tracker.calendar.start_therapy(new_e)

    def force_stop_therapy(self, raw_time, syn_time, therapy: ve.Therapies, last: bool = False):
        """ Force the ventilator therapy to activate until there is a better source of truth. """
        is_vent = therapy == ve.Therapies.VENTILATOR
        t_name = therapy.name.lower()
        e_id = eID.VENT_END if is_vent else eID.THERAPY_END
        line = ["-1", dt_to_ts(raw_time), dt_to_ts(syn_time), 'E', e_id, "", therapy.value[0]]
        if is_vent:
            line.extend(["", "0"])
            new_e = et.EventValParam(self.em, self.data, line)
        else:
            therapy_defs = self.data.metadata_messages[e_id]
            idx = 1 if len(therapy_defs["KeyID"]) == 2 else 2
            stop_vals = therapy_defs["KeyID"][idx]["TherapyStopTypes"][therapy.value[0]]["attributes"] or []
            for _ in stop_vals:
                line.append("")
            line.append("0")
            new_e = et.EventTherapy(self.em, self.data, line)
        tracker = getattr(self, t_name)
        tracker.calendar.stop_therapy(new_e, last=last)

    def process_events(self):
        """ Finish statistics calculations for each therapy after all events are entered. """

        # Process each therapy
        for therapy_name in {"ventilator", "oxygen", "cough", "suction", "nebulizer"}:
            therapy = getattr(self, therapy_name)
            therapy.finish_therapy()


def create_event_record(em: ErrorManager, data: vd.VOCSNData, line: list, range_started: bool = False,
                        filename: str = ""):
    """
    Create event record, calculate usage statistics and fill usage calendar data.
    :param em: Error manager.
    :param data: VOCSN data containers.
    :param line: Event record line.
    :param range_started: For time changes. Force display outside of report range after first record occurs in range.
    :param filename: Source filename if applicable.
    """

    # Lookup event ID
    r_type = line[3]
    e_id = line[4]

    # Check for invalid message IDs
    if e_id not in data.metadata_messages:
        error = Exception("Invalid message ID: {}".format(e_id))
        error.cat = ve.ErrorCat.RECORD_ERROR
        error.sub_cat = ve.ErrorSubCat.INVALID_REC
        raise error

    # No parameters
    if e_id in {eID.AUDIO_PAUSE_START, eID.USER_ACKNOWLEDGE_ALARMS, eID.VENT_START, eID.VENT_END, eID.PATIENT_CHANGE,
                eID.AUDIO_PAUSE_END}:
        e = e_types.EventValParam(em, data, line, filename=filename)

    # One or more parameters with same value type
    elif e_id in {eID.ALARM_START, eID.ALARM_END}:
        e = e_types.EventValParam(em, data, line, filename=filename)

    # Therapy start/stop events
    elif e_id in {eID.THERAPY_START, eID.THERAPY_END}:
        e = e_types.EventTherapy(em, data, line, filename=filename)

    # Settings presets
    elif e_id in eID.SETTINGS_PRESETS:
        e = e_types.EventSetting(em, data, line, filename=filename)

    # Control change event
    elif e_id in {eID.SETTINGS_CHANGE}:
        e = e_types.EventControl(em, data, line, range_started, filename=filename)

    # Access enum
    elif e_id in {eID.ACCESS_CODE_USED}:
        e = e_types.EventAccess(em, data, line, filename=filename)

    # Values only
    elif e_id in {eID.MAINTENANCE_SNAPSHOT, eID.CONFIG, eID.INSP_HOLD}:
        e = e_types.EventVal(em, data, line, filename=filename)

    # Pre-use test
    elif e_id in {eID.PRE_USE_TEST}:
        e = e_types.EventPreUseTest(em, data, line, filename=filename)

    # Therapy state
    elif e_id in {eID.THERAPY_STATE}:
        e = e_types.EventTherapyState(em, data, line, filename=filename)

    # Unexpected value
    else:
        em.log_warning("Unknown message type", ref_id=r_type, val=e_id)
        return None

    # Add values to applicability update stack
    if e and e_id in {eID.THERAPY_START, eID.THERAPY_END} and data.applicability_tracker:
        stack = data.applicability_tracker.stack
        for value in e.values:
            param = value.key
            if param in data.settings_all:
                setting = data.settings_all[param]
                if value not in stack.items:
                    stack.add_item(setting, value)

    # Return new event
    return e


def log_preset_period(tracker: TherapyTracker, time: datetime):
    """
    Log a therapy session message for the preset and preceding active therapy period.
    :param tracker: Therapy tracker.
    :param time: Preset time change.
    """

    # Log end of active period with this preset
    if tracker.calendar.active:

        # References
        data = tracker.data
        r_range = tracker.range
        therapy = tracker.therapy
        cal = tracker.calendar
        start = cal.preset_start
        start_e = cal.start_event
        therapy_id = start_e.therapy_id if hasattr(start_e, "therapy_id") else "2829"
        complete = ve.RecordCompleteState.COMPLETE

        # Constrain session to report period
        start = max(start, r_range.data_start)
        end = min(r_range.end, time)

        # Skip sessions out of range or with no effective length
        if start >= end - timedelta(seconds=1):
            return

        # Construct session record
        details = session_details(data, None, None, therapy)
        session = Session(therapy, therapy_id, start, end, complete, complete, details)
        data.utilization_presets.append(session)
        tracker.calendar.preset_start = end
