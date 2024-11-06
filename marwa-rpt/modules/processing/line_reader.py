#!/usr/bin/env python
"""
Line reader reads lines from the tar file handler, checks each line for data integrity and routes them to the
appropriate modules.

    Version Notes:
        1.0.0.0  - 10/15/2019 - Created file with read_data_line function.
        1.0.0.1  - 10/17/2019 - Added event routing.
        1.0.0.2  - 10/19/2019 - Connected to therapy session tracking.
        1.0.0.3  - 10/30/2019 - Improved error handling
        1.0.0.4  - 11/01/2019 - Added initial config line reader. Reordered conditions to reuse error handling.
        1.0.0.5  - 11/04/2019 - force vent to start and stop with first and last records.
        1.0.0.6  - 11/14/2019 - Moved forced therapy start to occur after first relevant settings snapshot.
        1.0.0.7  - 12/01/2019 - Integrated new system event list.
        1.0.0.8  - 12/05/2019 - Implemented patient reset, moved tracker initialization to usage.py.
        1.0.0.9  - 12/11/2019 - Moved event time capture to cover all event types.
        1.0.0.10 - 12/14/2019 - Added applicability processing.
        1.0.1.0  - 12/15/2019 - Implemented a post-processing update stack for event values.
        1.0.1.1  - 12/17/2019 - Moved some settings changes from system to appropriate config event group.
        1.0.1.2  - 12/20/2019 - Moved section availability override here.
        1.0.2.0  - 12/21/2019 - Integrated error management.
        1.0.2.1  - 12/26/2019 - Added unknown record type warning.
        1.0.2.2  - 01/08/2020 - Changed config line format.
        1.0.2.3  - 01/16/2020 - Added diagnostic output.
        1.0.2.4  - 01/17/2020 - Omitted 9005 settings change type records from processing.
        1.0.2.5  - 01/18/2020 - Fixed alignment of first settings dots.
        1.0.2.6  - 01/20/2020 - Disabled filter that suppressed the Trend Summary without trends.
        1.0.2.7  - 01/26/2020 - Improved initial preset record placement on settings chart.
        1.0.2.8  - 01/27/2020 - Added power records.
        1.0.2.9  - 02/09/2020 - Prevented unnecessary applicability assessment to improve performance.
        1.0.2.10 - 02/17/2020 - Added language update from config line. Switched from dict conditions to sets.
        1.0.2.11 - 02/28/2020 - Adjustments to support changes to preset label handling.
        1.0.2.12 - 03/12/2020 - Always process maintenance snapshot events from valid versions up to report end.
        1.0.2.13 - 04/06/2020 - Allow alarm records through prior to report period and stop at end of report. Created
                                exception in therapy start/stop handling to ignore insp. hold records.
        1.0.2.14 - 04/10/2020 - Removed Insp. hold handling. (data type changed)
        1.0.3.0  - 04/13/2020 - Added support for modifications needed for combined log.

"""

__author__ = "John Dorian for Sai Systems Technologies"
__copyright__ = "Copyright 2019"
__version__ = "1.0.3.0"

# Built-in modules
from datetime import datetime

# VOCSN modules
from modules.models.report import Report
from modules.readers.tar import TarManager
from modules.models import vocsn_enum as ve
from modules.models.report import ReportRange
from modules.models.errors import ErrorManager
from modules.models.vocsn_data import VOCSNData
from modules.readers.settings import load_settings_by_ver
from modules.processing.events import create_event_record
from modules.processing.monitoring import track_monitor_record
from modules.processing.therapy_state import set_therapy_states
from modules.models.vocsn_enum import EventIDs as eID, Therapies
from modules.processing.utilities import get_record_type, dt_to_ts
from modules.models.event_types import power_on_event, power_off_event, EventValue


def read_config(em: ErrorManager, data: VOCSNData, report: Report, tar: TarManager):
    """
    Read initial config and set dependent settings.
    :param em: Error manager.
    :param data: VOCSN data container.
    :param report: Report definitions.
    :param tar: TAR manager.
    :return: Success as bool, and error, used to abort without version info.
    """

    # Catch errors
    message = "Error while reading metadata"
    cat = ve.ErrorCat.FILE_ERROR
    sub_cat = ve.ErrorSubCat.INVALID_TAR
    try:

        # Reload config line with proper metadata
        try:
            line_parts = tar.config_line
            event = create_event_record(em, data, line_parts)
        except Exception as e:
            message = "Cannot read config message."
            raise e

        # Store language and settings
        report.set_language(event)

        # Load report settings
        try:
            report.settings = settings = load_settings_by_ver(data.lookup_version)
        except Exception as e:
            message = "Unable to load report settings."
            raise e

        # Set error thresholds
        try:
            em.setup(settings)
        except Exception as e:
            message = "Error while reading error level definitions."
            cat = ve.ErrorCat.PROCESS_ERROR
            sub_cat = ve.ErrorSubCat.INTERNAL_ERROR
            raise e

        # Setup report range definition
        try:
            report.range = ReportRange(settings, report.report_duration, report.start)
        except Exception as e:
            message = "Error while processing report range."
            cat = ve.ErrorCat.PROCESS_ERROR
            sub_cat = ve.ErrorSubCat.INTERNAL_ERROR
            raise e

        # # Disable unsupported report sections
        # if not report.range.use_trend:
        #     report.sections.trend_summary = False

    # Handle errors. Fatal: cannot run report with unknown version number
    except Exception as e:
        em.log_error(ve.Programs.REPORTING, cat, sub_cat, message, e)


def read_data_lines(em: ErrorManager, data: VOCSNData, report: Report, tar: TarManager, combo_log=True):
    """
    Read data lines from TarManager, check for integrity, and route appropriately.
    :param em: Error manager.
    :param data: VOCSN data container.
    :param report: Report definitions.
    :param tar: TAR manager.
    :param combo_log: Modify error management behavior for combined log processing.
    """

    # Catch processing errors
    try:

        # References and Variables
        tracker = data.events_tracker
        tm = data.time_manager
        r_range = report.range
        start_code = False
        record_count = 0
        range_started = False
        last_seq = 0

        # Disable error tracking until patient reset reached
        em.disable_tracking()

        # Get one line at a time from tar archive
        last_syn_data_time = None
        last_raw_data_time = None
        while tar.more_lines:

            # ----- Read and validate line ----- #

            # Read line from file
            em.set_line(None)
            line, next_is_7203, filename = tar.read_line(em)
            if em.status == ve.ErrorLevel.CRITICAL and not combo_log:
                return

            # Ignore blank lines
            if not line:
                continue
            record_count += 1

            # Catch record errors
            rec_type = get_record_type(line[2], line[3])
            try:

                # Mark applicability as out of date
                data.applicability_tracker.up_to_date = False

                # ----- Generate synthetic timestamps ----- #

                # Check for user time change
                tm.check_user_time_change(line)

                # Check for power failure/device reset
                tm.check_power_loss_reset(line)

                # Use current time offset to determine synthetic sequence time
                tm.set_synthetic_time(line)
                em.set_line(line, filename)

                # Track last event time in case therapies must be stopped at end of available data
                raw_time = datetime.utcfromtimestamp(int(line[1]))
                syn_time = datetime.utcfromtimestamp(int(line[2]))
                data.last_batch_raw = last_raw_data_time = raw_time
                data.last_batch_syn = last_syn_data_time = syn_time
                sequence = int(line[0])

                # Begin tracking messages for states and settings
                is_usage_timer = line[4] == eID.MAINTENANCE_SNAPSHOT
                if not range_started and sequence >= report.range.data_sequence:
                    if data.diag:
                        print("  First safe sequence:", line[0])
                    em.enable_tracking()
                    range_started = True

                # Populate initial settings
                if syn_time >= report.range.data_start and not r_range.data_started:
                    r_range.data_started = True
                    if data.diag:
                        print("  First valid sequence:", line[0])
                    if data.events_tracker.ventilator.calendar.active:
                        data.settings_tracker.update_history(report.range.data_start)
                    else:
                        data.settings_tracker.update_history(syn_time)

                # Always process usage timers
                if is_usage_timer and tar.first_valid_sequence <= sequence and syn_time < report.range.end:
                    pass

                # Skip records prior to patient start
                # Skip records after end of report range
                # Always process maintenance snapshots (patient-independent)
                elif (not range_started or syn_time > report.range.end) and not combo_log:
                    continue

                # Insert power on records
                if line[2] in data.power_up_times:
                    power_on = power_on_event(em, data, line[1], line[2])
                    data.events_all.append(power_on)
                    data.power_up_times.remove(line[2])

                # ----- Route line by data type ----- #

                # Get record type
                r_type = line[3]

                # Monitors
                if r_type == "M":

                    # Handle therapy state monitor
                    if line[4] == eID.THERAPY_STATE:
                        event = create_event_record(em, data, line, filename=filename)
                        set_therapy_states(em, data, report, event, start_code)

                    # Handle other value-based monitors
                    else:
                        track_monitor_record(em, data, report, line, combo_log, filename=filename)

                # Events and Settings
                elif r_type in {"E", "S"}:

                    # Don't process access control changes
                    if "9005" in line:
                        continue

                    # Interpret raw data and generate appropriate event record
                    event = create_event_record(em, data, line, range_started, filename=filename)
                    if not event:
                        continue

                    # Capture start code so that nearby vent-start capable messages are consistent
                    if event.id == eID.VENT_START and next_is_7203:
                        start_code = line[5]
                    start_code = None

                    # Store in master list
                    data.events_all.append(event)

                    # Alarms
                    if event.id in {eID.ALARM_START, eID.ALARM_END}:
                        data.alarms_tracker.add_event(event)

                    # Track therapy sessions
                    elif event.id in {eID.THERAPY_START, eID.THERAPY_END, eID.VENT_START, eID.VENT_END, eID.INSP_HOLD}:
                        data.events_tracker.add_event(event)

                    # Track control setting change
                    elif event.id == eID.SETTINGS_CHANGE:
                        data.settings_tracker.add_event(event)

                        # Associate with therapy trackers
                        therapy_name = event.therapy.name.lower()
                        if therapy_name == "system":
                            if event.control in {"22", "7", "8", "9"}:
                                data.events_tracker.ventilator.settings_events.append(event)
                            elif event.control in {"55", "89"}:
                                data.events_tracker.suction.settings_events.append(event)
                            elif event.control in {"56", "57"}:
                                data.events_tracker.nebulizer.settings_events.append(event)
                            else:
                                data.events_system.append(event)
                        else:
                            t_tracker = getattr(data.events_tracker, therapy_name)
                            t_tracker.settings_events.append(event)

                    # Settings
                    elif r_type == "S":

                        # Track settings preset changes
                        data.settings_tracker.add_event(event)

                    # Track system messages
                    elif event.id == eID.PATIENT_CHANGE:
                        for x in range(1, 4):
                            for preset_label_id in {"14502", "14503", "14504"}:
                                preset_val = EventValue(preset_label_id, "Preset Label", None, "Preset {}".format(x))
                                data.settings_all[preset_label_id].current[str(x)] = preset_val
                        et = data.events_tracker
                        et.ventilator.settings_events = []
                        et.oxygen.settings_events = []
                        et.cough.settings_events = []
                        data.events_system.append(event)

                    # Remainders, excluding maintenance snapshots
                    elif event.id != eID.MAINTENANCE_SNAPSHOT:
                        data.events_system.append(event)

                # Headers - No longer used
                elif r_type == "H":
                    pass

                # Config - Update language for settings chart
                elif r_type == "C":

                    # Interpret raw data and generate appropriate event record
                    event = create_event_record(em, data, line, range_started, filename=filename)
                    if not event:
                        continue

                    # Update language
                    language = data.settings_all["94"]
                    for val in event.values:
                        if val.key == "94":
                            language.update("0", val, event.syn_time)

                # Unknown record type
                else:
                    em.log_warning("Unknown message type", ref_id=r_type, val=line[3])

                # Insert power off records
                if line[4] == ve.EventIDs.VENT_END:
                    power_off = power_off_event(em, data, line[1], line[2])
                    data.events_all.append(power_off)

                # ---------- Post Processing ----------- #

                # Applicability and settings history updates not needed after monitor records (excluding therapy states)
                if r_type != "M" or line[4] == eID.THERAPY_STATE:

                    # Update applicability after all data have been processed.
                    data.applicability_tracker.update_all()

                    # Update settings history
                    if report.range.data_start <= syn_time <= report.range.data_end:
                        data.settings_tracker.update_history(syn_time)

                # Diagnostics
                if syn_time >= report.range.data_start:
                    last_seq = line[0]

            # Handle record errors
            except Exception as e:
                message = "Error while reading data message"
                cat = e.cat if hasattr(e, "cat") else ve.ErrorCat.RECORD_ERROR
                sub_cat = e.sub_cat if hasattr(e, "sub_cat") else ve.ErrorSubCat.INTERNAL_ERROR
                em.log_error(ve.Programs.REPORTING, cat, sub_cat, message, e, rec_type)

        # Clear error line
        em.set_line(None)

        # Diagnostics
        if data.diag:
            print("  Last sequence in range:", last_seq)

        # Stop ventilator at final data point
        last_syn_data_time = min(last_syn_data_time, report.range.end)
        last_raw_data_time = min(last_raw_data_time, report.range.end)
        if tracker.oxygen.calendar.active and last_raw_data_time and last_syn_data_time:
            tracker.force_stop_therapy(last_raw_data_time, last_syn_data_time, Therapies.OXYGEN, last=True)
        if tracker.ventilator.calendar.active and last_raw_data_time and last_syn_data_time:
            tracker.force_stop_therapy(last_raw_data_time, last_syn_data_time, Therapies.VENTILATOR, last=True)

        # Stop active alarms
        evt = create_event_record(em, data, ["-1", dt_to_ts(last_raw_data_time), dt_to_ts(last_syn_data_time),
                                             "E", "6028", "12058", "0", "0"],
                                  range_started=True)
        data.alarms_tracker.stop_all(evt)

    # Catch processing errors
    except Exception as e:
        message = "Error while processing data messages"
        cat = e.cat if hasattr(e, "cat") else ve.ErrorCat.PROCESS_ERROR
        sub_cat = e.sub_cat if hasattr(e, "sub_cat") else ve.ErrorSubCat.INTERNAL_ERROR
        em.log_error(ve.Programs.REPORTING, cat, sub_cat, message, e)
