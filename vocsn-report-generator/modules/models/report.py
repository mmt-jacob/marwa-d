#!/usr/bin/env python
"""
This modules contains report definition objects used to set report parameters including report type, patient
information, date range, and included sections.

    Version Notes:
        1.0.0.0 - 07/21/2019 - Created file with ReportType, Institute, Physician, Patient, ReportRange, and
                               Report classes.
        1.0.0.1 - 07/28/2019 - Added Avenir font, improved formatting, added sections field.
        1.0.0.2 - 09/07/2019 - Renamed some sections.
        1.0.0.3 - 09/10/2019 - Added report name.
        1.0.0.4 - 09/28/2019 - Changed displayed report end date to be inclusive, ending at end of day.
        1.0.0.5 - 10/02/2019 - Added monitor graph tick values.
        1.0.1.0 - 10/10/2019 - Changed trend calculations to compare to entire report range.
        1.0.1.1 - 10/23/2019 - Moved some items out of initialization to simplify interaction with report generator
        1.0.1.2 - 11/01/2019 - Added a set_language method.
        1.0.1.3 - 11/02/2019 - Added a trend day field to range.
        1.0.1.4 - 11/03/2019 - Added a report range day field.
        1.0.1.5 - 11/05/2019 - Corrected range calculation.
        1.0.1.6 - 11/19/2019 - Added a flag to disable trend when ont used on a report.
        1.0.1.7 - 11/28/2019 - Added new log sections.
        1.0.2.0 - 12/05/2019 - Implemented patient reset.
        1.0.2.1 - 12/13/2019 - Renamed sections. Ordered section names for cover page. Fixed a bug that could cause an
                               error on reports that don't compute trend values.
        1.0.2.2 - 12/20/2019 - Added support for report ranges of less than one day. Changed active section line to
                               reflect absence of unavailable sections.
        1.0.2.3 - 12/21/2019 - Added patient reset sequence number.
        1.0.2.4 - 12/29/2019 - Changed duration to always hours.
        1.0.2.5 - 01/01/2020 - Sourced report date from input to allow for localization.
        1.0.2.6 - 01/03/2020 - Added report label.
        1.0.2.7 - 01/04/2020 - Added report ID field.
        1.0.3.0 - 01/11/2020 - Added day-aligned report range
        1.0.3.1 - 01/15/2020 - Added a graph sample size for monitor graphs.
        1.0.3.2 - 01/16/2020 - Added patient end time, creating new data-restricted bounds for average calculations.
        1.0.4.0 - 01/17/2020 - Rearranged report range calculations.
        1.0.4.1 - 01/26/2020 - Added data started variable.
        1.0.4.2 - 02/12/2020 - Changed "Config" section display label to "Configuration".
        1.0.4.3 - 03/12/2020 - Added provision to change sequence number only.
        1.0.4.4 - 03/27/2020 - Added trend period field to store unadjusted trend duration.

"""

__author__ = "John Dorian for Sai Systems Technologies"
__copyright__ = "Copyright 2019"
__version__ = "1.0.4.4"

# Built-in modules
import math
from datetime import datetime, timedelta

# VOCSN modules
from modules.models.vocsn_enum import ReportType
from modules.processing.utilities import unit_int_to_td
from modules.processing.graph_range import calc_monitor_graph_x_ticks


class Institute:
    """Institution information"""

    def __init__(self, name: str):
        """
        Instantiate class
        :param name: Name of institution.
        """

        # Institution information
        self.name = name          # str - Name of institution


class Physician:
    """Physician information"""

    def __init__(self, name_fst: str, name_mid: str, name_lst: str, title: str, cred: str):
        """
        Instantiate class
        :param name_fst: First name.
        :param name_mid: Middle name or initial.
        :param name_lst: Last name.
        :param title: Title or credential (e.g. 'Dr.')
        :param cred: Credentials (e.g. 'RRT')
        """

        # Physician information
        self.name_fst = name_fst  # str - Patient first name
        self.name_mid = name_mid  # str - Patient middle name (or initial)
        self.name_lst = name_lst  # str - Patient last name
        self.title = title        # str - Title (e.g. "Dr.")
        self.credentials = cred   # str - Credentials (e.g. 'RRT')

    def full_name(self):
        """Return the full name with titles."""
        name = self.title + " " if self.title else ""
        name += self.name_fst + " " if self.name_fst else ""
        name += self.name_mid + " " if self.name_mid else ""
        name += self.name_lst + " " if self.name_lst else ""
        name += self.credentials + " " if self.credentials else ""
        return name


class Patient:
    """
    Patient class definition.
    NOTE: THIS CONSTITUTES PHI
    """

    def __init__(self, db_id: str, dob: datetime, ref_num: str, name_fst: str, name_mid: str, name_lst: str):
        """Instantiate class"""

        # Patient information
        self.db_id = db_id          # str - Patient ID for internal database records
        self.dob = dob              # datetime - Date of birth
        self.ref_num = ref_num      # str - Patient reference number for user records
        self.name_fst = name_fst    # str - Patient first name
        self.name_mid = name_mid    # str - Patient middle name (or initial)
        self.name_lst = name_lst    # str - Patient last name

    def full_name(self):
        """Return the full name with titles."""
        name = self.name_fst + " " if self.name_fst else ""
        name += self.name_mid + " " if self.name_mid else ""
        name += self.name_lst + " " if self.name_lst else ""
        return name

    def dob_string(self):
        """Return formatted start date"""
        return "{d.month}/{d.day}/{d.year}".format(d=self.dob)


class ReportRange:
    """Report range class"""

    def __init__(self, settings: dict, report_duration: int, start: datetime):
        """
        Instantiate class.
        :param settings: Settings definitions retrieve from JSON settings file corresponding to VOCSN software version.
        :param report_duration: Number of hours
        :param start: First day included in report
        """

        # Settings
        self.use_trend = False
        align_threshold = timedelta(minutes=5)
        
        # Interpret duration hours
        days = report_duration // 24
        hours = report_duration if report_duration < 24 else 0
        duration = timedelta(days=days, hours=hours)

        # States
        self.data_started = False
        
        # Metadata
        self.created = datetime.utcnow()

        # Full report range - matches defined report range
        self.start = start                          # datetime  - Start of report range
        self.end = end = start + duration           # datetime  - End of report range
        self.duration = duration                    # timedelta - Number of days in report range
        self.days = days                            # float     - Number of days of report range
        
        # Valid report range - constrained by:
        #   - Available data
        #   - Power/time loss events
        #   - Patient reset events
        # Set in the _calc_trends function, 
        # called from the time module.
        self.data_start = start                     # datetime  - Start of valid data
        self.data_end = end                         # datetime  - End of valid data
        self.data_duration = duration               # timedelta - total duration of valid data
        self.data_days = days                       # float     - Number of days of valid data
        self.data_sequence = -1                     # int       - Sequence number before first usable data record
        
        # Pre-trend range - Period from start of valid data to defined trend start
        self.pre_trend_start = None
        self.pre_trend_end = None
        self.pre_trend_duration = None
        self.pre_trend_days = None
        
        # Trend range - Period from start defined trend range to end of valid data
        self.trend_start = None
        self.trend_end = None
        self.trend_duration = None
        self.trend_days = None
        self.raw_trend_duration = None
        
        # Day-aligned report range
        # Used to distinguish full days from partial days
        one_day = timedelta(days=1)
        duration_days = timedelta(days=math.floor(self.days))
        start_of_day = datetime(year=start.year, month=start.month, day=start.day)
        close_to_end = start - start_of_day >= one_day - align_threshold
        close_to_start = start - start_of_day <= align_threshold
        self.days_start = start_of_day
        if not close_to_start:
            self.days_start = start_of_day + one_day
        self.days_end = self.days_start + duration_days
        if not (close_to_start or close_to_end) and self.days >= 1:
            self.days_end -= one_day

        # Extract settings dependent on report range
        found = False
        for r_rng in settings['ranges']:
            if report_duration == r_rng['report_duration']:
                found = True

                # Read values from settings
                self.name = r_rng["name"]
                self.trend_period = r_rng['trend_period']
                self.trend_units = r_rng['trend_units']
                self.graph_tick_inc = r_rng['graph_tick_inc']
                self.graph_sub_ticks = r_rng['graph_sub_ticks']
                self.graph_tick_units = r_rng['graph_tick_units']
                self.graph_samples_per_tick = r_rng['graph_samples_per_tick']
                if self.graph_tick_units == "days":
                    self.graph_tick_duration = timedelta(days=self.graph_tick_inc)
                elif self.graph_tick_units == "hours":
                    self.graph_tick_duration = timedelta(hours=self.graph_tick_inc)
                elif self.graph_tick_units == "minutes":
                    self.graph_tick_duration = timedelta(minutes=self.graph_tick_inc)
                else:
                    raise Exception("Unsupported graph tick increment: " + str(self.graph_tick_units))

                # Constrain monitor
                five = timedelta(minutes=5)
                graph_sample_min = self.graph_tick_duration / five
                self.graph_sample_size = self.graph_tick_duration / self.graph_samples_per_tick
                self.graph_samples_per_tick = min(graph_sample_min, self.graph_samples_per_tick)
                break

        # Invalid report range
        if not found:
            raise Exception("Invalid report range")

        self.average_start = start
        self.average_end = end
        self.average_days = self.days
        
        # Calculate trend threshold
        if self.trend_period:
            self.use_trend = True
            self.raw_trend_duration = unit_int_to_td(self.trend_period, self.trend_units)
            self.trend_start = end - self.raw_trend_duration

        # Calculate durations and trend values
        self._calc_trends()

        # Calculate graph tick range
        self.tick_labels = []
        self.tick_times = []
        self.tick_length = self.graph_tick_duration
        calc_monitor_graph_x_ticks(self)
        
    def _calc_trends(self):
        """ Calculate pre-trend and trend ranges. """
        
        # Calculate valid data range
        self.data_duration = self.data_end - self.data_start
        self.data_days = self.data_duration.total_seconds() / 86400
        
        # Ensure both pre-trend and trend ranges have valid data
        if self.use_trend:
            self.use_trend = self.data_start < self.trend_start < self.data_end
            
        # Calculate trend-related durations
        if self.use_trend:
            
            # Pre-trend values
            self.pre_trend_start = self.data_start
            self.pre_trend_end = self.trend_start
            self.pre_trend_duration = self.pre_trend_end - self.pre_trend_start
            self.pre_trend_days = self.pre_trend_duration.total_seconds() / 86400

            # Trend values
            self.trend_end = self.data_end
            self.trend_duration = self.trend_end - self.trend_start
            self.trend_days = self.trend_duration.total_seconds() / 86400

    def set_data_start(self, dt: datetime, sequence: int, seq_only: bool = False):
        """
        Recalculate all data date and range values.
        :param dt: Data start datetime.
        :param sequence: sequence number before first usable record.
        :param seq_only: Only capture sequence number used to filter data processing.
        """

        # Patient range definitions
        self.data_sequence = max(sequence, self.data_sequence)
        if not seq_only:
            self.data_start = min(max(dt, self.start, self.data_start), self.data_end)

        # Update calculations
        self._calc_trends()

    def set_data_end(self, dt: datetime):
        """
        Recalculate data date and range values.
        :param dt: Data start datetime.
        """

        # Data range definitions
        self.data_end = max(min(dt, self.end), self.data_start)

        # Update calculations
        self._calc_trends()

    def start_string(self):
        """Return formatted start date"""
        return "{d.month}/{d.day}/{d.year}".format(d=self.start)

    def range_string(self):
        """Return formatted report range"""
        # day = timedelta(days=1)
        # days = self.duration.total_seconds() / 86400
        # if days < 1:
        #     range_string = "{} {} - {} {}".format("{d.month}/{d.day}/{d.year}".format(d=self.start),
        #                                           "{}:{:02d}".format(self.start.hour, self.start.minute),
        #                                           "{d.month}/{d.day}/{d.year}".format(d=self.end),
        #                                           "{}:{:02d}".format(self.end.hour, self.end.minute))
        # elif days == 1:
        #     range_string = "{}".format("{d.month}/{d.day}/{d.year}".format(d=self.start))
        # else:
        #     range_string = "{} - {}".format("{d.month}/{d.day}/{d.year}".format(d=self.start),
        #                                     "{d.month}/{d.day}/{d.year}".format(d=self.end))
        # return range_string
        return "{} {} - {} {}".format("{d.month}/{d.day}/{d.year}".format(d=self.start),
                                      "{}:{:02d}".format(self.start.hour, self.start.minute),
                                      "{d.month}/{d.day}/{d.year}".format(d=self.end),
                                      "{}:{:02d}".format(self.end.hour, self.end.minute))

    def duration_string(self):
        """Return two-line duration string for cover sheet."""
        trend_units = self.trend_units
        if self.trend_period == 1:
            trend_units = trend_units[:-1]
        days = self.duration.total_seconds() / 86400
        if days <= 1:
            trend_string = "(no trending)"
        else:
            trend_string = "(data trended from last {} {})".format(self.trend_period, trend_units)
        return "{}  {}".format(self.name, trend_string)

    def is_tick(self, time: datetime):
        """ Check if a graph datum time value should be represented with a dot. """
        length = self.tick_length / self.graph_samples_per_tick
        is_tick = False
        for x, tick in enumerate(self.tick_times):
            if self.tick_labels[x] or x == 0:
                if tick <= time < tick + length:
                    is_tick = True
                    break
        return is_tick


class ReportSections:
    """Report sections can be enabled or disabled to customize the report."""

    def __init__(self):
        """Instantiate class"""

        # Available report sections
        # Cover is always enabled
        self.cover = True
        self.trend_summary = False
        self.settings_summary = False
        self.alarm_summary = False
        self.monitor_details = False
        self.therapy_log = False
        self.alarm_log = False
        self.config_log = False
        self.event_log = False

    def section_list(self):
        """ Return a list of sections as formatted strings. (Report only handles up to 9 sections.) """

        # Create ordered list of property names
        ordered_sections = [
            "trend_summary",
            "settings_summary",
            "alarm_summary",
            "monitor_details",
            "therapy_log",
            "alarm_log",
            "config_log",
            "event_log",
        ]

        # Create active section list
        active_sections = []
        for section in ordered_sections:
            if getattr(self, section):
                active_sections.append(section)

        # Construct display table data
        section_list = [["", "", ""], ["", "", ""], ["", "", ""]]
        row = 0
        col = 0
        for attr in active_sections:
                name = attr.replace("_", " ").title()
                name = name.replace("Config ", "Configuration ").title()
                section_list[row][col] = name
                if row >= 2:
                    col += 1
                    row = 0
                else:
                    row += 1
        return section_list


class Report:
    """This class defines the parameters for a report."""

    def __init__(self, r_id: str, r_type: ReportType, start_dt: datetime, duration: int, export_dt: datetime,
                 institute: Institute = None, physician: Physician = None, patient: Patient = None, notes: str = None,
                 report_date: datetime = None, label: str = ""):
        """
        Instantiate class
        :param r_id: Report ID.
        :param r_type: Report type.
        :param start_dt: Start datetime.
        :param duration: Report duration in days.
        :param export_dt: Export datetime from TAR modified date or filename.
        :param institute: Institution information.
        :param physician: Physician information.
        :param patient: Patient information.
        :param notes: Notes captured from user at report creation time.
        :param report_date: Date report was created.
        :param label: Report label.
        """

        # Formatting settings - loaded after opening TAR file
        self.settings = None
        self.language = None

        # Report parameters
        self.id = r_id
        self.name = None
        self.type = r_type
        self.label = label if label is not None else ""

        # Report sections
        self.sections = ReportSections()

        # Institution information
        self.institute = institute

        # Physician information
        self.physician = physician

        # Patient information
        self.patient = patient

        # Account information
        self.account = ""
        self.user = ""

        # Report range
        self.report_duration = duration     # Report period in hours
        self.report_date = report_date      # Date report is run, localized by client
        self.export_date = export_dt        # Export date from tar file
        self.start = start_dt               # First moment of report
        self.range = None                   # Full report range

        # Notes
        self.notes = notes if notes else ""

    def created_string(self):
        """Return formatted creation date"""
        return "{d.month}/{d.day}/{d.year}".format(d=self.report_date)

    def set_language(self, event):
        """
        Set report language from "C" message in data file.
        :param event:
        """

        for detail in event.values:
            if detail.key == "94":
                self.language = detail.str
        if not self.language:
            raise Exception("Language not defined.")
