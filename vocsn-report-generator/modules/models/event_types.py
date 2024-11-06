#!/usr/bin/env python
"""
Creates a base Event message type with extended variants for general event formats and several specific events with
unique formats.

    Version Notes:
        1.0.0.0  - 10/17/2019 - Created file with base event class and variants.
        1.0.0.1  - 10/18/2019 - Added some attributes needed by the alarm tracker.
        1.0.0.2  - 10/19/2019 - Added remaining event types.
        1.0.0.3  - 10/20/2019 - Added some default attributes.
        1.0.0.4  - 10/29/2019 - Added settings event type.
        1.0.0.5  - 10/31/2019 - Improved converters to handle unused fields in NumericCtl records.
        1.0.0.6  - 11/02/2019 - Fixed logic error for vent start/stop events.
        1.0.0.7  - 11/04/2019 - Updated converter functions for new metadata.
        1.0.0.8  - 11/05/2019 - Corrected some arguments passed to settings update methods. Completed pre-use test.
        1.0.0.9  - 11/14/2019 - Update use of get_val to pass a blank value where appropriate.
        1.0.0.10 - 11/19/2019 - Added partial therapy specification for settings events. Restored suction unit values.
        1.0.0.11 - 11/20/2019 - Updated therapy lookup for settings events.
        1.0.0.12 - 11/29/2019 - Fixed a preset index type mismatch.
        1.0.0.13 - 12/05/2019 - Added proper therapy association for EventControl types.
        1.0.0.14 - 12/08/2019 - Added EventTherapyState handler.
        1.0.1.0  - 12/10/2019 - Restructured EventControl to read newly available data positions from metadata.
        1.0.1.1  - 12/11/2019 - Removed some workarounds from the AARC demo.
        1.0.1.2  - 12/12/2019 - Added information needed on logs.
        1.0.1.3  - 12/15/2019 - Implemented an post-processing update stack for event values.
        1.0.1.4  - 12/18/2019 - Bug fixes in therapy start/stop metadata reading. Added force_display value.
        1.0.2.0  - 12/18/2019 - Reworked Event Therapy class to handle broader range of definition changes.
        1.0.2.1  - 12/19/2019 - Added a synonym lookup to handle older data in development.
        1.0.3.0  - 12/21/2019 - Implemented error management.
        1.0.3.1  - 01/09/2020 - Re-implemented synonym look-up. Standardized interpretation of access code used events.
                                Changed suction-pressure precision to 0.
        1.0.3.2  - 01/15/2020 - Expanded synonym application to include more event types. Improved error messages.
        1.0.3.3  - 01/27/2020 - Added constructors for power events.
        1.0.3.4  - 02/04/2020 - Expanded conditions for uninitialized 7203 message error.
        1.0.4.0  - 02/08/2020 - Restored full record length validation.
        1.0.4.1  - 02/17/2020 - Added version-dependent line length validation. Switched from dictionary conditions to
                                sets for performance.
        1.0.4.2  - 02/27/2020 - Corrected some records to be more extensible for future metadata definitions.
        1.0.4.3  - 03/13/2020 - Added preset to label value function to allow correct "spontaneous" override.
        1.0.4.4  - 03/27/2020 - Changed settings event control definition to array.
        1.0.4.5  - 03/29/2020 - Added record type for combined log.
        1.0.4.6  - 03/30/2020 - Added csv field list functions.
        1.0.4.7  - 04/06/2020 - Corrected value mapping in pre-use test events.
        1.0.4.8  - 04/08/2020 - Moved CSV line constrictor to vocsn-combined-log project.
        1.0.4.9  - 04/13/2020 - Added CRC handling and filename tracking, improved string support for combined log.
        4.0.4.10 - 04/13/2020 - Fixed line splitting error.

"""

__author__ = "John Dorian for Sai Systems Technologies"
__copyright__ = "Copyright 2019"
__version__ = "1.0.4.10"

# Built-in
from datetime import datetime

# VOCSN data modules
from modules.models import vocsn_enum as ve
from modules.processing import values as vals
from modules.processing import utilities as ut
from modules.models.errors import ErrorManager
from modules.models.vocsn_data import VOCSNData
from modules.processing.values import EventValue
from modules.models.vocsn_enum import EventIDs as eID
from modules.models.vocsn_enum import RecordCompleteState as rState
from modules.processing.utilities import preset_from_label, current_preset_label, ts_to_log


def check_param(p_id: str, metadata: str):
    """
    Check for parameter ID in metadata. Throws error if not found.
    :param p_id: Parameter ID.
    :param metadata: Metadata.
    """
    if p_id not in metadata:
        error = Exception("Unknown parameter ID: {}".format(p_id))
        error.cat = ve.ErrorCat.RECORD_ERROR
        error.sub_cat = ve.ErrorSubCat.INVALID_ID
        raise error


def check_length(data: VOCSNData, line: list, fixed: int, defs: dict):
    """
    Check line length against expected length.
    :param data: VOCSM Data reference.
    :param line: List of line fields.
    :param fixed: Number of fixed fields.
    :param defs: Dict of variable fields.
    """

    # References
    try:
        ver = int(data.gen_version)
    except (ValueError, TypeError):
        return

    # Don't validate length prior to 4.06.04
    if ver < 40604:
        return

    # Validate record length
    if len(line) - fixed < len(defs):
        error = Exception("Found incorrect record length")
        error.cat = ve.ErrorCat.RECORD_ERROR
        error.sub_cat = ve.ErrorSubCat.INVALID_REC
        raise error


class Event:
    """ Base VOCSN event. """

    def __init__(self, em: ErrorManager, data: VOCSNData, line: list, filename: str = ""):
        """ Initialize """

        # Set standard event metadata
        self.record_type = ve.LogRecordType.BATCH_EVENT
        self.em = em
        self.sequence = int(line[0])
        self.timestamp = int(line[1])
        self.raw_time = datetime.utcfromtimestamp(float(line[1]))
        self.syn_time = datetime.utcfromtimestamp(float(line[2]))
        self.valid = True
        self.invalid_detail = ""
        self.filename = filename
        for x in range(0, len(line)):
            line[x] = str(line[x])
        self.raw_data = "|".join(line)

        # Interpret CRC result
        self.crc_result = "N/A"
        if line[-1] in ["PASS", "FAIL"]:
            self.crc_result = line.pop(-1)

        # Set standard event descriptors
        self.message_type = line[3]
        self.id = line[4]

        # Check for synthetic events
        synthetic = "-" in self.id

        # Definitions
        self.definition = d = ve.custom_metadata_message[self.id] if synthetic else data.metadata_messages[self.id]

        # Perform synonym lookup
        if "data_class" in d.keys() and d["data_class"] == "ParamSynonym":
            self.id = d["definedBy_KeyID"]
            self.definition = d = data.metadata_messages[self.id]

        # Set additionally metadata
        self.name = d["MsgName"]
        self.label = None
        if "displayLabel" in d:
            self.label = d["displayLabel"]

        # Optional values used for persistent events
        self.values = []
        self.force_display = False
        self.therapy = ve.Therapies.SYSTEM
        self.complete = rState.COMPLETE
        self.truncated = rState.COMPLETE
        self.sub_therapy = ve.SubTherapies.SYSTEM
        self.control = None
        self.preset = None

    def __str__(self):
        """ String conversion for combined log. """
        s = ""
        for val in self.values:
            if s != "":
                s += ", "
            s += "{}".format(val.name)
            if val.name != val.key:
                s += " ({})".format(val.key)
            s += ": {}".format(val.str)
        return s


class EventVal(Event):
    """ VOCSN Event with a specified number of value parameter. """

    def __init__(self, em: ErrorManager, data: VOCSNData, line: list, filename: str = ""):
        """ Initialize. """

        # Extend super-class
        super().__init__(em, data, line, filename)

        # Initialize values
        self.param = None
        self.param_def = None
        self.values = []

        # References
        d = self.definition
        keys = d["KeyID"] or []

        # Validate line length
        check_length(data, line, 6, keys)

        # Process values and definitions
        line_idx = 5
        val_count = len(keys)
        for x in range(0, val_count):
            self.param = keys[x]
            check_param(self.param, data.metadata_parameters)
            self.param_def = pd = data.metadata_parameters[self.param]
            label = pd["displayLabel"]
            val_line = vals.get_vals(em, data, pd, self.param, label, line[line_idx + x])
            if val_line:
                self.values.append(val_line)

        # print("Values list", self.id, self.param, self.values)


class EventValParam(Event):
    """ VOCSN Event with a specified number of value parameter. """

    def __init__(self, em: ErrorManager, data: VOCSNData, line: list, filename: str = ""):
        """ Initialize. """

        # Extend super-class
        super().__init__(em, data, line, filename)

        # Initialize values
        self.param = None
        self.param_def = None
        self.param_label = None
        self.val_type = None
        self.fault_id = None
        self.fault_def = None
        self.fault = None
        self.alarm_priority = None

        # References
        d = self.definition
        keys = d["KeyID"] or []

        # Validate line length
        check_length(data, line, 6, keys)

        # Process parameter values and definitions
        if keys and self.id != "6004":
            val_count = len(keys) - 2
            self.param = line[5]
            check_param(self.param, data.metadata_parameters)
            self.param_def = pd = data.metadata_parameters[self.param]

            # Handle synonym lookups
            if "data_class" in pd and pd["data_class"] == "ParamSynonym":
                self.param = pd["definedBy_KeyID"]
                check_param(self.param, data.metadata_parameters)
                self.param_def = pd = data.metadata_parameters[self.param]

            # Continue regular processing
            self.param_label = pd["displayLabel"]
            self.val_type = pd["displayType"]
            self.values = []
            for x in range(0, val_count):
                label = keys[1 + x]
                val_line = vals.get_vals(em, data, pd, label, label, line[6+x])
                if val_line:
                    self.values.append(val_line)
            self.fault_id = keys[-1]
            check_param(self.fault_id, data.metadata_parameters)
            self.fault_def = data.metadata_parameters[self.fault_id]
            self.fault = vals.get_vals(em, data, self.fault_def, "14505", "Fault", line[-2])
            self.alarm_priority = pd["alarmPriority"]

            # Therapy/system component association
            for group, defs in data.metadata_grouping.items():
                if self.param in keys:
                    name = group.upper()
                    if name == "VENTILATION":
                        name = "VENTILATOR"
                    for therapy in ve.Therapies:
                        if name == therapy.name:
                            self.therapy = therapy
                            break
                    break

        # Set therapy association for ventilator events that don't use any value lines
        if self.id in {eID.VENT_START, eID.VENT_END}:
            self.therapy = ve.Therapies.VENTILATOR
            self.sub_therapy = ve.SubTherapies.VENTILATOR

        # Lookup preset number for vent start
        if self.id == eID.VENT_START:
            group = data.settings_presets[ve.PresetMIDs.VENTILATOR.value[0]]
            self.preset = group["current_preset"]
            self.preset_label = current_preset_label(data, self.therapy, self.preset)

        # print("parameter change", self.sequence, self.id, self.param, self.val_type, self.values, self.fault)


class EventControl(Event):
    """ VOCSN control change event. """

    def __init__(self, em: ErrorManager, data: VOCSNData, line: list, range_started: bool = False, filename: str = ""):
        """ Initialize. """

        # Extend super-class
        super().__init__(em, data, line, filename)

        # Optional fields
        self.new_preset_label = ""
        self.old_preset_label = ""

        # Control change type - currently a positional value
        self.type = line[7]

        # Read metadata file
        line_idx = 4
        self.message_defs = md = data.metadata_messages[eID.SETTINGS_CHANGE]["KeyID"]
        for def_line in md:
            line_idx += 1

            # Control parameter ID
            if def_line == "ParamID":
                self.control = line[line_idx]

            # Capture preset
            if def_line == "9100":
                self.preset = line[line_idx]

        # Accommodate older metadata versions that don't explicitly list the ParamID field
        if "ParamID" not in md:
            self.control = line[5]

        # Process control attribute values and definitions
        check_param(self.control, data.metadata_parameters)
        self.control_def = cd = data.metadata_parameters[self.control]

        # Handle synonym lookups
        if "data_class" in cd and cd["data_class"] == "ParamSynonym":
            self.control = cd["definedBy_KeyID"]
            check_param(self.control, data.metadata_parameters)
            self.param_def = cd = data.metadata_parameters[self.control]

        # Reference names and labels
        self.control_name = cd["tagName"]
        self.control_label = cd["displayLabel"]
        self.control_type = cd["displayType"]

        # Therapy/system component association
        self.therapy, self.sub_therapy = ut.lookup_therapy(data, self.control)

        # Process control type attributes and definitions
        self.type_def = td = data.metadata_ctrl_types[self.type]
        self.type_name = td["tagName"]

        # Lookup preset label
        from modules.processing.utilities import current_preset_label
        self.preset_label = current_preset_label(data, self.therapy, self.preset).strip('"')

        # Values only
        ad = td["attributes"]
        if self.type in {"9002", "9003", "9004", "9005", "9008", "9009"}:

            # Validate line length
            check_length(data, line, 9, ad)

            # Process each detail value
            def_offset = 0
            for x in range(0, 2):

                # Process value
                val_line = vals.get_vals(em, data, cd, self.control, ad[x - def_offset], line[8+x].strip('"'),
                                         preset=self.preset)
                if val_line:
                    self.values.append(val_line)

        # Mixed values and enum values
        elif self.type in {"9000", "9006"}:

            # Validate line length
            check_length(data, line, 9, ad)

            # Process each detail value
            enum_vals = td["enum_ref"]["OnOffState"] if ("enum_ref" in td.keys()) else None
            for x in range(0, 4):

                # Ignore on/off data for records that aren't on/off type
                if "OnOff" not in self.control_type:
                    if x in {1, 3}:
                        continue

                # Read value
                attr = ad[x]
                val = line[8+x]
                if "OnOffState" in attr:
                    val_line = EventValue(attr, attr, None, enum_vals[val])
                else:
                    val_line = vals.get_vals(em, data, cd, attr, attr, val)
                if val_line:
                    self.values.append(val_line)

        # Unexpected control data type
        else:
            error = Exception("Unknown control change type: {}".format(self.type))
            error.cat = ve.ErrorCat.RECORD_ERROR
            error.sub_cat = ve.ErrorSubCat.INVALID_ID
            raise error

        # Preserve times in logs if they exceed report range
        if self.control in {"91", "92"}:
            self.force_display = range_started

        # print("control change", self.id, self.type_name, self.control, self.type, self.preset)


class EventTherapy(Event):
    """ VOCSN Event with a specified number of value parameter. """

    def __init__(self, em: ErrorManager, data: VOCSNData, line: list, filename: str = ""):
        """ Initialize. """

        # Extend super-class
        super().__init__(em, data, line, filename)

        # Initialize values
        self.values = []
        self.preset_label = None
        self.is_preset_change_only = False

        # Defaults
        self.sub_therapy = ve.SubTherapies.SYSTEM

        # Look up therapy
        d = self.definition
        keys = d["KeyID"] or []

        # Read lines
        line_idx = 4
        expected_length = 6
        for line_id in keys:
            line_idx += 1

            # Preset name
            if line_id == "therapy-preset-label":
                expected_length += 1
                self.preset_label = line[line_idx].strip('"')

            # Handle therapy duration
            elif line_id == "therapy-duration-seconds":
                expected_length += 1
                val = float(line[line_idx]) if line[line_idx] else 0
                dur = "therapy-duration-seconds"
                val_line = EventValue(dur, dur, val, "{} seconds".format(val))
                if val_line:
                    self.values.append(val_line)

            # Therapy type
            elif type(line_id) is dict:
                expected_length += 1
                if "TherapyStartTypes" in line_id:
                    therapy_defs = line_id["TherapyStartTypes"]
                else:
                    therapy_defs = line_id["TherapyStopTypes"]
                self.therapy_id = line[line_idx]
                self.therapy_def = td = therapy_defs[self.therapy_id] or {}
                for therapy in ve.Therapies:
                    if self.therapy_id in therapy.value:
                        self.therapy = therapy
                for therapy in ve.SubTherapies:
                    if self.therapy_id == therapy.value:
                        self.sub_therapy = therapy

                # No more parameters
                if not td["attributes"]:
                    continue

                # Handle suction pressure
                for param in td["attributes"]:
                    line_idx += 1
                    expected_length += 1
                    val = line[line_idx]

                    # Suction pressure
                    if param == "suction-pressure":
                        val = float(val) if val != "" else None
                        unit = line[line_idx + 1]
                        if unit == "":
                            unit = None
                        else:
                            unit = td["enum_ref"]["SuctionUnits"][unit]
                        val_str = val
                        if val:
                            if unit:
                                val_str = "{0:.0f} {1:}".format(val, unit)
                        val_line = EventValue(param, param, val, val_str, unit)
                        if val_line:
                            self.values.append(val_line)

                    # Suction units handled above
                    elif param == "SuctionUnits":
                        continue

                    # Handle preset only change
                    elif param == "is-preset-change-only":
                        self.is_preset_change_only = val == "1"

                    # Handle remaining values
                    else:
                        check_param(param, data.metadata_parameters)
                        pd = data.metadata_parameters[param]
                        label = pd["displayLabel"]
                        val_line = vals.get_vals(em, data, pd, param, label, val, allow_blank=True)
                        if val_line:
                            self.values.append(val_line)

        # Validate line length
        check_length(data, line, expected_length, {})

        # Lookup preset number
        if self.preset_label:
            self.preset = preset_from_label(data, self.therapy, self.preset_label)


class EventTherapyState(Event):
    """ Therapy state event. """

    def __init__(self, em: ErrorManager, data: VOCSNData, line: list, filename: str = ""):
        """ Initialize. """

        # Extend super-class
        super().__init__(em, data, line, filename)

        # Therapy activation states
        self.ventilator_active = False
        self.oxygen_active = False
        self.flush_active = False
        self.cough_active = False
        self.suction_active = False
        self.nebulizer_active = False

        # Preset values
        self.ventilator_preset = None
        self.oxygen_preset = None
        self.cough_preset = None

        # Modes
        self.flush_mode = None
        self.flush_mode_id = None
        self.nebulizer_id = None
        self.nebulizer_mode = None

        # References
        param_defs = self.definition["KeyID"] or []

        # Validate line length
        check_length(data, line, 6, param_defs)

        # Process each therapy state
        line_idx = 5
        for param in param_defs:

            # Check for uninitialized records
            val = line[line_idx]
            if param in {"14600", "14601", "14602", "14603", "14604", "14605"} and val == "0":
                    error = Exception("Uninitialized therapy state record - Skipping")
                    error.cat = ve.ErrorCat.MID_ERROR
                    error.sub_cat = ve.ErrorSubCat.INVALID_REC
                    raise error

            # Read information for parameter
            check_param(param, data.metadata_parameters)
            pd = data.metadata_parameters[param]
            label = pd["displayLabel"]
            val_line = vals.get_vals(em, data, pd, param, label, val)

            # Map values
            if param == "14600":
                if val in {"1", "2", "3"}:
                    self.ventilator_active = True
                    self.ventilator_preset = val
                else:
                    self.ventilator_active = data.events_tracker.ventilator.calendar.active
            elif param == "14601":
                self.oxygen_active = val in {"1", "2", "3"}
                if self.oxygen_active:
                    self.oxygen_preset = val
            elif param == "14602":
                self.flush_active = val_line.str != "Off"
                if self.flush_active:
                    self.flush_mode_id = val
                    self.flush_mode = val_line.str
            elif param == "14603":
                self.cough_active = val in {"1", "2", "3"}
                if self.cough_active:
                    self.cough_preset = val
            elif param == "14604":
                self.suction_active = val_line.str == "On"
            elif param == "14605":
                self.nebulizer_active = val_line.str != "Off"
                if self.nebulizer_active:
                    self.nebulizer_mode_id = val
                    self.nebulizer_mode = val_line.str
            else:
                error = Exception("Unknown therapy state record: {}".format(param))
                error.cat = ve.ErrorCat.RECORD_ERROR
                error.sub_cat = ve.ErrorSubCat.INVALID_ID
                raise error

            # Next line
            line_idx += 1


class EventSetting(Event):
    """ VOCSN settings preset event. """

    def __init__(self, em: ErrorManager, data: VOCSNData, line: list, filename: str = ""):
        """ Initialize. """

        # Extend super-class
        super().__init__(em, data, line, filename)

        # Therapy association
        self.sub_therapy = ve.SubTherapies.SYSTEM
        for s_therapy in ve.SettingTherapies:
            if self.id in s_therapy.value:
                for therapy in ve.Therapies:
                    if therapy.name == s_therapy.name:
                        self.therapy = therapy
                        break
                for therapy in ve.SubTherapies:
                    if therapy.name == s_therapy.name:
                        self.sub_therapy = therapy
                        break
                break

        # Definitions
        d = self.definition
        keys = d["KeyID"] or []

        # Settings values
        md_idx = 0
        data_idx = 5
        self.control_type = []
        for x in range(md_idx, len(keys)):

            # Lookup control definition and type
            self.control = c = keys[md_idx]
            self.control_def = cd = data.metadata_parameters[self.control]

            # Validate parameter iD
            check_param(self.control, data.metadata_parameters)

            # Handle synonym lookups
            if "data_class" in cd and cd["data_class"] == "ParamSynonym":
                self.param = cd["definedBy_KeyID"]
                check_param(self.param, data.metadata_parameters)
                self.param_def = cd = data.metadata_parameters[self.param]

            # Lookup names and labels
            self.control_name = cd["tagName"]
            self.control_label = cl = cd["displayLabel"]
            ct = cd["displayType"]
            val = line[data_idx]

            # Preset values
            if self.control == "9100":
                self.preset = line[data_idx]

            # Add value
            else:

                # Preset label
                if self.control in {"14502", "14503", "14504"}:
                    self.preset_label = line[data_idx].strip('"')

                # Parameter values
                val_line = vals.get_vals(em, data, cd, c, cl, val, ct, preset=self.preset)
                if val_line:
                    self.control_type.append(ct)
                    self.values.append(val_line)

            # Next value
            md_idx += 1
            data_idx += 1

        # Validate line length
        check_length(data, line, 6, keys)


class EventConfig(Event):
    """ VOCSN settings preset event. """

    def __init__(self, em: ErrorManager, data: VOCSNData, line: list, filename: str = ""):
        """ Initialize. """

        # Extend super-class
        super().__init__(em, data, line, filename)

        # References
        d = self.definition

        # Validate line length
        check_length(data, line, 6, d)

        # Settings values
        for x in range(0, len(d["KeyID"])):

            # Add values
            param = d["KeyID"][x]
            val = line[5 + x]
            check_param(param, data.metadata_parameters)
            pd = data.metadata_parameters[param]
            label = pd["displayLabel"]
            val_line = vals.get_vals(em, data, pd, label, label, val)
            if val_line:
                self.values.append(val_line)


class EventAccess(Event):
    """ VOCSN access event with enum value. """

    def __init__(self, em: ErrorManager, data: VOCSNData, line: list, filename: str = ""):
        """ Initialize. """

        # Extend super-class
        super().__init__(em, data, line, filename)

        # References
        d = self.definition
        keys = d["KeyID"]

        # Validate line length
        check_length(data, line, 6, keys)

        # Value
        enum_vals = keys[0]["AccessGranted"]
        label = "Access Granted"
        field = line[5]
        value = enum_vals[field]
        self.values.append(EventValue(label, label, None, value, field))

        # print("access", self.id, self.value)


class EventPreUseTest(Event):
    """ VOCSN Event with a specified number of value parameter. """

    def __init__(self, em: ErrorManager, data: VOCSNData, line: list, filename: str = ""):
        """ Initialize. """

        # Extend super-class
        super().__init__(em, data, line, filename)

        # Initialize values
        self.values = []

        # Setup
        d = self.definition
        val_defs = d["KeyID"] or []

        # Validate line length
        check_length(data, line, 6, val_defs)

        # Test result
        key = "PreUseTestResult"
        result_enum = val_defs[0][key]
        self.values.append(EventValue(key, key, None, result_enum[line[5]]))

        # Remaining values
        for x in range(1, len(val_defs)):
            list_item = val_defs[x]
            key = list(list_item.keys())[0]
            val_def = list_item[key]
            name = val_def["displayLabel"]
            val_line = vals.get_vals(em, data, val_def, key, name, line[5+x])
            if val_line:
                self.values.append(val_line)

        # print("Values list", self.id, self.param, self.values)


def power_on_event(em: ErrorManager, data: VOCSNData, raw_ts, syn_ts):
    """ Create power on event. """
    line = [-1, str(raw_ts), str(syn_ts), 'E', '6004-On']
    return Event(em, data, line)


def power_off_event(em: ErrorManager, data: VOCSNData, raw_ts, syn_ts):
    """ Create power off event. """
    line = [-1, str(raw_ts), str(syn_ts), 'E', '6003-Off']
    return Event(em, data, line)
