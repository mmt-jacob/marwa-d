#!/usr/bin/env python
"""
Python script for use in command line to update environment file from database.

    Version Notes:
        1.0.0.0 - 03/09/2020 - Created file with update_config function.

"""

__author__ = "John Dorian for Sai Systems Technologies"
__copyright__ = "Copyright 2019"
__version__ = "1.0.0.0"

# Built-in modules
import os
import sys
import argparse

# Azure library
from azure.cosmosdb.table import TableService


def update_config(env_path):
    """ Read configuration environment from file, settings from database, then update local .env file. """

    # Check for file
    if not os.path.exists(env_path):
        raise(Exception("Environment configuration file not found: {}".format(env_path)))

    # Read configuration database information
    print("  Loading configuration source")
    env_source = []
    settings = Settings()
    with open(env_path, 'r') as file:
        for line in file:
            try:
                env_source.append(line)
                if len(line) > 0 and '=' in line and line[0] is not '#':
                    key, val = line.replace(' ', '').split('=')[0:2]
                    if key == "CONFIG_TABLE_NAME":
                        settings.table_name = val.strip()
                    elif key == "CONFIG_TABLE_KEY":
                        settings.table_key = val.strip().ljust(88, '=')
                    elif key == "CONFIG_TABLE":
                        settings.table = val.strip()
                    elif key == "CONFIG_SELECT":
                        settings.config = val.strip()
            except Exception as e:
                str(e)

    # Read config
    print("  Reading configuration")
    table_service = TableService(account_name=settings.table_name, account_key=settings.table_key)
    config = table_service.get_entity(settings.table, settings.config, "")

    # Construct and write .env file
    eol = "\n"
    print("  Constructing configuration file")
    c = ""
    c += "##############################" + eol 
    c += "##                          ##" + eol
    c += "##      Report  System      ##" + eol
    c += "##   Shared Configuration   ##" + eol
    c += "##     (Auto-Generated)     ##" + eol
    c += "##                          ##" + eol
    c += "##############################" + eol
    c += eol
    c += "# Server Configuration" + eol
    c += "REACT_APP_HOST = " + str(config.AppHost) + eol
    c += "REACT_APP_PORT_DEV = " + str(config.AppPortDev) + eol
    c += "REACT_APP_PORT_PROD = " + str(config.AppPortProd) + eol
    c += "REACT_APP_GQL_PORT_DEV = " + str(config.GQLPortDev) + eol
    c += "REACT_APP_GQL_PORT_PROD = " + str(config.GQLPortProd) + eol
    c += eol
    c += "# Azure Table Storage account" + eol
    c += "TABLE_NAME = " + str(config.TableName) + eol
    c += "TABLE_KEY = " + str(config.TableKey) + eol
    c += eol
    c += "# SMTP Email Credentials" + eol
    c += "EMAIL_ADDRESS = " + str(config.EmailAddress) + eol
    c += "EMAIL_HOST = " + str(config.EmailHost) + eol
    c += "EMAIL_PORT = " + str(config.EmailPort) + eol
    c += "EMAIL_IS_SECURE = " + str(config.EmailIsSecure) + eol
    c += "EMAIL_USER = " + str(config.EmailUser) + eol
    c += "EMAIL_PASS = " + str(config.EmailPass) + eol
    c += eol
    c += "# Landing page" + eol
    c += "REACT_APP_USE_VAL_LANDING = " + str(config.ValidationLanding) + eol
    c += eol
    c += "# Session Control" + eol
    c += "REACT_APP_INACTIVITY_SHOWDIALOG = " + str(config.InactivityShowDialog) + eol
    c += "REACT_APP_INACTIVITY_LOGOUT = " + str(config.InactivityLogout) + eol
    c += eol
    c += "# Upload Timeouts" + eol
    c += "REACT_APP_TIMEOUT_PENDING = " + str(config.TimeoutPending) + eol
    c += "REACT_APP_TIMEOUT_UPLOADING = " + str(config.TimeoutUploading) + eol
    c += "REACT_APP_TIMEOUT_QUEUED = " + str(config.TimeoutQueued) + eol
    c += "REACT_APP_TIMEOUT_PROCESSING = " + str(config.TimeoutProcessing) + eol
    c += "REACT_APP_RETRY_DELAY = " + str(config.RetryDelay) + eol
    c += eol
    c += "# Report Generator Settings" + eol
    c += "REPORT_CHECK_FREQUENCY = " + str(config.CheckFrequency) + eol
    c += "REPORT_WORKERS = " + str(config.Workers) + eol
    c += "REPORT_CLEANUP_HOUR = " + str(config.CleanupHour) + eol

    # Update environment config file
    print("Updating timestamp records")
    env = ""
    for line in env_source:
        if "LAST_DB_UPDATE" in line:
            env += "LAST_DB_UPDATE = {}{}".format(config.Timestamp, eol)
        else:
            env += line
    with open(env_path, 'w+') as file:
        if env:
            file.write(env)
    if not env:
        raise Exception("Generated blank environment configuration file")

    # Write environment file
    if c:
        env_file = env_path.replace(".conf", "")
        with open(env_file, 'w+') as file:
            file.write(c)
    else:
        raise Exception("Generated blank environment file")
    print("Configuration update complete")

    
class Settings:
    """ Settings container. """
    
    def __init__(self):
        """ Initialize. """
        self.table_name = ""
        self.table_key = ""
        self.table = ""
        self.config = ""


if __name__ == "__main__":
    """ Entry point from command line. """

    # Setup message
    print("VOCSN Multi-View Configuration Updater - v{}".format(__version__))

    # Define arguments and options
    parser = argparse.ArgumentParser(prog="update_config.py", description="Re-write .env file from database.")
    parser.add_argument('env_path', type=str, help='Path to .env.conf')

    # Process arguments and options
    a = parser.parse_args(sys.argv[1:])
    path = a.env_path

    # Start update
    update_config(path)