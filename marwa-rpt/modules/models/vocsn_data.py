#!/usr/bin/env python
"""
This modules contains data container objects for organizing the data read from VOCSN logs. It provides a standard data
format that can be consumed by the report modules.

    Version Notes:
        1.0.0.0  - 07/21/2019 - Created file with VOCSNData class.
        1.0.0.1  - 08/23/2019 - Added some test functions to directly parse JSON to populate report data containers.
        1.0.0.2  - 10/04/2019 - Added fields for tracking utilization and persistent event data problems.
        1.0.1.0  - 10/05/2019 - Started integrating final metadata definitions. Changed settings containers.
        1.0.1.1  - 10/15/2019 - Added time management.
        1.0.1.2  - 10/16/2019 - Modified monitor data classes to work with external record looping.
        1.0.1.3  - 10/17/2019 - Added parameter metadata and moved Event class.
        1.0.1.4  - 10/20/2019 - Changed some arguments for the event tracker.
        1.0.1.5  - 10/28/2019 - Added settings tracker.
        1.0.1.6  - 10/29/2019 - Added synonym records.
        1.0.1.7  - 10/31/2019 - Added monitor record property to facilitate sine segmentation. Added therapy lookup.
        1.0.1.8  - 11/01/2019 - Added a function to set VOCSN identifiers.
        1.0.1.9  - 11/06/2019 - Changed arguments for MonitorChannel, added ratio normalization.
        1.0.1.10 - 11/14/2019 - Added configuration interpretation from model.
        1.0.1.11 - 11/29/2019 - Added config event reference list.
        1.0.1.12 - 12/09/2019 - Added suction-pressure to therapy association list.
        1.0.1.13 - 12/10/2019 - Added therapy start/stop and control change type definition references in metadata.
        1.0.1.14 - 12/14/2019 - Added applicability fields to monitor channel model.
        1.0.1.15 - 12/16/2019 - Added label string definitions, values needed for changes to FiO2 monitor processing.
        1.0.1.16 - 12/18/2019 - Removed some workarounds.
        1.0.1.17 - 12/19/2019 - Added specific therapy ID to sessions.
        1.0.1.18 - 12/20/2019 - Added filter to force development VOCSN software version when not set.
        1.0.1.19 - 12/21/2019 - Implemented error management and added config event storage.
        1.0.1.20 - 12/26/2019 - Changed error handling to allow low level category reassignment.
        1.0.1.21 - 01/11/2020 - Corrected an error function name.
        1.0.2.0  - 01/18/2020 - Implemented pre-trend average calculations for monitor data.
        1.0.2.1  - 01/19/2020 - Centralized trend logic. Changed to dynamic applicability module loader.
        1.0.2.2  - 01/24/2020 - Added generalized version to make release/development versions interchangeable.
        1.0.2.3  - 01/27/2020 - Added power-up times, used to insert power-up records.
        1.0.2.4  - 02/01/2020 - Updated to new log format.
        1.0.2.5  - 02/04/2020 - Split version update from config update.
        1.0.2.6  - 02/18/2020 - Adjusted monitor record indexing.
        1.0.2.7  - 03/30/2020 - Added monitor records for combined log.
        1.0.2.8  - 04/06/2020 - Added an integer form of the VOCSN software version.
        1.0.2.9  - 04/13/2020 - Added last batch record time.

"""

__author__ = "John Dorian for Sai Systems Technologies"
__copyright__ = "Copyright 2019"
__version__ = "1.0.2.8"

# Built-in modules
from datetime import datetime

# VOCSN modules
from modules.models import vocsn_enum as ve
from modules.models.errors import ErrorManager
from modules.processing.values import de_norm_val
from modules.models.vocsn_enum import Therapies, RecordCompleteState as rState


class VOCSNData:
    """Data container for VOCSN log data"""

    def __init__(self, em: ErrorManager, diag: bool = False):
        """ Instantiate class. Python objects persist in memory as long as there are references. Complex variable types
        like custom classes are always stored as references to the objects in memory. The event and monitoring data
        lists here overlap, but refer to the same objects in memory. This allows for efficient thematic enumeration. """

        # Error and diagnostic management
        self.diag = diag
        self.errors = em

        # Device identifiers - set from "C" record
        self.model = ""                    # str - Device model
        self.model_id = ""                 # str - Device model value index number
        self.version = ""                  # str - VOCSN software version
        self.int_ver = 0                   # int - Integer form of version
        self.first_version = ""            # str - First valid version in data
        self.gen_version = ""              # str - General version without "R" or "D"
        self.lookup_version = ""           # str - Version name used to lookup definition files
        self.configuration = ""            # str - Device component configuration
        self.sn = ""                       # str - Device serial number

        # Metadata
        self.config_message = None         # Event from config line
        self.metadata_raw = None           # JSON dict - Raw metadata
        self.metadata_grouping = None      # JSON dict - Therapy groupings
        self.metadata_t_start = None       # JSON dict - Therapy start definitions
        self.metadata_t_stop = None        # JSON dict - Therapy stop definitions
        self.metadata_messages = None      # JSON dict - Message definitions
        self.metadata_parameters = None    # JSON dict - Parameter definitions
        self.metadata_ctrl_types = None    # JSON dict - Control data types
        self.metadata_events = {}          # JSON dict - Event definitions
        self.metadata_monitors = {}        # JSON dict - Monitor definitions
        self.metadata_7201 = {}            # JSON dict - Definitions for monitors that appear in 7201 message
        self.metadata_settings = {}        # JSON dict - Settings definitions
        self.metadata_alarms = {}          # JSON dict - Alarm definitions
        self.metadata_synonyms = {}        # JSON dict - Synonyms for looking up old values
        self.tar_manager = None            # Tar file manager reads out batch records in proper sequence

        # Event data
        self.events_all = []               # list[Event] - All events
        self.events_alarm = []             # list[Event] - References to alert events
        self.events_config = []            # list[Event] - References to configuration events
        self.events_system = []            # list[Event] - References to system events (most 6000 messages)
        self.events_therapy = []           # list[Event] - References to therapy events
        self.events_tracker = None         # Usage statistics tracker

        # Utilization (therapy sessions)
        self.utilization_all = []          # list[Session]   - All therapy sessions
        self.utilization_presets = []      # list[Session]   - Sessions divided by applicable preset
        self.power_up_times = []           # list[timestamp] - Device power-up times

        # Alarm data
        self.alarms_all = []               # list[Alarm] - All alarms
        self.alarms_tracker = None         # Alarm statistics tracker

        # Monitor data
        self.monitors_log = []             # list(MonitorLogRecord) - Log lines for combined log
        self.monitors_all = {}             # dict[ID: MonitorChannel] - All monitored data
        self.monitors_7201 = {}            # dict[ID: MonitorChannel] - 7201 message parameters
        self.monitors_patient = {}         # dict[ID: MonitorChannel] - Monitored patient statistics
        self.monitors_equip = {}           # dict[ID: MonitorChannel] - Monitored equipment statistics

        # Settings data
        self.settings_all = {}             # dict[Setting] - All settings
        self.settings_presets = {}         # dict[Setting] - References to settings by preset group
        self.settings_therapies = {}       # dict[Setting] - References to settings by therapy group
        self.settings_tracker = None       # Settings tracker

        # Maintenance records
        self.slogger_1 = []                # System log series 1
        self.slogger_2 = []                # System log series 2
        self.crash_log = []                # Crash log
        self.usage_mon = []                # Usage monitor data (redundant with monitor events
        self.dev_config = []               # Device config data

        # Applicability logic
        self.applicability_tracker = None  # Applicability tracker

        # Time management
        self.time_manager = None           # Time Tracker looks for discontinuity in time and corrects with offsets
        self.last_batch_raw = None         # Last raw datetime encountered (used by combined log)
        self.last_batch_syn = None         # Last syn datetime encountered (used by combined log)

        # Display values
        self.label_strings = None          # JSON dict - Long and short string definitions used in the report.

        # Data integrity
        self.persistent_event_out_of_range = False
        self.persistent_event_incomplete = False

        # Load provisional metadata
        self.metadata_messages = ve.custom_metadata_message
        self.metadata_parameters = ve.custom_metadata_parameters

    def set_version(self, event):
        """
        Set VOCSN unit parameters, setup data trackers.
        :param event: Config event record.
        """

        # Read event attributes
        for detail in event.values:

            # VOCSN software version
            # Note: "NOT_SET" versions are only encountered during development. Force a "D" suffix in this case.
            self.config_message = event
            if detail.name == "VERSION":
                self.set_version_only(detail.str)
            if detail.name == "SERIAL NUMBER":
                self.sn = detail.str.replace('"', '')
            if detail.name == "MODEL":
                self.model_id = str(detail.num)
                self.model = self.configuration = detail.str.replace('"', '')

    def set_version_only(self, version: str):
        """ Set version only. """
        gen_ver = version.replace('"', '').replace('.', '')
        ver = version.replace('"', '')
        if ver and ver[-1] in {"R", "D"}:
            gen_ver = gen_ver[0:-1]
        self.version = ver
        self.gen_version = gen_ver
        try:
            self.int_ver = int(self.gen_version)
        except ValueError:
            pass

    def init_trackers(self, em: ErrorManager, report):

        """
        Set VOCSN unit parameters, setup data trackers.
        :param em: Error manager.
        :param report: Report definitions.
        """

        # Catch errors
        try:

            # Import additional modules here to prevent circular reference
            from modules.processing.time import TimeTracker
            from modules.processing.alarms import AlarmTracker
            from modules.processing.events import EventTracker
            from modules.processing.settings import SettingsTracker

            # Setup data trackers for each monitor channel
            for key, defs in self.metadata_parameters.items():
                data_class = defs['data_class']
                if data_class == "Monitor":
                    self.add_monitor(report, key, defs)

            # Setup data trackers
            self.events_tracker = EventTracker(em, self, report)
            self.settings_tracker = SettingsTracker(em, self, report)
            self.alarms_tracker = AlarmTracker(em, self, report)
            # Applicability tracker is defined dynamically in TarManager during line reads

        # Handle errors
        except Exception as e:
            message = "Error while initializing VOCSN logic models"
            cat = e.cat if hasattr(e, "cat") else ve.ErrorCat.RECORD_ERROR
            sub_cat = e.sub_cat if hasattr(e, "sub_cat") else ve.ErrorSubCat.INTERNAL_ERROR
            em.log_error(ve.Programs.REPORTING, cat, sub_cat, message, e)

    def therapy_lookup(self, param_id: str):
        """ Lookup therapy from parameter ID. """
        defs = self.metadata_grouping
        if param_id in defs["Ventilation"]["KeyID"]:
            return Therapies.VENTILATOR
        if param_id in defs["Oxygen"]["KeyID"]:
            return Therapies.OXYGEN
        if param_id in defs["Cough"]["KeyID"]:
            return Therapies.COUGH
        if param_id in {"56", "57"}:
            return Therapies.NEBULIZER
        if param_id in {"54", "55", "suction-pressure"}:
            return Therapies.SUCTION
        else:
            return Therapies.SYSTEM

    def add_monitor(self, report, m_id, json_def):
        """
        Add a record to a monitor channel.
        :param report: Report definitions.
        :param m_id: Monitor channel ID.
        :param json_def: Monitor channel definition.
        """

        # Catch errors
        try:

            # Ignore definition fields
            if "_" in m_id:
                return

            # Create monitor data channel
            channel = MonitorChannel(self, report, self.errors, m_id, json_def)

            # Get therapy association
            for group, associations in self.metadata_grouping.items():
                if m_id in associations:
                    channel.group = getattr(Therapies, group.capitalize())

            # Add to data container
            self.monitors_all[m_id] = channel
            params_7201 = self.metadata_messages["7201"]["KeyID"]
            key = m_id + "_N"
            if key in params_7201:
                self.monitors_7201[m_id] = channel

        # Handle errors
        except Exception as e:
            message = "Failed to create monitor channel"
            self.errors.log_error(ve.Programs.REPORTING, ve.ErrorCat.META_ERROR, ve.ErrorSubCat.TREND_DEF, message, e,
                                  p_id=m_id)

    def finish_calcs(self):
        """ Finish calculations that must be performed once all records are loaded. """

        # Monitor data
        for _, monitor in self.monitors_all.items():
            monitor.process_channel()

        # Event data
        self.events_tracker.process_events()

        # Alarm data
        self.alarms_tracker.process_events()

        # Settings data
        self.settings_tracker.process_events()


class MonitorChannel:
    """ Monitored trend data channel. """

    def __init__(self, data, report, em, m_id, json_def):
        """
        Instantiate
        :param data: VOCSN data container.
        :param em: Error manager reference. (Master stored in VOCSNData parent.
        :param m_id: Monitor Channel ID.
        :param json_def: JSON definitions for monitor channel.
        """

        # Metadata
        self.errors = em
        self.id = m_id
        self.definition = d = json_def
        self.display_label = d['displayLabel']
        self.display_type = d['displayType']
        self.display_units = d['displayUnits']
        self.precision = d['precision']
        self.scale_factor = d['scaleFactor']
        self.tag_name = d['tagName']
        self.ratio = self.display_type == "ratioMonitor"
        self.uses_percentiles = False       # Filled later based on context in CSV
        self.group = None

        # Data
        self.data = data
        self.records = []
        self.graph_samples = []
        self.average = None
        self.trend = None
        self.pre_trend = None
        self.trend_delta = None
        self.trend_percent = None

        # Display data
        self.graph_y_min = 0.0
        self.graph_y_max = 0.0
        self.ticks = []

        # Variables to track average statistics
        self.avg_total = 0.0
        self.avg_count = 0.0
        self.trend_total = 0.0
        self.trend_count = 0.0
        self.pre_trend_total = 0.0
        self.pre_trend_count = 0.0

        # Applicability
        self.applicable = True
        self.model_applicability = True

        # Sample tracking used to re-sample data
        from modules.processing.monitoring import MonitorTracker
        self.tracker = MonitorTracker(report, self)

    def add_record(self, seq: int, ts: int, fill: float, val1, val2=None, val3=None):
        """
        Add a record to a monitor channel.
        :param seq: Sequence number.
        :param ts: Timestamp number.
        :param fill: Samples represent five minutes. This is the percentage full for each sample.
        :param val1: First value.
        :param val2: Second value. (Optional)
        :param val3: Third Value. (Optional)
        """

        # Add new record
        fill = fill if fill is not None else 1
        record = self.MonitorRecord(self, seq, ts, fill, val1, val2, val3)
        self.records.append(record)
        return record

    def add_graph_sample(self, seq: int, ts: int, val1, val2=None, val3=None, has_data: bool = True):
        """
        Add a graph sample from trend records.
        :param seq: Sequence number.
        :param ts: Timestamp number.
        :param val1: First value.
        :param val2: Second value. (Optional)
        :param val3: Third Value. (Optional)
        :param has_data: Indicates that sample has valid data. (Optional)
        """

        # Add new record
        record = self.MonitorRecord(self, seq, ts, 1.0, val1, val2, val3, has_data)
        self.graph_samples.append(record)

    def process_channel(self):
        """ Handle average calculations for individual monitor channel. """
        from modules.processing.utilities import calc_trend

        # Complete samples and calculations
        r = self.tracker.range
        self.tracker.finish_channel()
        if self.avg_count > 0:
            self.average = de_norm_val(self.avg_total / self.avg_count, self.ratio)
        if r.use_trend:
            if self.trend_count > 0:
                self.trend = de_norm_val(self.trend_total / self.trend_count, self.ratio)
            if self.pre_trend_count > 0:
                self.pre_trend = de_norm_val(self.pre_trend_total / self.pre_trend_count, self.ratio)
            self.trend_delta, self.trend_percent = calc_trend(self.pre_trend, self.trend)

    class MonitorRecord:
        """ Monitor data record """

        def __init__(self, channel, seq, ts, fill, val1, val2=None, val3=None, has_data=True):
            """
            Add a record to a monitor channel.
            :param channel: Reference to parent monitor channel.
            :param seq: Sequence number.
            :param ts: Timestamp number.
            :param fill: Samples represent five minutes. This is the percentage full for each sample.
            :param val1: First value.
            :param val2: Second value. (Optional)
            :param val3: Third Value. (Optional)
            :param has_data: Indicates record contains data. Graph summary record only.
            """

            # References
            self.channel = channel

            # Descriptors
            self.sequence = int(seq)
            if type(ts) == datetime:
                self.time = ts
            else:
                self.time = datetime.utcfromtimestamp(float(ts))

            # Data values
            self.fill = fill
            self.val1 = float(val1) if has_data else None
            self.val2 = float(val2) if val2 else val2
            self.val3 = float(val3) if val3 else val3

            # Data flag - Used in graph samples to denote summary samples with no data
            self.has_data = has_data

        def __str__(self):
            """
            Format a monitor record according to channel rules.
            :return: Record as formatted string.
            """

            # References
            scale = self.channel.scale_factor
            units = self.channel.display_units
            precision = self.channel.precision

            # Format function
            def m_format(val):
                val = val * scale
                val = '%.{0}f'.format(precision) % val
                if units == "%":
                    return "{}%".format(val)
                else:
                    return "{} {}".format(val, units)

            # Construct string
            return "{}, {}, {}".format(m_format(self.val1), m_format(self.val2), m_format(self.val3))


class Session:
    """ Therapy session. Expresses utilization. """

    def __init__(self, therapy: Therapies, therapy_id: str, start: datetime, stop: datetime, complete: rState,
                 truncated: rState, details: list):
        """
        Create session record.
        :param therapy: Therapy association.
        :param therapy_id: Specific therapy ID. (differentiates nebulizer sources)
        :param start: Start time.
        :param stop: Stop time.
        :param complete: if true, records are intact. False if start or stop were missing.
        :param truncated: if true, record exceeded report range.
        :param details: list of details to appear in logs.
        """

        # Therapy info
        self.therapy = therapy
        self.sub_therapy = therapy_id

        # Time information
        self.start = start
        self.stop = stop
        self.duration = stop - start
        self.complete = complete
        self.truncated = truncated

        # Detail lines used in logs
        self.details = details
