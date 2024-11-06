#!/usr/bin/env python
"""
Consolidate all available data and return populated data containers.

    Version Notes:
        1.0.0.0  - 03/29/2020 - Created from with combined_log function.
        1.0.0.1  - 03/30/2020 - Moved to list assemblers in log record classes to populate csv fields.
        1.1.0.0  - 04/07/2020 - Rearranged files and changed the function of this file to return data container, not
                                generate a report.
        1.1.0.1  - 04/13/2020 - Added flags to tell MVR modules to adjust behavior for combined log.

"""

__author__ = "John Dorian for Sai Systems Technologies"
__copyright__ = "Copyright 2020"
__version__ = "1.1.0.1"

# Built-in modules
import os
import re
from datetime import datetime, timedelta

# VOCSN modules
from modules.models.report import Report
from modules.readers.tar import TarManager
from modules.models import vocsn_data as vd
from modules.models import vocsn_enum as ve
from modules.models.errors import ErrorManager
from modules.readers.sys_log import SlogParser
from modules.processing import line_reader as lr
from modules.readers.crash_log import CrashParser
from modules.readers.usage_mon import UsageParser
from modules.processing.time import scan_time_data
from modules.readers.dev_config import DevConfParser
from modules.readers.settings import read_software_version


def combine_data(work_dir: str, temp_dir: str, data_file: str, diag: bool = False):
    """
    Create a usage report in PDF format.
    :param work_dir: Working directory
    :param temp_dir: Temporary folder.
    :param data_file: Tar file name/path.
    :param diag: Raises errors immediately for diagnostics.
    :return: Completed report path.
    """

    # Variables
    start = datetime.utcnow()

    # Adapt to run environment (for testing reports independently from the main system)
    parent = 0
    while not os.path.exists(os.path.join(work_dir, "resources")) and parent < 5:
        print(os.path.join(work_dir, "resources"))
        work_dir += "../"
        parent += 1

    # Validate directory and data_file
    if not os.path.exists(os.path.join(work_dir, temp_dir)):
        raise Exception("Working directory not found.")
    if not os.path.exists(os.path.join(work_dir, temp_dir, data_file)):
        raise Exception("Input TAR file not found.")

    # Prepare terminal notes
    if diag:
        print("Processing TAR File " + data_file)
        print("  Started: {}".format(start))

    # Prepare error manager
    em = ErrorManager(
        program="Combined Log",
        filename="",
        diag=diag,
        ignore_crit=True)

    # Prepare dates and report data container
    hours = 99999   # Set to include all data
    date_parts = re.sub(r'[^0-9_]', '', data_file.split(os.sep)[-1]).split('_')
    batch, sn, date, time = [date_parts[i] for i in range(0, 4)]
    export_dt = end_dt = datetime(year=int(date[0:4]), month=int(date[4:6]), day=int(date[6:8]),
                                  hour=int(time[0:2]), minute=int(time[2:4]), second=int(time[4:6]))
    start_dt = end_dt - timedelta(hours=hours)
    report = Report(
        r_id="NO_REPORT",
        r_type=ve.ReportType.USAGE,
        start_dt=start_dt,
        duration=hours,
        export_dt=export_dt
    )

    # Create VOCSN data container and record list
    log_records = []
    vent_data = vd.VOCSNData(em, diag)

    # Read TAR file
    #   - Calculate MD5 hash and compare with hash from browser at time of upload - (Too slow in browser)
    #   Open TAR file
    #   Verify presence of data files
    #   Reorder batch files in case of rollover
    #   Search for last occurrence of a "C" config message for version number
    #   Validate VOCSN software version
    #   Load metadata, applicability, and labels based on initial VOCSN software version
    #   Read and validate presence of metadata in file
    #   Organize and index metadata
    TarManager(em, vent_data, report, work_dir, temp_dir, data_file, orig_hash=None, combo_log=True)
    tar = vent_data.tar_manager

    # Process batch data from TAR
    if diag:
        print("  Reading batch data")
    _process_batch_data(em, tar, report, vent_data)

    # Process log data from TAR
    if diag:
        print("  Reading log data")
    _process_log_data(em, tar, vent_data, log_records)

    # Return data
    return log_records, vent_data


def _process_batch_data(em: ErrorManager, tar: TarManager, report: Report, data: vd.VOCSNData):
    """
    Process ventilator data from batch files. Mimics same behavior in report script, without rendering a report.
    :param em:
    :param tar:
    :param report:
    :param data:
    :return:
    """

    # TODO: add robust error handling here

    # Read VOCSN software version
    #   Set VOCSN unit identifiers from config record
    read_software_version(em, data, tar)

    # Check for version number
    #   Verify presence of config record
    #   Load settings from file
    #   Setup error level thresholds
    #   Create report range definition
    #   Disable unsupported report sections
    #   Set report language from config record
    #   Construct report range definitions
    lr.read_config(em, data, report, tar)

    # Scan for time adjustments and data range restrictions
    #   Initialize time tracker
    #   Step through all records, adjusting for time changes
    #   Calculate offset used to align report to end time
    #   Identify:
    #     1) Power loss/time reset events
    #     2) Patent reset evens
    #     3) Data limits (earliest and latest records)
    #   Set data range to above three constraints
    scan_time_data(em, data, report, tar)

    # Initialize activity trackers
    data.init_trackers(em, report)

    # Read contents of each tar file
    #   Read one record at a time
    #   Performs CRC check
    #   Reloads metadata, applicability, and labels if version changes
    #   Process records to events
    #   Route events to data trackers
    lr.read_data_lines(em, data, report, tar, combo_log=True)

    # Finish calculations
    #   Calculate monitor data averages and statistics
    data.finish_calcs()


def _process_log_data(em: ErrorManager, tar: TarManager, data: vd.VOCSNData, records: list):
    """
    Consolidate all data sources into a combined log.
    :param em: Error manager.
    :param tar: Tar manager.
    :param data: VOCSN data container.
    :param records: List of combined log records.
    """

    # TODO: Robust error handling here

    # Add events from batch files
    records += data.events_all

    # Add monitor records
    records += data.monitors_log

    # Add system log files
    bin_data, file_index = tar.read_log_file_series(1)
    s_log = SlogParser(data, bin_data, file_index, 1)
    records += s_log.records
    bin_data, file_index = tar.read_log_file_series(2)
    s_log = SlogParser(data, bin_data, file_index, 2)
    records += s_log.records

    # Crash log
    bin_data = tar.read_bin_file(tar.crash_log)
    crash = CrashParser(em, data, bin_data)
    records += crash.records

    # Device config
    bin_data = tar.read_bin_file(tar.device_config)
    d_conf = DevConfParser(em, data, bin_data, tar.device_config)
    records += d_conf.records

    # Usage monitor
    bin_data = tar.read_bin_file(tar.usage_mon)
    u_mon = UsageParser(em, data, bin_data, tar.usage_mon)
    records += u_mon.records

    # Add warnings and errors from Multi-View system
    records += em.warnings
    records += em.errors

    # Sort by synthetic time
    records.sort(key=lambda rec: rec.syn_time or datetime(1900, 1, 1))
