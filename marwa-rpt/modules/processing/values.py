#!/usr/bin/env python
"""
Value interpreters for all message types. Most return a three-part value type with key, numerical value, and string
representation including units.

    Version Notes:
        1.0.0.0  - 10/17/2019 - Created file with some value interpreters.
        1.0.0.1  - 10/19/2019 - Finished mapping for alarm and setting events.
        1.0.0.2  - 10/20/2019 - Modified value interpreters to pass None for blank values.
        1.0.0.3  - 10/31/2019 - Improved converters to handle unused fields in NumericCtl records.
        1.0.0.4  - 11/01/2019 - Added ratio to string converter.
        1.0.0.5  - 11/02/2019 - Changed num value for enum types to None.
        1.0.0.6  - 11/04/2019 - Updated value converters for new metadata.
        1.0.0.7  - 11/05/2019 - Modified value function to handle monitor types with appropriate error handling.
        1.0.0.8  - 11/06/2019 - Added ratio normalization functions and pre-use test value types.
        1.0.0.9  - 11/14/2019 - Changed get_val function to have option to return blank value object.
        1.0.0.10 - 11/17/2019 - Fixed routing for OnOffAlarm data type type.
        1.0.0.11 - 11/27/2019 - Moved FiO2 filter to monitor.py.
        1.0.0.12 - 12/01/2019 - Removed space before % sign in string values.
        1.0.0.13 - 12/11/2019 - Removed some workarounds from the AARC deom.
        1.0.0.14 - 12/14/2019 - Added fields for applicability.
        1.0.0.15 - 12/17/2019 - Started cleaning up commented sections.
        1.0.1.0  - 12/21/2019 - Implemented error management.
        1.0.1.1  - 12/26/2019 - Allowed invalid alarm values for diagnostics.
        1.0.1.2  - 01/02/2020 - Adjusted de-normalization to handle 0.
        1.0.1.3  - 01/30/2020 - Disabled warnings about alarm values used for diagnostics.
        1.0.1.4  - 02/01/2020 - Updated to new log format.
        1.0.1.5  - 02/04/2020 - Added Japanese language label filter.
        1.0.1.6  - 02/05/2020 - Fixed a log bug in the normalization function. Added enum value to model return value.
        1.0.2.0  - 02/28/2020 - Added support for the "spontaneous" override.
        1.0.3.0  - 04/05/2020 - Added support for the "volume targeted" overrides.
        1.0.3.1  - 04/06/2020 - Constrained volume targeted mode override to v4.06.05 and up.
        1.0.3.2  - 04/10/2020 - Added override maintenance due value for expired emergency models.

"""

__author__ = "John Dorian for Sai Systems Technologies"
__copyright__ = "Copyright 2019"
__version__ = "1.0.3.2"

# VOCSN modules
from modules.models import vocsn_enum as ve
from modules.models.errors import ErrorManager


class EventValue:
    """ Data container for an event value with key, numeric, and string values. """
    def __init__(self, key: str, name: str, num, string, enum=None, alt_str: str = None):
        self.key = key
        self.name = name
        self.num = num
        self.str = string
        self.alt_str = alt_str
        self.enum = enum
        self.applicable = True
        
        
def read_ratio(value):
    """ Convert a number to a ratio. """
    
    # Standardize input
    try:
        value = float(value)
    except ValueError:
        return value

    # Prevent unneeded decimals
    if int(value) == value:
        value = int(value)
        
    # Create ratio label
    if value > 1:
        label = "{}:1".format(value)
    elif value < -1:
        label = "1:{}".format(abs(value))
    else:
        label = "1:1"
    return label


def get_vals(em: ErrorManager, data, param_def: dict, key: str, name: str, val_in: str, display_type: str = None,
             val_only: bool = False, allow_blank: bool = False, preset=None):
    """ Interpret values based on their parameter definitions. """

    def _get_scaled_num(defs: dict, val: str):
        try:
            if val == "NA":
                return None
            if val is not None and val != "":
                val = float(val)
                return val * float(defs["scaleFactor"])
        except (ValueError, TypeError) as error:
            m = "Invalid numeric value"
            em.log_error(ve.Programs.REPORTING, ve.ErrorCat.MID_ERROR, ve.ErrorSubCat.INVALID_REC, m, error,
                         p_id=defs["tagName"], val=val)
        return None

    def _get_string(defs: dict, val):
        if val is not None and val != "":
            val = "{0:.{1}f}".format(val, defs["precision"])
            units = defs["displayUnits"]
            if units is not None and units != "":
                if units == "%":
                    val += "{}".format(units)
                else:
                    val += " {}".format(units)
            return val
        else:
            return None

    def _get_ratio(defs: dict, val):
        try:
            if val is not None and val != "":
                val = read_ratio(val)
                return val
        except TypeError as error:
            m = "Invalid ratio value ({}) for parameter: {}".format(val, defs["tagName"])
            em.log_error(ve.Programs.REPORTING, ve.ErrorCat.MID_ERROR, ve.ErrorSubCat.INVALID_REC, m, error,
                         p_id=defs["tagName"], val=val)
        return None

    # Require valid input
    if not val_in:
        return None

    # References
    d = param_def
    d_class = "custom"
    if "data_class" in d:
        d_class = d["data_class"]
    d_type = display_type if display_type else d["displayType"]

    # Return components
    num = None
    enum = None
    string = ""
    alt_string = None

    # ----- Route by data class, then parameter type ----- #

    # Monitor
    if d_class == "Monitor":

        # Numeric monitor
        if d_type == "numericMonitor":
            num = _get_scaled_num(param_def, val_in)
            string = _get_string(param_def, num)

            # Emergency model expiration override
            if key == "12004" and "Emergency".lower() in data.model.lower():
                try:
                    numeric = int(val_in)
                    if numeric <= 0:
                        string = "Device Expired - Maximum Hours"
                except Exception as e:
                    print(e)

        # Enum monitor
        if d_type == "enumMonitor":
            enum = val_in
            val_enum = param_def["TextFromEnumValue"]
            if val_in in val_enum:
                string = val_enum[val_in]
                num = val_in
            else:
                message = "Error while processing monitor value"
                e = Exception("Invalid monitor enum value".format(val_in, key))
                em.log_error(ve.Programs.REPORTING, ve.ErrorCat.MID_ERROR, ve.ErrorSubCat.INVALID_REC, message, e,
                             p_id=key, val=val_in)
                string = val_in

        # Ration monitor
        elif d_type == "ratioMonitor":
            num = _get_scaled_num(param_def, val_in)
            string = _get_ratio(param_def, num)

    # Alarm
    elif d_class == "Alarm":

        # Numeric values:
        if d_type in {"OnOffAlarm", "OnOffBoundedAlarm"}:

            # Numeric portion
            on_off_alarm = d_type == "OnOffAlarm"
            if "state" not in key and not on_off_alarm:
                num = _get_scaled_num(param_def, val_in)
                string = _get_string(param_def, num)

            # On/off portion
            else:
                if on_off_alarm:
                    enum = val_in
                    val_enum = param_def["TextFromEnumValue"]
                else:
                    val_enum = param_def["OnOffState"]
                if val_in in val_enum:
                    string = val_enum[val_in]
                else:

                    # Invalid on/off values are allowed for alarms because this can occur in diagnostic mode.
                    # em.log_warning("Invalid alarm on/off value, allowed for diagnostics.", p_id=key, ref_id=val_in)
                    string = val_in

            # Blank strings mean a value is required to be "ON"
            if string == "":
                string = "ON"

        # Enum values
        elif d_type == "EnumAlarm":
            num = None
            enum = val_in
            val_enum = param_def["TextFromEnumValue"]
            if val_in in val_enum:
                string = val_enum[val_in]
            else:

                # Invalid enum values are allowed for alarms because this can occur in diagnostic mode.
                # em.log_warning("Invalid alarm enum value, allowed for diagnostics.", p_id=key, ref_id=val_in)
                string = val_in

        # String values
        elif d_type == "AlwaysOnAlarm":
            string = val_in

        # Numeric values
        else:
            message = "Error while processing alarm value"
            e = Exception("Invalid alarm type")
            em.log_error(ve.Programs.REPORTING, ve.ErrorCat.MID_ERROR, ve.ErrorSubCat.INVALID_REC, message, e,
                         rec_type=ve.RecordType.EVENT, r_id=d_type)
            return None

    # Setting
    elif d_class == "Setting":
        message = "Error while processing setting value"

        # Numeric values
        if d_type in {"OnOffNumericSetting", "NumericSetting"}:

            # Numeric portion
            if "state" not in key:
                num = _get_scaled_num(param_def, val_in)
                string = _get_string(param_def, num)

            # On/off portion
            else:
                val_enum = param_def["OnOffState"]
                if val_in in val_enum:
                    string = val_enum[val_in]
                else:

                    # Self-generated blank value
                    string = val_in

                    # Invalid data
                    e = Exception("Invalid setting on/off value")
                    em.log_error(ve.Programs.REPORTING, ve.ErrorCat.MID_ERROR, ve.ErrorSubCat.INVALID_REC, message, e,
                                 p_id=key, val=val_in)

                # Blank strings mean a value is required to be "ON"
                if string == "":
                    string = "ON"

        # Enum Setting
        elif d_type in {"EnumSetting", "OnOffSetting"}:
            enum = val_in
            val_enum = param_def["TextFromEnumValue"]

            # Ventilation mode override
            if key == "24":
                circuit_type = data.settings_all["13"].current_enum(preset)
                volume_targeted = data.settings_all["27"].current_enum(preset)

                # Spontaneous mode override
                if val_in == "2225" and circuit_type == "2052":
                    alt_string = "Spontaneous"

                # Volume targeted override
                if volume_targeted in ["0", "2150", "2152"] and 40605 <= data.int_ver:

                    # Vol. Targeted PS
                    if val_in == "2225":
                        alt_string = "Vol. Targeted-PS"

                    # Vol. Targeted PC
                    if val_in == "2226":
                        alt_string = "Vol. Targeted-PC"

                    # Vol. Targeted SIMV
                    if val_in == "2227":
                        alt_string = "Vol. Targeted-SIMV"

            # Look up enum value
            if val_in in val_enum:
                string = val_enum[val_in]
                if key == "14501":
                    num = val_in
            else:
                string = ""

                # Invalid data
                e = Exception("Invalid setting enum value")
                em.log_error(ve.Programs.REPORTING, ve.ErrorCat.MID_ERROR, ve.ErrorSubCat.INVALID_REC, message, e,
                             p_id=key, val=val_in)

            # Special filters
            if val_in == "13002":
                string = "Japanese"

            # Blank strings mean a value is required to be "ON"
            if string == "" and d_type != "EnumSetting":
                string = "ON"

        # String values
        elif d_type == "StringLiteralSetting":
            string = val_in

        # Unexpected value type
        else:
            e = Exception("Unknown setting value type")
            em.log_error(ve.Programs.REPORTING, ve.ErrorCat.MID_ERROR, ve.ErrorSubCat.INVALID_REC, message, e, p_id=key,
                         val=d_type)

    # Custom definitions found in pre-use test
    elif d_class == "custom":
        message = "Error while handling specialized value type."

        # String literal measurement
        if d_type == "StringLiteralMeasure":
            string = val_in
            if key == "14501":
                num = val_in

        elif d_type == "NumericMeasure":
            num = _get_scaled_num(param_def, val_in)
            string = _get_string(param_def, num)

        # Unexpected value type
        else:
            e = Exception("Unknown value type")
            em.log_error(ve.Programs.REPORTING, ve.ErrorCat.MID_ERROR, ve.ErrorSubCat.INVALID_REC, message, e, p_id=key,
                         val=d_type)
            return None

    # Data Type
    elif d_class == "DataType":
        pass

    # Unknown data class
    else:
        message = "Error while reading parameter value"
        e = Exception("Unknown data class")
        em.log_error(ve.Programs.REPORTING, ve.ErrorCat.MID_ERROR, ve.ErrorSubCat.INVALID_REC, message, e, p_id=key,
                     val=d_class)
        return None

    # Don't generate blanks
    if num is None and string == "":
        if allow_blank:
            return EventValue(key, name, None, None)
        else:
            return None

    # Return value
    if val_only:
        return num
    else:
        return EventValue(key, name, num, string, enum, alt_string)


def norm_val(val, ratio):
    """ Check if units are ratio and normalize number space. """
    if ratio:
        if val > 1:
            val -= 1
        elif val < -1:
            val += 1
        else:
            val = 0
    return val


def de_norm_val(val, ratio):
    """ Check if units are ratio and de-normalize number space. """
    if ratio:
        if val >= 0:
            val += 1
        elif val < 0:
            val -= 1
    return val
