#!/usr/bin/env python
"""
Usage monitor interpreter. Reads binary data from usageMonitor.dat files for integration with the Multi-View Reporting
system to consolidate event and maintenance data into a combined log.

    Version Notes:
        1.0.0.0 - 03/29/2020 - Created file with UsageMon and UsageLine classes.
        1.0.0.1 - 03/30/2020 - Added csv field list functions.
        1.0.0.2 - 04/08/2020 - Moved CSV line constructor to vocsn-combined-log project.
        1.0.0.3 - 04/13/2020 - Added CRC check.

"""

__author__ = "Ventec Life Systems and John Dorian for Sai Systems Technologies"
__copyright__ = "Copyright 2019"
__version__ = "1.0.0.2"

# Built-in modules
import json
import crc16

# VOCSN modules
from modules.models.errors import ErrorManager
from modules.models.vocsn_enum import LogRecordType


class UsageLine:
    """ Usage monitor line record. """

    def __init__(self, data, record: dict, seq: int, crc_result: str, filename):
        """ Construct system log record. """

        # Store values
        self.record_type = LogRecordType.USAGE_MON
        self.crc_result = crc_result
        self.sequence = seq
        self.data = record
        self.raw_time = data.last_batch_raw
        self.syn_time = data.last_batch_syn
        self.filename = filename
        self.key = ""
        self.value = ""
        self.raw_data = str(record)

        # Format keys/value pairs
        d = self.data
        if "version" in d.keys():
            self.key = "sysVersion"
            self.value = d['version']
        else:
            if "ticks" in d.keys():
                self.key = d['id'].split('.')[-1]
                self.value = "{} hours, {} ticks".format(d['hours'], d['ticks'])
            else:
                self.key = d['id'].split('.')[-1]
                self.value = "{} hours".format(d['hours'])

    def __str__(self):
        """ String converter. """
        return "{}: {}".format(self.key, self.value)


class UsageParser:
    """ Crash log parser. """

    def __init__(self, em: ErrorManager, mvr_data, _data, filename):
        """
        Instantiate parser and parse data.
        :param em: Error mananger.
        :param mvr_data: VOCSN data container.
        :param _data: Binary data from files.
        :param filename: Source filename.
        """

        # Variables
        self.records = []

        # Read monitor lines
        seq = 0
        for line in _data.split(b'\n'):
            if b'{' in line:

                # Parse JSON
                json_rec = json.loads(line)

                # Check CRC
                data_line = bytes(json.dumps(json_rec['record']), "utf-8")
                data_line = data_line.replace(b'{', b'{ ')
                data_line = data_line.replace(b'}', b' }')
                data_line = data_line.replace(b',', b' ,')
                data_line = data_line.replace(b':', b' :')
                crc_orig = json_rec['crc16']
                crc_new = crc16.crc16xmodem(data_line, 0xffff)
                if crc_orig == crc_new:
                    crc_result = "PASS"
                else:
                    crc_result = "FAIL"

                # Create log record
                seq += 1
                rec = json_rec['record']
                self.records.append(UsageLine(mvr_data, rec, seq, crc_result, filename))
