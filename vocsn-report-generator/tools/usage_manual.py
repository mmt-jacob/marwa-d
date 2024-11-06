#!/usr/bin/env python
"""
Run a usage report manually with specified file and options. Provides a command line entry point for the report.

    Version Notes:
        1.0.0.0 - 01/23/2020 - Created main with input file and duration options.

"""

__author__ = "John Dorian for Sai Systems Technologies"
__copyright__ = "Copyright 2019"
__version__ = "1.0.0.0"

# Built-in
import os
import re
import sys
import argparse
from shutil import move
from datetime import datetime, timedelta

# Contextualize
DIR = ".."
sys.path.append(DIR)

# VOCSN modules
from reports.usage import usage_report
from modules.models.report import Report
from modules.models import vocsn_enum as ve
from modules.models.errors import ErrorManager


if __name__ == "__main__":
    """
    Entry point from command line.

    Optional Parameters:
        input      (str): Path and file name of tar file to process.
        diag       (bool): Output log to console for diagnostics. Increases verbosity. Raises errors for debugging
        errors     (bool): Display all warnings and errors. Default is 7 days (168)
        period      (int): Report duration - Number of hours to run report.
        out_path    (str): Output directory. Default is /output
        help       (bool): Display help messages only.
    """

    # Define arguments and options
    parser = argparse.ArgumentParser(prog="Manual Usage Report", description="Generate a Usage Report from a tar file.")
    parser.add_argument('input', type=str, help='Input tar file path and name.')
    parser.add_argument('-d', '--diag', action='store_true', help="Output diagnostic information to stdout. Increases "
                                                                  "verbosity and number of warnings and errors "
                                                                  "displayed. Raises errors and tracebacks.")
    parser.add_argument('-e', '--errors', action='store_true', help="Display all warnings and errors.")
    parser.add_argument('-o', '--out_path', type=str, help="Specify output location. Default: /output")
    parser.add_argument('-p', '--period', type=int, help="(int) Report duration in hours. Options:\n" +
                                                         "1 Hour: (1) | " +
                                                         "3 Hours: (3) | " +
                                                         "6 Hours: (6) | " +
                                                         "12 Hours: (12) | " +
                                                         "1 Day: (24) | " +
                                                         "3 Days: (72) | " +
                                                         "7 Days: (168) | " +
                                                         "30 Days: (720) | " +
                                                         "60 Days: (1440) | " +
                                                         "90 Days: (2160) | " +
                                                         "180 Days: (4320) | " +
                                                         "Default: 168")

    # Process arguments and options
    a = parser.parse_args(sys.argv[1:])

    # Default values
    hours = 168
    duration = timedelta(hours=hours)
    out_path = "output"

    # Validate options
    if not a.input:
        print("An input file must be specified.")
        exit(1)
    try:
        if a.period:
            hours = int(a.period)
            if hours not in [1, 3, 6, 12, 24, 72, 168, 720, 1440, 2160, 4320]:
                raise Exception("Invalid report range")
            duration = timedelta(hours=hours)
    except Exception as e:
        invalid = e
        print("Please enter a valid report period.")
        exit(1)
    if a.out_path:
        check_path = os.path.join(DIR, a.out_path)
        if not os.path.exists(check_path):
            print("Specified output path does not exist.")
            exit(1)
        out_path = a.out_path

    # Prepare error management
    em = ErrorManager("Usage", "Manual", a.diag, a.errors)

    # Prepare dates
    file_name = a.input.split(os.sep)[-1]
    parts = re.sub(r'[a-zA-Z.]', '', file_name).split('_')
    _, _, date_str, time_str = parts[0:4]
    export_dt = datetime(year=int(date_str[0:4]),
                         month=int(date_str[4:6]),
                         day=int(date_str[6:8]),
                         hour=int(time_str[0:2]),
                         minute=int(time_str[2:4]))
    start_dt = export_dt - duration
    report_dt = datetime.utcnow()

    # Prepare report definition
    r_id = "Manual"
    r_type = ve.ReportType.USAGE
    report = Report(r_id, r_type, start_dt, hours, export_dt, report_date=report_dt)
    
    # Enable all report sections
    s = report.sections
    s.trend_summary = True
    s.settings_summary = True
    s.alarm_summary = True
    s.monitor_details = True
    s.therapy_log = True
    s.alarm_log = True
    s.config_log = True
    s.event_log = True

    # Prepare paths
    temp_path = os.path.join("temp", "manual")
    rel_temp_path = os.path.join(DIR, "temp", "manual")
    if not os.path.exists(rel_temp_path):
        os.makedirs(rel_temp_path)

    # Generate report
    file = usage_report(em, report, temp_path, a.input, a.diag)

    # Move file to output directory
    if file:
        rel_file = os.path.join(rel_temp_path, file)
        move(os.path.join(DIR, "output", rel_file), os.path.join(DIR, out_path, file))

    # Write session log
    em.write_log()

    # Cleanup
    os.rmdir(rel_temp_path)
