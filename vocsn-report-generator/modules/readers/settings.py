#!/usr/bin/env python
"""
Functions for reading settings files.

    Version Notes:
        1.0.0.0 - 09/07/2019 - Created file with load_settings_by_ver.
        1.0.0.1 - 12/03/2019 - Capture most recent patient change event.
        1.0.0.2 - 12/21/2019 - Added software version reader. Added patient reset sequence number.
        1.0.0.3 - 01/01/2020 - Disabled error tracking during patient reset scan.
        1.0.0.4 - 01/16/2020 - Standardized data start procedure. Improved error handling during patient reset scan.
        1.0.0.5 - 01/22/2020 - Relocated settings files.
        1.0.0.6 - 02/01/2020 - Updated to new log format.
        1.0.1.0 - 02/17/2020 - Set data start to a day before the start of the report.
        1.0.1.1 - 03/12/2020 - Added a sequence-number-only flag to the data start set function.
        1.0.1.2 - 04/01/2020 - Added version-only update prior to parsing record to allow for simultaneous version/model
                               change in synthetic data.
        1.0.1.3 - 04/13/2020 - Added support for modifications needed for combined log.

"""

__author__ = "John Dorian for Sai Systems Technologies"
__copyright__ = "Copyright 2019"
__version__ = "1.0.1.3"

# Built-in modules
import os
import json
from datetime import datetime, timedelta

# VOCSN modules
from modules.models.report import Report
from modules.readers.tar import TarManager
from modules.models import vocsn_enum as ve
from modules.models.errors import ErrorManager
from modules.models.vocsn_data import VOCSNData
from modules.processing.events import create_event_record


def read_software_version(em: ErrorManager, data: VOCSNData, tar: TarManager):
    """ Read config line and set VOCSN software version. """

    # Catch errors
    try:

        # Convert config line to event record
        line_parts = tar.config_line

        # Load metadata for target version
        data.set_version_only(line_parts[4])

        # Store VOCSN software version and metadata-dependent identifiers
        event = create_event_record(em, data, line_parts)
        data.set_version(event)

    # Handle errors
    except Exception as e:
        message = "Error reading config line"
        em.log_error(ve.Programs.REPORTING, ve.ErrorCat.FILE_ERROR, ve.ErrorSubCat.INVALID_TAR, message, e)


def load_settings_by_ver(ver: str):
    """
    Load settings file that corresponds with a specified VOCSN software version.
    :param ver: VOCSN software version number.
    :return: Settings file loaded as JSON object.
    """

    # Construct expected file name
    fn = os.path.join("config", "settings", "settings_{}.json".format(ver))

    # Contextualize
    if not os.path.exists(fn):
        fn = os.path.join("..", fn)

    # Check that metadata file exists for version
    if not os.path.exists(fn):
        raise Exception("No settings file for version {}.".format(ver))

    # Access file
    with open(fn, 'r') as file:
        settings = json.load(file)
    return settings


def check_patient_start(em: ErrorManager, report: Report, data: VOCSNData, tar: TarManager):
    """
    Scan all data and identify the most recent patient reset record prior to processing stage.
    :param em: Error manager.
    :param report: Report definitions.
    :param data: VOCSN data container.
    :param tar: Tar file manager/data reader.
    """

    # Catch errors
    c_line = None
    try:

        # Variables and references
        started = False
        r = report.range
        tm = data.time_manager
        start_fence = (report.range.start - timedelta(hours=25)).timestamp()

        # Disable error tracking while handling potentially out-dated data
        em.disable_tracking()

        # Read all lines
        while tar.more_lines:
            line, _, _ = tar.read_line(em, silent=True)

            # Skip invalid lines
            if line and len(line) > 3:

                # Catch errors
                try:

                    # Check for user time change
                    tm.check_user_time_change(line)

                    # Check for power failure/device reset
                    tm.check_power_loss_reset(line)

                    # Set synthetic time
                    tm.set_synthetic_time(line)
                    c_line = line

                    # Check for patient change record
                    timestamp = int(line[2])
                    if line and line[4] == ve.EventIDs.PATIENT_CHANGE:

                        # Update the patient start time
                        seq = int(line[0])
                        dt = datetime.utcfromtimestamp(timestamp)
                        r.set_data_start(dt, seq)

                    # Set data processing start no earlier than a day before the report range (sequence only)
                    if timestamp >= start_fence and not started:
                        started = True
                        seq = int(line[0])
                        dt = datetime.utcfromtimestamp(timestamp)
                        r.set_data_start(dt, seq, seq_only=True)

                # Ignore individual errors at this state
                except Exception as e:
                    e.ignore = True

        # Disable error tracking while handling potentially out-dated data
        em.enable_tracking()

    # Handle errors
    except Exception as e:
        em.enable_tracking()
        message = "Error while processing patient reset event"
        em.log_error(ve.Programs.REPORTING, ve.ErrorCat.PROCESS_ERROR, ve.ErrorSubCat.INTERNAL_ERROR, message, e,
                     line=c_line)

    # Reset readers
    tar.reset()
    data.time_manager.reset()
