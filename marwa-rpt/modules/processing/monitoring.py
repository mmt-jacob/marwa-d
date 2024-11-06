#!/usr/bin/env python
"""
Classes and functions used for processing statistics from monitored data channels.

    Version Notes:
        1.0.0.0  - 09/07/2019 - Created with beginning of calc_averages function.
        1.0.0.1  - 09/08/2019 - Completed calc_averages function.
        1.0.0.2  - 10/01/2019 - Added monitor graph Y-axis range/tick calculations.
        1.0.0.3  - 10/10/2019 - Renamed some fields.
        1.0.1.0  - 10/16/2019 - Restructured to work with external record loop.
        1.0.1.1  - 10/24/2019 - Improved average and trend calculations.
        1.0.1.2  - 11/03/2019 - Interpret 21% FiO2 as no data.
        1.0.1.3  - 11/04/2019 - Move monitor column definition from header to metadata.
        1.0.1.4  - 11/05/2019 - Added support for monitor graph minimum y-scale range.
        1.0.1.5  - 11/19/2019 - Disabled trend calculations for 1 day report.
        1.0.1.6  - 11/27/2019 - Changed FiO2 graph to always show value, even when 21%.
        1.0.1.7  - 12/05/2019 - Implemented patient reset. Modified display logic for FiO2 monitors.
        1.0.1.8  - 12/09/2019 - Corrected patient record data constraint.
        1.0.1.9  - 12/13/2019 - Added handling for "INV" data values.
        1.0.1.10 - 12/16/2019 - Changed FiO2 graph logic to be mutually exclusive.
        1.0.1.11 - 12/21/2019 - Implemented error handling.
        1.0.1.12 - 01/11/2020 - Adjusted to allow graph ticks to be unaligned from calendar.
        1.0.1.13 - 01/15/2020 - Put FiO2 monitors back to normal, excluding 21%/NA values.
        1.0.2.0  - 01/17/2020 - Added pre-trend range tracking.
        1.0.3.0  - 01/18/2020 - Completed pre-trend averaging.
        1.0.3.1  - 02/17/2020 - Performance adjustments
        1.0.3.2  - 02/18/2020 - Adjusted monitor indexing.
        1.0.3.3  - 02/28/2020 - Corrected inclusion logic for 9411 FiO2 monitor.
        1.0.3.4  - 03/13/2020 - Removed O2 flush from FiO2 monitor filter.
        1.0.3.5  - 03/27/2020 - Corrected test condition to more reliably prevent index error in unusual conditions.
        1.0.3.6  - 03/28/2020 - Constrained monitor records to exclude exact matches with end datetime.
        1.0.4.0  - 03/30/2020 - Added combined log records.
        1.0.4.1  - 04/13/2020 - Added flag for combined log processing and crc result handling, updated combined log
                                data container.
        1.0.4.2  - 04/13/2020 - Fixed line splitting error.

"""

__author__ = "John Dorian for Sai Systems Technologies"
__copyright__ = "Copyright 2019"
__version__ = "1.0.4.2"

# Built-in modules
import math
from datetime import datetime, timedelta

# VOCSN data modules
from modules.models.report import Report
from modules.models import vocsn_enum as ve
from modules.models.errors import ErrorManager
from modules.processing.values import get_vals
from modules.models.vocsn_data import VOCSNData
from modules.processing.utilities import ts_to_log
from modules.models.vocsn_data import MonitorChannel
from modules.processing.values import norm_val, de_norm_val
from modules.processing.graph_range import auto_calc_graph_ticks


class MonitorTracker:
    """ Monitored data re-sampling tracker. """

    def __init__(self, report: Report, channel: MonitorChannel):
        """ Instantiate """

        # References
        self.report = report
        self.channel = channel
        self.range = r_range = report.range

        # Check if channel is ratio
        self.ratio = channel.ratio

        # Re-sampled record specifications
        self.total_samples = math.floor(r_range.data_duration / r_range.graph_tick_duration *
                                        r_range.graph_samples_per_tick)
        self.sample_duration = r_range.data_duration / self.total_samples if self.total_samples \
            else timedelta(minutes=5)
        self.default_sample_start = r_range.data_start
        self.default_sample_end = r_range.data_start + self.sample_duration

        # Running counters
        self.has_data = False
        self.total_count = 0
        self.sample_count = 0
        self.val_max = None
        self.val_avg_total = 0
        self.val_avg_count = 0
        self.val_min = None
        self.sample_start = self.default_sample_start
        self.sample_end = self.default_sample_end

        # Values for calculating monitor graph Y-axis range
        self.avg_5th_count = 0
        self.avg_5th_total = 0
        self.avg_5th_min = None
        self.avg_95th_count = 0
        self.avg_95th_total = 0
        self.avg_95th_max = None
        self.ticks_y = None

    def _reset_val_counters(self):
        """ Reset value counters. """
        self.val_max = None
        self.val_avg_total = 0.0
        self.val_avg_count = 0.0
        self.val_min = None

    def _reset_avg_counters(self):
        self.avg_5th_count = 0
        self.avg_5th_total = 0
        self.avg_5th_min = None
        self.avg_95th_count = 0
        self.avg_95th_total = 0
        self.avg_95th_max = None
        self.ticks_y = None

    def _count_sample(self, record: MonitorChannel.MonitorRecord):
        """ Count values from monitor record into graph sample values. """

        # Add to count of data samples
        self.sample_count += 1

        # Single sample
        if not self.channel.uses_percentiles:
            self.val_avg_total += norm_val(record.val1, self.ratio) * record.fill
            self.val_avg_count += record.fill

        # Three-part sample
        # Min/Max values default as None so that default values never influence the min/max comparison
        else:
            self.val_avg_total += norm_val(record.val2, self.ratio) * record.fill
            self.val_avg_count += record.fill
            val1 = norm_val(record.val1, self.ratio)
            val3 = norm_val(record.val3, self.ratio)
            if self.val_max is not None:
                self.val_max = max(self.val_max, val3)
            else:
                self.val_max = val3
            if self.val_min is not None:
                self.val_min = min(self.val_min, val1)
            else:
                self.val_min = val1

    def add_sample(self, record: MonitorChannel.MonitorRecord):
        """
        Count the values from a monitor record into re-sampled channel samples.
        :param record: Monitor channel data record.
        """

        # Ignore records for previous patient
        if record.time < self.range.data_start:
            return

        # Old record - ignore
        if record.time < self.sample_start:
            return

        # Record in range - add to new sample
        if self.sample_start <= record.time < self.sample_end:
            self._count_sample(record)

        # Record is newer - catch up with newer sample
        else:

            # Advance sample until record is in range
            while self.sample_end < record.time and self.total_count < self.total_samples and \
                    self.sample_start < self.range.data_end:
                self._advance_sample()

            # Count sample
            if record.time < self.range.data_end:
                self._count_sample(record)

    def _advance_sample(self):
        """ Finalize current sample and reset for the next. """

        # Finalize current sample
        avg = de_norm_val(self.val_avg_total / self.val_avg_count if self.val_avg_count else 0, self.ratio)
        if self.val_min is None:
            self.val_min = 0
        if self.val_max is None:
            self.val_max = 0
        v_min = de_norm_val(self.val_min, self.ratio)
        v_max = de_norm_val(self.val_max, self.ratio)
        has_data = self.sample_count > 0

        # Add graph sample
        if self.channel.uses_percentiles:
            self.channel.add_graph_sample(self.total_count, self.sample_start, v_min, avg, v_max, has_data)
        else:
            self.channel.add_graph_sample(self.total_count, self.sample_start, avg, has_data=has_data)

        # Update monitor graph range calculation values
        if self.sample_count > 0 and has_data:
            self.avg_5th_count += 1
            self.avg_5th_total += self.val_min
            if self.avg_5th_min is not None:
                self.avg_5th_min = min(self.avg_5th_min, self.val_min)
            else:
                self.avg_5th_min = self.val_min
            self.avg_95th_count += 1
            self.avg_95th_total += self.val_max
            if self.avg_95th_max is not None:
                self.avg_95th_max = max(self.avg_95th_max, self.val_max)
            else:
                self.avg_95th_max = self.val_max

        # Reset for next sample
        self.sample_start = self.sample_end
        self.sample_end += self.sample_duration
        self.total_count += 1
        self.sample_count = 0
        self._reset_val_counters()

    def finish_channel(self):
        """ In case there is partial data, fill in the rest of the samples for a channel to complete its records. """

        # Advance sample until record is in range
        while self.total_count < self.total_samples:
            self._advance_sample()

        # Calculate final monitor graph Y-axis range
        avg_5th = de_norm_val(self.avg_5th_total / self.avg_5th_count if self.avg_5th_count > 0 else 0, self.ratio)
        avg_95th = de_norm_val(self.avg_95th_total / self.avg_95th_count if self.avg_95th_count > 0 else 0, self.ratio)

        # Set graph range
        graph_def = None
        chan = self.channel
        graph_defs = self.report.settings["display"]["monitor_graphs"]
        if chan.id in graph_defs:
            graph_def = graph_defs[chan.id]
        auto_calc_graph_ticks(chan, self.avg_5th_min, avg_5th, avg_95th, self.avg_95th_max, graph_def)


def track_monitor_record(em: ErrorManager, data: VOCSNData, report: Report, line: list, combo_log: bool = False,
                         filename: str = None):

    # References
    r_range = report.range

    # Get record metadata
    seq = line[0]
    r_type = line[3]
    msg_id = line[4]
    raw_ts = int(line[1])
    syn_ts = int(line[2])
    log_details = []
    col_num = 5

    # Interpret CRC result
    crc_result = "N/A"
    if combo_log and line[-1] in ["PASS", "FAIL"]:
        crc_result = line.pop(-1)

    # Ignore undefined messages
    md_m = data.metadata_messages
    if msg_id not in md_m:
        em.log_warning("Unknown message type", ref_id=r_type, val=msg_id)
        return

    # Range check
    dt = datetime.utcfromtimestamp(float(syn_ts))
    raw_dt = datetime.utcfromtimestamp(float(raw_ts))
    in_range = r_range.data_start <= dt < r_range.data_end
    in_pre_trend = r_range.use_trend and r_range.data_start <= dt < r_range.trend_start
    in_trend = r_range.use_trend and r_range.trend_start <= dt < r_range.data_end

    # Create monitor records for each channel
    na = ["NA", "INV"]
    bad_channels = []
    m_def = md_m[msg_id]
    col_defs = m_def["KeyID"]
    if msg_id == "7201":
        param_defs = data.metadata_7201
        mon_trackers = data.monitors_7201
    else:
        param_defs = data.metadata_parameters
        mon_trackers = data.monitors_all
    while col_num < len(col_defs):
        def_idx = col_num - 5

        # Lookup monitor channel
        full_key = col_defs[def_idx]
        key = full_key.split('_')[0]
        val_def = param_defs[key]
        c = mon_trackers[key]
        tracker = c.tracker
        percentile = "_" in full_key
        c.uses_percentiles = percentile

        # Extract percentile data
        time = None
        if c.uses_percentiles:
            time = line[col_num].strip()
            fill = float(time) * 0.2
            val1 = line[col_num + 1].strip()
            val2 = line[col_num + 2].strip()
            val3 = line[col_num + 3].strip()
            col_num += 4

            # Skip invalid data
            if val1 in na:
                continue

            # Process values
            v1 = get_vals(em, data, val_def, key, "", val1, None)
            v2 = get_vals(em, data, val_def, key, "", val2, None)
            v3 = get_vals(em, data, val_def, key, "", val3, None)
            val1 = v1.num
            val2 = v2.num
            val3 = v3.num

        # Single value monitors
        else:
            val1 = line[col_num].strip()
            col_num += 1

            # Skip invalid data
            if val1 in na:
                continue

            # Process value
            v1 = get_vals(em, data, val_def, key, "", val1, None)
            val1 = v1.num
            val2 = val3 = v2 = v3 = fill = None

        # Store a log record
        if combo_log:
            log_details.append(MonitorLogDetail(c, v1, v2, v3, time))

        # Handle monitor errors
        try:

            # Filter monitored FiO2 channel by O2 delivery mode
            if key == "9411":
                o2_therapy_active = data.events_tracker.oxygen.calendar.active
                if not o2_therapy_active:
                    continue
                o2_delivery = data.settings_all["87"].current_enum()
                if o2_delivery != "3075":
                    continue

            # Check for valid data
            if val1 is None:
                continue
            if c.uses_percentiles and (val2 is None or val2 in na or val3 is None or val3 in na):
                continue

            # Create monitor data record
            rec = c.add_record(seq, dt, fill, val1, val2, val3)

            # Process records
            if c.uses_percentiles:
                val = norm_val(rec.val2, c.ratio) * rec.fill
            else:
                val = norm_val(rec.val1, c.ratio)

            # Re-sample for graph
            tracker.add_sample(rec)

            # # After updating graph, do not include 21% for FiO2 in average/trend calculation
            # if key in ["9411", "9412"] and (val1 == val2 == val3 == 21.0):
            #     continue

            # Mark data available
            c.tracker.has_data = True

            # Track main average
            if in_range:
                c.avg_count += rec.fill
                c.avg_total += val

            # Track trend averages
            if r_range.use_trend:
                if in_pre_trend:
                    c.pre_trend_count += rec.fill
                    c.pre_trend_total += val
                if in_trend:
                    c.trend_count += rec.fill
                    c.trend_total += val

        # Handle monitor errors
        except Exception as e:

            # Bad monitor ID
            if key in data.monitors_all:
                if key not in bad_channels:
                    message = "Error while reading monitor message"
                    e = Exception("Unknown monitor")
                    em.log_error(ve.Programs.REPORTING, ve.ErrorCat.LOW_ERROR, ve.ErrorSubCat.INVALID_ID, message, e,
                                 p_id=key)
                    bad_channels.append(key)

            # Other errors
            else:
                message = "Error while reading monitor message"
                em.log_error(ve.Programs.REPORTING, ve.ErrorCat.LOW_ERROR, ve.ErrorSubCat.INTERNAL_ERROR, message, e)

    # Construct log record
    data.monitors_log.append(MonitorLogRecord(line, m_def['MsgName'], raw_dt, dt, log_details, crc_result=crc_result,
                                              filename=filename))


class MonitorLogRecord:
    """ Create record for use in the combined log. """

    def __init__(self, line: list, name: str, raw_time: datetime, syn_time: datetime, details, crc_result,
                 filename=None):
        """ Initialize record. """

        # Attributes
        self.record_type = ve.LogRecordType.BATCH_MON
        self.sequence = line[0]
        self.message_type = line[3]
        self.id = line[4]
        self.name = name
        self.raw_time = raw_time
        self.syn_time = syn_time
        self.channel_vals = details
        self.crc_result = crc_result
        self.filename = filename
        for x in range(0, len(line)):
            line[x] = str(line[x])
        self.raw_data = "|".join(line)

    def __str__(self):
        log_str = ""
        for cv in self.channel_vals:
            if log_str != "":
                log_str += ", "
            log_str += str(cv)
        return log_str


class MonitorLogDetail:
    """ Single monitor channel record. """

    def __init__(self, c: MonitorChannel, val1, val2, val3, fill):
        self.channel = c
        self.use_percentile = c.uses_percentiles
        self.val1 = val1
        self.val2 = val2
        self.val3 = val3
        self.fill = fill

    def __str__(self):
        if self.use_percentile:
            return "{}: [ 5th: {}, 50th: {}, 95th: {}, N: {} ]".format(self.channel.display_label, self.val1.str,
                                                                       self.val2.str, self.val3.str, self.fill)
        else:
            return "{}: {}".format(self.channel.display_label, self.val1.str)
