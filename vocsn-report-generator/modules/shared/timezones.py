#!/usr/bin/env python
"""
Data class object definitions for

    Version Notes:
        0.0.0.1 - 07/03/2018 - Created file
        1.0.0.0 - 07/24/2018 - Ready for internal testing.
        1.0.0.1 - 10/29/2018 - Added handler for time inputs.

"""

# Built-in Python libraries
import pytz
from datetime import datetime


__author__ = "John Dorian for Sai Systems Technologies"
__copyright__ = "Copyright 2018"
__version__ = "1.0.0.1"


"""
Time Zone Conversions
---------------------
Provides time zone conversion functions.
"""


def to_utc(time_string, from_tz):
    """
    Convert a time from a specified time zone to UTC.
    :param time_string: Time string ('YYYY-MM-DD')
    :param from_tz: (str) pytz timezone
    :return: time zone aware datetime in UTC
    """

    # Define time zones
    utc = pytz.utc
    loc_tz = pytz.timezone(from_tz)

    # Convert time
    if len(time_string.split(' ')) > 1:
        naive_time = datetime.strptime(time_string, '%Y-%m-%d %H:%M:%S.%f')
    else:
        naive_time = datetime.strptime(time_string, '%Y-%m-%d')
    local_time = loc_tz.localize(naive_time)
    utc_time = local_time.astimezone(utc)

    return utc_time


def to_local(time_string, to_tz):
    """
    Convert a time from UTC to a specified time zone.
    :param time_string: Time string ('YYYY-MM-DD')
    :param to_tz: (str) pytz timezone
    :return: time zone aware datetime in specified local time zone.
    """

    # Define time zones
    utc = pytz.utc
    loc_tz = pytz.timezone(to_tz)

    # Convert time
    if isinstance(time_string, datetime):
        naive_time = time_string
    else:
        if len(time_string.split(' ')) > 1:
            naive_time = datetime.strptime(time_string, '%Y-%m-%d %H:%M:%S.%f')
        else:
            naive_time = datetime.strptime(time_string, '%Y-%m-%d')
    utc_time = utc.localize(naive_time)
    local_time = utc_time.astimezone(loc_tz)

    return local_time


def now_utc_pac():
    """Get a datetime for now in UTC and Pacific time."""
    # Time
    now_utc = pytz.utc.localize(datetime.utcnow())
    tz = pytz.timezone("US/Pacific")
    now_pac = now_utc.astimezone(tz)
    return now_utc, now_pac
