#!/usr/bin/env python
"""
Common utilities.

    Version Notes:
        1.0.0.0 - 07/22/2019 - Created file with flex_float function.
        1.0.0.1 - 09/26/2019 - Added temp name generator.
        1.0.0.2 - 10/03/2019 - Added therapy icon path lookup function.
        1.0.0.3 - 10/16/2019 - Made flex_float pass None
        1.0.0.4 - 10/17/2019 - Added datetime to timestamp converter.
        1.0.0.5 - 11/19/2019 - Updated for new graphics names.
        1.0.0.7 - 11/28/2019 - Added a variable precision function for 1-ish precision.
        1.0.0.8 - 12/05/2019 - Moved a unit time convert here.
        1.0.1.0 - 12/10/2019 - Moved therapy lookups here from settings.
        1.0.1.1 - 12/12/2019 - Moved label strings filters here.
        1.0.1.2 - 12/17/2019 - Added label lookup.
        1.0.2.0 - 12/21/2019 - Implemented error management. Moved some preset lookup functions here.
        1.0.2.1 - 01/01/2020 - Created a safe read function that handles differences in value type between Azure records
                               created by Python and JavaScript.
        1.0.2.2 - 01/09/2020 - Fixed a bug where the config therapy type doesn't exist.
        1.0.2.3 - 01/16/2020 - Added detail to label lookup warning.
        1.0.3.0 - 01/19/2020 - Created a centralized trend logic function.
        1.0.3.1 - 02/17/2020 - Switched from dict conditions to sets for performance.
        1.0.3.2 - 02/27/2020 - Changed current settings data type from str to EventVal.
        1.0.3.3 - 03/30/2020 - Added timestamp interpreter for combined log.

"""

__author__ = "John Dorian for Sai Systems Technologies"
__copyright__ = "Copyright 2019"
__version__ = "1.0.3.3"

# Built-in modules
import os
from datetime import datetime, timedelta, timezone

# 3rd party modules
from reportlab.platypus import Image
from reportlab.lib.units import inch

# VOCSN Modules
from modules.models import vocsn_enum as ve
from modules.models.errors import ErrorManager
from modules.models.vocsn_data import VOCSNData


def ts_to_log(ts: datetime):
    """ Standard date/time format for combined log. """
    return ts.strftime("%m/%d/%Y %H:%M:%S")


def calc_trend(t1: float = None, t2: float = None) -> (float, float):
    """
    Calculate trend delta and percentage following these rules where Num is a non-zero decimal value.
      Trend 1   Trend 2   Delta   Percent
      -------   -------   -----   -------
       None      None      None    None
       None      Num       None    None
       Num       None      None    None
       0         0         0       0
       0         Num       Num     +/-100%
       Num       0         -Num    -/+100%
       Num       Num       Dif     Percent
    :param t1: Pre-trend period average.
    :param t2: Trend period average.
    :return: Delta, Percentage
    """

    # No trend possible
    if t1 is None or t2 is None:
        trend = perc = None

    # Regular calculation
    elif t1 != 0 and t2 != 0:
        trend = t2 - t1
        perc = trend / t1

    # Both values are 0
    elif t1 == t2 == 0:
        trend = perc = 0

    # Pre-trend is 0
    elif t1 == 0:
        trend = t2
        perc = t2 / abs(t2)

    # Tend is 0
    else:
        trend = -t1
        perc = -t1 / abs(t1)

    # Return values
    return trend, perc


def flex_float(num: float, places: int):
    """
    Round a floating point number depending on the number of digits to the left of the decimal point.
    :param num: Number to round.
    :param places: Places (digit characters) as a target.
    :return: Rounded number.
    """

    # Pass None
    if not num:
        return num

    # Get digits to left of decimal
    left = len(str(num).split('.')[0])

    # Calculate number of digits to right of decimal
    right = max(0, places - left)

    # Round value
    value = round(num, right)

    # Convert to int with no digits after decimal point
    if right == 0:
        value = int(value)

    # Return rounded number
    return value


def safe_read(value):
    """
    Read a value from an Azure data type safely, handling formats from either JavaScript or Python.
    :return: Value from record.
    """
    if hasattr(value, "_"):
        value = value._
    if hasattr(value, "value"):
        value = value.value
    return value


def temp_name(file_type):
    """
    Generate an available temporary file name.
    :param file_type: File extension.
    """

    # Contextualize program directory
    root = ".."
    if os.path.exists("reports"):
        root = ""

    # Create temp folder if needed
    temp_dir = os.path.join(root, "temp")
    if not os.path.exists(temp_dir):
        os.mkdir(temp_dir)

    for x in range(1, 999):
        name = os.path.join(root, "temp", "tmp_{:03d}.{}".format(x, file_type))
        if not os.path.isfile(name):
            return name


def trend_img(prog_dir, letter, size, path_only=False):
    """
    Construct an image header block for use in the trend summary table.
    :param prog_dir: Execution directory
    :param letter: Therapy letter
    :param size: Image size from ImgSize class
    :param path_only: If true, returns the file path only.
    :return: Reportlab image
    """
    dim = 0.8 * inch
    path = os.path.join(prog_dir, "resources", "images", "therapy_icons", "Multi-View_{}-{}.png".format(letter, size))
    if path_only:
        return path
    else:
        return Image(path, dim, dim)


def dt_to_ts(dt: datetime):
    """
    Convert naive datetime to Unix timestamp.
    :param dt: Datetime to convert to timestamp
    :return: timestamp
    """
    return dt.replace(tzinfo=timezone.utc).timestamp()


def var_precision(num):
    """
    Convert a number to a string with 1 decimal precision when under 10, 0 when over.
    :param num: int or float.
    :return: string with desired precision.
    """
    if abs(num) >= 10:
        return "{:.0f}".format(num)
    else:
        return "{:.1f}".format(num)


def unit_int_to_td(val: int, units: str = "days"):
    """
    Convert an integer to a timedelta in provided units.
    :param val: Number of units.
    :param units: Time unit.
    :return:
    """
    if units == "days":
        return timedelta(days=val)
    elif units == "hours":
        return timedelta(hours=val)
    return None


# Set record type
def get_record_type(m_type: str, m_id: str):
    if m_id == "7203":
        return ve.RecordType.SETTINGS
    if m_type == "E":
        return ve.RecordType.EVENT
    elif m_type == "M":
        return ve.RecordType.MONITOR
    elif m_type == "S":
        return ve.RecordType.SETTINGS
    elif m_type in {"H", "C"}:
        return ve.RecordType.GENERAL
    else:
        return ve.RecordType.UNKNOWN


def lookup_therapy_from_name(name: str):
    """
    Lookup therapy ID from therapy name.
    :param name: Therapy name.
    :return: Therapy preset message ID list.
    """

    # Set preset group
    t_id = None
    for therapy in ve.SettingTherapies:
        if name in therapy.name:
            t_id = therapy.value

    # preset not found
    if not t_id:
        error = Exception("Unable to lookup therapy from name")
        error.cat = ve.ErrorCat.MID_ERROR
        error.sub_cat = ve.ErrorSubCat.INTERNAL_ERROR
        raise error

    # Found preset group
    return t_id


def lookup_preset_from_name(name: str):
    """
    Lookup preset group from therapy name.
    :param name: Therapy name.
    :return: Therapy preset message ID list.
    """

    # Translate into therapy groups
    if name in {"SUCTION", "NEBULIZER", "SYSTEM"}:
        name = "NEB_SUC_SYS"

    # Set preset group
    preset = None
    for therapy in ve.PresetMIDs:
        if name in therapy.name:
            preset = therapy.value

    # preset not found
    if not preset:
        error = Exception("Unable to lookup preset from therapy name.")
        error.cat = ve.ErrorCat.MID_ERROR
        error.sub_cat = ve.ErrorSubCat.INTERNAL_ERROR
        raise error

    # Found preset group
    return preset


def lookup_therapy_group(data, m_id: str):
    """
    Lookup therapy group association from message id.
    :param data: VOCSN data container reference.
    :param m_id: Message ID.
    :return: Therapy group name.
    """

    # Set therapy group
    group = None
    for t_group in ve.SettingTherapies:
        if m_id in t_group.value:
            group = t_group.name.lower()

    # Group not found
    if not group:
        error = Exception("Unable to lookup therapy from group ID.")
        error.cat = ve.ErrorCat.MID_ERROR
        error.sub_cat = ve.ErrorSubCat.INTERNAL_ERROR
        raise error

    # Found group
    return data.settings_therapies[group], group


def lookup_therapy(data, m_id: str):
    """
    Lookup therapy association from message id.
    :param data: VOCSN data container reference.
    :param m_id: Message ID.
    :return: Therapy and Subtherapy enum.
    """
    therapy = ve.Therapies.SYSTEM
    sub_therapy = ve.SubTherapies.SYSTEM
    for group, defs in data.metadata_grouping.items():
        if m_id in defs["KeyID"]:
            name = group.upper()
            if name == "VENTILATION":
                name = "VENTILATOR"
            if name == "CONFIG":
                name = "SYSTEM"
            therapy = getattr(ve.Therapies, name)
            sub_therapy = getattr(ve.SubTherapies, therapy.name)
            break
    return therapy, sub_therapy


def current_preset_id(therapy: ve.Therapies):
    """
    Lookup current preset ID for therapy.
    :param therapy: Therapy type.
    :return: Preset label ID.
    """
    preset_label_id = None
    if therapy == ve.Therapies.VENTILATOR:
        preset_label_id = "14502"
    elif therapy == ve.Therapies.OXYGEN:
        preset_label_id = "14503"
    elif therapy == ve.Therapies.COUGH:
        preset_label_id = "14504"
    return preset_label_id


def current_preset_label(data: VOCSNData, therapy: ve.Therapies, preset):
    """
    Lookup preset label from therapy
    :param data: VOCSN Data Model
    :param therapy: Therapy type.
    :param preset: Preset number.
    :return: Therapy preset label.
    """
    preset_label = ""
    preset_label_id = current_preset_id(therapy)
    if preset_label_id and preset:
        preset_label_setting = data.settings_all[preset_label_id]
        preset_val = preset_label_setting.current[preset]
        preset_label = preset_val.str if preset_val else None
    if preset_label is None and preset:
        preset_label = "Preset {}".format(preset)
    return preset_label


def preset_from_label(data: VOCSNData, therapy: ve.Therapies, label: str):
    """
    Lookup the current preset from the preset label.
    :param data: VOCSN data container.
    :param therapy: Therapy association.
    :param label: Preset label to search for.
    :return: Preset number.
    """

    # Therapies that use presets
    if therapy in {ve.Therapies.VENTILATOR, ve.Therapies.OXYGEN, ve.Therapies.COUGH}:
        preset = None
        group_id = lookup_preset_from_name(therapy.name)
        group = data.settings_presets[group_id[0]]
        label_id = current_preset_id(therapy)
        preset_param = group[label_id]
        for preset_num, preset_label in preset_param.current.items():
            if preset_label and preset_label.str == label:
                preset = preset_num
                break
        return preset

    # Therapies that don't use preset
    else:
        return 0


def label_lookup(em: ErrorManager, data: VOCSNData, param_id: str, short: bool = False):
    """
    Lookup parameter label in string definition
    :param em: Error manager.
    :param data: VOCSN data container.
    :param param_id: Parameter ID.
    :param short: Use shorter label definition.
    :return: Label if available or None.
    """

    # Default to None
    label = None

    # Lookup label
    if param_id in data.label_strings:
        if short:
            label = data.label_strings[param_id]["short"]
        else:
            label = data.label_strings[param_id]["long"]
    else:
        print(param_id)
        em.log_warning("Unable to lookup label from definitions", ref_id=param_id)

    # Return label if available
    return label


def filter_label(label: str):
    """
    Filter a parameter label to appear human-friendly.
    :param label: Parameter tag name
    """
    label = label.replace('Evt', 'Event')
    label = label.replace('Id', 'ID')
    label = label.replace('T ', 'Tidal ')
    label = label.replace("Setting ID ", "")
    label = label.replace("Sys", "System")
    label = label.replace("Fio2", "FiO2")
    label = label.replace("Fi O2", "FiO2")
    label = label.replace("Peepalarm", "PEEP Alarm")
    label = label.replace("Peep", "PEEP")
    label = label.replace("Ipap", "IPAP")
    label = label.replace("Pc ", "PC ")
    label = label.replace("Tcontrol", "Termination")
    label = label.replace("Sup ", "Support ")
    label = label.replace("Press ", "Pressure ")
    label = label.replace("Pres ", "Pressure ")
    label = label.replace("V ", "Volume ")
    label = label.replace("Insp ", "Inspiratory ")
    label = label.replace("Dis ", "Disconnect ")
    label = label.replace("I Time ", "Inspiratory Time ")
    label = label.replace("Cyc ", "Cycle ")
    label = label.replace("Trig ", "Trigger ")
    label = label.replace("Comp ", "Compensation ")
    label = label.replace("Insuf ", "Insufflation ")
    label = label.replace("Insuff. ", "Insufflation ")
    label = label.replace("Exsuf ", "Exsufflation ")
    label = label.replace("Conc ", "Concentrator")
    label = label.replace("Equiv ", "Equivalent ")
    label = label.replace("Ext ", "External ")
    label = label.replace("Change Change", "Change")
    label = label.replace("Preusetestresult", "Result")
    label = label.replace(" Event", "")
    label = label.replace(" Seconds", "")
    label = label.replace("-", " ")
    label = label.replace("_", " ")
    return label
