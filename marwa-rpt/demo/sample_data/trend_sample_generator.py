#!/usr/bin/env python
"""
Generate sample trend data for creating and testing reports

    Version Notes:
        1.0.0.0 - 08/26/2019 - Created file.

"""

__author__ = "John Dorian for Sai Systems Technologies"
__copyright__ = "Copyright 2019"
__version__ = "1.0.0.0"

# Built-in modules
import os
import csv
import sys
import json
import random
import traceback
import numpy as np
from datetime import datetime, timedelta

# VOCSN modules
from demo import sample_data as sd


# Starting values
#   Values are generated on two random cycles. A long
#   random cycle is used to "shape" the data. The contour
#   of this "shape" is defined periodically with targets.
#   A short random cycle is used to introduce "noise".
#
#   Value definitions [start, min, max, range, short, long]
#     start:  Starting value
#     min:    Minimum target value
#     max:    Maximum target value
#     range:  Short random cycle range (percent)
#     short:  Shortest sample count between target change
#     long:   Longest sample count between target change
start_vals = {
    'airwayPresMonitorID':              [   7,    5,   9,  7,  30,   90],
    'meanAirwayPresMonitorID':          [ 6.5,    6,   7,  2,  90,  150],
    'peakInspPresMonitorID':            [   8,    5,  11,  5,  30,   90],
    'peepMonitorID':                    [ 7.5,    7,  10,  5,  90,  200],
    'I2ERatioID':                       [0.75,  0.5,   1,  5,  30,   90],
    'exhTidalVolumeMonitorID':          [   5,    4,   7,  5,  30,   90],
    'minuteVolumeMonitorID':            [   5,    4,   7,  5,  30,   90],
    'breathRateMonitorID':              [  14,   10,  20,  7,  30,   90],
    'leakFlowMonitorID':                [  20,   15,  25,  5,  30,   90],
    'patientTrigBreathsMonitorID':      [  80,   60,  95,  5,  30,   90],
    'monitorFIO2':                      [  80,   60,  95,  2,  30,   90],
    'EstFiO2MonitorID':                 [  80,   60,  95,  2,  30,   90],
    'sysIntBattAbsSOCMonitorID':        [ 100,   50,  90,  0, 600, 1200],
    'sysRemBatt1AbsSOCMonitorID':       [ 100,   50,  90,  0, 600, 1200],
    'sysRemBatt2AbsSOCMonitorID':       [ 100,   50,  90,  0, 600, 1200],
    'sysIntBattRelSOCMonitorID':        [ 100,   50,  90,  0, 600, 1200],
    'sysRemBatt1RelSOCMonitorID':       [ 100,   50,  90,  0, 600, 1200],
    'sysRemBatt2RelSOCMonitorID':       [ 100,   50,  90,  0, 600, 1200],
    'o2ConcPhase4DeltaRpmMonitorID':    [ 120,  110, 130,  2,  30,   90],
    'CoughAirwayPresMonitorID':         [   8,    5,  11,  5,  30,   90],
}


# Monitor data generator class
class MonitorData:

    def __init__(self, mid, chnl):

        # ID, Definition
        self.id = mid
        self.channel = chnl

        # Data generation parameters
        vals = start_vals[chnl.tag_name]
        self.start = vals[0]
        self.min = vals[1]
        self.max = vals[2]
        self.range = vals[3]
        self.short = vals[4]
        self.long = vals[5]

        # Tracking values
        self.current = self.start
        self.count = 0
        self.target = 0
        self.target_count = 0

        # Start values
        self.get_target()

        # Records
        self.data = []

    def get_target(self):
        self.target = int(round(random.uniform(self.min, self.max)))
        self.target_count = int(round(random.uniform(self.min, self.max)))

    def __loguniform(self, v_range, sign=None):
        if not sign:
            sign = random.randint(0, 1)
        val = random.uniform(0, 1) ** 2 * v_range
        if sign:
            val = -val
        # print("{}   {}".format(v_range, val))
        return val

    def next(self):

        # Set new target
        self.count += 1
        if self.count >= self.target_count:
            self.count = 0
            self.get_target()
        self.current = self.current + (self.target - self.current) * (1 / self.target_count)
        val_50 = self.current * ((100 + self.__loguniform(self.range)) / 100)
        # print(self.current)
        # print(val_50)
        val_95 = val_50 + ((self.current * 0.2) * ((100 + self.__loguniform(self.range * 10, 1)) / 100))
        val_05 = val_50 - ((self.current * 0.2) * ((100 + self.__loguniform(self.range * 10, 0)) / 100))
        self.data.append([val_05, val_50, val_95])


# Settings
channels = 19
days = 30
samples = days * 24 * 12

# Retrieve sample data
data = sd.sample_data()

# Populate models from metadata
context = ""
filename = os.path.join(context, "TrendMetaData_NOT_SET.json.bak")
with open(filename, 'r') as file:
    monitor_defs = json.load(file)
    for m_key, m_def in monitor_defs['Parameters'].items():
        if m_def['data_class'] == "Monitor":
            data.add_monitor(m_key, m_def)

# Create monitor data generators
generators = []
for m_id, channel in data.monitors_all.items():
    if '_' not in m_id:
        if channel.tag_name in start_vals.keys():
            generators.append(MonitorData(m_id, channel))

# Generate data
for gen in generators:
    for x in range(0, samples):
        gen.next()

# Convert to data table for csv
time = datetime(year=2019, month=5, day=1)
csv_data = []
headers = ["sequence", "timestamp", "type"]
for gen in generators:
    headers.append(str(gen.id) + "_05")
    headers.append(str(gen.id) + "_50")
    headers.append(str(gen.id) + "_95")
    headers.append(str(gen.id) + "_Time")
for x in range(0, samples):
    line = [x, time.timestamp(), "M"]
    for gen in generators:
        line.append(gen.data[x][0])
        line.append(gen.data[x][1])
        line.append(gen.data[x][2])
        line.append(5)
    csv_data.append(line)
    time += timedelta(minutes=5)

# Write csv
with open('demo.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile, delimiter=',')
    writer.writerow(headers)
    for x in range(0, samples):
        writer.writerow(csv_data[x])
