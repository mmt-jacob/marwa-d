#!/usr/bin/env python
"""
Run report generator at regular intervals and, reported errors and optionally send email updates.

    Version Notes:
        1.0.0.0 - 10/23/2019 - Created file based on SAI status monitor.
        1.0.1.0 - 01/04/2020 - Cleaned code and added temp/log file cleanup.
        1.0.1.1 - 01/12/2020 - Changed to Process workers to isolate memory and improve performance.
        1.1.0.0 - 01/22/2020 - Cleaned unused settings. Moved control of some values to settings.
        1.1.0.1 - 01/23/2020 - Added version number.
        1.1.0.2 - 01/27/2020 - Added production variable.
        1.1.0.3 - 01/30/2020 - Shortened timeout when job reservations are released to new workers.
        1.1.1.0 - 02/13/2020 - Moved report generator settings to .env file.

"""

__author__ = "John Dorian for Sai Systems Technologies"
__copyright__ = "Copyright 2018"
__version__ = "1.1.1.0"

SYSTEM_VER = "1.01.01"
REPORT_VER = "1.01.01"

# Built-in
import gc
import os
import sys
import time
import shutil
import argparse
import traceback
from multiprocessing import Process
from datetime import datetime, timedelta

# Companion Python files
from config import config
from download_manager import build_batch
from report_generator import build_reports
from modules.models import vocsn_enum as ve
from modules.processing.utilities import safe_read, dt_to_ts

# Azure library
from azure.storage.file import FileService
from azure.cosmosdb.table import TableService, Entity


# ----- Global Variables ----- #

# Daemon vars
diag = False
prod = False
frequency = 1
settings = None
operational = True
credentials = None
process_count = 2
pool = []
t = None

# Azure vars
table_service = None
file_service = None

# Daily vars
did_cleanup = False
cleanup_hour = 14

# Monitor statistics
last_run = datetime(2000, 1, 1)


def d_print(message: str):
    """ Print if DIAG specified. """
    global diag
    if diag:
        print(message)


def azure_connection():
    """ Create Azure connection handlers. """
    global table_service, file_service, credentials
    table_service = TableService(account_name=credentials['account'], account_key=credentials['key'])
    file_service = FileService(account_name=credentials['account'], account_key=credentials['key'])


def read_settings():
    """ Get Azure credentials, setup table service instance, and read settings. """
    global settings, credentials, frequency, process_count, cleanup_hour
    global table_service, file_service, prod

    # Output action to log and console in diagnostic mode.
    d_print("Loading settings")

    # Read credentials from file
    d_print("  Loading Azure credentials")
    result, credentials, settings = config.get_azure_credentials(prod)
    if result.has_error:
        raise Exception("Enable to load Azure credentials.")

    # Set global vars
    frequency = settings.frequency
    process_count = settings.processes
    cleanup_hour = settings.cleanup_hour
    azure_connection()


def get_report_queue() -> [Entity]:
    """ Retrieve entire report queue. """
    global diag

    # Variables
    queue_items = []
    start = datetime.utcnow()
    expired = dt_to_ts(start - timedelta(minutes=2))

    # Catch errors
    try:

        # Retrieve items in report queue (no filters needed)
        table = "ReportQueue"
        result = table_service.query_entities(table)

        # Check for unprocessed items
        for item in result:

            # Check for items in "Queued" status
            if item.Status.value == ve.ProcessingState.QUEUED.value:
                queue_items.append(item)

            # Check for expired reservation
            elif safe_read(item.StartDT) < expired:
                queue_items.append(item)

    # Handle errors
    except Exception as e:
        print("Error: Unable to read report queue.", str(e))

        # Reset Azure connection
        azure_connection()

    # Return queue list
    return queue_items


def get_batch_queue() -> [Entity]:
    """ Retrieve entire batch queue. """
    global diag

    # Variables
    queue_items = []
    start = datetime.utcnow()
    expired = dt_to_ts(start - timedelta(minutes=1))

    # Catch errors
    try:

        # Retrieve items in batch queue (no filters needed)
        table = "BatchQueue"
        result = table_service.query_entities(table)

        # Check for unprocessed items
        for item in result:

            # Check for items in "Queued" status
            if item.Status.value == ve.ProcessingState.QUEUED.value:
                queue_items.append(item)

            # Check for expired reservation
            elif safe_read(item.StartDT) < expired:
                queue_items.append(item)

    # Handle errors
    except Exception as e:
        print("Error: Unable to read batch queue.", str(e))

        # Reset Azure connection
        azure_connection()

    # Return queue list
    return queue_items


def run_report(queue_item: Entity, use_prod: bool, use_diag: bool):
    """Run Report Generator"""

    # Capture default output
    sys_out = sys.stdout
    sys_err = sys.stderr

    # Pass arguments
    try:
        build_reports(queue_item, use_prod, use_diag)
    except Exception as e:
        message = "Fatal Error: Report Generator encountered a fatal error processing a report.\n"
        message += "{}\n".format(str(e))
        message += traceback.format_exc()
        print(message)

    # Restore stdout and stderr to terminal
    sys.stdout = sys_out
    sys.stderr = sys_err


def run_batch(queue_item: Entity, use_prod: bool, use_diag: bool):
    """Run Batch Generator"""

    # Capture default output
    sys_out = sys.stdout
    sys_err = sys.stderr

    # Pass arguments
    try:
        build_batch(queue_item, use_prod, use_diag)
    except Exception as e:
        message = "Fatal Error: Report Generator encountered a fatal error processing a batch download.\n"
        message += "{}\n".format(str(e))
        message += traceback.format_exc()
        print(message)

    # Restore stdout and stderr to terminal
    sys.stdout = sys_out
    sys.stderr = sys_err


def cleanup_files():
    """ Delete old log and temp files. """

    def del_item(p):
        """ Delete path recursively. """
        shutil.rmtree(p)

    def check_item(p, fence):
        """ Check folder. Delete if old. """
        timestamp = os.path.getmtime(p)
        age = datetime.fromtimestamp(timestamp)
        if age < fence:
            del_item(p)
            return True
        return False

    # Log age fence
    period = timedelta(days=96)
    age_fence = datetime.utcnow() - period

    # Remove old logs
    print("Cleaning log files...")
    logs = "logs"
    years = os.listdir(logs)
    for year in years:
        item = os.path.join(logs, year)
        months = os.listdir(item)
        if len(months) == 0:
            del_item(item)
            print("  {0: <12} Remove".format(year))
            continue
        print("  {0: <12} Keep".format(year))
        for month in months:
            item = os.path.join(logs, year, month)
            if check_item(item, age_fence):
                print("    {0: <10} Remove".format(month))
            else:
                print("    {0: <10} Keep".format(month))

    # Temp age fence
    period = timedelta(days=1)
    age_fence = datetime.utcnow() - period

    # Remove old temp files
    print("Cleaning temp files...")
    temp = "temp"
    folders = os.listdir(temp)
    for folder in folders:
        item = os.path.join(temp, folder)
        if check_item(item, age_fence):
            print("  {0: <12} Remove".format(folder))
        else:
            print("  {0: <12} Keep".format(folder))


# ----- MAIN LOOP ----- #

def main():
    """ Main loop. """
    global settings, t, did_cleanup, cleanup_hour, last_run
    global prod, diag, pool, process_count, frequency

    # ----- Run Status Monitor ---- #

    # Catch errors
    try:

        # Check if run is needed
        if datetime.utcnow() - last_run >= frequency:
            start = datetime.utcnow()
            last_run = start

            # Clear completed threads
            remove = []
            for worker in pool:
                if not worker.is_alive():
                    remove.append(worker)
            for worker in remove:
                worker.terminate()
                pool.remove(worker)
                gc.collect()

            # Check for new reports in queue at specified frequency, run up to max threads
            # Batches are run first because they are shorter and their existence is predicated
            # On reports getting processes so they will not block report processing, while
            # the reverse could block batches entirely under high loads.
            if len(pool) < process_count:

                # Get batch queue
                queue = get_batch_queue()
                for item in queue:
                    if len(pool) < process_count:
                        p = Process(target=run_batch, args=(item, prod, diag))
                        p.start()
                        pool.append(p)

                # Get report queue
                queue = get_report_queue()
                for item in queue:
                    if len(pool) < process_count:
                        p = Process(target=run_report, args=(item, prod, diag))
                        p.start()
                        pool.append(p)

    # Handle errors
    except Exception as e:
        print(e)

    # ----- Daily Tasks ---- #

    try:

        # Check if it's time to send the daily report
        if datetime.now().hour == cleanup_hour:
            if not did_cleanup:

                # Catch errors
                try:

                    # Send daily report
                    cleanup_files()
                    did_cleanup = True

                # Handle errors
                except Exception as e:
                    print(e)

        else:
            did_cleanup = False

    # Handle errors
    except Exception as e:
        print(e)


if __name__ == "__main__":
    """
    Entry point from command line.

    Optional Parameters:
        diag  (bool): Output log to console for diagnostics.
    """

    # Setup message
    print("VOCSN Multi-View Report System - v{}".format(SYSTEM_VER))
    print("VOCSN Report Generator - v{}".format(REPORT_VER))

    # Define arguments and options
    parser = argparse.ArgumentParser(prog="report_generator_d",
                                     description="Continuously run Report Generator to check connectivity status of "
                                                 "all deployed equipment.")
    parser.add_argument('-d', '--diag', action='store_true', help="Output diagnostic information to stdout.")
    parser.add_argument('-p', '--production', action='store_true', help="Use production credentials.")

    # Process arguments and options
    a = parser.parse_args(sys.argv[1:])
    diag = a.diag
    prod = a.production

    # Get settings
    read_settings()

    # Ensure directories exist
    print("Checking directories")
    for path in ["logs", "temp"]:
        if not os.path.exists(path):
            os.mkdir(path)

    # Initial file cleanup
    cleanup_files()

    # Start main loop
    print("")
    print("--- Report Generator System Ready ---")
    print("")
    while True:
        last_run_time = datetime.utcnow()
        main()
        time_left = max(0.0, (1 - (datetime.utcnow() - last_run_time).total_seconds()))
        time.sleep(time_left)
