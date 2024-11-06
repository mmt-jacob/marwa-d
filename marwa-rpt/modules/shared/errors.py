#!/usr/bin/env python
"""
Classes to manage error states and messages. The following terms have specific scope:
    "Error" - A report report has failed.
    "Critical" - An entire period has failed.
    "Fatal" - An entire report session has failed.

    Version Notes:
        0.0.0.1 - 07/14/2018 - Created file with a general error manager and one for Period scripts.
        0.0.0.2 - 07/17/2018 - Created a MainErrorManager class or the Reports Manager script. Removed the payload, so
                               these error status classes will be returned in a list alongside payloads.
        0.0.0.3 - 07/18/2018 - Tweaked some attribute names.
        0.0.0.4 - 07-19-2018 - Added some attributes to the PeriodErrorManager class.
        1.0.0.0 - 07/24/2018 - Ready for internal testing.

"""

__author__ = "John Dorian for Sai Systems Technologies"
__copyright__ = "Copyright 2018"
__version__ = "1.0.0.0"


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


class MainErrorManager:
    """Track error states and messages for the Reports Manager."""

    def __init__(self):
        """Initialize error manager instance."""

        # Error status properties
        self.have_fatal = False
        self.have_critical = False
        self.have_error = False
        self.critical_count = 0
        self.error_count = 0
        self.reports_delivered = 0
        self.reports_failed = 0

        # Period status properties
        self.periods = []

        # Messages
        self.messages = []

        # Stats
        self.run_time = None
        self.start_time = None

    def add_error(self, message, fatal=False):
        """
        Record error.
        :param message: Error message.
        :param fatal: (bool) True indicates a fatal error. Entire will abort.
        """

        # Store values
        self.have_fatal = fatal
        self.have_error = True
        self.error_count += 1
        self.messages.append(message)

    def any_error(self):
        """Check if there were any errors."""
        return self.have_error or self.have_critical or self.have_fatal


class PeriodErrorManager:
    """Track error states and messages for Period scripts."""

    def __init__(self, period):
        """Initialize error manager instance."""

        # Period
        self.period = period

        # Error status properties
        self.have_critical = False
        self.have_error = False
        self.error_count = 0

        # Report status properties
        self.reports_generated = 0
        self.reports_available = 0
        self.reports_unavailable = 0
        self.reports = ReportStatus()

        # Messages
        self.messages = []

        # Not used. Just creates consistency with main type.
        self.have_fatal = False

    def add_error(self, message, critical=False):
        """
        Record error.
        :param message: Error message.
        :param critical: (bool) True indicates a fatal error. Period will abort.
        """

        # Store values
        self.have_critical = critical
        self.have_error = True
        self.error_count += 1
        self.messages.append(message)

    def any_error(self):
        """Check if there were any errors."""
        return self.have_error or self.have_critical


class ReportStatus:
    """Tracks report status for Period scripts."""

    def __init__(self):
        """Initialize report status instance."""

        # Report status properties
        self.generated_success = 0
        self.generated_failed = 0
        self.delivered_success = 0
        self.delivered_failed = 0
