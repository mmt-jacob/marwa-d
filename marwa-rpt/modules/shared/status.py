#!/usr/bin/env python
"""
Classes to manage facility and equipment status, script completion status and errors.

    Version Notes:
        0.0.0.1 - 07/26/2018 - Created file from Report Delivery System shared/errors.py. Started with
                               StatusMonitorTracker and EquipmentStatus.
        1.0.0.0 - 11/02/2018 - Slimmed down file to only handle errors. Connectivity status moved to
                               connection_tracker.py
        1.0.0.1 - 11/12/2018 - Added a success method to the status monitor tracker.
        1.0.0.2 - 02/14/2020 - Corrected StatusMonitorTracker to initialize start_time in init function.
        1.0.0.3 - 03/11/2020 - Added queue time.

"""

__author__ = "John Dorian for Sai Systems Technologies"
__copyright__ = "Copyright 2018"
__version__ = "1.0.0.3"


class GeneralResultErrorManager:
    """Tracks basic error status and message."""

    def __init__(self):
        """Initialize error manager instance."""

        # Error properties
        self.has_error = False
        self.message = ""

    def set_error(self, message):
        """
        Set error.
        :param message: Error message.
        """

        # Store values
        self.has_error = True
        self.message = message


class StatusMonitorTracker:
    """Tracks equipment and error status."""

    def __init__(self):
        """Initialize tracker instance."""

        # Error properties
        self.start_time = None
        self.queue_time = None
        self.have_critical = False
        self.have_fatal = False
        self.have_error = False
        self.messages = []

    def success(self):
        """Report success."""
        return not (self.have_error or self.have_fatal or self.have_critical)

    def add_error(self, message, fatal=False):
        """
        Set error.
        :param message: Error message.
        :param fatal: (bool) If true, error is fatal, meaning the status monitor has failed.
        """

        # Store values
        self.have_error = True
        if fatal:
            self.have_fatal = True
        self.messages.append(message)
