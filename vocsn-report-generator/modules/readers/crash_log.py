#!/usr/bin/env python
"""
Crash Log interpreter. Reads crash log binaries for integration with the Multi-View Reporting
system to consolidate event and maintenance data into a combined log.

    Version Notes:
        1.0.0.0 - 03/29/2020 - Created file with SlogParser and SlogLine classes.
        1.0.0.1 - 04/08/2020 - Moved CSV line constructor to vocsn-combined-log project.
        1.0.0.2 - 04/13/2020 - Added CRC placeholders, added fields for combined log.

"""

__author__ = "Ventec Life Systems and John Dorian for Sai Systems Technologies"
__copyright__ = "Copyright 2019"
__version__ = "1.0.0.2"

# Built-in modules
import time
from struct import unpack
from datetime import datetime

# VOCSN modules
from modules.models.errors import ErrorManager
from modules.processing.time import TimeTracker
from modules.models.vocsn_data import VOCSNData
from modules.models.vocsn_enum import LogRecordType


class CrashLine:
    """ System log line record. """

    def __init__(self, tm: TimeTracker, record: dict, seq: int):
        """ Construct system log record. """

        # Prepare times
        ts = float(record['secs'])
        syn_ts = tm.get_synthetic_time(ts)
        record['syn_secs'] = syn_ts

        # Store values
        self.record_type = LogRecordType.CRASH_LOG
        self.crc_result = "N/A"
        self.sequence = seq
        self.data = record
        self.raw_ts = ts
        self.syn_ts = syn_ts
        self.raw_time = datetime.utcfromtimestamp(self.raw_ts)
        self.syn_time = datetime.utcfromtimestamp(self.syn_ts)
        self.filename = record['file']
        self.raw_data = str(record)

    def __str__(self):
        """ String converter. """
        d = self.data
        return 'Expression: {}, file: {}, line: {}'.format(d['expression'], d['file'], d['line'])


class CrashParser:
    """ Crash log parser. """

    record_length = 248

    def __init__(self, em: ErrorManager, v_data: VOCSNData, _data, **kwargs):

        self.records = list()
        keys = kwargs.keys()
        self.src_filename = None
        if 'file' in keys:
            self.src_filename = kwargs['file']

        self.is_json = False
        if 'json' in keys:
            self.is_json = kwargs['json']

        self.is_local = False
        if 'local' in keys:
            self.is_local = kwargs['local']

        self.timeformatstr = '%Y-%m-%d %H:%M:%S'
        if 'time_format' in keys and kwargs['time_format'] is not None:
            self.timeformatstr = kwargs['time_format']

        self.verbose = False
        if 'verbose' in keys:
            self.verbose = kwargs['verbose']

        records = list(self.parse_records(_data, self.record_length))

        seq = 0
        for record in records:

            # Expression = 108 char string
            # File = 128 char string
            # Line = unsigned int
            # Value = int
            # Time = unsigned int
            expression, file, line, value, secs = unpack('108s128sIiI', record)
            expression = expression.decode(encoding='ascii', errors='replace').split("\0")[0]
            file = file.decode(encoding='ascii', errors='replace').split("\0")[0]

            if self.is_local:
                timestamp = time.strftime(self.timeformatstr, time.localtime(secs))
            else:
                timestamp = time.strftime(self.timeformatstr, time.gmtime(secs))

            data = {'expression': expression, 'file': file, 'line': line, 'value': value, 'secs': secs,
                    'timestamp': timestamp}
            seq += 1
            rec = CrashLine(v_data.time_manager, data, seq)
            self.records.append(rec)

    def get_record(self, _index):
        return self.records[_index]

    def get_record_count(self):
        return len(self.records)

    @staticmethod
    def parse_records(_list, n):
        # Using list comprehension
        chunk_count = (len(_list) + n - 1) // n
        return [_list[i * n: (i + 1) * n] for i in range(chunk_count)]
