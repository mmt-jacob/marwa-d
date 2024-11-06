#!/usr/bin/env python
"""
The Download Manager checks the database for batch download requests in the BatchQueue table. If found, it reserves the
job, downloads the requested reports, bundles them into a ZIP file, uploads it to Azure, and marks the job as complete.

    Version Notes:
        1.0.0.0 - 12/30/2019 - Created file based on the report_generator.
        1.0.0.1 - 01/01/2020 - Added safe read function.
        1.0.1.0 - 01/04/2020 - Improved error handling
        1.0.1.1 - 01/15/2020 - Added request date to queue item.
        1.0.1.2 - 01/20/2020 - Added protection against invalid queue items.
        1.0.1.3 - 01/22/2020 - Cleaned unused settings functions.
        1.1.0.0 - 01/24/2020 - Moved queue retrieval to daemon.
        1.1.1.0 - 01/30/2020 - Added database log upload.
        1.1.2.0 - 02/13/2020 - Moved report generator settings to .env file.

"""

__author__ = "John Dorian for Sai Systems Technologies"
__copyright__ = "Copyright 2018"
__version__ = "1.1.2.0"

# Built-in
import os
import sys
import json
import shutil
import string
import random
import zipfile
from datetime import datetime

# Companion Python files
from config import config
from modules.models import vocsn_enum as ve
from modules.models.errors import ErrorManager
from modules.shared import status as status_script

# Azure library
from azure.cosmosdb.table import TableService, Entity
from azure.storage.file import FileService, ContentSettings

DIAG = None


def build_batch(queue_item: Entity, prod: bool, diag: bool):
    """
    Main section.
    -------------
    :param queue_item: Batch queue item.
    :param prod: If true, use production credentials.
    :param diag: Print diagnostic lines.
    :return: [status result, error detail]

    Perform these tasks:
      - Reserve the queue item/batch.
      - Download the requested report files to the VM.
      - Zip the files.
      - Upload zip file to file storage.
      - Update queued report as complete.
      - Clean up files on VM.
    """

    global DIAG

    # Queue item required
    if not queue_item:
        return

    # ------ Setup ------ #

    DIAG = diag
    batch_id = queue_item.RowKey
    temp_dir = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    em = ErrorManager("Download Manager", "B" + temp_dir, diag)

    # Initialize status/error manager
    status = status_script.StatusMonitorTracker()
    status.start_time = datetime.now()

    # Diagnostic output
    d_print("-----------------------")
    d_print("-   Download Manager  -")
    if diag:
        d_print("-  (Diagnostic Mode)  -")
    d_print("-----------------------" + "\n")

    # Load Azure credentials from file. Create table service instance.
    # Note: Does not create log file at this point because if offline it could generate one log a second.
    try:
        table_service, file_service, settings = read_settings(prod, status)
    except Exception as e:
        message = "Failed to load settings"
        em.log_error(ve.Programs.FILE_MAN, ve.ErrorCat.FILE_ERROR, ve.ErrorSubCat.INTERNAL_ERROR, message, e)
        em.print_status()
        return

    # ----- Gather information needed to bundle reports ----- #

    # Check batch queue and pick a request
    reserved, err = reserve_batch(em, queue_item, table_service)
    if not reserved and not err:
        return  # No records to process
    if err or not queue_item:
        if queue_item:
            del_queue(em, table_service, queue_item)
            em.record = queue_item.PartitionKey
        store_log(em, table_service, batch_id)
        return
    em.record = em.filename = queue_item.RowKey

    # Copy files to local VM storage
    #   Updates progress in database
    print("Assembling batch file", queue_item.RowKey)
    batch_ent, temp_dir, temp_files, err = get_reports(em, table_service, file_service, queue_item, temp_dir)
    if err:
        if batch_ent:
            set_error(em, table_service, batch_ent, queue_item)
        store_log(em, table_service, batch_id)
        return

    # ----- Bundle reports ----- #

    # Start bundling reports
    zip_file, err = bundle_reports(em, temp_dir, temp_files, batch_ent)
    if err and batch_ent:
        set_error(em, table_service, batch_ent, queue_item)
        store_log(em, table_service, batch_id)
        return

    # ----- Upload and cleanup ----- #

    # Place zip in storage account
    zip_path, err = upload_zip(em, table_service, file_service, temp_dir, zip_file, batch_ent)
    if err and batch_ent:
        set_error(em, table_service, batch_ent, queue_item)
        store_log(em, table_service, batch_id)
        return

    # Update database records
    err = update_tables(em, table_service, zip_path, zip_file, queue_item, batch_ent)
    if err and batch_ent:
        set_error(em, table_service, batch_ent, queue_item)

    # Log results and exit
    clean_vm(em, temp_dir)

    # Write session log
    print("Batch file complete.")
    store_log(em, table_service, batch_id)


def d_print(message: str):
    """ Print if DIAG specified. """
    global DIAG
    if DIAG:
        print(message)


def store_log(em: ErrorManager, table_service: TableService, batch_id: str):
    """
    Store error log lines in local files and database.
    :param em: Error manager.
    :param table_service: Azure tableservice.
    :param batch_id: Batch ID.
    """

    # Write log to file
    em.write_log()

    # Write log to database
    em.upload_log(table_service, "BatchLog", batch_id)


def set_error(em: ErrorManager, table_service: TableService, batch_ent: Entity, queue_ent: Entity):
    """
    Set batch record to error state on error.
    :param em: Error manager.
    :param table_service: Azure table service handler.
    :param batch_ent: Batch record entity.
    :param queue_ent: Batch record entity.
    """
    d_print("  ERROR: Removing broken batch record.")
    try:
        batch_ent.Status = ve.ProcessingState.ERROR.value
        batch_ent.ErrorLevel = em.status.value
        etag = batch_ent.etag
        batch_ent.etag = table_service.update_entity("Batches", batch_ent, if_match=etag)
        del_queue(em, table_service, queue_ent)
    except Exception as e:
        message = "Attempt to remove problematic batch queue record failed"
        em.log_error(ve.Programs.FILE_MAN, ve.ErrorCat.RECORD_ERROR, ve.ErrorSubCat.DB_ERROR, message, e)


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
        table_service.delete_entity("BatchQueue", partition_key, row_key)
        print("Warning: Encountered invalid batch queue item. Deleting record.")
    except Exception as e:
        message = "Attempt to remove problematic batch queue record failed"
        em.log_error(ve.Programs.FILE_MAN, ve.ErrorCat.RECORD_ERROR, ve.ErrorSubCat.DB_ERROR, message, e)


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


def reserve_batch(em: ErrorManager, queue_item: Entity, table_service: TableService):
    """
    Check the database for unprocessed batch requests in the batch queue.
    :param em: Error Manager.
    :param queue_item: Batch queue entity.
    :param table_service: Azure table service.
    :return: Reserved batch entity.
    """

    # Variables
    table = "BatchQueue"

    # Override err out to suppress Azure messages
    sys.stderr = open(os.devnull, 'w')

    # Reserve queue item by marking it as processing
    # Use concurrency check to ensure only one manager gets the item
    # Abort processing if record cannot be locked
    try:
        d_print("  Reserving batch queue item.")
        queue_item.Status.value = ve.ProcessingState.PROCESSING.value
        queue_item.StartDT = datetime.utcnow().timestamp()
        etag = queue_item.etag
        table_service.update_entity(table, queue_item, if_match=etag)
    except Exception as e:
        if "Precondition Failed" in str(e):
            return False, False
        message = "Unable to reserve batch queue record"
        em.log_error(ve.Programs.FILE_MAN, ve.ErrorCat.RECORD_ERROR, ve.ErrorSubCat.DB_ERROR, message, e)
        sys.stderr = sys.__stderr__
        return False, True

    # Restore error output
    sys.stderr = sys.__stderr__

    # Return report entity
    return True, False


def get_reports(em: ErrorManager, table_service: TableService, file_service: FileService, queue_ent: Entity,
                temp_dir: str):
    """
    Download requested reports to be bundled.
    :param em: Error manager.
    :param table_service: Azure table service.
    :param file_service: Azure file service.
    :param queue_ent: Batch queue request details from database.
    :param temp_dir: Temporary directory.
    :return: [Temporary local directory, file names]
    """

    # Variables
    file_names = []
    batch_ent = None

    # Catch errors
    d_print("Get batch record for processing")
    try:

        # Request batch details from database
        d_print("  Looking up batch details")
        session_id = queue_ent.PartitionKey
        batch_id = queue_ent.RowKey
        table = "Batches"
        filters = "PartitionKey eq '{}' and RowKey eq '{}'".format(session_id, batch_id)
        result = table_service.query_entities(table, filters)

        # No records
        if len(result.items) == 0:
            return

        # Update status in batch record
        batch_ent = result.items[0]
        sn_list = json.loads(batch_ent.SNList)
        report_list = json.loads(batch_ent.ReportIDList)
        target = len(sn_list) + 2
        progress = 1 / target
        batch_ent.Status = ve.ProcessingState.PROCESSING.value
        batch_ent.Progress = progress
        etag = batch_ent.etag
        batch_ent.etag = table_service.update_entity("Batches", batch_ent, if_match=etag)

        # Create temporary local directory
        d_print("  Creating working directory")
        attempts = 0
        making_dir = True
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

        # Download each report
        for x in range(0, len(sn_list)):

            # Read report detail values
            sn = sn_list[x]
            report_id = report_list[x]

            # Get report details
            table = "Reports"
            filters = "PartitionKey eq '{}' and RowKey eq '{}'".format(sn, report_id)
            result = table_service.query_entities(table, filters)
            report_ent = result.items[0]

            # Ensure unique file name
            file_path = report_ent.FilePath
            file_name = local_file_name = report_ent.FileName
            i = 0
            parts = file_name.split('.')
            while os.path.exists(os.path.join(temp_dir, local_file_name)):
                local_file_name = "{} ({}).{}".format(parts[0], i, parts[-1])
                i += 1
            destination = os.path.join(temp_dir, local_file_name)

            # Copy file from file service to local storage
            d_print("  Downloading report: {}".format(report_id))
            share = "vocsn-reports"
            file_service.get_file_to_path(share, file_path, file_name, destination)
            file_names.append(local_file_name)

            # Update processing progress
            progress = (x + 1) / target
            batch_ent.Progress = progress
            etag = batch_ent.etag
            batch_ent.etag = table_service.update_entity("Batches", batch_ent, if_match=etag)

            # Eventually we could check file integrity here

    # Handle errors
    except Exception as e:
        message = "Failed to copy report files from file storage"
        em.log_error(ve.Programs.FILE_MAN, ve.ErrorCat.FILE_ERROR, ve.ErrorSubCat.OS_ERROR, message, e)
        return batch_ent, None, None, True

    return batch_ent, temp_dir, file_names, False


def bundle_reports(em: ErrorManager, temp_dir: str, report_files: list, batch_ent: Entity):
    """
    Bundle report files into zip archive.
    :param em: Error manager.
    :param temp_dir: Temporary folder.
    :param report_files: List of report file names.
    :param batch_ent: Batch request entity.
    :return: Zip filename.
    """

    # Catch errors
    try:

        # Construct zip file
        d_print("Bundling files")
        zip_name = "{}.zip".format(batch_ent.RowKey)
        file_name = os.path.join(temp_dir, zip_name)
        with zipfile.ZipFile(file_name, 'w', zipfile.ZIP_DEFLATED) as zip_file:

            # Add multiple files to the zip
            for file in report_files:
                file_path = os.path.join(temp_dir, file)
                zip_file.write(file_path, file)

            # Return zip file name
            return zip_name, False

    # Handle errors
    except Exception as e:
        message = "Unable to zip report files"
        em.log_error(ve.Programs.FILE_MAN, ve.ErrorCat.FILE_ERROR, ve.ErrorSubCat.OS_ERROR, message, e)
        return None, True


def upload_zip(em: ErrorManager, table_service: TableService, file_service: FileService, temp_dir: str, zip_file: str,
               batch_ent: Entity):
    """
    Upload completed zip file to permanent storage.
    :param em: Error manager.
    :param table_service: Azure table service.
    :param file_service: Azure file service.
    :param temp_dir: Temporary working directory
    :param zip_file: Zip file name
    :param batch_ent: Batch entity from database.
    """

    # Override err out to suppress Azure messages
    directory = None
    sys.stderr = open(os.devnull, 'w')

    # Catch errors
    d_print("Uploading zip file to file storage")
    try:

        # Create directory for file
        share = "vocsn-batches"
        batch_dt = datetime.fromtimestamp(batch_ent.RequestDT.value)
        source_path = os.path.join(temp_dir, zip_file)
        paths = [batch_dt.year, "{:02d}".format(batch_dt.month), "{:02d}".format(batch_dt.day)]
        directory = ""
        for idx, path in enumerate(paths):
            if directory != "":
                directory += "/"
            directory += str(paths[idx])
            file_service.create_directory(share, directory)

        # Request data file details from database
        file_service.create_file_from_path(share, directory, zip_file, source_path,
                                           content_settings=ContentSettings(content_type='application/zip'))

    # Handle errors
    except Exception as e:
        message = "Zip upload failed"
        em.log_error(ve.Programs.FILE_MAN, ve.ErrorCat.FILE_ERROR, ve.ErrorSubCat.DB_ERROR, message, e)
        sys.stderr = sys.__stderr__
        return directory, True

    # Restore err out
    sys.stderr = sys.__stderr__

    # Update processing progress
    try:
        sn_list = json.loads(batch_ent.SNList)
        reports = len(sn_list)
        table = "Batches"
        progress = (reports + 1) / (reports + 2)
        batch_ent.Progress = progress
        etag = batch_ent.etag
        batch_ent.etag = table_service.update_entity(table, batch_ent, if_match=etag)

    # Non-essential function, ignore
    except Exception as e:
        message = "Unable to update processing progress"
        em.log_error(ve.Programs.FILE_MAN, ve.ErrorCat.RECORD_ERROR, ve.ErrorSubCat.DB_ERROR, message, e)
        return None, True

    # Return file storage path
    return directory, False


def update_tables(em: ErrorManager, table_service: TableService, zip_path: str, zip_name: str, queue_ent: Entity,
                  batch_ent: Entity):
    """
    Update information in database.
    :param em: Error manager.
    :param table_service: Azure table service.
    :param zip_path: Directory in file storage.
    :param zip_name: Completed zip file name.
    :param queue_ent, Queue entity.
    :param batch_ent: Batch entity.
    """

    # Catch errors
    d_print("Updating database")
    try:

        # Determine status
        if not zip_path:
            status = ve.ProcessingState.ERROR.value
        else:
            status = ve.ProcessingState.COMPLETED.value

        # Update batch record
        d_print("  Updating batch record")
        table = "Batches"
        batch_ent.FilePath = zip_path
        batch_ent.FileName = zip_name
        batch_ent.Status = status
        batch_ent.Progress = 1
        batch_ent.ErrorLevel = em.status.value
        etag = batch_ent.etag
        table_service.update_entity(table, batch_ent, if_match=etag)

        # Delete batch queue
        d_print("  Removing batch queue entry")
        table = "BatchQueue"
        partition_key = queue_ent.PartitionKey
        row_key = queue_ent.RowKey
        table_service.delete_entity(table, partition_key, row_key)

    # Handle errors
    except Exception as e:
        message = "Final batch table status updates failed"
        em.log_error(ve.Programs.FILE_MAN, ve.ErrorCat.RECORD_ERROR, ve.ErrorSubCat.DB_ERROR, message, e)
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
        em.log_error(ve.Programs.FILE_MAN, ve.ErrorCat.BACKEND_ERROR, ve.ErrorSubCat.OS_ERROR, message, e,
                     error_level=ve.ErrorLevel.MINOR)
