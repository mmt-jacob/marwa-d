#!/usr/bin/env python
"""
Read settings out of strings files and return dictionary objects.

    Version Notes:
        1.0.0.0 - 06/13/2018 - Created file with get_credentials and get_defaults.
        1.0.0.1 - 07/08/2018 - Added facility blacklist function.
        2.0.0.0 - 07/15/2018 - Changed from returning dictionaries to returning result class with dictionary payload.
                               Added email credentials.
        2.0.0.1 - 07-17-2018 - Changed the functions to return a list of a status instance alongside the payload.
                               Tweaked the error formatting.
        2.0.0.2 - 07/18/2018 - Improved error handling.
        2.0.0.3 - 07/18/2018 - Added report archive directory function.
        2.0.0.4 - 07/24/2018 - Made some changes to use correct system directory separator characters.
        2.1.0.0 - 11/02/2018 - Added features for Status Monitor
        2.1.0.1 - 11/06/2018 - Added timeouts config file.
        2.1.0.2 - 11/07/2018 - Turned Timeouts into a proper class.
        2.2.0.0 - 01/10/2019 - Added legacy settings and low signal threshold.
        2.2.1.0 - 01/22/2020 - Cleaned unused functions.
        2.3.0.0 - 01/23/2020 - Changed to shared settings file with web system.
        2.3.0.1 - 01/27/2020 - Added production variable.
        2.4.0.0 - 02/13/2020 - Moved system settings to unified .env file.
        2.4.0.1 - 03/09/2020 - Updated to database-driven configuration format.

"""

__author__ = "John Dorian for Sai Systems Technologies"
__copyright__ = "Copyright 2018"
__version__ = "2.4.0.1"

# Built-in
import os
import traceback
from datetime import timedelta

# Companion scripts
from modules.shared import status


def get_azure_credentials(prod: bool):
    """
    Read Azure credentials from file.
    :param prod: If true, use production configuration.
    :return: List containing error manager and dictionary with account and key.
    """

    # Vars
    config_file = '../.env'
    result = status.GeneralResultErrorManager()
    settings = Settings()
    credentials = {}

    # Read file
    try:
        if not os.path.exists(config_file):
            config_file = "../{}".format(config_file)
        with open(config_file, 'r') as fd:
            for line in fd:
                try:
                    if len(line) > 0 and '=' in line and line[0] is not '#':
                        key, val = line.replace(' ', '').split('=')[0:2]
                        if key == "TABLE_NAME":
                            credentials['account'] = val.strip()
                        elif key == "TABLE_KEY":
                            credentials['key'] = val.strip().ljust(88, '=')
                        elif key == "REPORT_CHECK_FREQUENCY":
                            settings.frequency = timedelta(seconds=int(val.strip()))
                        elif key == "REPORT_WORKERS":
                            settings.processes = int(val.strip())
                        elif key == "REPORT_CLEANUP_HOUR":
                            settings.cleanup_hour = int(val.strip())
                except Exception as e:
                    str(e)
        if 'account' not in credentials or 'key' not in credentials or not \
                (settings.frequency and settings.processes and settings.cleanup_hour):
            result.set_error('Azure credentials not found in system configuration file.\nFile: {}\n'.format(config_file))
    except FileNotFoundError:
        result.set_error('Unable to open shared system configuration file.\nFile: {}\n'.format(config_file))
        result.message += traceback.format_exc()
    except Exception as error:
        result.set_error('Unexpected error while reading shared system configuration file.\nFile: {}\n'
                         .format(config_file))
        result.message += "{}".format(str(error))
        result.message += traceback.format_exc()

    # Return result
    return result, credentials, settings


class Settings:
    """Object used for storing timeouts for facility/CMS/monitor."""
    def __init__(self):
        self.frequency = 1
        self.processes = 2
        self.cleanup_hour = 14
