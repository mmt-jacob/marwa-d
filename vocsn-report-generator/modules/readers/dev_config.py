#!/usr/bin/env python
"""
Device config interpreter. Reads and interprets device config files for integration with the Multi-View Reporting
system to consolidate event and maintenance data into a combined log.

    Version Notes:
        1.0.0.0 - 03/30/2020 - Created file with SlogParser and SlogLine classes.
        1.0.0.1 - 04/08/2020 - Moved CSV line constructor to vocsn-combined-log project.
        1.0.0.2 - 04/13/2020 - Added CRC check, added fields for combined log.

"""

__author__ = "Ventec Life Systems and John Dorian for Sai Systems Technologies"
__copyright__ = "Copyright 2019"
__version__ = "1.0.0.2"

# Built-in modules
import crc16
from struct import calcsize, unpack_from

# VOCSN modules
from modules.models.errors import ErrorManager
from modules.models.vocsn_enum import LogRecordType


class DevConfLine:
    """ System log line record. """

    def __init__(self, data, record: dict, line_num: int, crc_result: str, filename: str):
        """ Construct system log record. """

        # Store values
        self.record_type = LogRecordType.DEV_CONFIG
        self.crc_result = crc_result
        self.sequence = line_num
        self.data = {
            'raw_time': None,
            'syn_time': None,
            'info': record,
            'sequence': line_num
        }
        self.raw_time = data.last_batch_raw
        self.syn_time = data.last_batch_syn
        self.filename = filename
        self.raw_data = str(record)

        # Format key/value pairs
        self.key = list(record.keys())[0]
        self.value = record[self.key]

    def __str__(self):
        """ String converter. """
        return '{}: {}'.format(self.key, self.value)


class DevConfParser:
    """ Device config parser. """

    def __init__(self, em: ErrorManager, mvr_data, _data, filename):
        """
        Instantiate parser and parse data.
        :param em: Error manager.
        :param mvr_data: VOCSN data container.
        :param _data: Binary data from files.
        :param filename: Source filename.
        """

        # Variables
        self.records = []

        key_fmt = 33 * 's'
        value_fmt = 33 * 's'
        reserved_fmt = '<H'
        crc16_fmt = '<H'

        def string_from_bytes(_bytes):
            s = [(c.decode('utf-8)')) for c in _bytes if c != b'\00']
            return ''.join(s)

        offset = 0
        line = 0
        while offset < len(_data):

            # Read data line
            pair = {}
            start_offset = offset
            key = string_from_bytes(unpack_from(key_fmt, _data, offset))
            offset += calcsize(key_fmt)
            value = string_from_bytes(unpack_from(value_fmt, _data, offset))
            offset += calcsize(value_fmt)
            offset += calcsize(reserved_fmt)
            crc_orig = unpack_from(crc16_fmt, _data, offset)[0]
            end_offset = offset
            offset += calcsize(crc16_fmt)
            pair[key] = value
            line += 1

            # Check CRC
            data_line = _data[start_offset:end_offset]
            crc_new = crc16.crc16xmodem(data_line, 0xffff)
            if crc_orig == crc_new:
                crc_result = "PASS"
            else:
                crc_result = "FAIL"

            # Construct data container
            self.records.append(DevConfLine(mvr_data, pair, line, crc_result, filename))
