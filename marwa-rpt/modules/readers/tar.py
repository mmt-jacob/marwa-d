#!/usr/bin/env python
"""
Classes and functions for handling TAR files.

    Version Notes:
        1.0.0.0 - 10/04/2019 - Created file with an unpacker for TAR files.
        1.0.0.1 - 10/15/2019 - Added file integrity checking, and reordering in case of batch rollover. Created combined
                               batch file line reader.
        1.0.0.2 - 11/01/2019 - Added method to retrieve device identifiers and version numbers.
        1.0.0.3 - 11/04/2019 - Added support for comma separation and comma-space separation. Updated CRC check.
        1.0.0.4 - 12/05/2019 - Added tar reader reset.
        1.0.0.5 - 12/08/2019 - Added a lookahead for 7203 messages.
        1.0.0.6 - 12/10/2019 - Restored multi-file reading (impaired from earlier change)
        1.0.1.0 - 12/21/2019 - Integrated error handling. Disabled reading metadata from TAR file to use local copy.
        1.0.1.1 - 01/06/2020 - Expanded search area to entire data file for config line.
        1.0.2.0 - 02/04/2020 - Added version filter to tar manager to prevent data as early as possible from entering
                               the system.
        1.0.2.1 - 02/05/2020 - Added data filename update to error manager.
        1.0.2.2 - 03/12/2020 - Track first valid sequence to start processing maintenance records.
        1.0.2.3 - 03/13/2020 - Added protection against a line of commas (found once in synthetic data).
        1.0.2.4 - 03/27/2020 - Improved aberrant line detection. Added additional context in error logging.
        1.0.3.0 - 03/29/2020 - Added indexing for maintenance file.
        1.0.4.0 - 04/13/2020 - Added modifications for combined log processing: track CRC results and file source.

"""

__author__ = "John Dorian for Sai Systems Technologies"
__copyright__ = "Copyright 2019"
__version__ = "1.0.4.0"

# Built-in modules
import os
import sys
import tarfile
import hashlib

# 3rd party modules
import crc16

# VOCSN modules
from modules.models import vocsn_enum as ve
from modules.models.errors import ErrorManager
from modules.readers.strings import load_labels
from modules.processing.versions import check_ver
from modules.readers.metadata import read_metadata
from modules.processing.utilities import get_record_type
from modules.processing.applicability import lookup_applicability


class TarManager:
    """ Container for managing contents of TAR file. """

    def __init__(self, em: ErrorManager, data, report, path: str, temp_dir: str, file: str, orig_hash: str = None,
                 combo_log=False):
        """
        Load a TAR file and populate the manager.
        :param em: Error manager.
        :param data: VOCSN data container.
        :param report: Report definitions.
        :param path: Working Directory.
        :param temp_dir: Temporary file parent.
        :param file: TAR file name/path.
        :param orig_hash: Original MD5 file hash to ensure integrity.
        :param combo_log: Modify error management behavior for combined log processing.
        """

        # References
        self.em = em
        self.data = data
        self.report = report
        data.tar_manager = self

        # Properties
        self.data_found = False
        self.hash = orig_hash
        self.last_accessed = None
        self.path = path
        self.temp_path = temp_dir
        self.combo_log = combo_log

        # Files
        self.metadata = None
        self.tar = em.data_file = file
        self.batch_files = []
        self.slogger_1_files = []
        self.slogger_2_files = []
        self.device_config = None
        self.crash_log = None
        self.usage_mon = None
        self.file_count = 0

        # Config record
        self.config_line = None

        # Reader values
        self.more_lines = False
        self.file_data = None
        self.current_file_idx = 0
        self.current_line_idx = 0
        self.current_file_name = ""
        self.file_line_count = 0
        self.last_file = False
        self.bad_records = 0
        self.first = True
        self.valid_version = False
        self.no_valid_version = True
        self.found_version = None
        self.first_valid_sequence = None
        self.last_sequence = 0

        # Open and check tar file
        self._check_files()
        self._get_config()

    def _get_config(self):
        """ Locate and store initial config record. """

        # Open file and step through lines
        while self.more_lines:

            # Read each line
            line, _, _ = self.read_line(self.em)

            # Check valid lines only
            if len(line) < 3:
                continue

            # Store config record and move on
            event_type = line[2]
            if event_type == 'C':
                line.insert(2, line[1])
                self.config_line = line.copy()

        # Reset for next pass
        self.reset()

        # Ensure a valid software version was found
        if self.no_valid_version:
            raise Exception("TAR file contains no recognized versions")

        # Set final found version as source for settings file
        self.data.lookup_version = self.found_version

    def _check_files(self):
        """ Open Tar file, check for required files and archive integrity. """

        # Handle errors
        try:

            # Variables
            limit_batch = 0
            max_batch = 0
            min_batch = sys.maxsize

            # # Check archive data integrity with MD5 hash
            # new_hash = hashlib.md5(open(self.tar, 'rb').read()).hexdigest()
            # if new_hash != self.hash:
            #     print("Error: File failed MD5 hash check.")
            #     return

            # Open file
            file_path = os.path.join(self.path, self.temp_path, self.tar)
            with tarfile.open(file_path) as tar:

                # Identify required file
                for member in tar.getmembers():

                    # Get name and stats
                    name = member.name
                    low_name = name.lower()
                    ext = name.split('.')[-1]
                    self.last_accessed = os.stat(file_path).st_atime

                    # Metadata
                    if "trendmetadata" in low_name:
                        f = tar.extractfile(member)
                        self.metadata = f.read().decode('UTF-8')

                    # Crash log
                    elif "crashlog" in low_name:
                        self.crash_log = name

                    # Usage monitor data
                    elif "usagemonitors" in low_name:
                        self.usage_mon = name

                    # Device config
                    elif "deviceconfig" in low_name:
                        self.device_config = name

                    # System logger files
                    elif "slogger" in low_name:
                        if "log1" in low_name:
                            self.slogger_1_files.append(name)
                        elif "log2" in low_name:
                            self.slogger_2_files.append(name)

                    # Data files
                    elif ext == "csv":
                        name = member.name
                        self.file_count += 1
                        batch_str = name.split('.')[0].split('_')[-1]
                        batch = int(batch_str)
                        if max_batch == 0:
                            limit_batch = _get_max_batch(batch_str)
                        min_batch = min(min_batch, batch)
                        max_batch = max(max_batch, batch)
                        self.batch_files.append({
                            "batch": batch,
                            "name": name
                        })

            # Sort log file lists
            self.slogger_1_files.sort(key=lambda file: int(file[17:-4]))
            self.slogger_2_files.sort(key=lambda file: int(file[17:-4]))

            # Check for required files
            self.data_found = True
            if len(self.batch_files) == 0:
                self.data_found = False
                raise Exception("TAR file contains no batch files.")
            else:
                self.more_lines = True

            # Handle batch number rollover
            middle_batch = limit_batch * 0.5
            rollover = (max_batch - min_batch) > middle_batch
            if rollover:
                files = self.batch_files
                loop_protect = 0
                while rollover:
                    loop_protect += 1
                    first = files[0]["batch"]
                    if first > middle_batch:
                        rollover = False
                    else:
                        files.append(files.pop(0))
                    if loop_protect > max_batch:
                        raise Exception("File indexing error.")

        # Handle errors
        except Exception as e:
            message = "Error while reading and indexing files"
            self.em.log_error(ve.Programs.REPORTING, ve.ErrorCat.FILE_ERROR, ve.ErrorSubCat.INVALID_TAR, message, e)
                
    def read_line(self, em: ErrorManager, silent: bool = False):
        """
        Batch file reader. Automatically continues from one batch file to the nex in the tar file.
        :param em: Error manager.
        :param silent: If true, no errors are logged to avoid redundant entries.
        """
        
        # Load new file
        def _load_file(t: TarManager):
            """ Load new CSV file into memory. """
            file_path = os.path.join(t.path, t.temp_path, t.tar)
            with tarfile.open(file_path) as tar_file:
                t.current_file_name = t.batch_files[t.current_file_idx]["name"]
                file_member = tar_file.extractfile(t.current_file_name)
                file_bytes = file_member.read()
                file_bytes = file_bytes.replace(b'\r', b'')
                t.file_data = file_bytes.split(b'\n')
                t.current_line_idx = 0
                t.current_file_idx += 1
                t.file_line_count = len(t.file_data)
            if t.current_file_idx >= t.file_count:
                t.last_file = True

        # Required variables
        d = self.data
        line_parts = None
        next_is_7203 = False
        r_type = ve.RecordType.UNKNOWN
        sub_cat = ve.ErrorSubCat.INVALID_REC

        # Catch errors during file read
        try:

            # First line - load first file
            if not self.file_data and self.current_file_idx < self.file_count:
                _load_file(self)

            # Advance to next file
            elif self.current_line_idx >= self.file_line_count:
                if self.current_file_idx < self.file_count:
                    _load_file(self)

            # Read next line
            line = self.file_data[self.current_line_idx]
            self.current_line_idx += 1

            # Skip blank line
            line_parts = []
            if line != b'':

                # Strip extra commas
                line = line.replace(b', ', b',')
                while len(line) > 0:
                    if line[-1] == 44:
                        line = line[:-1]
                    else:
                        break

                # Decode and split line to parts
                if line != b'' and len(line) > 4 and line[:4] != b'\x00\x00\x00\x00':
                    line_parts = line.decode('utf-8').split(',')
                    r_type = get_record_type((line_parts[2]), line_parts[3])

                    # Check sequence numbering
                    seq = int(line_parts[0])
                    last_seq = self.last_sequence
                    self.last_sequence = seq
                    if last_seq + 1 != seq and seq > 1:
                        # e = Exception("Missing sequence number")
                        missing = str(self.last_sequence-1)
                        em.log_warning("Missing sequence number", ref_id=missing)
                        # em.log_error(ve.Programs.REPORTING, ve.ErrorCat.RECORD_ERROR, sub_cat,
                        #              "Missing sequence number", e, ve.RecordType.UNKNOWN,
                        #              line=[missing, "", "", "", ""], r_id=missing)

                    # Check CRC
                    crc_orig = int(line_parts[-1])
                    crc_new = crc16.crc16xmodem(line[:-5], 0xffff)
                    crc_result = "PASS"
                    if crc_orig != crc_new:
                        crc_result = "FAIL"
                        self.bad_records += 1
                        if not self.combo_log:
                            sub_cat = ve.ErrorSubCat.CRC_FAILED
                            if self.first:
                                raise Exception("Data record failed CRC check")
                            else:
                                return None, None
                    line_parts.append(crc_result)

            # Mark when at end of data
            if self.last_file:
                if self.current_line_idx >= self.file_line_count:
                    self.more_lines = False

            # Check if next record is therapy state
            next_is_7203 = False
            if self.current_line_idx < self.file_line_count:
                next_line = self.file_data[self.current_line_idx]
                if len(next_line) >= 4:
                    if next_line[3] == "7203":
                        next_is_7203 = True

            # Check for new versions and re-index metadata if valid
            if len(line_parts) > 4 and line_parts[3] == "7000":
                new_ver = str(line_parts[4]).strip('"')
                gen_ver = new_ver.replace('"', '').replace('.', '')
                if gen_ver and gen_ver[-1] in {"R", "D"}:
                    gen_ver = gen_ver[0:-1]
                valid_ver, use_int_md = check_ver(em, gen_ver, self.path)
                if valid_ver:
                    self.no_valid_version = False
                    self.found_version = valid_ver
                    d.set_version_only(new_ver)
                    read_metadata(em, d, use_int_md)
                    load_labels(em, d, valid_ver)
                    d.applicability_tracker = lookup_applicability(d, valid_ver)
                    if not self.valid_version:
                        self.valid_version = True
                        self.first_valid_sequence = int(line_parts[0])
                        if self.first:
                            d.first_version = new_ver
                else:
                    self.valid_version = False
                    if self.first:
                        d.first_version = d.version

        # Handle file read errors
        except Exception as e:
            if self.bad_records >= 20:
                raise Exception("Too many lines failed CRC check - Aborting")
            if not silent:
                mock_line = None
                if line_parts and len(line_parts) > 4:
                    mock_line = line_parts.copy()
                    mock_line.insert(2, line_parts[1])
                try:
                    ref_message = "file: {} line: {}".format(self.batch_files[self.current_file_idx]["name"],
                                                             self.current_line_idx)
                except Exception as e2:
                    ref_message = str(e2)
                message = "Error while reading line from batch file"
                em.log_error(ve.Programs.REPORTING, ve.ErrorCat.RECORD_ERROR, sub_cat, message, e, r_type,
                             line=mock_line, r_id=ref_message)

        # Return line
        return line_parts, next_is_7203, self.current_file_name

    def read_bin_file(self, filename: str):
        """
        Read raw data from file in TAR, specified by filename.
        :param filename: Name of file to access.
        :return: Binary contents of file.
        """

        # Read file
        file_path = os.path.join(self.path, self.temp_path, self.tar)
        with tarfile.open(file_path, 'r:') as tar_file:
            file_member = tar_file.extractfile(filename)
            return file_member.read()

    def read_log_file_series(self, series: int):
        """
        :param series: Log file series.
        :return: Concatenated binary data, filename index by byte address.
        """

        # Read each file into memory
        bin_data = b''
        filenames = []
        addr = 0
        files = getattr(self, "slogger_{}_files".format(series))
        file_path = os.path.join(self.path, self.temp_path, self.tar)
        with tarfile.open(file_path) as tar_file:
            for file in files:
                filenames.append([addr, file])
                file_member = tar_file.extractfile(file)
                file_data = file_member.read()
                addr += len(file_data)
                bin_data += file_data
        return bin_data, filenames

    def reset(self):
        """ Reset reader to beginning of batch records. """
        self.first = False
        self.bad_records = 0
        self.file_data = None
        self.last_file = False
        self.more_lines = True
        self.current_file_idx = 0
        self.current_line_idx = 0
        self.valid_version = False


def _get_max_batch(batch: str):
    """ Determine maximum possible batch number. """
    max_str = ""
    for _ in range(0, len(batch)):
        max_str += '9'
    return int(max_str)
