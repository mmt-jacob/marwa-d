#!/usr/bin/env python
"""
This report module accepts a data container object and a report definition object to produce a VOCSN Usage Report in
PDF format with customizable sections.

    Version Notes:
        1.0.0.0 - 07/21/2019 - Created from SAI Report Delivery System report formatting modules.
        1.0.0.1 - 07/28/2019 - Implemented Avenir font and added report sections.
        1.0.0.2 - 09/07/2019 - Added trend/calendar section.
        1.0.0.3 - 10/02/2019 - Added alarm_summary section.
        1.0.0.4 - 10/04/2019 - Added settings_summary section.
        1.0.0.5 - 10/05/2019 - Moved more processing functions here.
        1.0.1.0 - 10/15/2019 - Moved record processing here.
        1.0.1.1 - 10/18/2019 - Added alarm tracking at item-level iteration.
        1.0.1.2 - 10/20/2019 - Changed some arguments for event tracker.
        1.0.1.3 - 10/23/2019 - Modified inputs to work with report generator starter script.
        1.0.2.0 - 10/26/2019 - Adapted for integration with report_generator.py
        1.0.3.0 - 11/01/2019 - Restructured to inject VOCSN identifiers from data files.
        1.0.3.1 - 11/20/2019 - Disabled trend summary on one day report.
        1.0.4.0 - 11/29/2019 - Added therapy and alarm logs.
        1.0.4.1 - 12/05/2019 - Implemented patient reset.
        1.0.4.2 - 12/12/2019 - Moved to multiBuild method to support linking and page numbering.
        1.0.4.3 - 12/16/2019 - Added string definitions from file.
        1.0.4.4 - 12/20/2019 - Updated some comments.
        1.0.5.0 - 12/21/2019 - Added error management.
        1.0.5.1 - 01/03/2020 - Added time scan function.
        1.0.5.2 - 01/04/2020 - Moved error manager initialization to report generator.
        1.0.6.0 - 01/05/2020 - Integrated improved logging to file.
        1.0.6.1 - 01/12/2020 - Created an explicit reference allocation so it can't be skipped.
        1.0.7.0 - 01/16/2020 - Consolidated time and data scans into one function. Added diagnostic lines.
        1.0.7.1 - 03/29/2020 - Return tar and data references.

"""

__author__ = "John Dorian for Sai Systems Technologies"
__copyright__ = "Copyright 2019"
__version__ = "1.0.7.1"

# Built-in
from datetime import datetime

# VOCSN report sections
from reports.sections import cover
from reports.sections import event_log
from reports.sections import alarm_log
from reports.sections import config_log
from reports.sections import therapy_log
from reports.sections import alarm_summary
from reports.sections import trend_calendar
from reports.sections import monitor_details
from reports.sections import settings_summary

# VOCSN data modules
from modules.models import report as r
from modules.readers.tar import TarManager
from modules.models import vocsn_enum as ve
from modules.models import vocsn_data as vd
from reports.elements.general import set_refs
from modules.models.errors import ErrorManager
from reports.elements.templates import FormattedPage
from reports.elements.general import report_doc_setup
from modules.readers.settings import read_software_version

# VOCSN processing modules
from modules.processing.resource_loader import *
from modules.processing import line_reader as lr
from modules.processing.time import scan_time_data

# Report Constants
TITLE = "VOCSN Usage Report"
AUTHOR = "Ventec Life Systems"
DIR = ""


def _critical(em: ErrorManager):
    """ Check for abort condition. """
    crit = em.status == ve.ErrorLevel.CRITICAL
    if crit:
        print("Encountered critical error.")
    return crit


def usage_report(em: ErrorManager, report: r.Report, temp_dir: str, data_file: str, diag: bool = False):
    """
    Create a usage report in PDF format.
    :param em: Error manager.
    :param report: Report definitions.
    :param temp_dir: Temporary working directory.
    :param data_file: Tar file name/path.
    :param diag: Raises errors immediately for diagnostics.
    :return: Completed report path.
    """
    global START

    # Required return values
    out_file = None
    data = None
    tar = None

    # Prepare terminal notes
    START = datetime.utcnow()
    print("Generating report " + report.id)
    print("  Started: {}".format(START))

    # Top-level error handling
    try:

        # Global variables
        global DIR

        # Adapt to run environment (for testing reports independently from the main system)
        if not os.path.exists("resources"):
            DIR = "../"

        # Create VOCSN data container
        data = vd.VOCSNData(em, diag)

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
        TarManager(em, data, report, DIR, temp_dir, data_file, orig_hash=None)
        tar = data.tar_manager
        if _critical(em):
            return out_file, tar, data

        # Read VOCSN software version
        #   Set VOCSN unit identifiers from config record
        read_software_version(em, data, tar)
        if _critical(em):
            return out_file, tar, data

        # Check for version number
        #   Verify presence of config record
        #   Load settings from file
        #   Setup error level thresholds
        #   Create report range definition
        #   Disable unsupported report sections
        #   Set report language from config record
        #   Construct report range definitions
        lr.read_config(em, data, report, tar)
        if _critical(em):
            return out_file, tar, data

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
        if _critical(em):
            return out_file, tar, data

        # Initialize activity trackers
        data.init_trackers(em, report)
        if _critical(em):
            return out_file, tar, data

        # Set report and file name
        report.name = "Usage Report"
        date_str = "{:02d}-{:02d}-{}".format(report.start.month, report.start.day, report.start.year)
        time_str = "{:02d}-{:02d}".format(report.start.hour, report.start.minute)
        if report.label != "":
            out_file = "VOCSN {} Usage Report {} {} {} {}.pdf".format(report.label, data.sn, date_str, time_str,
                                                                      report.range.name)
        else:
            out_file = "VOCSN {} Usage Report {} {} {}.pdf".format(data.sn, date_str, time_str, report.range.name)

        # Read contents of each tar file
        #   Read one record at a time
        #   Performs CRC check
        #   Reloads metadata, applicability, and labels if version changes
        #   Process records to events
        #   Route events to data trackers
        lr.read_data_lines(em, data, report, tar)
        if _critical(em):
            return out_file, tar, data

        # Finish calculations
        #   Calculate monitor data averages and statistics
        data.finish_calcs()

        # Prepare ReportLab document
        #   Override BaseDocTemplate to insert VOCSN data object references to expose during document build
        #   Define page size and margins
        #   Set memory references used during the build process
        story = []
        filename = os.path.join(DIR, temp_dir, out_file)
        set_refs(data, report, DIR)
        doc = report_doc_setup(em, data, report, TITLE, AUTHOR, DIR, filename)
        if _critical(em):
            return out_file, tar, data

        # Catch report document errors
        try:

            # Generate report section
            sec = report.sections
            cover.cover_section(DIR, doc, report, data, story)
            if sec.trend_summary:
                trend_calendar.trend_calendar_section(em, DIR, doc, report, data, story)
            if sec.settings_summary:
                settings_summary.settings_summary_section(em, DIR, doc, report, data, story)
            if sec.alarm_summary:
                alarm_summary.alarm_summary_section(em, DIR, doc, report, data, story)
            if sec.monitor_details:
                monitor_details.monitor_details_section(em, DIR, doc, report, data, story)
            if sec.therapy_log:
                therapy_log.therapy_log_section(DIR, doc, report, data, story)
            if sec.alarm_log:
                alarm_log.alarm_log_section(em, DIR, doc, report, data, story)
            if sec.config_log:
                config_log.config_log_section(em, DIR, doc, report, data, story)
            if sec.event_log:
                event_log.event_log_section(em, DIR, doc, report, data, story)

            # Generate report
            #   Use custom page format with some footer content to capture page numbers where they are available.
            doc.multiBuild(story, canvasmaker=FormattedPage)

            # End lines
            print("Processed report " + report.id)
            print("  VOCSN SW Version:", data.version)

            # Diagnostics
            if diag:
                print("Interpreted Ranges")
                print("  Target Range: ", report.range.start, "-", report.range.end)
                print("   Valid Range: ", report.range.data_start, "-", report.range.data_end)

        # Handle report document errors
        except Exception as e:
            message = "Error during ReportLab document build process"
            em.log_error(ve.Programs.REPORTING, ve.ErrorCat.PROCESS_ERROR, ve.ErrorSubCat.INTERNAL_ERROR, message, e)

    # Catch errors
    except Exception as e:
        if diag:
            raise e
        message = "Caught top-level report error"
        em.log_error(ve.Programs.REPORTING, ve.ErrorCat.PROCESS_ERROR, ve.ErrorSubCat.INTERNAL_ERROR, message, e)

    # Return file name
    return out_file, tar, data
