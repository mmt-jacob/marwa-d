#!/usr/bin/env python
"""
Error tracking and management logic for processing VOCSN data.

    Version Notes:
        1.0.0.0 - 08/23/2019 - Created file with ErrorManager class.
        1.0.1.0 - 12/19/2019 - Expanded error structure and logic. Added warning management.
        1.0.1.1 - 12/20/2019 - Moved settings initializeation to setup function.
        1.0.1.2 - 12/26/2019 - Fixed improper string handling in error/warning printer.
        1.0.1.3 - 01/01/2020 - Added ability to disable error tracking when processing records out of range.
        1.0.2.0 - 01/04/2020 - Added file logging.
        1.0.2.1 - 01/05/2020 - Improved error status updates.
        1.0.2.2 - 01/09/2020 - Added leading 0 to day log folder.
        1.0.2.3 - 01/23/2020 - Added a flag to print all errors from print_status.
        1.0.3.0 - 01/30/2020 - Added upload to database.
        1.0.3.1 - 01/31/2020 - Added system name and processing datetime.
        1.0.3.2 - 02/01/2020 - Created line awareness in error manager for batch data.
        1.0.4.0 - 03/01/2020 - Added line consolidation for error and warning records.
        1.0.4.1 - 03/29/2020 - Added datetime fields to warning and error classes.
        1.0.4.2 - 03/30/2020 - Added attributes and functions for combined log.
        1.0.4.3 - 04/07/2020 - Added a parameter to ignore critical errors for combined log.
        1.0.4.4 - 04/08/2020 - Moved CSV line interpreter to vocsn-combined-log project.
        1.0.4.5 - 04/13/2020 - Improved data structures for combined log.
        1.0.4.6 - 04/13/2020 - Improved combined log string output.

"""

__author__ = "John Dorian for Sai Systems Technologies"
__copyright__ = "Copyright 2019"
__version__ = "1.0.4.6"

# Built-in modules
import os
import sys
import socket
from datetime import datetime

# VOCSN modules
from modules.models import vocsn_enum as ve

# Azure modules
from azure.cosmosdb.table import TableService, TableBatch, Entity

# Globals
LINE = None
FILE = None


def error_info():
    """
    Gather exception information.
    :return: [Exception type, file, line number]
    """

    # Contents of sys.exc_info are not referenced, since they may not be garbage collected.
    # Structure of sys.exec_info:
    #   [type, value, traceback]

    # Specific exception-related attributes
    filename = line = name = ""
    info = sys.exc_info()
    if info:
        if info[2]:
            line = info[2].tb_lineno
            name = info[2].tb_frame.f_code.co_name
            filename = info[2].tb_frame.f_code.co_filename
    return filename, line, name


class VOCSNError:
    """ VOCSN processing error container """
    global LINE, FILE

    def __init__(self, prog: ve.Programs, cat: ve.ErrorCat, sub_cat: ve.ErrorSubCat, message: str = None,
                 p_id: str = None, r_id: str = None, val: any = None, e: Exception = None):
        """
        Parse and store an error.
        :param prog: Program the error is from.
        :param cat: Exception category.
        :param sub_cat: Subcategory.
        :param message: Custom error message/details.
        :param p_id: Parameter ID.
        :param r_id: Reference ID.
        :param val: Value.
        :param e: Exception caught.
        """
        from modules.processing.utilities import dt_to_ts
        global LINE

        # Get exception details
        filename, line, name = error_info()
        root = "VOCSN Reporting System"
        if root in filename:
            filename = filename.split(root)[1]

        # Error attributes
        self.data_filename = FILE
        self.record_type = ve.LogRecordType.REPORT_ERROR
        self.crc_result = "N/A"
        self.dt = round(dt_to_ts(datetime.utcnow()))
        self.program = prog
        self.category = cat
        self.subcategory = sub_cat
        self.message = message
        self.sequence = LINE[0] if LINE else None
        self.raw_time_s = LINE[1] if LINE else None
        self.syn_time_s = LINE[2] if LINE else None
        self.rec_type = LINE[3] if LINE else None
        self.message_id = LINE[4] if LINE else None
        self.parameter_id = p_id
        self.reference_id = r_id
        self.value = val
        self.filename = filename
        self.line = line
        self.type = e.__class__.__name__
        self.detail = str(e)
        self.count = 1

        # Set time if possible
        self.raw_time = None
        self.syn_time = None
        try:
            self.raw_time = datetime.utcfromtimestamp(float(LINE[1]))
            self.syn_time = datetime.utcfromtimestamp(float(LINE[2]))
        except Exception as err:
            str(err)

    def __str__(self):
        return "Program: {}|Category: {}|Subcategory: {}|Message: {}|Sequence: {}|MessageID: {}|ParamID: {}|RefID: {}" \
               "|Value: {}|CodeFIle: {}|Line: {}|Detail: {}"\
            .format(self.program.name, self.category.name, self.subcategory.name, self.message, self.sequence,
                    self.message_id, self.parameter_id, self.reference_id, self.value, self.filename, self.line,
                    self.detail)


class VOCSNWarning:
    """ VOCSN warning message. """
    global LINE, FILE

    def __init__(self, message: str = None, p_id: str = None, r_id: str = None, val=None):
        """
        Store warning message attributes.
        :param message: Text warning message.
        :param p_id: Parameter ID if available.
        :param r_id: Reference ID if available.
        :param val: Value if available.
        """
        from modules.processing.utilities import dt_to_ts

        # Warning attributes
        self.data_filename = FILE
        self.record_type = ve.LogRecordType.REPORT_WARN
        self.crc_result = "N/A"
        self.dt = round(dt_to_ts(datetime.utcnow()))
        self.program = ve.Programs.REPORTING
        self.category = ve.ErrorCat.WARNING
        self.subcategory = ve.ErrorSubCat.DATA_IRREGULARITY
        self.message = message
        self.sequence = LINE[0] if LINE else None
        self.raw_time_s = LINE[1] if LINE else None
        self.syn_time_s = LINE[2] if LINE else None
        self.rec_type = LINE[3] if LINE else None
        self.message_id = LINE[4] if LINE else None
        self.parameter_id = p_id
        self.reference_id = r_id
        self.value = val
        self.count = 1

        # Set time if possible
        self.raw_time = None
        self.syn_time = None
        try:
            self.raw_time = datetime.utcfromtimestamp(float(LINE[1]))
            self.syn_time = datetime.utcfromtimestamp(float(LINE[2]))
        except Exception as err:
            str(err)

    def __str__(self):
        return "Program: {}|Category: {}|Subcategory: {}|Message: {}|Sequence: {}|MessageID: {}|ParamID: {}|RefID: {}" \
               "|Value: {}"\
            .format(self.program.name, self.category.name, self.subcategory.name, self.message, self.sequence,
                    self.message_id, self.parameter_id, self.reference_id, self.value)


class ErrorThresholds:
    """ Error threshold definitions. """
    
    def __init__(self, settings: dict):
        """ Populate values from settings definitions. """
        defs = settings["thresholds"]
        self.event = int(defs["event"])
        self.config = int(defs["config"])
        self.monitor = int(defs["monitor"])
        self.general = int(defs["general"])
        self.unknown = int(defs["unknown"])


class ErrorManager:
    """ VOCSN data processing error management. """
    global LINE

    # Error level criteria
    criteria = {
        "critical": [
            ve.ErrorCat.FILE_ERROR,
            ve.ErrorCat.PROCESS_ERROR,
        ],
        "section": [
            ve.ErrorCat.REPORT_SECTION
        ],
        "advisory": [
            ve.ErrorCat.MID_ERROR
        ],
        "minor": []
    }

    def __init__(self, program: str, filename: str, diag: bool = False, errors: bool = False,
                 ignore_crit: bool = False):
        """ Instantiate """

        # Settings
        self.diag = diag
        self.enabled = True
        self.data_file = None
        self.program = program
        self.filename = filename
        self.record = "record-not-set"
        self.start = datetime.utcnow()
        self.full_errors = errors
        self.run_time = None
        self.ignore_crit = ignore_crit

        # Overall status
        self.status = ve.ErrorLevel.NO_ERRORS
        self.lost_event = 0
        self.lost_monitor = 0
        self.lost_config = 0
        self.lost_general = 0
        self.lost_unknown = 0

        # Thresholds
        self.critical = None
        self.advisory = None
        self.minor = None
        self.report_failed = False

        # Error tracking
        self.errors = []            # List[EventError] - Errors encountered while loading
        self.warnings = []          # List[EventWarning] - Warnings encountered while loading
        self.unique_messages = []   # List[str] = Unique message identifiers to prevent duplicates

    def enable_tracking(self):
        """ Disable tracking when processing records out of range. """
        self.enabled = True

    def disable_tracking(self):
        """ Disable tracking when processing records out of range. """
        self.enabled = False

    def setup(self, settings: dict):
        """
        Setup error thresholds once settings are loaded.
        :param settings: System settings with error thresholds.
        """
        levels = settings["errors"]["level"]
        self.critical = ErrorThresholds(levels["critical"])
        self.advisory = ErrorThresholds(levels["advisory"])
        self.minor = ErrorThresholds(levels["minor"])

    @staticmethod
    def set_line(line: list = None, filename: str = None):
        """
        Set the last data line that will be referenced by warnings and errors.
        :param line: Data line array.
        :param filename: Source filename.
        """
        global LINE, FILE

        # Store line
        if line and type(line) is list and len(line) >= 6:
            LINE = line
        else:
            LINE = None

        # Store source filename
        FILE = filename

    def log_error(self, prog: ve.Programs, cat: ve.ErrorCat, sub_cat: ve.ErrorSubCat, message: str, e: Exception,
                  rec_type: ve.RecordType = None, error_level: ve.ErrorLevel = None, unique: str = None,
                  line: list = None, p_id: str = None, r_id: str = None, val=None):
        """
        Parse and store an error.
        :param prog: Program the error is from.
        :param cat: Exception category.
        :param sub_cat: Subcategory.
        :param message: Custom error message/details.
        :param e: Exception caught.
        :param rec_type: Record type (event, config, monitor, or general).
        :param error_level: Optional error level override.
        :param unique: Unique message identifier included when a message should only appear once.
        :param line: Provide line data outside main processing loop.
        :param p_id: Parameter ID if available.
        :param r_id: Reference ID if available.
        :param val: Value if available.
        """
        global LINE

        # No logging when disabled
        if not self.enabled:
            return

        # Ignore duplicate unique messages
        if unique and unique in self.unique_messages:
            return

        # Set line data override
        old_line = LINE
        if line:
            LINE = line

        # Create error record
        error = VOCSNError(prog, cat, sub_cat, message, e=e, p_id=p_id, r_id=r_id, val=val)

        # Store all errors in diagnostic mode
        if self.diag:
            self.errors.append(error)

        # Only store unique errors with counts in normal operation
        else:
            found = False
            for existing in self.errors:
                if existing.category == error.category and \
                        existing.subcategory == error.subcategory and \
                        existing.message == error.message and \
                        existing.message_id == error.message_id:
                    existing.count += 1
                    found = True
                    break
            if not found:
                self.errors.append(error)

        # Observe level override
        if error_level is not None:
            self.status = error_level

        # Contextual error level determination
        else:

            # Handle early errors before error criteria are defined
            if None in [self.critical, self.advisory, self.minor]:
                self.status = ve.ErrorLevel.CRITICAL

            # Regular handling once thresholds defined
            else:

                # Update record error counters
                if error.category == ve.ErrorCat.RECORD_ERROR:
                    if rec_type == ve.RecordType.EVENT:
                        self.lost_event += 1
                    elif rec_type == ve.RecordType.SETTINGS:
                        self.lost_config += 1
                    elif rec_type == ve.RecordType.MONITOR:
                        self.lost_monitor += 1
                    elif rec_type == ve.RecordType.GENERAL:
                        self.lost_general += 1
                    else:
                        self.lost_unknown += 1

                # Check for critical error conditions
                if self.check_error_level(error, "critical"):
                    self.status = ve.ErrorLevel.CRITICAL

                # Check for section error conditions
                elif self.check_error_level(error, "section"):
                    self.status = ve.ErrorLevel.SECTION

                # Check for advisory error conditions
                elif self.check_error_level(error, "advisory"):
                    self.status = ve.ErrorLevel.ADVISORY

                # Any error constitutes at least a minor error condition
                else:
                    self.status = ve.ErrorLevel.MINOR

        # Restore previous line data
        if line:
            LINE = old_line

        # Raise errors immediately in diagnostic mode
        if self.diag and not self.ignore_crit and self.status == ve.ErrorLevel.CRITICAL:
            raise e

    def log_warning(self, message: str = None, p_id: str = None, ref_id: str = None, val=None, unique: str = None,
                    line: list = None):
        """
        Log a warning message with any available reference values.
        :param message: Text warning message.
        :param p_id: Parameter ID if available.
        :param ref_id: Reference ID if available.
        :param val: Value if available.
        :param unique: Unique message identifier included when a message should only appear once.
        :param line: Provide line data outside main processing loop.
        """
        global LINE

        # No logging when disabled
        if not self.enabled:
            return

        # Ignore duplicate unique messages
        if unique and unique in self.unique_messages:
            return

        # Set line data override
        old_line = LINE
        if line:
            LINE = line

        # Construct and store warning
        warning = VOCSNWarning(message, p_id, ref_id, val)

        # Store all warnings in diagnostic mode
        if self.diag:
            self.warnings.append(warning)

        # Only store unique errors with counts in normal operation
        else:
            found = False
            for existing in self.warnings:
                if existing.category == warning.category and \
                        existing.subcategory == warning.subcategory and \
                        existing.message == warning.message and \
                        existing.message_id == warning.message_id:
                    existing.count += 1
                    found = True
                    break
            if not found:
                self.warnings.append(warning)

        # Escalate error level if appropriate
        if self.status == ve.ErrorLevel.NO_ERRORS:
            self.status = ve.ErrorLevel.WARNINGS

        # Restore previous line data
        if line:
            LINE = old_line

    def check_error_level(self, error: VOCSNError, level: str):
        """
        Check for critical error conditions.
        :param error: VOCSN error container.
        :param level: Severity level.
        :return: Are severity level criteria met.
        """

        # References
        cat_list = self.criteria[level]
        thresholds = getattr(self, level) if hasattr(self, level) else None

        # Categorical conditions
        if error.category in cat_list:
            return True
        
        # Threshold-based conditions
        types = {"event", "config", "monitor", "general", "unknown"}
        if thresholds:
            for rec_type in types:
                limit = getattr(thresholds, rec_type)
                count = getattr(self, "lost_" + rec_type)
                if count >= limit:
                    return True

        # Criteria not met
        return False

    def print_status(self):
        """ Print status to terminal. """

        def s(string, attr: str = None):
            if attr and type(string) is not str:
                return getattr(string, attr) if string and hasattr(string, attr) else ""
            else:
                return string if string else ""

        # Max print count
        if self.full_errors:
            max_print = 99999
        else:
            max_print = 10 if not self.diag else 500

        # Print error results
        result = "Complete" if self.status not in [ve.ErrorLevel.CRITICAL] else "FAILED"
        print("  Result:", result)
        print("  Error Status:", self.status.name.replace('_', ' ').title())
        print("  Warnings: {}".format(len(self.warnings)))
        if len(self.warnings) > 0:
            print("    {0:<5} {1:<45} {2:<6} {3:<8} {4:<5} {5:<8} {6:<8}"
                  .format("COUNT", "MESSAGE", "SEQ", "M.ID", "P.ID", "REF ID", "VAL"))
        for x in range(0, min(max_print, len(self.warnings))):
            warn = self.warnings[x]
            print("    {0:<5} {1:<45} {2:<6} {3:<8} {4:<5} {5:<8} {6:<8}"
                  .format(s(warn.count),
                          s(warn.message)[:44],
                          s(warn.sequence),
                          s(warn.message_id)[:8],
                          s(warn.parameter_id)[:5],
                          s(warn.reference_id)[:8],
                          s(warn.value)[:8]))
        if len(self.warnings) > max_print:
            print("    ...")
        print("  Errors: {}".format(len(self.errors)))
        if len(self.errors) > 0:
            print("    {0:<5} {1:<14} {2:<16} {3:<40} {4:<6} {5:<4} {6:<5} {7:<6} {8:<14} {9:<4} {10:<16} {11:<44}"
                  .format("COUNT", "CATEGORY", "SUBCATEGORY", "MESSAGE", "SEQ", "M.ID", "P.ID", "VAL", "FILENAME",
                          "LINE", "ERROR", "DETAIL"))
        for x in range(0, min(max_print, len(self.errors))):
            error = self.errors[x]
            print("    {0:<5} {1:<14} {2:<16} {3:<40} {4:<6} {5:<4} {6:<5} {7:<6} {8:<14} {9:<4} {10:<16} {11:<44}"
                  .format(s(error.count),
                          s(error.category, "name")[:14],
                          s(error.subcategory, "name")[:16],
                          s(error.message)[:40],
                          s(error.sequence),
                          s(error.message_id),
                          s(error.parameter_id[:5]) if error.parameter_id else "",
                          s(error.value)[:6],
                          s(error.filename)[-14:],
                          s(error.line),
                          s(error.type)[:16],
                          s(error.detail)[:44]))
        if len(self.errors) > max_print:
            print("    ...")
        print("  Run Time: " + str(self.run_time))
        print("")

    def write_log(self):
        """ Write errors to log file. """
        
        def tstr(s):
            return str(s) if s is not None else ""

        def write_line(file, fields: list):
            for field in fields:
                file.write(str(field) + ",")
            file.write("\n")

        # Require filename
        if not self.filename:
            print("Cannot generate log file without filename.")
            return

        # Catch errors
        try:

            # Determine context
            context = ""
            if not os.path.exists(os.path.join(context, "modules")):
                context = ".."

            # Create date folders if needed
            logs = "logs"
            now = datetime.utcnow()
            year = str(now.year)
            month = "{:02}".format(now.month)
            day = "{:02}".format(now.day)
            log_path = context
            for folder in [logs, year, month, day]:
                log_path = os.path.join(log_path, folder)
                if not os.path.exists(log_path):
                    os.mkdir(log_path)

            # Measure run time
            self.run_time = rt = now - self.start

            # Lookup system name
            sys_name = socket.gethostname()

            # Create file
            filename = os.path.join(log_path, self.filename + ".csv")
            with open(filename, 'w+') as f:

                # Info lin
                if self.data_file:
                    line = ["Info", self.data_file]
                    write_line(f, line)
                line = ["Info", self.program, self.record, self.status.name]
                write_line(f, line)
                line = ["Info", "Errors: " + str(len(self.errors)), "Warnings: " + str(len(self.warnings))]
                write_line(f, line)
                line = ["Info", "Start: " + str(self.start)]
                write_line(f, line)
                line = ["Info", "Run time: " + str(rt)]
                write_line(f, line)

                # Header
                line = [
                    "System Name",
                    "Program",
                    "Processed Time",
                    "Line Type",
                    "Count",
                    "Category",
                    "Subcategory",
                    "Description",
                    "Sequence",
                    "Raw Time",
                    "Syn Time",
                    "Record Type",
                    "Message ID",
                    "Parameter ID",
                    "Reference ID",
                    "Value",
                    "Filename",
                    "Line",
                    "Error Type",
                    "Detail"
                ]
                write_line(f, line)

                # Warning lines
                for w in self.warnings:
                    line = [tstr(sys_name),
                            tstr(w.program.name if w.program.name else ""),
                            tstr(w.dt),
                            tstr("Warning"),
                            tstr(w.count),
                            tstr(w.category.name if w.category else ""),
                            tstr(w.subcategory.name if w.subcategory else ""),
                            tstr(w.message),
                            tstr(w.sequence),
                            tstr(w.raw_time_s),
                            tstr(w.syn_time_s),
                            tstr(w.rec_type),
                            tstr(w.message_id),
                            tstr(w.parameter_id),
                            tstr(w.reference_id),
                            tstr(w.value)]
                    write_line(f, line)

                # Error lines
                for e in self.errors:
                    line = [tstr(sys_name),
                            tstr(e.program.name if e.program.name else ""),
                            tstr(e.dt),
                            tstr("Error"),
                            tstr(e.count),
                            tstr(e.category.name if e.category else ""),
                            tstr(e.subcategory.name if e.subcategory else ""),
                            tstr(e.message),
                            tstr(e.sequence),
                            tstr(e.raw_time_s),
                            tstr(e.syn_time_s),
                            tstr(e.rec_type),
                            tstr(e.message_id),
                            tstr(e.parameter_id),
                            tstr(e.reference_id),
                            tstr(e.value),
                            tstr(e.filename),
                            tstr(e.line),
                            tstr(e.type),
                            tstr(e.detail)]
                    write_line(f, line)

        # Handle errors
        except Exception as e:
            message = "Log file failed."
            self.log_error(ve.Programs.REPORTING, ve.ErrorCat.FILE_ERROR, ve.ErrorSubCat.INTERNAL_ERROR, message, e)

        # Print message to console
        self.print_status()

    def upload_log(self, table_service: TableService, table: str, record_id: str):
        """
        Write warning and error lines to Azure database.
        :param table_service: Azure TableService instance with credentials.
        :param table: Destination table name.
        :param record_id: Report or batch ID.
        """

        def s(string: str):
            """ Safe-format strings. """
            if string is None:
                return string
            if hasattr(string, "name"):
                return str(string.name)
            else:
                return str(string)

        # Variables
        rec_num = 0
        lines = []

        # Lookup system name
        sys_name = socket.gethostname()

        # Populate warnings
        for w in self.warnings:
            rec_num += 1
            ent = Entity()
            ent.PartitionKey = s(record_id)
            ent.RowKey = "{:06d}-{}".format(rec_num, str(w.dt)[5:])
            ent.SystemName = sys_name
            ent.Program = s(w.program)
            ent.ProcessedDT = s(w.dt)
            ent.Type = "Warning"
            ent.Count = s(w.count)
            ent.Category = s(w.category)
            ent.Subcategory = s(w.subcategory)
            ent.Description = s(w.message)
            ent.Sequence = s(w.sequence)
            ent.RawTime = s(w.raw_time_s)
            ent.SynTime = s(w.syn_time_s)
            ent.RecordType = s(w.rec_type)
            ent.MessageID = s(w.message_id)
            ent.ParameterID = s(w.parameter_id)
            ent.ReferenceID = s(w.reference_id)
            ent.Value = s(w.value)
            lines.append(ent)

        # Populate errors
        for e in self.errors:
            rec_num += 1
            ent = Entity()
            ent.PartitionKey = record_id
            ent.RowKey = "{:06d}".format(rec_num)
            ent.SystemName = sys_name
            ent.Program = s(e.program)
            ent.ProcessedDT = s(e.dt)
            ent.Type = "Error"
            ent.Count = s(e.count)
            ent.Category = s(e.category)
            ent.Subcategory = s(e.subcategory)
            ent.Description = s(e.message)
            ent.Sequence = s(e.sequence)
            ent.RawTime = s(e.raw_time_s)
            ent.SynTime = s(e.syn_time_s)
            ent.RecordType = s(e.rec_type)
            ent.MessageID = s(e.message_id)
            ent.ParameterID = s(e.parameter_id)
            ent.ReferenceID = s(e.reference_id)
            ent.Value = s(e.value)
            ent.Filename = s(e.filename)
            ent.Line = s(e.line)
            ent.ErrorType = s(e.type)
            ent.ErrorMessage = s(e.detail)
            lines.append(ent)

        # Upload in batches
        count = 0
        batch = TableBatch()
        for line in lines:
            batch.insert_entity(line)
            count += 1
            if count >= 100:
                table_service.commit_batch(table, batch)
                batch = TableBatch()
                count = 0
        if count > 0:
            table_service.commit_batch(table, batch)
