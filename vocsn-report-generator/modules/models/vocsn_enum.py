#!/usr/bin/env python
"""
Data value enumerations used by VOCSN data objects.

    Version Notes:
        1.0.0.0  - 08/23/2019 - Created file with program and error category definitions.
        1.0.0.1  - 09/07/2019 - Moved ReportType here from main report file.
        1.0.0.2  - 09/17/2019 - Added image size enum.
        1.0.0.3  - 10/04/2019 - Added record completion enum.
        1.0.0.4  - 10/17/2019 - Changed ID values to string to match new data files.
        1.0.0.5  - 10/19/2019 - Added audio pause cancel to event enum.
        1.0.0.6  - 10/29/2019 - Added settings message enum.
        1.0.0.7  - 10/30/2019 - Added preset message enum.
        1.0.0.8  - 11/01/2019 - Added config message to event ID enum
        1.0.0.9  - 11/04/2019 - Added data types class.
        1.0.0.10 - 11/07/2019 - Added custom suction metadata definition.
        1.0.0.11 - 11/19/2019 - Updated for new graphics names. Added blank value to Active states.
        1.0.0.12 - 11/22/2019 - Added monitor therapy associations.
        1.0.0.13 - 11/29/2019 - Added a pressure unit conversion enum.
        1.0.0.14 - 12/05/2019 - Added medium small image size.
        1.0.0.15 - 12/08/2019 - Added therapy state ID.
        1.0.0.16 - 12/14/2019 - Added model enum.
        1.0.0.17 - 12/21/2019 - Created provisional metadata for reading config line.
        1.0.0.18 - 12/29/2019 - Changed status values. Added section indexes.
        1.0.0.19 - 01/05/2019 - Renamed some error management enums values.
        1.0.0.20 - 01/15/2020 - Added time change enum.
        1.0.0.21 - 01/27/2020 - Added power events.
        1.0.0.22 - 03/29/2020 - Added error sub-category for combined log. Added record type enum.
        1.0.1.0  - 04/01/2020 - Added new VCSN+Pro and V+Pro models.
        1.0.1.1  - 04/02/2020 - Removed patchwork metadata additions from previous versions.
        1.0.1.2  - 04/06/2020 - Added Insp. Hold "therapy" enum value.
        1.0.1.3  - 04/10/2020 - Removed Insp. Hold "therapy" enum value. (Data type changed) Added an expiration alarm.

"""

__author__ = "John Dorian for Sai Systems Technologies"
__copyright__ = "Copyright 2019"
__version__ = "1.0.1.3"

# Built-in modules
from enum import Enum, auto


class ReportType(Enum):
    """ Available report types """
    USAGE = auto()
    MAINTENANCE = auto()


class ProcessingState(Enum):
    """ Report processing states. """
    ERROR = -1
    EDITING = 0
    PENDING = 1
    UPLOADING = 2
    QUEUED = 3
    PROCESSING = 4
    COMPLETED = 5


# Report section indexes
Sections = {
    0: "cover",
    1: "trend_summary",
    2: "settings_summary",
    3: "alarm_summary",
    4: "monitor_details",
    5: "therapy_log",
    6: "alarm_log",
    7: "config_log",
    8: "event_log",
}


class Programs(Enum):
    """ Error Categories """
    REPORT_GEN = auto()         # Report generator script management daemon.
    REPORTING = auto()          # Error while processing a single record.
    COMBO_LOG = auto()          # Combined log data processor.
    FILE_MAN = auto()           # File manager (zips file batches).


class LogRecordType(Enum):
    """ Record types for combined log. """
    BATCH_MON = auto()
    BATCH_EVENT = auto()
    REPORT_WARN = auto()
    REPORT_ERROR = auto()
    DEV_CONFIG = auto()
    CRASH_LOG = auto()
    SYS_LOG_1 = auto()
    SYS_LOG_2 = auto()
    USAGE_MON = auto()


class Therapies(Enum):
    """ Therapy mCodes. First item is primary key. """
    VENTILATOR = ["2829"]
    OXYGEN = ["2828", "2830"]
    COUGH = ["2827"]
    SUCTION = ["2826"]
    NEBULIZER = ["2825", "2831"]
    SYSTEM = ["-1"]


class SettingTherapies(Enum):
    """ Setting message ID/therapy associations. """
    VENTILATOR = ["5002", "5003"]
    OXYGEN = ["5004"]
    COUGH = ["5005"]
    SUCTION = ["55"]
    NEBULIZER = ["57"]
    SYSTEM = ["5001"]

    # Old values
    # VENTILATOR = ["10000", "10001"]
    # OXYGEN = ["10002"]
    # COUGH = ["10003"]
    # SUCTION = ["55"]
    # NEBULIZER = ["57"]
    # SYSTEM = ["10004"]


class SubTherapies(Enum):
    """ Therapy mCodes """
    VENTILATOR = "2829"
    OXYGEN = "2828"
    OXYGEN_FLUSH = "2830"
    COUGH = "2827"
    SUCTION = "2826"
    NEBULIZER = "2825"
    NEBULIZER_EXT = "2831"
    SYSTEM = "-1"
    
    
class PresetIDs:
    """ Preset indexes. """
    VENTILATOR = ["1", "2", "3"]
    OXYGEN = ["1", "2", "3"]
    COUGH = ["1", "2", "3"]
    NEB_SUC_SYS = ["0"]


class PresetMIDs(Enum):
    """ Preset indexes. """
    VENTILATOR = ["5002", "5003"]
    OXYGEN = ["5004"]
    COUGH = ["5005"]
    NEB_SUC_SYS = ["5001"]


class Models:
    VOCSN_PRO = "14000"
    VCSN_PRO = "14005"
    VC_PRO = "14001"
    V_PRO = "14004"
    VOCSN = "14003"
    VC = "14002"
    VOCSN_PRO_E = "13100"
    VCSN_PRO_E = "13105"
    VC_PRO_E = "13101"
    V_PRO_E = "13104"
    VOCSN_E = "13103"
    VC_E = "13102"


class EventIDs:
    """ Static event IDs. """

    # Start/Stop
    ALARM_START = "6000"
    ALARM_END = "6028"
    VENT_START = "6004"
    VENT_END = "6003"
    THERAPY_START = "6014"
    THERAPY_END = "6015"

    # Preset/Settings
    PATIENT_CHANGE = "6013"
    SETTINGS_CHANGE = "6006"

    # System events
    AUDIO_PAUSE_START = "6001"
    AUDIO_PAUSE_END = "6026"
    ACCESS_CODE_USED = "6012"
    PRE_USE_TEST = "6016"
    INSP_HOLD = "6009"

    # Settings
    SETTINGS_PRESETS = [
        "5001",
        "5002",
        "5003",
        "5004",
        "5005"
    ]

    # Config settings
    CONFIG = "7000"
    THERAPY_STATE = "7203"

    # Not used
    USER_ACKNOWLEDGE_ALARMS = "6002"
    MAINTENANCE_SNAPSHOT = "6022"


class DataTypes:
    """ Data type lists """

    # List of data types that use on/off settings with a value
    ON_OFF_VAL_TYPES = [
        "OnOffBoundedAlarm",
        "OnOffNumericSetting",
    ]

    # List of data typs that use on/off settings
    ON_OFF_TYPES = [
        "OnOffAlarm",
        "OnOffSetting",
        "OnOffBoundedAlarm",
        "OnOffNumericSetting",
    ]

    # Active states
    ACTIVE = [
        "ON",
        "Enabled",
        ""
    ]

    # Time Change records
    TIME_CHANGE = [
        "91",
        "92"
    ]


class RecordCompleteState(Enum):
    """ Record completion states. """
    COMPLETE = 0
    MISSING_START = 1
    MISSING_END = 2


class ErrorLevel(Enum):
    """ Error Status Definitions """
    NO_ERRORS = 0               # Processed report with no errors.
    WARNINGS = 1                # Encountered warning messages while processing report.
    MINOR = 2                   # Encountered minor errors, but was able to generate report.
    ADVISORY = 3                # Encountered errors that may compromise the accuracy of information on the report.
    SECTION = 4                 # Unable to create one or more of the requested sections.
    CRITICAL = 5                # Report generation failed.


class ErrorCat(Enum):
    """ Error Categories """
    WARNING = auto()            # Non-error warning.
    LOW_ERROR = auto()          # Low level error for diagnostics.
    MID_ERROR = auto()          # Mid level error triggers an advisory message.
    FILE_ERROR = auto()         # Error while reading data from raw VOCSN data files.
    RECORD_ERROR = auto()       # Error while processing a single record.
    BACKEND_ERROR = auto()      # Error only affects backend resources. Report is OK.
    PROCESS_ERROR = auto()      # Internal error in report generator program.
    REPORT_SECTION = auto()     # Error occurred at a report section level.


class ErrorSubCat(Enum):
    """ Error Sub-Categories """
    DB_ERROR = auto()           # Error communicating with database.
    OS_ERROR = auto()           # OS threw an error.
    CRC_FAILED = auto()         # Checksum failed.
    INVALID_ID = auto()         # Encountered invalid ID.
    INVALID_TAR = auto()        # Encountered invalid TAR archive.
    INVALID_REC = auto()        # Encountered invalid data record.
    MISSING_REC = auto()        # Record missing based on sequence number.
    METADATA_ERROR = auto()     # Error parsing or traversing metadata.
    INTERNAL_ERROR = auto()     # Error likely caused by flaws in the report generator.
    COMBO_LOG_ERROR = auto()    # Error while processing combined log.
    DATA_IRREGULARITY = auto()  # Data does not conform to specification.


class RecordType(Enum):
    """ Type of data record if known when error is encountered. """
    EVENT = auto()              # 6000 series message
    MONITOR = auto()            # 7200 series message
    GENERAL = auto()            # Misc. message type (unimportant)
    SETTINGS = auto()           # 5000 series message
    UNKNOWN = auto()            # Unknown message type


class ImgSizes:
    """ Available image sizes. """
    SML = "Small"
    MDS = "Med_Small"
    MED = "Medium"
    LRG = "Large"


class PressureUnits:
    """ Pressure units conversions. """
    mmHg_to_Pa = 133.322
    Pa_to_mmHg = 1 / mmHg_to_Pa


class MonitorTherapies(Enum):
    """ Monitor therapy associations. """
    ventilator = ["9402", "9403", "9404", "9405", "9406", "9407", "9408", "9409", "9410", "12082", "12083"]
    oxygen = ["9411", "9412"]
    cough = ["12024", "12025", "12026"]


custom_metadata_message = {
    "7000": {
        "Applicability": [
            "Bulk-USB",
            "Stream-RS232"
        ],
        "KeyID": [
            "14500",
            "12042",
            "14501",
            "94"
        ],
        "MsgID": "7000",
        "MsgName": "ConfigSettingsMsg",
        "MsgType": "C",
        "Notes": None
    },
    "6003-Off": {
        "Applicability": [
            "Bulk-USB",
        ],
        "KeyID": None,
        "MsgID": "6003-Off",
        "MsgName": "PowerOff",
        "MsgType": "E",
        "displayLabel": "Device Powered Off",
        "Notes": "Synthetic event generated by report system."
    },
    "6004-On": {
        "Applicability": [
            "Bulk-USB",
        ],
        "KeyID": None,
        "MsgID": "6004-On",
        "MsgName": "PowerOn",
        "MsgType": "E",
        "displayLabel": "Device Powered On",
        "Notes": "Synthetic event generated by report system."
    },
}

custom_metadata_parameters = {
    "suction-pressure": {
        "data_class": "Setting",
        "displayLabel": "SUCTION PRESSURE",
        "displayType": "NumericSetting",
        "displayUnits": None,
        "notes": "This type uses dynamic units",
        "precision": 0,
        "scaleFactor": 1.0,
        "tagName": "suction-pressure"
    },
    "SuctionUnits": {
        "data_class": "Setting",
        "displayLabel": "SUCTION UNITS",
        "displayType": "StringLiteralSetting",
        "displayUnits": None,
        "notes": "Dynamic units for suction pressure",
        "precision": None,
        "scaleFactor": None,
        "tagName": "suction-units"
    },
    "therapy-duration-seconds": {
        "data_class": "Setting",
        "displayLabel": "NEBULIZER DURATION",
        "displayType": "NumericSetting",
        "displayUnits": "Seconds",
        "notes": "This attribute is used by all therapies, but only tracked as a setting for the nebulizer.",
        "precision": 0,
        "scaleFactor": 1.0,
        "tagName": "therapy-duration-seconds"
    },
    # "12042": {
    #     "data_class": "Setting",
    #     "displayLabel": "SERIAL NUMBER",
    #     "displayType": "StringLiteralSetting",
    #     "displayUnits": None,
    #     "precision": None,
    #     "scaleFactor": None,
    #     "tagName": "SerialNumberID"
    # },
    # "14500": {
    #     "data_class": "Setting",
    #     "displayLabel": "VERSION",
    #     "displayType": "StringLiteralSetting",
    #     "displayUnits": None,
    #     "precision": None,
    #     "scaleFactor": None,
    #     "tagName": "SoftwareVersion"
    # },
    # "14501": {
    #     "TextFromEnumValue": {
    #         "14000": "V+O+C+S+N+Pro",
    #         "14001": "V+C+Pro",
    #         "14002": "V+C",
    #         "14003": "V+O+C+S+N"
    #     },
    #     "data_class": "Setting",
    #     "displayLabel": "MODEL",
    #     "displayType": "EnumSetting",
    #     "displayUnits": None,
    #     "precision": None,
    #     "scaleFactor": None,
    #     "tagName": "VentModel"
    # },
    # "94": {
    #     "TextFromEnumValue": {
    #         "0": "English",
    #         "1": "English",
    #         "13001": "English",
    #         "13002": "\u65e5\u672c\u8a9e"
    #     },
    #     "data_class": "Setting",
    #     "displayLabel": "LANGUAGE",
    #     "displayType": "EnumSetting",
    #     "displayUnits": None,
    #     "precision": None,
    #     "scaleFactor": None,
    #     "tagName": "Language"
    # },
}
