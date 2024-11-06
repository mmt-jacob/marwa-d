#!/usr/bin/env python
"""
The Generator interacts with the Ventec reporting system to manage reserving and updating an item from the report
queue, starting a report script, storing the report, and cleaning up the VM>

Note that stdout and stderr are automatically written to the log file.

    Version Notes:
        1.0.0.0 - 10/23/2019 - Created file based on the SAI Status Monitor.
        1.0.0.1 - 12/12/2019 - Renamed some sections.
        1.0.1.0 - 12/29/2019 - Adapted to new Usage arguments. Added section input from database.
        1.0.1.1 - 01/01/2020 - Sourced report date from input to allow for localization. Added safe read.
        1.0.2.0 - 01/05/2020 - Integrated error logging to file.
        1.0.2.1 - 01/06/2020 - Added error status fields to report records.
        1.0.2.2 - 10/16/2020 - Pass report export date.
        1.0.2.3 - 01/17/2020 - Adjusted print lines.
        1.0.2.4 - 01/22/2020 - Cleaned unused settings functions.
        1.1.0.0 - 01/24/2020 - Moved queue retrieval to daemon.
        1.1.0.1 - 01/27/2020 - Added production variable.
        1.1.1.0 - 01/30/2020 - Added database log upload.
        1.1.2.0 - 02/13/2020 - Moved report generator settings to .env file.
        1.1.2.1 - 03/11/2020 - Added queue time.
        1.1.2.2 - 03/31/2020 - Recalculate start time from end time to ensure consistency with web app.

"""

__author__ = "John Dorian for Sai Systems Technologies"
__copyright__ = "Copyright 2018"
__version__ = "1.1.2.2"

# Built-in
import os
import sys
import json
import shutil
import string
import random
import socket
from datetime import datetime, timedelta

# Companion Python files
from config import config
from modules.models.report import Report
from modules.models import vocsn_enum as ve
from modules.models.errors import ErrorManager
from modules.shared import status as status_script
from modules.models.vocsn_enum import Sections, ErrorLevel
from modules.processing.utilities import safe_read, dt_to_ts

# Reports
from reports.usage import usage_report

# Azure library
from azure.cosmosdb.table import TableService, Entity
from azure.storage.file import FileService, ContentSettings

global DIAG


def build_reports(queue_item: Entity, prod: bool, diag: bool):
    """
    Main section.
    -------------
    :param queue_item: Report queue item.
    :param prod: If true, use production credentials.
    :param diag: Print diagnostic lines.
    :return: [status result, error detail]

    Perform these tasks:
      - Reserve the queue item/report.
      - Download the associated data file to the VM.
      - Process report.
      - Upload completed report to file storage.
      - Update queued report as complete.
      - Clean up files on VM.
    """

    global DIAG

    # Queue item required
    if not queue_item:
        return

    # ------ Setup ------ #

    DIAG = diag
    abort = False
    report_file = None
    report_path = None
    report_id = queue_item.ReportID
    temp_dir = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    em = ErrorManager("Report Generator", "R" + temp_dir, DIAG)

    # Initialize status/error manager
    status = status_script.StatusMonitorTracker()
    status.start_time = datetime.utcnow()

    # Diagnostic output
    d_print("-----------------------")
    d_print("-   Report Generator  -")
    if diag:
        d_print("-  (Diagnostic Mode)  -")
    d_print("-----------------------" + "\n")

    # Load Azure credentials from file. Create table service instance.
    # Note: Does not create log file at this point because if offline it could generate one log a second.
    try:
        table_service, file_service, settings = read_settings(prod, status)
    except Exception as e:
        message = "Failed to load settings"
        em.log_error(ve.Programs.REPORTING, ve.ErrorCat.FILE_ERROR, ve.ErrorSubCat.INTERNAL_ERROR, message, e)
        em.print_status()
        return

    # ----- Gather information needed to run report ----- #

    # Check reserve the provided queue item and report
    reserved, err = reserve_report(em, queue_item, table_service)
    if not reserved and not err:
        return  # No records to process
    if err or not queue_item:
        if queue_item:
            del_queue(em, table_service, queue_item)
            em.record = queue_item.PartitionKey
        store_log(em, table_service, report_id)
        return
    em.record = em.filename = queue_item.ReportID

    # Build report definitions
    report_def, report_entity, err = create_report_def(em, table_service, queue_item, status)
    if err:
        if report_entity:
            set_error(em, table_service, report_entity, queue_item)
        store_log(em, table_service, report_id)
        return

    # Copy file to local VM storage
    temp_dir, temp_file, err = get_raw_data(em, table_service, file_service, report_entity, temp_dir)
    if err and report_entity:
        set_error(em, table_service, report_entity, queue_item)
        store_log(em, table_service, report_id)
        return

    # ----- Generate report - Combined log will be attempted no matter what past this point. ----- #

    # Start processing report
    try:
        # Performance profiling
        # # import cProfile
        # # cProfile.runctx('usage_report(em, report_def, temp_dir, temp_file, diag)', globals(), locals())
        # # exit()
        report_file, tar, data = usage_report(em, report_def, temp_dir, temp_file, diag)
    except Exception as e:
        message = "Encountered an unhandled error while processing a report"
        em.log_error(ve.Programs.REPORT_GEN, ve.ErrorCat.PROCESS_ERROR, ve.ErrorSubCat.INTERNAL_ERROR, message, e)
    if em.status == ErrorLevel.CRITICAL:
        abort = True
        print("Error: Encountered an error while processing a report")
        set_error(em, table_service, report_entity, queue_item)
        # store_log(em, table_service, report_id)

    # ----- Upload report results ----- #

    # Place report in storage account
    if not abort:
        d_print("Uploading report")
        report_path, err = upload_report(em, file_service, report_def, temp_dir, report_file)
        if err and report_entity:
            abort = True
            set_error(em, table_service, report_entity, queue_item)
            # store_log(em, table_service, report_id)

    # Update database records
    if report_path and not abort:
        d_print("Updating database records")
        err = update_tables(em, table_service, report_path, report_file, queue_item, report_entity, status)
        if err and report_entity:
            set_error(em, table_service, report_entity, queue_item)

    # ----- Cleanup ----- #

    # Log results and exit
    clean_vm(em, temp_dir)

    # Write session log
    store_log(em, table_service, report_id)


def d_print(message: str):
    """ Print if DIAG specified. """
    global DIAG
    if DIAG:
        print(message)


def store_log(em: ErrorManager, table_service: TableService, report_id: str):
    """
    Store error log lines in local files and database.
    :param em: Error manager.
    :param table_service: Azure tableservice.
    :param report_id: Report ID.
    """

    # Write log to file
    em.write_log()

    # Write log to database
    em.upload_log(table_service, "ReportLog", report_id)


def set_error(em: ErrorManager, table_service: TableService, report_ent: Entity, queue_ent: Entity):
    """
    Set batch record to error state on error.
    :param em: Error manager.
    :param table_service: Azure table service handler.
    :param report_ent: Batch record entity.
    :param queue_ent: Batch record entity.
    """
    d_print("  ERROR: Removing broken batch record.")
    try:
        report_ent.Status = ve.ProcessingState.ERROR.value
        report_ent.ErrorLevel = em.status.value
        etag = report_ent.etag
        report_ent.etag = table_service.update_entity("Reports", report_ent, if_match=etag)
        del_queue(em, table_service, queue_ent)
    except Exception as e:
        message = "Attempt to remove problematic batch queue record failed"
        em.log_error(ve.Programs.REPORT_GEN, ve.ErrorCat.RECORD_ERROR, ve.ErrorSubCat.DB_ERROR, message, e)


def del_queue(em: ErrorManager, table_service: TableService, queue_ent: Entity):
    """
    To prevent process looping, delete queues on error.
    :param em: Error manager.
    :param table_service: Azure table service handler.
    :param queue_ent: Batch record entity.
    """
    d_print("  ERROR: Removing broken batch queue item.")
    try:
        partition_key = queue_ent.PartitionKey
        row_key = queue_ent.RowKey
        table_service.delete_entity("ReportQueue", partition_key, row_key)
    except Exception as e:
        message = "Attempt to remove problematic batch queue record failed"
        em.log_error(ve.Programs.REPORT_GEN, ve.ErrorCat.RECORD_ERROR, ve.ErrorSubCat.DB_ERROR, message, e)


def read_settings(prod: bool, status: status_script.StatusMonitorTracker) -> tuple:
    """
    Get Azure credentials, setup table service instance, and read settings.
    :param prod: If true, use production credentials.
    :param status: Error manager.
    :return: TableService instance, timeout times (object), last record time, list of email contacts for errors,
             list of email contacts for faults, list of sms contacts for faults.
    """

    # Output action to log and console in diagnostic mode.
    d_print("Loading settings")

    # ---------- Critical Settings ---------- #

    # Read credentials from file
    d_print("  Loading Azure credentials")
    result, credentials, settings = config.get_azure_credentials(prod)

    # Error Check
    if result.has_error:
        status.add_error(result.message, True)

    # Create table service instance
    table_service = TableService(account_name=credentials['account'], account_key=credentials['key'])
    file_service = FileService(account_name=credentials['account'], account_key=credentials['key'])
    return table_service, file_service, settings


def reserve_report(em: ErrorManager, queue_item: Entity, table_service: TableService):
    """
    Reserve the report for processing.
    :param em: Error manager.
    :param queue_item: Report queue entity.
    :param table_service: Azure table service.
    """

    # Variables
    table = "ReportQueue"

    # Override err out to suppress Azure messages
    sys.stderr = open(os.devnull, 'w')

    # Reserve queue item by marking it as processing
    # Use concurrency check to ensure only one generator gets the item
    # Abort processing if record cannot be locked
    try:
        d_print("  Reserving report queue item.")
        queue_item.Status.value = ve.ProcessingState.PROCESSING.value
        queue_item.StartDT = dt_to_ts(datetime.utcnow())
        etag = queue_item.etag
        table_service.update_entity(table, queue_item, if_match=etag)
    except Exception as e:
        if "Precondition Failed" in str(e):
            return False, False
        message = "Unable to reserve report queue record"
        em.log_error(ve.Programs.REPORT_GEN, ve.ErrorCat.RECORD_ERROR, ve.ErrorSubCat.DB_ERROR, message, e)
        sys.stderr = sys.__stderr__
        return False, True

    # Restore error output
    sys.stderr = sys.__stderr__

    # Return report entity
    return True, False


def create_report_def(em: ErrorManager, table_service: TableService, queue_item: Entity,
                      status: status_script.StatusMonitorTracker):
    """
    Retrieve report details from Reports table and construct a report definition.
    :param em: Error manager.
    :param table_service: Azure table service.
    :param queue_item: Report queue item.
    :param status: Report status tracker.
    :return: Report definition.
    """

    # Return values
    report_ent = None
    report_def = None

    # Catch errors
    try:

        # Request report details from database
        d_print("Getting report details")
        sn = queue_item.PartitionKey
        report_id = queue_item.ReportID
        table = "Reports"
        filters = "PartitionKey eq '{}' and RowKey eq '{}'".format(sn, report_id)
        result = table_service.query_entities(table, filters)
        report_ent = result.items[0]

        # Update report status to "Processing"
        report_ent.Status.value = ve.ProcessingState.PROCESSING.value
        table_service.update_entity(table, report_ent)

        # Get update etag back from database
        result = table_service.query_entities(table, filters)
        report_ent = result.items[0]

        # Read report detail values
        duration = safe_read(report_ent.ReportHours)
        dur_td = timedelta(hours=duration)
        end_dt = datetime.utcfromtimestamp(safe_read(report_ent.ReportEnd))
        start_dt = end_dt - dur_td
        export_dt = datetime.utcfromtimestamp(safe_read(report_ent.ExportDT))

        # Build report definition
        d_print("  Building report definitions.")
        report_type = getattr(ve.ReportType, report_ent.ReportType.upper())
        try:
            report_date = datetime.utcfromtimestamp(safe_read(report_ent.ReportDate))
        except (AttributeError, TypeError):
            report_date = datetime.utcnow()
        label = safe_read(report_ent.Label) if hasattr(report_ent, "Label") else ""
        institute = None
        physician = None
        patient = None
        notes = None
        report_def = Report(report_id, report_type, start_dt, duration, export_dt, institute, physician, patient, notes,
                            report_date, label=label)
        report_def.account = report_ent.AccountID   # TODO: Route account info from DB table when available
        
        # Set sections
        section_def = report_def.sections
        sections = json.loads(report_ent.Sections)
        for idx in sections:
            section = Sections[idx]
            if hasattr(section_def, section):
                setattr(section_def, section, True)

        # Capture queue start time
        if hasattr(report_ent, "QueueDT"):
            status.queue_time = datetime.utcfromtimestamp(safe_read(report_ent.QueueDT))

    # Handle errors
    except Exception as e:
        message = "Error while reading details from report table"
        em.log_error(ve.Programs.REPORT_GEN, ve.ErrorCat.RECORD_ERROR, ve.ErrorSubCat.DB_ERROR, message, e)
        return report_def, report_ent, True

    return report_def, report_ent, False


def get_raw_data(em: ErrorManager, table_service: TableService, file_service: FileService, report_ent: Entity,
                 temp_dir: str):
    """
    Get data file information from database and copy file to local working directory.
    :param em: Error manager.
    :param table_service: Azure table service.
    :param file_service: Azure file service.
    :param report_ent: Report details from database.
    :param temp_dir: Temporary directory.
    :return: [Temporary local directory, file name]
    """

    # Catch errors
    d_print("Get data file for processing")
    try:

        # Request data file details from database
        d_print("  Looking up file details")
        sn = report_ent.PartitionKey
        data_file_id = report_ent.DataFileID
        table = "DataFiles"
        filters = "PartitionKey eq '{}' and RowKey eq '{}'".format(sn, data_file_id)
        result = table_service.query_entities(table, filters)
        report_ent = result.items[0]

        # Read data file detail values
        file_path = report_ent.FilePath[1:]
        file_name = report_ent.FileName

        # Create temporary local directory
        d_print("  Creating working directory")
        attempts = 0
        making_dir = True
        if not os.path.exists("temp"):
            os.mkdir("temp")
        while making_dir:
            attempts += 1
            try:
                temp_dir = os.path.join("temp", temp_dir)
                if not os.path.exists(temp_dir):
                    os.mkdir(temp_dir)
                    making_dir = False
            except Exception as e:
                if attempts > 10:
                    raise e

        # Copy file from file service to local storage
        d_print("  Downloading data file")
        share = "vocsn-data"
        destination = os.path.join(temp_dir, file_name)
        file_service.get_file_to_path(share, file_path, file_name, destination)

        # Eventually we could check file integrity here

    # Handle errors
    except Exception as e:
        message = "Failed to copy data file from file storage"
        em.log_error(ve.Programs.REPORT_GEN, ve.ErrorCat.FILE_ERROR, ve.ErrorSubCat.DB_ERROR, message, e)
        return temp_dir, None, True

    return temp_dir, file_name, False


def upload_report(em: ErrorManager, file_service: FileService, report: Report, temp_dir: str, report_file: str):
    """
    Upload completed report to permanent storage.
    :param em: Report error manager.
    :param file_service: Azure file service.
    :param report: Report definition.
    :param temp_dir: Temporary working directory
    :param report_file: Completed report file.
    """

    # Override err out to suppress Azure messages
    sys.stderr = open(os.devnull, 'w')

    # Catch errors
    d_print("Uploading report to file storage")
    try:

        # Create directory for file
        share = "vocsn-reports"
        report_dt = report.report_date
        source_path = os.path.join(temp_dir, report_file)
        paths = [report_dt.year, "{:02d}".format(report_dt.month), "{:02d}".format(report_dt.day)]
        directory = ""
        for idx, path in enumerate(paths):
            if directory != "":
                directory += "/"
            directory += str(paths[idx])
            file_service.create_directory(share, directory)

        # Request data file details from database
        file_service.create_file_from_path(share, directory, report_file, source_path,
                                           content_settings=ContentSettings(content_type='application/pdf'))

    # Handle errors
    except Exception as e:
        message = "Report upload failed"
        em.log_error(ve.Programs.REPORT_GEN, ve.ErrorCat.FILE_ERROR, ve.ErrorSubCat.DB_ERROR, message, e)
        sys.stderr = sys.__stderr__
        return None, True

    # Restore err out
    sys.stderr = sys.__stderr__

    # Return file storage path
    return directory, False


def update_tables(em: ErrorManager, table_service: TableService, report_path: str, report_name: str, queue_item: Entity,
                  report_entity: Entity, run_status):
    """
    Update information in database.
    :param em: Report error manager.
    :param table_service: Azure table service.
    :param report_path: Directory in file storage.
    :param report_name: Completed report file name.
    :param queue_item, Queue entity.
    :param report_entity: Report entity.
    :param run_status: Status tracker.
    :return:
    """

    # Catch errors
    d_print("Updating database")
    try:

        # Determine status
        if not em or em.status == ve.ErrorLevel.CRITICAL:
            status = ve.ProcessingState.ERROR.value
            report_path = ""
            report_name = ""
        else:
            status = ve.ProcessingState.COMPLETED.value
        run_time = round((datetime.utcnow() - run_status.start_time).total_seconds(), 2)
        queue_time = None
        if run_status.queue_time:
            queue_time = round((run_status.start_time - run_status.queue_time).total_seconds(), 2)

        # Update Report record
        d_print("  Updating Report record")
        table = "Reports"
        report_entity.FilePath = report_path
        report_entity.FileName = report_name
        report_entity.Status.value = status
        report_entity.ErrorLevel = em.status.value
        report_entity.RunTime = run_time
        report_entity.QueueTime = queue_time
        report_entity.ProcessedBy = socket.gethostname()
        etag = report_entity.etag
        table_service.update_entity(table, report_entity, if_match=etag)

        # Delete report queue
        d_print("  Removing report queue entry")
        table = "ReportQueue"
        partition_key = queue_item.PartitionKey
        row_key = queue_item.RowKey
        table_service.delete_entity(table, partition_key, row_key)

    # Handle errors
    except Exception as e:
        message = "Final report table status updates failed"
        em.log_error(ve.Programs.REPORT_GEN, ve.ErrorCat.RECORD_ERROR, ve.ErrorSubCat.DB_ERROR, message, e)
        return True

    # Success
    return False


def clean_vm(em: ErrorManager, temp_dir: str):
    """ Remove temporary files. """
    d_print("Removing temporary files")
    try:
        shutil.rmtree(temp_dir)
    except Exception as e:
        message = "Unable to remove temporary files."
        em.log_error(ve.Programs.REPORT_GEN, ve.ErrorCat.BACKEND_ERROR, ve.ErrorSubCat.OS_ERROR, message, e)
