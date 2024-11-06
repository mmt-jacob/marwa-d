#!/usr/bin/env python
"""
Sample data used to generate demonstration reports.

    Version Notes:
        1.0.0.0 - 07/22/2019 - Created file with sample data for Usage report.
        1.0.0.1 - 10/02/2019 - Added reference to eID enum.
        1.0.0.2 - 10/04/2019 - Renamed timestamp fields.
        1.0.0.4 - 10/05/2019 - Moved metadata import to usage.py
        1.0.0.5 - 10/15/2019 - Moved monitor data read to usage.py

"""

__author__ = "John Dorian for Sai Systems Technologies"
__copyright__ = "Copyright 2019"
__version__ = "1.0.0.5"

# Built-in modules
from datetime import datetime

# VOCSN Modules
from modules.models import vocsn_data as vd
from modules.models.event_types import Event
from modules.models.vocsn_enum import EventIDs as eID


def sample_data():
    """Data container for VOCSN log data"""

    # Create VOCSN data container
    model = "VOCSN"
    version = 0.1
    config = "V+O+C+S+N+Pro"
    sn = "123456"
    data = vd.VOCSNData()

    # Return populated data
    return data


def load_data(data: vd.VOCSNData):
    """ Load sample data from json object. """

    # # Load monitor data
    # filename = os.path.join("..", "demo", "sample_data", "demo.csv")
    #
    # with open(filename, 'r') as file:
    #
    #     # Process data from monitor data CSV
    #     reader = csv.reader(file, delimiter=',')
    #     headers = next(reader, None)
    #     row_num = 0
    #     for row in reader:
    #
    #         # Get record metadata
    #         seq = row[0]
    #         ts = row[1]
    #         m_type = row[2]
    #         col_num = 3
    #
    #         # Load records
    #         bad_channels = []
    #         while col_num < len(row) - 3:
    #             key = headers[col_num].strip().split('_')[0]
    #             val1 = row[col_num].strip()
    #             val2 = row[col_num + 1].strip()
    #             val3 = row[col_num + 2].strip()
    #             time = row[col_num + 3].strip()
    #             col_num += 4
    #             if key in data.monitors_all:
    #                 channel = data.monitors_all[key]
    #                 fill = float(time) / 5
    #                 channel.add_record(seq, ts, fill, val1, val2, val3)
    #             else:
    #                 bad_channels.append(key)
    #                 print("Warning: Bad monitor channel: {}".format(key))
    #                 # TODO: add to errors
    #             # col_num += 1
    #         row_num += 1
    #
    # # Load demo data file
    # demo_data = os.path.join("..", "demo", "sample_data", "eventlog.json")
    # j_data = rj.read_json(demo_data)

    # Step through events
    limiter = 10000
    count = 0
    for record in reversed(j_data):
        if count >= limiter:
            break
        count += 1

        # Construct event
        event = Event()

        # Interpret event
        for attr, val in record.items():
            if attr == "sequence":
                event.sequence = val
            if attr == "eventId":
                event.id = val
            if attr == "mTs":
                event.raw_time = val
                event.timestamp = val
                event.datetime = datetime.fromtimestamp(val)
            if attr == "mTsOverflow":
                event.time_overflow = val == 1
            if attr == "event":
                event.name = val
            if attr == "isCrcOkEntry":
                event.crc_ok = val == 1
            if attr == "details":
                event.details = val
                # for d_attr, d_val in val.items():
                #     event.details.append(event.Detail(d_attr, d_val))
            if False:
                event.is_on_off = val == "true"

        # Skip unwanted records (e.g. eof)
        if not event.datetime:
            continue

        # Store event
        data.events_all.append(event)
        if event.id in [eID.ALARM_START, eID.ALARM_END]:
            data.events_alarm.append(event)
        if event.id in [eID.VENT_START, eID.VENT_END, eID.THERAPY_START, eID.THERAPY_END]:
            data.events_therapy.append(event)
        # if event.event_id in [6014, 6015]:
        #     data.alerts.append(event)
        # if event.event_id in [6006]:
        #     data.config.append(event)


