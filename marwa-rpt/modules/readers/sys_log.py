#!/usr/bin/env python
"""
System log interpreter. Developed by Ventec Life Systems to read binary data from system log (slogger) files and
construct human-readable text. Adapted by SAI Systems Techonologies for integration with the Multi-View Reporting
system to consolidate event and maintenance data into a combined log.

    Version Notes:
        1.0.0.0 - 03/29/2020 - Created file with SlogParser and SlogLine classes.
        1.0.0.1 - 04/08/2020 - Moved CSV line constructor to vocsn-combined-log project.
        1.0.0.2 - 04/13/2020 - Added CRC placeholders and filename tracking.

"""

__author__ = "Ventec Life Systems and John Dorian for Sai Systems Technologies"
__copyright__ = "Copyright 2019"
__version__ = "1.0.0.2"

# Built-in modules
import time
from struct import unpack
from datetime import datetime

# VOCSN modules
from modules.processing.time import TimeTracker
from modules.models.vocsn_data import VOCSNData
from modules.models.vocsn_enum import LogRecordType


class SlogLine:
    """ System log line record. """

    def __init__(self, tm: TimeTracker, record: dict, log_num: int, seq: int):
        """ Construct system log record. """

        # Prepare times
        ts = float(record['info']['secs'])
        ms = float(record['info']['msec'])
        syn_ts = tm.get_synthetic_time(ts)
        record['info']['syn_secs'] = syn_ts

        # Store values
        self.record_type = LogRecordType.SYS_LOG_2 if log_num == 1 else LogRecordType.SYS_LOG_1
        self.crc_result = "N/A"
        self.data = record
        self.sequence = seq
        self.raw_ts = ts + 0.001 * ms
        self.syn_ts = syn_ts
        self.raw_time = datetime.utcfromtimestamp(self.raw_ts)
        self.syn_time = datetime.utcfromtimestamp(self.syn_ts)
        self.filename = record['filename']
        self.raw_data = str(record)

    def __str__(self):
        """ String converter. """
        return self.data['text']


class SlogParser:
    """ System log parser. """

    # Location markers
    header_int_count = 3
    header_byte_count = 12

    def __init__(self, v_data: VOCSNData, _data, file_index, log_num, **kwargs):
        """
        Instantiate parser and parse data.
        :param v_data: VOCSN data container.
        :param _data: Concatenated binary data from all log files in series.
        :param file_index: list of byte address/filename pairs.
        :param log_num: Log series number.
        :param kwargs: Keyword arguments
        """

        keys = kwargs.keys()
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

        self.size_bytes = len(_data)
        self.records = []
        records = list(self.parse(_data, file_index))
        seq = 0
        for rec in records:
            seq += 1
            self.records.append(SlogLine(v_data.time_manager, rec, log_num, seq))

    def parse(self, _data, file_index):
        ptr = 0

        file_ptr = 0
        while ptr < self.size_bytes:
            while file_ptr < len(file_index) - 1 and ptr < file_index[file_ptr + 1][0]:
                file_ptr += 1
            filename = file_index[file_ptr][1]
            if self.is_ham(_data[ptr: ptr + self.header_byte_count]):
                ptr, record, raw = self.parse_ham_record(_data, ptr)
            else:
                ptr, record, raw = self.parse_record(_data, ptr)
            record['filename'] = filename
            yield record

    def is_ham(self, _header):
        header = unpack('{}I'.format(self.header_int_count), _header)
        major = header[1] & 0xfffff
        return major == 0

    def parse_header(self, _header):
        header = unpack('{}I'.format(self.header_int_count), _header)

        secs = header[2]
        if self.is_local:
            timestamp = time.strftime(self.timeformatstr, time.localtime(secs))
        else:
            timestamp = time.strftime(self.timeformatstr, time.gmtime(secs))
        msec = (header[0] >> 4) & 0x3ff
        severity = header[0] & 0x07
        major = header[1] & 0xfffff
        minor = (header[1] >> 20) & 0xfff

        count = ((header[0] >> 16) & 0xff) + self.header_int_count
        msg_byte_count = 4 * (count - self.header_int_count)

        info = {'secs': secs, 'timestamp': timestamp, 'msec': msec, 'severity': severity, 'major': major,
                'minor': minor, 'count': count}

        return msg_byte_count, info

    def parse_record(self, _data, _ptr):
        msg_byte_count, info = self.parse_header(_data[_ptr: _ptr + self.header_byte_count])

        total_byte_count = self.header_byte_count + msg_byte_count

        raw_record = _data[_ptr: _ptr + total_byte_count]
        raw_msg = raw_record[self.header_byte_count:]

        message = raw_msg.decode(encoding='ascii', errors='replace').split("\0")[0]
        message = message.rsplit('\n', 1)[0]

        return _ptr + total_byte_count, {'info': info, 'text': message}, raw_record

    def parse_ham_record(self, _data, _ptr):
        ptr, record, raw = self.parse_record(_data, _ptr)

        while ptr + self.header_byte_count < self.size_bytes and self.is_ham(_data[ptr: ptr + self.header_byte_count]):
            ptr, ham_record, ham_raw = self.parse_record(_data, ptr)
            record['text'] += ham_record['text']
            raw += ham_raw
        #  Prepend text message with HAM LOG:
        record['text'] = 'HAM LOG:  ' + record['text']
        return ptr, record, raw
