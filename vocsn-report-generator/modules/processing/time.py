#!/usr/bin/env python
"""
Time management protects against discontinuity in time, which can be caused by two events:
  1) User time change. This is a handled event, but can cause incorrect duration calculations.
  2) Power failure. Loss of power resets the system time,causing severe discontinuity possibly inverting event sequence.
These are handled by creating a synthetic time sequence. Each time one of the above events occur, an offset is applied
to the raw timestamps and tracked independently. User time changes can be fully corrected because the new and old times
are recorded. Power loss offsets assume reversion to Unix epoch in 1970, allowing for an approximate offset estimation.

    Version Notes:
        1.0.0.0 - 10/16/2019 - Created file with time gap detection and offset calculation.
        1.0.0.1 - 12/05/2019 - Added line length protection.
        1.0.0.2 - 12/20/2019 - Added protection so that time offset is only calculated at start of invalid time period.
        1.0.1.0 - 01/03/2020 - Added a time scan function to anchor all synthetic time to last record.
        1.0.1.1 - 01/05/2020 - Changed terminal output
        1.0.1.2 - 01/07/2020 - Added an offset reset.
        1.0.1.3 - 01/14/2020 - Began implementing updated power reset requirements.
        1.0.2.0 - 01/16/2020 - Consolidated time and data scans into one function.
        1.0.2.1 - 01/27/2020 - Added tracking for power-up events.
        1.0.2.2 - 02/01/2020 - Updated to new log format.
        1.0.2.3 - 02/03/2020 - Added version filter to beginning of last contiguous sequence of valid versions.
        1.0.3.0 - 03/29/2020 - Added raw -> syn time converter to work outside context of reading through batch data.
        1.0.3.1 - 04/13/2020 - Changed read_line to new format.

"""

__author__ = "John Dorian for Sai Systems Technologies"
__copyright__ = "Copyright 2019"
__version__ = "1.0.3.1"

# Built-in modules
from datetime import datetime

# VOCSN modules
from modules.models.report import Report
from modules.readers.tar import TarManager
from modules.models import vocsn_enum as ve
from modules.models.errors import ErrorManager
from modules.models.vocsn_data import VOCSNData
from modules.processing.utilities import dt_to_ts
from modules.models.event_types import EventControl
from modules.readers.settings import check_patient_start


class TimeTracker:
    """ Data container object to track raw and synthetic times. """

    def __init__(self, em: ErrorManager, data: VOCSNData, report: Report):
        """ Initialize tracker. """

        # References
        self.em = em
        self.data = data
        self.report = report

        # Times
        self.last_raw_time = None       # Original time unchanged from data record
        self.last_syn_time = None       # Synthetic time with offset added

        # Offset info
        self.offset = 0                 # Time offset. Treated cumulatively
        self.initial_offset = 0         # Starting offset to anchor endpoint offset at 0
        self.offset_history = []        # Offset changes used for determining synthetic time out of context.
        self.history_set = False

        # States
        self.unsafe_time = False
        self.unsafe_time_sequence_num = None
        self.pre_time_loss_suppression = False

    def reset(self):
        """ Reset for another pass. """
        self.last_raw_time = None
        self.last_syn_time = None
        self.offset = self.initial_offset
        if not self.history_set:
            self.offset_history.insert(0, [0, self.initial_offset])
            self.history_set = True

    def check_user_time_change(self, line: list):
        """
        Check for a user time change event.
        :param line: Data record line.
        """

        # Check for time change record
        if (len(line) < 5) or line[3] != "6006" or line[4] not in ve.DataTypes.TIME_CHANGE or "9005" in line:
            return

        # First pass to read line
        temp_line = line.copy()
        record_time = line[1]
        temp_line.insert(2, record_time)
        event = EventControl(self.em, self.data, temp_line)

        # Calculate time offset
        # after = None
        before = None
        for detail in event.values:
            if detail.name == "was-epoch-time-value":
                before = detail.num
            # if detail.name == "is-epoch-time-value":
            #     after = detail.num
        after = int(line[1])
        if before is None or after is None:
            raise Exception("Time can't interpret time change.")
        self.offset += before - after
        if not self.history_set:
            self.offset_history.append([int(record_time), self.offset])

    def check_power_loss_reset(self, line: list, evaluate: bool = False):
        """
        Check for the signature of a power reset.
        :param line: Data record line.
        :param evaluate: Evaluate the last power reset event.
        """

        # Check if time moves backward, indicating a time loss
        record_time = int(line[1])
        if self.last_raw_time is None:
            self.last_raw_time = record_time
        reference = self.last_raw_time - 10
        if (len(line) < 5) or line[3] != "6006" or line[4] not in ve.DataTypes.TIME_CHANGE:
            if record_time < reference:

                # Mark beginning of unset time
                # Synthetic time must be calculated later
                if evaluate:
                    self.unsafe_time_sequence_num = int(line[0])

                # Calculate time offset based on last time recorded if available
                self.offset += self.last_raw_time - record_time
                if not self.history_set:
                    self.offset_history.append([record_time, self.offset])

        # Save last records
        self.last_raw_time = record_time

    def set_synthetic_time(self, line: list):
        """
        Apply time offsets to record an insert. To be used only while reading batch data.
        :param line: Data record line.
        """

        # Calculate synthetic time
        raw_time = int(line[1])
        syn_time = raw_time + self.offset

        # Store in record line
        line.insert(2, syn_time)

    def get_synthetic_time(self, ts):
        """
        Convert timestamp from raw to synthetic. To be used after batch data has been processed.
        :param ts: Raw timestamp
        :return: Synthetic timestamp
        """
        raw_ts = float(ts)
        offset = 0
        for off_change in self.offset_history:
            if raw_ts > off_change[0]:
                offset = off_change[1]
        return ts + offset


def set_report_offset(em: ErrorManager, data: VOCSNData, report: Report, tar: TarManager):
    """
    Read data lines from TarManager, check for integrity, and route appropriately.
    :param em: Error manager.
    :param data: VOCSN data container.
    :param report: Report definitions.
    :param tar: TAR manager.
    """

    # Vars and references
    old_time = 1262304000  # 1/1/2010 00:00:00
    tm = data.time_manager = TimeTracker(em, data, report)
    a_time = dt_to_ts(report.export_date)
    # a_time = data.tar_manager.last_accessed  # Time TAR file was accessed
    syn_time = 0
    raw_time = 0

    # Catch errors
    try:

        # Disable error tracking until patient reset reached
        em.disable_tracking()

        # Get one line at a time from tar archive to assess time changes
        line = None
        while tar.more_lines:

            # ----- Read and validate line ----- #

            # Read line from file
            line, _, _ = tar.read_line(em)

            # Ignore blank lines
            if not line:
                continue

            # Catch record errors
            try:

                # Check for user time change
                tm.check_user_time_change(line)

                # Check for power failure/device reset
                # Evaluate the final power loss event this pass only
                tm.check_power_loss_reset(line, evaluate=True)

                # Use current time offset to determine synthetic sequence time
                tm.set_synthetic_time(line)

                # Track last event time in case therapies must be stopped at end of available data
                raw_time = int(line[1])
                syn_time = int(line[2])

            # Ignore individual errors at this state
            except Exception as e:
                e.ignore = True

        # Restore error tracking
        em.enable_tracking()

        # Assess offset for controlled time changes
        tm.initial_offset = raw_time - syn_time

        # Anchor to modified time if time was never set
        # This will mark report as unsafe and fail
        if raw_time < old_time:
            tm.initial_offset = a_time - syn_time
            em.log_warning("Setting large time offset for old times", line=line)

    # Time scan failed
    except Exception as e:
        em.enable_tracking()
        message = "Error while scanning time"
        em.log_error(ve.Programs.REPORTING, ve.ErrorCat.PROCESS_ERROR, ve.ErrorSubCat.INVALID_TAR, message, e)

    # Reset trackers
    tm.reset()
    tar.reset()


def check_time(em: ErrorManager, data: VOCSNData, report: Report, tar: TarManager, view_old: bool = False):
    """
    Constrain usable data range to available data range.
    Record vent power-up times to insert records in appropriate places later.
    If a power/time loss event was detected, check if it is in report range.
    If so, suppresses data prior to loss, places warning on report.
    :param em: Error manager.
    :param data: VOCSN data container.
    :param report: Report definitions.
    :param tar: TAR manager.
    :param view_old: When true, time resets are ignored and displayed for validation and forensic purposes.
    """

    # Vars and references
    first = True
    version_start = False
    syn_time = datetime(year=2000, month=1, day=1)
    tm = data.time_manager

    # Catch errors
    try:

        # Get one line at a time from tar archive to assess time changes
        while tar.more_lines:

            # ----- Read and validate line ----- #

            # Read line from file
            line, _, _ = tar.read_line(em)

            # Ignore blank lines
            if not line or line == []:
                continue

            # Catch errors
            try:

                # Disable error tracking until patient reset reached
                em.disable_tracking()

                # Check for user time change
                tm.check_user_time_change(line)

                # Check for power failure/device reset
                tm.check_power_loss_reset(line)

                # Use current time offset to determine synthetic sequence time
                seq = int(line[0])
                tm.set_synthetic_time(line)
                syn_time = datetime.utcfromtimestamp(line[2])

                # Constrain to most recent software version
                if line[4] == "7000" and not version_start and line[5].strip('"') == data.first_version:
                    report.range.set_data_start(syn_time, seq)
                    version_start = True

                # Capture first record
                if first:
                    report.range.set_data_start(syn_time, seq)
                    first = False

                # Record power-up event times
                if line[4] == ve.EventIDs.VENT_START:
                    data.power_up_times.append(line[2])

                # Restore error tracking
                em.enable_tracking()

                # Found time loss event
                if seq == tm.unsafe_time_sequence_num:

                    # Constrain range to exclude all data from before time loss
                    if not view_old:
                        report.range.set_data_start(syn_time, seq)

                        # Log and mark flags if in report range
                        if report.range.data_start <= syn_time <= report.range.end:
                            tm.pre_time_loss_suppression = True
                            em.log_warning("Encountered power loss/time reset", line=line)

                    # Displaying data anyway for forensics
                    else:
                        print("  -------- WARNING: Showing pre-time loss data. --------")
                        em.log_warning("Showing data predating a time loss event - Testing only", unique="PTLD")

            # Ignore individual errors at this state
            except Exception as e:
                e.ignore = True

        # Restore error tracking
        em.enable_tracking()

        # Capture last record
        report.range.set_data_end(syn_time)

    # Time scan failed
    except Exception as e:
        em.enable_tracking()
        message = "Error while evaluating time"
        em.log_error(ve.Programs.REPORTING, ve.ErrorCat.PROCESS_ERROR, ve.ErrorSubCat.INVALID_TAR, message, e)

    # Reset reader
    tar.reset()
    tm.reset()


def scan_time_data(em: ErrorManager, data: VOCSNData, report: Report, tar: TarManager):
    """
    Scan data to set time offset, check for data constraints.
    :param em: Error manager.
    :param data: VOCSN data container.
    :param report: Report definitions.
    :param tar: TAR manager.
    """

    # USE THIS FOR VALIDATION/FORENSICS TO VIEW OLD DATA
    # REGARDLESS OF TIME OR PATIENT RESET
    #   True  = Show multiple patients/times
    #   False = Normal: Suppress previous patients/times
    view_old = False
    if view_old:
        print("!--------------------------------------!")
        print("!-- WARNING: DISPLAYING ALL PATIENTS --!")
        print("!--     NOT SAFE FOR PRODUCTION      --!")
        print("!--------------------------------------!")

    # Set report offset
    set_report_offset(em, data, report, tar)
    if em.status == ve.ErrorLevel.CRITICAL:
        return

    # Set data bounds and check for time loss
    check_time(em, data, report, tar, view_old)
    if em.status == ve.ErrorLevel.CRITICAL:
        return

    # Check for patient resets
    if not view_old:
        check_patient_start(em, report, data, tar)
