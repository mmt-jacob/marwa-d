#!/usr/bin/env python
"""
Classes and functions used for tracking alarm events and processing statistics.

    Version Notes:
        1.0.0.0 - 09/22/2019 - Created with AlarmTracker class.
        1.0.0.1 - 09/28/2019 - Completed initial attempt at alarm tracking.
        1.0.0.2 - 09/29/2019 - Added time bucket name field.
        1.0.0.3 - 10/04/2019 - Renamed event timestamp fields.
        1.0.1.0 - 10/10/2019 - Changed to compare trend with entire report period.
        1.0.1.1 - 10/17/2019 - Updated module locations.
        1.0.2.0 - 10/18/2019 - Updated for compatibility with new data files.
        1.0.2.1 - 10/19/2019 - Updated therapy references to use standard form.
        1.0.2.2 - 10/20/2019 - Corrected missing record message to not occur at beginning/end of report range
        1.0.2.3 - 10/31/2019 - Added alarm severity.
        1.0.2.4 - 11/07/2019 - Fixed some incorrect argument types and prevented creating blank alarms.
        1.0.2.5 - 11/22/2019 - Added trend calculations.
        1.0.2.6 - 11/24/2019 - Fixed a zero-division protection to fall back on the right data type.
        1.0.2.7 - 12/05/2019 - Implemented patient reset.
        1.0.2.8 - 12/21/2019 - Implemented error management.
        1.0.2.9 - 01/09/2020 - Added a stop-all-alarms function.
        1.0.3.0 - 01/18/2020 - Implemented pre-trend average calculations.
        1.0.3.1 - 02/27/2020 - Corrected the record length for the synthetic alarm start/stop.
        1.0.3.2 - 04/06/2020 - Adjusted date comparators.

"""

__author__ = "John Dorian for Sai Systems Technologies"
__copyright__ = "Copyright 2019"
__version__ = "1.0.3.2"

# Built-in
import calendar
from datetime import timedelta

# VOCSN data modules
from modules.models.report import Report
from modules.models import vocsn_enum as ve
from modules.models.report import ReportRange
from modules.models.errors import ErrorManager
from modules.models.vocsn_data import VOCSNData
from modules.processing.utilities import dt_to_ts
from modules.processing.utilities import calc_trend
from modules.models.event_types import EventValParam
from modules.models.vocsn_enum import Therapies, EventIDs as eID, RecordCompleteState as rState


class AlarmTracker:
    """
    High-level container class to organize all alarm-tracking activity.
    To be run in two passes:
      1) Add individual events using the add_event() method to process slarm starts/stops.
      2) Run calc_stats() to calculate all the statistics needed for the report.
    """

    def __init__(self, em: ErrorManager, data: VOCSNData, report: Report):
        """ Initialize. """

        # Reference
        r_range = report.range
        settings = report.settings
        self.em = em
        self.range = r_range

        # Active alarm tracker for tracking individual alarm starts/stops to construct complete alarms
        self.event_tracker = AlarmEventTracker(em, data, r_range)

        # Trackers using different categorization of complete alarms
        self.all_alarms = data.alarms_all = []
        self.calendar = AlarmCalendar()
        self.stats = AlarmStats(r_range)
        self.therapy_man = TherapyManager(em, settings)

    def add_event(self, e: EventValParam):
        """ Track an individual alarm record. """

        # Process alarm start/stop event.
        # If this completes an alarm, it will be returned
        alarm = self.event_tracker.add_event(e)

        # Track completed alarm
        if alarm:
            self.all_alarms.append(alarm)

    def process_events(self):
        """ Calculate alarm statistics. To be run after adding all events. """

        # End any active alarms at the end of the report
        tracker = self.event_tracker
        last = True
        while len(tracker.alarms) > 0:
            for alarm_type, start in tracker.alarms.items():
                tracker.force_end(alarm_type, last)
                break

        # Alarm tracking process results in alarms sorted by end time.
        # Sort by start time
        self.all_alarms.sort(key=lambda a: a.start_syn)

        # Process statistics for each alarm
        for alarm in self.all_alarms:

            # Track calendar statistics
            self.calendar.track_alarm(alarm)

            # Track global statistics
            self.stats.track_alarm(alarm)

            # Add to bucket statistics
            self.therapy_man.route_alarm(alarm)

        # Calculate final statistics
        self.stats.finish_calcs()

    def stop_all(self, ref_e):
        """ Stop all active alarms. Used at power down. """
        tracker = self.event_tracker
        while len(tracker.alarms) > 0:
            for alarm_type, start in tracker.alarms.items():
                tracker.force_end(alarm_type, ref_e=ref_e)
                break


class Alarm:
    """ Alarm class. """

    def __init__(self, start: EventValParam, end: EventValParam, complete: rState, truncated: rState):
        """ Initialize. """

        # IDs
        self.alarm_id = start.param
        self.fault_id = start.fault
        self.therapy = start.therapy
        self.label = start.param_label
        self.test = start.sequence

        # Times
        self.start_raw = start.raw_time
        self.start_syn = start.syn_time
        self.end_raw = end.raw_time
        self.end_syn = end.syn_time
        self.duration = self.end_syn - self.start_syn
        self.complete = complete
        self.truncated = truncated

        # Alarm metrics
        self.limit = start.values["limitValue"] if hasattr(start.values, "limitValue") else None
        self.measured = start.values["measuredValue"] if hasattr(start.values, "measuredValue") else None
        self.severity = start.alarm_priority


class AlarmCalendar:
    """ Container for time-based alarm tracking. """

    def __init__(self):
        """ Initialize. """

        # Trackers
        self.days = []
        self.times = []

        # Add trackers for each day of the week
        for day in range(0, 7):
            self.days.append(AlarmDayBucket(day))

        # Add trackers for times of day in 3 hour increments
        hour = 0
        for day in range(0, 8):
            self.times.append(AlarmTimeBucket(hour))
            hour += 3

    def track_alarm(self, alarm: Alarm):
        """ Track alarm in time-based buckets. """

        # Track day of week
        day = alarm.start_syn.weekday()
        self.days[day].count_alarm()

        # Track time of day
        index = alarm.start_syn.hour // 3
        self.times[index].count_alarm()


class AlarmDayBucket:
    """ Alarm duration bucket. """

    def __init__(self, day: int):
        """ Initialize. """

        # Weekday information
        self.day = day
        self.name = calendar.day_name[day]

        # Bucket-level statistics
        self.count = 0

    def count_alarm(self):
        """ Count alarm in this bucket if it is within the bucket duration range. """
        self.count += 1


class AlarmTimeBucket:
    """ Alarm duration bucket. """

    def __init__(self, hour: int):
        """ Initialize. """

        # Duration timings
        self.start = hour
        self.end = hour + 3
        self.name = "{:02d}:00-{:02d}:00".format(self.start, self.end)

        # Bucket-level statistics
        self.count = 0

    def count_alarm(self):
        """ Count alarm in this time range bucket. """
        self.count += 1


class AlarmEventTracker:
    """ Track alarm starts and stops. """

    def __init__(self, em: ErrorManager, data: VOCSNData, r_range: ReportRange):
        """ Initialize. """
        
        # References
        self.em = em
        self.data = data
        self.r_range = r_range

        # Active alarm records
        self.alarms = {}
        self.alarm_type_starts = []

    def add_event(self, e: EventValParam):
        """ Track an individual alarm record. """

        # Get alarm type
        alarm = None
        alarm_type = e.param
        if not alarm_type:
            error = Exception("Encountered alarm with no type.")
            error.cat = ve.ErrorCat.MID_ERROR
            error.sub_cat = ve.ErrorSubCat.INTERNAL_ERROR
            raise error

        # Alarm start
        if e.id == eID.ALARM_START:

            # Alarm already active - this shouldn't happen
            if alarm_type in self.alarms.keys():
                self.force_end(alarm_type)

            # New alarm
            self._start_alarm(e, alarm_type)

        # Alarm end
        elif e.id == eID.ALARM_END:

            # Alarm start is missing - this shouldn't happen
            if alarm_type not in self.alarms.keys():
                self._force_start(e, alarm_type)

            # End alarm
            alarm = self._stop_alarm(e, alarm_type)

        # Invalid event ID - this shouldn't happen
        else:
            error = Exception("Unexpected ID in alarm tracker: {}".format(e.id))
            error.cat = ve.ErrorCat.MID_ERROR
            error.sub_cat = ve.ErrorSubCat.INTERNAL_ERROR
            raise error

        # Return completed alarm
        return alarm

    def _force_start(self, e: EventValParam, alarm_type: str):
        """
        Artificially force an alarm to start when an end is found while not already active.
        :param e: Current end event, used to make up a start time.
        :param alarm_type: Alarm type.
        """

        # Create an artificial start record. Mark record as incomplete
        first = alarm_type not in self.alarm_type_starts
        raw_time = e.raw_time - timedelta(seconds=10)
        syn_time = e.syn_time - timedelta(seconds=10)
        record_line = ["-1", dt_to_ts(raw_time), dt_to_ts(syn_time), 'E', eID.ALARM_START, e.param, "", "", "-1", "0"]
        new_e = self.alarms[alarm_type] = EventValParam(self.em, self.data, record_line)
        new_e.name = "Alarm - Partial Record"
        if not first:
            new_e.complete = rState.MISSING_START
        self._start_alarm(new_e, alarm_type)

        # Log missing record
        if not first:
            self.em.log_warning("Encountered alarm stop without a start")

    def force_end(self, alarm_type: str, last: bool = False, ref_e=None):
        """
        Artificially force an alarm to end when a start is found while already active.
        :param alarm_type: Alarm type.
        :param last: Indicates last alarm. Will be extended to end of the report.
        :param ref_e: Reference event. Use times from this.
        """

        # Terminate previous alarm and mark incomplete
        old_e = self.alarms[alarm_type]
        old_e.name = "Alarm - Partial Record"
        if ref_e:
            raw_time = ref_e.raw_time
            syn_time = ref_e.syn_time
        else:
            raw_time = old_e.raw_time + timedelta(seconds=10)
            syn_time = old_e.syn_time + timedelta(seconds=10)
        record_line = ["-1", dt_to_ts(raw_time), dt_to_ts(syn_time), 'E', eID.ALARM_END, old_e.param, "-1", "0"]
        new_e = EventValParam(self.em, self.data, record_line)
        if not last:
            old_e.complete = rState.MISSING_END
        alarm = self._stop_alarm(new_e, alarm_type)
        if alarm:
            self.data.alarms_all.append(alarm)

        # Log missing record
        if not last:
            self.em.log_warning("Encountered alarm start without a stop")

    def _start_alarm(self, e: EventValParam, alarm_type: str):
        """ Start an alarm. """
        started = self.alarm_type_starts
        if alarm_type not in started:
            started.append(alarm_type)
        self.alarms[alarm_type] = e

    def _stop_alarm(self, e: EventValParam, alarm_type: str):
        """
        Stop an active alarm.
        :param e: Alarm stop event.
        :param alarm_type: Alarm type.
        :return: Completed Alarm object.
        """

        # References
        r = self.r_range

        # Complete alarm record
        alarm = None
        start = self.alarms[alarm_type]
        end = e
        start_in_range = r.data_start <= start.syn_time <= r.end
        end_in_range = r.data_start <= end.syn_time <= r.end
        contains_range = start.syn_time < r.data_start and r.data_end < end.syn_time

        # Alarm at least partially overlaps report range
        if start_in_range or end_in_range or contains_range:

            # Alarm is completely contained within report period
            if start_in_range and end_in_range:
                truncated = rState.COMPLETE

            # Alarm is partially contained within report period - adjust times.
            else:

                # Set truncated type
                if not start_in_range:
                    truncated = rState.MISSING_START
                else:
                    truncated = rState.MISSING_END

                start.raw_time = max(start.raw_time, r.data_start)
                start.syn_time = max(start.syn_time, r.data_start)
                end.raw_time = min(end.raw_time, r.end)
                end.syn_time = min(end.syn_time, r.end)

            # Create alarm
            alarm = Alarm(start, end, start.complete, truncated)

        # Remove from active alarm list and return completed alarm
        del self.alarms[alarm_type]
        return alarm


class AlarmStats:
    """ Track global alarm statistics. """

    def __init__(self, r_range: ReportRange):
        """ Initialize. """
        
        # Reference
        self.range = r_range

        # Variables
        self.total_count = 0
        self.total_duration = None

        # Averages
        self.avg_duration = None
        self.avg_occurrence = None

        # Pre-trends
        self.pre_trend_count = 0
        self.pre_trend_duration = None
        self.pre_trend_occurrence = None

        # Trends
        self.trend_count = 0
        self.trend_duration = None
        self.trend_occurrence = None
        self.trend_duration_delta = None
        self.trend_occurrence_delta = None
        self.trend_duration_percentage = None
        self.trend_occurrence_percentage = None

    def track_alarm(self, alarm: Alarm):
        """ Track alarm in statistics. """
        if self.total_duration is None:
            self.total_duration = timedelta(seconds=0)
            self.trend_duration = timedelta(seconds=0)
            self.pre_trend_duration = timedelta(seconds=0)
        self.total_count += 1
        self.total_duration += alarm.duration
        if self.range.use_trend:
            if self.range.data_start <= alarm.start_syn < self.range.trend_start:
                self.pre_trend_count += 1
                self.pre_trend_duration += alarm.duration
            if self.range.trend_start <= alarm.start_syn <= self.range.data_end:
                self.trend_count += 1
                self.trend_duration += alarm.duration
            
    def finish_calcs(self):
        """ Calculate statistics once all events are processed. """

        # Averages
        if self.total_count > 0 and self.range.data_days > 0:
            self.avg_duration = self.total_duration / self.total_count
            self.avg_occurrence = self.total_count / self.range.data_days
            
            # Trends
            if self.range.use_trend:
                self.pre_trend_duration = self.pre_trend_duration / self.pre_trend_count if self.pre_trend_count else \
                    timedelta(days=0)
                self.trend_duration = self.trend_duration / self.trend_count if self.trend_count else timedelta(days=0)
                self.trend_duration_delta, self.trend_duration_percentage = \
                    calc_trend(self.pre_trend_duration.total_seconds(), self.trend_duration.total_seconds())
                self.pre_trend_occurrence = self.pre_trend_count / self.range.pre_trend_days
                self.trend_occurrence = self.trend_count / self.range.trend_days
                self.trend_occurrence_delta, self.trend_occurrence_percentage = \
                    calc_trend(self.pre_trend_occurrence, self.trend_occurrence)


class TherapyManager:
    """ Container for AlarmTherapy trackers. """

    def __init__(self, em: ErrorManager, settings: dict):

        # Therapy trackers
        self.therapies = {}

        # Populate therapies
        for therapy in Therapies:
            name = therapy.name.lower()
            self.therapies[name] = AlarmTherapy(em, settings, name)

    def route_alarm(self, alarm: Alarm):
        therapy = alarm.therapy.name.lower()
        if therapy in self.therapies:
            self.therapies[therapy].add_alarm(alarm)


class AlarmTherapy:
    """ Therapy alarm container. """

    def __init__(self, em: ErrorManager, settings: dict, therapy: int):

        # References
        self.em = em
        self.settings = settings

        # Identifiers
        self.therapy = therapy

        # Therapy-level statistics
        self.count = 0
        self.total_duration = timedelta(seconds=0)
        self.avg_duration = timedelta(seconds=0)

        # Alarm types
        self.alarm_types = {}

    def add_alarm(self, alarm: Alarm):
        """ Add alarm, creating new alarm type if needed. """

        # Check if alarm type already exists
        if alarm.alarm_id in self.alarm_types.keys():
            alarm_type = self.alarm_types[alarm.alarm_id]

        # Create new alarm type
        else:
            alarm_type = self.alarm_types[alarm.alarm_id] = AlarmType(self.settings, alarm)

        # Count statistics
        self.count += 1
        self.total_duration += alarm.duration
        self.avg_duration = self.total_duration / self.count
        alarm_type.add_alarm(alarm)


class AlarmType:
    """ Tracker for alarms of a specific type. """

    class Bucket:
        """ Alarm duration bucket. """

        def __init__(self, low: str, high: str):
            """ Initialize. """

            # Duration timings
            self.low = timedelta(seconds=int(low))
            self.high = timedelta(seconds=int(high)) if high else timedelta(days=10000)

            # Bucket-level statistics
            self.count = 0

        def count_if_in_range(self, alarm: Alarm):
            """ Count alarm in this bucket if it is within the bucket duration range. """
            if self.low <= alarm.duration < self.high:
                self.count += 1

    def __init__(self, settings: dict, alarm: Alarm):
        """ Initialize using a reference alarm to derive type. """

        # Identifiers
        self.id = alarm.alarm_id
        self.name = alarm.label
        self.severity = alarm.severity

        # Alarm-type level statistics
        self.count = 0
        self.total_duration = timedelta(seconds=0)
        self.avg_duration = timedelta(seconds=0)

        # Alarm duration buckets
        self.buckets = []
        bucket_defs = settings["tables"]["alarm_duration_splits"]
        for bucket in bucket_defs:
            self.buckets.append(self.Bucket(bucket['low'], bucket['high']))

    def add_alarm(self, alarm: Alarm):

        # Add to statistics
        self.count += 1
        self.total_duration = timedelta(seconds=0)
        self.avg_duration = timedelta(seconds=0)

        # Add to buckets
        for bucket in self.buckets:
            bucket.count_if_in_range(alarm)
