#!/usr/bin/env python
"""
Classes and functions for tracking settings for tracking settings and recording changes over time.

    Version Notes:
        1.0.0.0  - 10/05/2019 - Created file with SettingsTrakcer and supporting classes.
        1.0.1.0  - 10/10/2019 - Changed trend calculation to compare trend with entire report range.
        1.0.2.0  - 10/30/2019 - Completed average calculations based on setting on/off time.
        1.0.2.1  - 10/31/2019 - Added tracking for setting names.
        1.0.2.2  - 11/01/2019 - Added flag to detect active settings.
        1.0.2.3  - 11/04/2019 - Fixed settings tracking. (Some ID values were mixed up)
        1.0.2.3  - 11/05/2019 - Fixed bug with precision.
        1.0.3.0  - 11/07/2019 - Reworked conversion from therapy start/stop values to settings.
        1.0.3.1  - 11/19/2019 - Fixed data type being passes between two stages of processing.
        1.0.3.2  - 11/22/2019 - Multiple changes to support proper settings agerage calculations.
        1.0.3.3  - 11/29/2019 - Added line to populate new config event list.
        1.0.4.0  - 12/05/2019 - Implemented patient reset. Fixed a bug that showed spurious changes at end of report.
                               Fixed preset change logic to consistently ignore 6006 messages. Added preset lookups.
                               Fixed bug where first preset label was not captured in utilization session details.
        1.0.4.1  - 12/10/2019 - Added proper vent preset handling to 6006 records (was out of date. Added specificity to
                               a warning message. Moved therapy start/stop metadata lookup to metadata reader.
        1.0.4.2  - 12/11/2019 - Corrected some preset label lookup lines.
        1.0.4.3  - 12/12/2019 - Added information needed in logs.
        1.0.4.4  - 12/14/2019 - Added applicability fields to Settings model.
        1.0.5.0  - 12/15/2019 - Added post-processing update stack for event values.
        1.0.5.1  - 12/18/2019 - Added settings tracking for settings outside of preset groups. Added robustness to some
                               lookup functions.
        1.0.5.2  - 12/20/2019 - Added backward compatibility for parameter synonyms.
        1.0.5.3  - 12/21/2019 - Implemented error management. Moved some preset lookup functions to utilities.
        1.0.5.4  - 01/07/2020 - Added a value conversion protection.
        1.0.5.5  - 01/18/2020 - Implemented pre-trend average calculations.
        1.0.5.6  - 01/19/2020 - Centralized trend logic.
        1.0.5.7  - 01/26/2020 - Adjusted preset history filter.
        1.0.5.8  - 02/01/2020 - Updated to new log format.
        1.0.5.9  - 02/04/2020 - Filtered OFF to Off and ON to On.
        1.0.5.10 - 02/17/2020 - Fixed a bug where string values were not always read from EventValue types. Switched
                                from dict conditions to sets for performance.
        1.0.5.11 - 02/26/2020 - Added session tracking on 87 oxygen mode change.
        1.1.0.0  - 02/27/2020 - Changed current setting data type fron str to EventVal.
        1.1.0.1  - 02/28/2020 - Added "spontaneous" override.
        1.1.0.2  - 03/11/2020 - Added preset override to current preset function.
        1.1.1.0  - 03/27/2020 - Corrected datetime filter on preset history population, added filters to catch
                                intermediate states in the middle of a recursive event processing sequence. Corrected
                                data type reference. Corrected settings record inclusion filter to properly consider
                                applicability changes.
        1.1.1.1  - 03/28/2020 - Corrected settings average calculations to include unterminated sessions.
        1.1.1.2  - 03/29/2020 - Use "was" preset values on ventilation preset change ensuring self-consistency.
        1.1.2.0  - 04/05/2020 - Added volume-targeted mode override.
        1.1.2.1  - 04/06/2020 - Constrained volume targeted mode overrids to v4.06.05 and up.

"""

__author__ = "John Dorian for Sai Systems Technologies"
__copyright__ = "Copyright 2019"
__version__ = "1.1.2.1"

# Built-in modules
from datetime import datetime, timedelta

# VOCSN modules
from modules.models.report import Report
from modules.models import vocsn_enum as ve
from modules.models.report import ReportRange
from modules.models.errors import ErrorManager
from modules.processing import utilities as ut
from modules.models.vocsn_data import VOCSNData
from modules.processing.values import EventValue
from modules.models import event_types as e_types
from modules.processing.utilities import calc_trend
from modules.processing.events import TherapyTracker, log_preset_period
from modules.processing.utilities import current_preset_id, current_preset_label


class SettingsTracker:
    """ Process and store settings changes. """

    def __init__(self, em: ErrorManager, data: VOCSNData, report: Report):
        """
        Initialize manager with settings definitions.
        :param em: Error manager.
        :param data: VOCSN data container.
        :param report: Report definitions.
        """

        # References
        self.em = em
        self.data = data
        self.report = report

        # Properties
        self.first = True

        # Populate permanent groups
        for therapy in ve.SettingTherapies:
            data.settings_therapies[therapy.name.lower()] = {}

        # Populate preset groups
        setting_defs = data.metadata_settings
        for m_id, group_def in data.metadata_messages.items():

            # Only read preset group definition records
            if int(m_id) >= 6000:
                continue

            # Define groups
            preset_group = data.settings_presets[m_id] = {}
            preset = "0" if m_id == "5001" else "1"
            data.settings_presets[m_id]["current_preset"] = preset
            data.settings_presets[m_id]["preset_history"] = []
            data.settings_presets[m_id]["last_change"] = None

            # Add setting to groups
            key_list = group_def["KeyID"]
            for key in key_list:

                # Skip state records (tracked within corresponding setting model)
                if "state" in key:
                    continue

                # Lookup setting definition
                definition = setting_defs[key]

                # Store setting in appropriate groups
                # Note: Preset IDs are not global, so are only tracked in each preset group.
                therapy_group, therapy_name = ut.lookup_therapy_group(data, m_id)
                tracker = getattr(self.data.events_tracker, therapy_name) if therapy_name != "system" else None
                setting = Setting(em, report, key, definition, tracker, preset_group, m_id)
                if key != "9100":
                    data.settings_all[key] = setting
                preset_group[key] = setting

                # Set therapy group
                if therapy_group is not None:
                    therapy_group[key] = setting
                    continue

        # Populate settings trackers for therapy start/stop values
        start_defs = data.metadata_t_start
        end_defs = data.metadata_t_stop
        if not start_defs or not end_defs:
            error = Exception("Missing therapy start/end definitions in metadata.")
            error.cat = ve.ErrorCat.PROCESS_ERROR
            error.sub_cat = ve.ErrorSubCat.METADATA_ERROR
            raise error
        start_stop_defs = [start_defs, end_defs]
        for def_list in start_stop_defs:
            for t_id, therapy_start in def_list.items():
                for therapy in ve.Therapies:
                    if t_id in therapy.value:
                        if not therapy_start["attributes"]:
                            continue
                        for key in therapy_start["attributes"]:

                            # Skip state records (tracked within corresponding setting model)
                            if "state" in key:
                                continue

                            # Skip irrelevant values
                            if key == "is-preset-change-only":
                                continue
                            if key == "therapy-duration-seconds" and therapy != ve.Therapies.NEBULIZER:
                                continue

                            # If not already lists, add start/stop value to settings lists
                            if key not in data.settings_all:
                                definition = data.metadata_parameters[key]
                                t_id = ut.lookup_therapy_from_name(therapy.name)[-1]
                                p_id = ut.lookup_preset_from_name(therapy.name)[-1]
                                therapy_group, therapy_name = ut.lookup_therapy_group(data, t_id)
                                tracker = getattr(data.events_tracker, therapy_name) if therapy_name != "system" \
                                    else None
                                preset_group = data.settings_presets[p_id]
                                setting = Setting(em, report, key, definition, tracker, preset_group, t_id,
                                                  start_stop=True)
                                preset_group[key] = setting
                                therapy_group[key] = setting
                                data.settings_all[key] = setting

        # Add settings remaining settings
        for param, definition in data.metadata_parameters.items():
            if definition["data_class"] == "ParamSynonym":
                continue
            if "Setting" not in definition["displayType"]:
                continue
            if param in data.settings_all:
                continue
            setting = Setting(em, report, param, definition)
            setting.preset_group = {"current_preset": "0", "last_change": None}
            data.settings_all[param] = setting

    def update_setting(self, setting_id: str, preset: str, time: datetime, value: e_types.EventValue,
                       state: e_types.EventValue, was_val: bool = False, update_preset: bool = True,
                       preset_label: str = None):
        """
        Update a setting.
        :param setting_id: Setting ID used as index key.
        :param preset: Preset number.
        :param time: New setting change time.
        :param value: New setting value.
        :param state: On/Off state value.
        :param was_val: If true, value represents a previous state
        :param update_preset: If true, change the current preset for the group to the new preset value.
        :param preset_label: Optional preset label.
        """

        # States are processed together with their primary setting parameter ID.
        if "state" in setting_id:
            return

        # Handle unexpected setting type
        if setting_id not in self.data.settings_all.keys():
            raise Exception("Unknown setting control ID: {}".format(setting_id))

        # Update settings model
        setting = self.data.settings_all[setting_id]
        # v = value.num if value.num is not None else value.str
        s = (state.str in ve.DataTypes.ACTIVE) if state else setting.states[preset]
        setting.update(preset, value, time, s, was_val, update_preset=update_preset, new_label=preset_label)

    @staticmethod
    def change_preset(tracker: TherapyTracker, r_range: ReportRange, preset_group: dict, preset_idx: str, preset_label,
                      time: datetime):
        """ Change a preset and all the included settings. """

        # No preset to update
        if not preset_idx or preset_idx == "0":
            return

        # Stop tracking after report range
        if time > r_range.data_end:
            return

        # Make sure there is actually a change
        # Note: Last preset label is the last preset label for the NEW preset setting.
        last_preset_idx = preset_group["current_preset"]
        last_preset_label = current_preset_label(tracker.data, tracker.therapy, preset_idx)
        if not preset_label:
            preset_label = last_preset_label
        preset_changed = (last_preset_idx != preset_idx) or (last_preset_label != preset_label)

        # Mark preset change
        preset_history = preset_group["preset_history"]
        if preset_changed:
            log_preset_period(tracker, time)
            preset_group["current_preset"] = preset_idx
            time = max(time, r_range.data_start)
            if r_range.data_started:
                preset_history.append(PresetChange(preset_idx, preset_label, time))

            # Process changes to all included settings
            for key, setting in preset_group.items():
                if type(setting) == Setting:
                    setting.update(preset_idx, setting.current[preset_idx], time, setting.states[preset_idx],
                                   update_preset=False, old_preset=last_preset_idx)

    def process_events(self):
        """ Calculate trends for all settings. """

        # Check all settings
        for key, setting in self.data.settings_all.items():

            # Catch errors
            try:

                # Filter changes, excluding intermediate states (changes at same timestamp)
                remove = []
                for idx, item in enumerate(setting.history):
                    if idx > 0:
                        if setting.history[idx].time == setting.history[idx - 1].time:
                            remove.append(idx - 1)
                offset = 0
                for idx in remove:
                    del setting.history[idx - offset]
                    offset += 1

                # Only process numeric values - Exclude preset setting IDs
                s_type = setting.definition["displayType"]
                if s_type == "NumericSetting":
                    if "ActivePreset" not in setting.definition["tagName"]:
                        setting.calc_trends()
                if "numeric" in s_type.lower():
                    setting.calc_trends()

            # Handle error for failed setting channel
            except Exception as e:
                self.em.log_error(ve.Programs.REPORTING, ve.ErrorCat.PROCESS_ERROR, ve.ErrorSubCat.INTERNAL_ERROR,
                                  "Error while calculating settings trends", e)

    def vent_preset(self, event: e_types.Event, value: EventValue, was: EventValue = None):
        """ Handle a ventilation preset change. """

        # Track change
        tracker = self.data.events_tracker.ventilator
        if was:
            old_preset = was.str.split(' ')[-1]
        else:
            old_preset = self.data.settings_presets["5002"]["current_preset"]
        new_preset = value.str.split(' ')[-1]
        event.old_preset_label = current_preset_label(self.data, ve.Therapies.VENTILATOR, old_preset)
        event.new_preset_label = current_preset_label(self.data, ve.Therapies.VENTILATOR, new_preset)
        r_range = self.report.range
        group = self.data.settings_presets["5002"]
        self.change_preset(tracker, r_range, group, new_preset, event.new_preset_label, event.syn_time)
        group = self.data.settings_presets["5003"]
        self.change_preset(tracker, r_range, group, new_preset, event.new_preset_label, event.syn_time)

    def add_event(self, event: e_types.Event):
        """
        Track settings changes from preset snapshot events.
        :param event: Setting event line from data file.
        """

        # Setting change
        e_id = event.id
        if e_id == ve.EventIDs.SETTINGS_CHANGE:

            # Identify values and states
            is_val = None
            was_val = None
            is_state = None
            was_state = None
            for val in event.values:
                if "State" in val.name:
                    if "was" in val.name:
                        was_state = val
                    else:
                        is_state = val
                else:
                    if "was" in val.name:
                        was_val = val
                    else:
                        is_val = val

            # Handle FiO2 setting - On/Off determined by value. 21% = Off, >21% = On
            if event.control == "41":
                is_num = event.values[1].num
                was_num = event.values[0].num
                is_on = is_num > 21
                is_state_num = 1 if is_on else 0
                is_state_str = "ON" if is_on else "OFF"
                is_state = e_types.EventValue(event.control, "is-OnOffState", is_state_num, is_state_str)
                event.values.append(is_state)
                was_on = was_num > 21
                was_state_num = 1 if was_on else 0
                was_state_str = "ON" if was_on else "OFF"
                was_state = e_types.EventValue(event.control, "was-OnOffState", was_state_num, was_state_str)
                event.values.insert(1, was_state)

            # On/Off only events need value routed as state
            if hasattr(event, "control_type") and event.control_type in {"OnOffSetting", "OnOffAlarm"}:
                is_state = is_val

            # Update ventilator preset
            if is_val and is_val.key == "22":
                self.vent_preset(event, is_val, was_val)

            # Process control changes
            if is_val:
                self.update_setting(event.control, event.preset, event.syn_time, is_val, is_state, update_preset=False)

            # Store reference in list
            self.data.events_config.append(event)

        # Setting snapshot
        elif e_id in ve.EventIDs.SETTINGS_PRESETS:

            # Process each value in preset
            for x in range(0, len(event.values)):

                # Identify values and states
                value = event.values[x]
                if not value:
                    continue
                c_type = getattr(event, "control_type")[x]
                if "OnOff" in c_type and c_type not in {"OnOffSetting", "OnOffAlarm"}:
                    state = event.values[x+1]
                    x += 1
                else:
                    state = EventValue(value.key, value.name, None, "ON")

                # Update ventilator preset
                if value.key == "22":
                    self.vent_preset(event, value)

                # Process settings change
                label = event.preset_label if hasattr(event, "preset_label") else None
                self.update_setting(value.key, event.preset, event.syn_time, value, state, update_preset=False,
                                    preset_label=label)

    def update_history(self, time):
        """ Enter initial value for all settings. """

        def are_equal(c_1, c_2):
            e = c_1.value == c_2.value
            if type(c_1) is PresetChange:
                e = c_1.label == c_2.label and e
            else:
                e = c_1.active == c_2.active and e
                e = c_1.enabled == c_2.enabled and e
                e = c_1.applicable == c_2.applicable and e
            return e

        # Settings history
        for _, setting in self.data.settings_all.items():
            if type(setting) is Setting:
                app = setting.applicable
                val = setting.current_value()
                state = setting.current_state()
                active = setting.tracker.calendar.active if setting.tracker else True
                if val is not None:
                    changed = True
                    change = SettingsChange(val, time, active, state, applicable=app)
                    if len(setting.history) > 0:
                        last_change = setting.history[-1]
                        changed = not are_equal(change, last_change)
                    if changed:
                        setting.history.append(change)

        # Preset History
        t = ve.Therapies
        m = ve.PresetMIDs
        groups = self.data.settings_presets
        therapies = [t.VENTILATOR, t.OXYGEN, t.COUGH]
        group_ids = [m.VENTILATOR, m.OXYGEN, m.COUGH]
        for x in range(0, 3):
            therapy = therapies[x]
            group_id = group_ids[x].value[0]
            group = groups[group_id]
            history = group["preset_history"]
            preset = group["current_preset"]
            label = current_preset_label(self.data, therapy, preset)
            if preset is not None:
                changed = True
                change = PresetChange(preset, label, time)
                if len(history) > 0:
                    last_change = history[-1]
                    changed = not are_equal(change, last_change)
                if changed:
                    history.append(change)


class Setting:
    """ Setting model. Tracks current setting while processing data and stores list of changes. """

    def __init__(self, em: ErrorManager, report: Report, settings_id: str, definition: dict, tracker:
                 TherapyTracker = None, preset_group: dict = None, preset_group_id: str = None,
                 start_stop: bool = False):
        """ Initialize. """

        # Properties
        self.id = settings_id
        self.definition = definition
        self.display_type = definition["displayType"]
        self.name = definition["displayLabel"].title()
        self.always_on = self.display_type not in ve.DataTypes.ON_OFF_TYPES
        self.start_stop = start_stop
        self.tracker = tracker
        self.em = em

        # Group association
        self.preset_group = preset_group

        # Applicability
        self.applicable = True
        self.model_applicability = True

        # Values
        is_label = settings_id == "9100"
        self.current = init_preset_list(preset_group_id, self.id, self.name, is_label)
        self.states = init_preset_list(preset_group_id)
        self.active = False
        self.history = []
        self.last_time = None
        self.was_used = False
        self.preset_group_id = preset_group_id

        # Average trackers
        self.range = r_range = report.range
        self.track_avg = SettingAverage(r_range.data_start, r_range.data_end)
        self.track_pre_trend = SettingAverage(r_range.data_start, r_range.trend_start)
        self.track_trend = SettingAverage(r_range.trend_start, r_range.data_end)
        self.average_value = None
        self.trend_value = None
        self.trend_delta = None
        self.trend_percent = None

    def update(self, new_preset, new_value, time: datetime, new_state: bool = True, was_value: bool = False,
               force: bool = False, update_preset: bool = False, old_preset: str = None, new_label: str = None):
        """
        Update the current state and add a change record to the history for this setting.
        :param new_preset: New preset number.
        :param new_value: New setting value.
        :param time: Change time.
        :param new_state: New on/off state.
        :param was_value: Indicates a change was missed and a time must be reconstructed.
        :param force: Store a change event event if no change. (First record in report range)
        :param update_preset: If true, updates preset to new preset value.
        :param old_preset: Previous preset index. Used to check if individual value changed.
        :param new_label: New preset label.
        """

        # Function to set a new mode override
        def set_mode_override(tracker, string, enum):
            tracker.override_active = True
            tracker.override_mode = EventValue("24", "modeControlSettingID", None, string, enum)
            return tracker.override_mode

        # References and vars
        new_enum = None
        vent_val = None
        event_val = None

        # Standardize format
        if type(new_value) == e_types.EventValue:
            event_val = new_value
            new_value = new_value.num if new_value.num is not None else new_value.str
            new_enum = event_val.enum

        # Lookup old values
        if not old_preset:
            old_preset = self.preset_group["current_preset"]
        old_label = None
        if self.tracker:
            old_label = current_preset_label(self.tracker.data, self.tracker.therapy, new_preset)
        if new_label is None:
            new_label = old_label
        last_change = self.preset_group["last_change"]
        if new_preset is None:
            new_preset = old_preset
        old_active = self.active
        old_event_val = self.current[old_preset]
        old_value = None
        if old_event_val:
            old_value = old_event_val.num if old_event_val.num is not None else old_event_val.str
        old_state = self.states[old_preset]

        # Value not provided, reuse old value
        if event_val is None:
            event_val = self.current[new_preset]
            if not event_val:
                return
        if new_value is None:
            new_value = event_val.num if event_val.num is not None else event_val.str
        if new_state is None:
            new_state = self.states[new_preset]

        # Force always-on settings on
        if self.always_on:
            new_state = True

        # Look up therapy active state
        new_active = self.tracker.calendar.active if self.tracker else True
        if new_active is None and self.display_type not in ve.DataTypes.ON_OFF_VAL_TYPES:
            new_active = True

        # This only happens if a record is already logged as missing
        # Make up a time if we missed a change
        if was_value:
            lt = self.last_time
            if last_change:
                if lt:
                    lt = max(lt, last_change)
                else:
                    lt = last_change
            if lt:
                time = lt + (time - lt) * 0.5
            else:
                time = time - timedelta(minutes=5)

        # Enable setting in report if used
        if new_state:
            self.was_used = True

        # Ventilation mode overrides
        is_mode = self.id == "24"
        is_circuit = self.id == "13"
        is_volume_targeted = self.id == "27"
        if (is_mode or is_circuit or is_volume_targeted) and (old_preset == new_preset or update_preset):

            # References
            d = self.tracker.data
            vent = d.events_tracker.ventilator
            mode = d.settings_all["24"].current_enum()
            bi_level = (new_enum if is_mode else mode) in ["2225", "2230"]
            mouthpiece = (new_enum if is_circuit else d.settings_all["13"].current_enum()) == "2052"
            volume_targeted = (new_enum if is_volume_targeted else d.settings_all["27"].current_enum()) \
                in ["0", "2150", "2152"]

            # Update base mode
            if is_mode and event_val and event_val.enum not in ["2222", "2223", "2224", "2230"]:
                vent.base_mode = event_val
            bm = vent.base_mode

            # Spontaneous override
            if bi_level and mouthpiece and not volume_targeted:
                mode_value = "Spontaneous"
                mode_enum = "2230"
                if mode != mode_enum:
                    vent_val = set_mode_override(vent, mode_value, mode_enum)
                if is_mode:
                    event_val = vent_val
                    new_value = mode_value
                    new_enum = mode_enum

            # Volume targeted override
            elif volume_targeted and 40605 <= self.tracker.data.int_ver:
                mode_value = mode_enum = None

                # Vol. Targeted PS
                if bm.enum in ["2225", "2222"]:
                    mode_value = "Vol. Targeted-PS"
                    mode_enum = "2222"

                # Vol. Targeted PC
                elif bm.enum in ["2226", "2223"]:
                    mode_value = "Vol. Targeted-PC"
                    mode_enum = "2223"

                # Vol. Targeted SIMV
                elif bm.enum in ["2227", "2224"]:
                    mode_value = "Vol. Targeted-SIMV"
                    mode_enum = "2224"

                # No Override
                else:
                    vent.override_active = False
                    vent.override_mode = None
                    vent_val = vent.base_mode
                    new_value = vent_val.str
                    new_enum = vent_val.enum

                # Update mode value
                if mode_value and mode_enum:
                    if mode != mode_enum:
                        vent_val = set_mode_override(vent, mode_value, mode_enum)
                    if is_mode:
                        event_val = vent_val
                        new_value = mode_value
                        new_enum = mode_enum

            # No override
            else:
                if vent.override_mode:
                    if is_mode:
                        vent.override_active = False
                        vent.override_mode = None
                    vent_val = vent.base_mode
                    new_value = vent_val.str
                    new_enum = vent_val.enum

        # Ignore unchanged states
        if (new_preset == old_preset) and (new_label == old_label) and (new_value == old_value) and \
                (new_state == old_state) and (new_active == old_active) and not force and \
                (not vent_val or not is_mode):
            return

        # Update preset values
        self.current[new_preset] = event_val
        self.states[new_preset] = new_state
        self.active = new_active

        # Stop tracking after report range
        if time > self.range.end:
            return

        # Update label
        if old_label != new_label and self.tracker:
            label_id = current_preset_id(self.tracker.therapy)
            if label_id in self.preset_group:
                preset_val = EventValue(label_id, "Preset Label", None, new_label)
                self.preset_group[label_id].current[new_preset] = preset_val

        # Update preset
        if update_preset and new_preset is not None:
            if new_preset != self.preset_group["current_preset"]:
                self.preset_group["last_change"] = time
            SettingsTracker.change_preset(self.tracker, self.range, self.preset_group, new_preset, new_label, time)

        # Update ventilator mode if needed
        if vent_val and not is_mode:
            self.tracker.data.settings_all["24"].update(new_preset, vent_val, time)

        # Update Oxygen Mode
        current_preset = self.preset_group["current_preset"]
        if self.id == "87" and current_preset == new_preset:

            # Create EventValue if needed
            if not event_val:
                event_val = EventValue("87", "Oxygen Delivery Mode", None, new_enum)

            # Update O2 mode durations
            self.tracker.track_o2_mode(time, event_val)

    def current_value(self):
        """ Get current value in context of event processing sequence. """
        preset = self.preset_group["current_preset"] if self.preset_group else None
        if not preset:
            return None
        if preset:
            setting_val = self.current[preset]
        elif "0" in self.current:
            setting_val = self.current["0"]
        else:
            return None
        if setting_val is None:
            return None
        if setting_val.num is not None:
            return setting_val.num
        else:
            return setting_val.str

    def current_state(self):
        """ Get current state in context of event processing sequence. """
        preset = self.preset_group["current_preset"] if self.preset_group else None
        if preset:
            return self.states[preset]
        elif "0" in self.current:
            return self.current["0"]
        else:
            return None

    def current_enum(self, preset_num=None):
        """ Get current value as enum. """
        preset = preset_num if preset_num is not None else self.preset_group["current_preset"]
        if preset is None:
            return None
        setting_val = self.current[preset]
        if setting_val is None:
            return None
        else:
            return setting_val.enum

    def calc_trends(self):
        """ Calculate trend statistics. """

        def _add_to_average(set_change: SettingsChange, avg: SettingAverage):
            """ Add time preceding setting change to average calculations. """

            # Variables
            ct = set_change.time
            cv = float(set_change.value) if set_change.value is not None else None
            ca = set_change.active
            ce = set_change.enabled
            cap = set_change.applicable

            # Skip invalid types
            if cv is None:
                return

            # Constrain time to range
            if ct is not None and avg.start <= ct and avg.last_time is not None and avg.last_time <= avg.end:

                # First numerical record in range - initialize values so field shows on report
                if avg.total_val is None:
                    avg.total_val = 0
                    avg.total_time = timedelta(seconds=0)
                    avg.average = 0

                # Add to average time
                start_time = min(max(avg.last_time, avg.start), avg.end)
                end_time = ct = max(min(ct, avg.end), avg.start)
                time = end_time - start_time

                # Only add to average when setting is enabled and applicable, and therapy is in use
                if time.total_seconds() > 0 and avg.last_enabled and avg.last_active and avg.last_applicable:
                    avg.total_time += time
                    avg.total_val += time.total_seconds() * avg.last_value

            # Update last values
            avg.last_time = ct
            if cv is not None:
                avg.last_value = cv
            avg.last_active = ca
            avg.last_enabled = ce
            avg.last_applicable = cap

            # Value set
            if not avg.is_set and avg.total_val is not None and avg.total_val > 0:
                avg.is_set = True

        # Finish calculations
        def _finish_average(avg: SettingAverage):

            # Check if final addition is needed
            if avg.last_time:
                start_time = min(max(avg.last_time, avg.start), avg.end)
                time = avg.end - start_time
                if time.total_seconds() > 0 and avg.last_value is not None and avg.last_enabled and avg.last_active \
                        and avg.last_applicable:

                    # Initialize if needed
                    if avg.total_val is None:
                        avg.total_val = 0
                        avg.total_time = timedelta(seconds=0)
                        avg.average = 0

                    # Add time
                    avg.total_time += time
                    avg.total_val += time.total_seconds() * avg.last_value

        # Catch errors from single event
        try:

            # Process each setting change and update averages
            # data_list = combined_list if combined_list else self.history
            for change in self.history:

                # Report range average
                _add_to_average(change, self.track_avg)

                # Trend range average
                if self.range.use_trend:
                    _add_to_average(change, self.track_pre_trend)
                    _add_to_average(change, self.track_trend)

            # Finish calculations
            _finish_average(self.track_avg)
            if self.range.use_trend:
                _finish_average(self.track_pre_trend)
                _finish_average(self.track_trend)

            # Calculate trend values
            t_avg = self.track_avg
            if t_avg.is_set:
                self.average_value = t_avg.total_val / t_avg.total_time.total_seconds()
                if self.range.use_trend:
                    pre_trend = self.track_pre_trend
                    trend = self.track_trend
                    if pre_trend.is_set and trend.is_set:
                        pre_trend_value = pre_trend.total_val / pre_trend.total_time.total_seconds()
                        self.trend_value = trend.total_val / trend.total_time.total_seconds()
                        self.trend_delta, self.trend_percent = calc_trend(pre_trend_value, self.trend_value)

        # Handle errors
        except Exception as e:
            self.em.log_error(ve.Programs.REPORTING, ve.ErrorCat.PROCESS_ERROR, ve.ErrorSubCat.INTERNAL_ERROR,
                              "Error calculating trend for setting", e, p_id=self.id)


class SettingAverage:
    """ Container for settings average calculations. """

    def __init__(self, start, end):
        """ Instantiate. """
        self.is_set = False
        self.start = start
        self.end = end
        self.range = None
        if end and start:
            self.range = end - start
        self.last_applicable = False
        self.last_enabled = False
        self.last_active = False
        self.last_value = None
        self.last_time = None
        self.total_time = None
        self.total_val = None
        self.average = None


class SettingsChange:
    """ Track the time and value for a setting change. """

    def __init__(self, val, time: datetime, active: bool, enabled: bool = True, applicable: bool = True):
        """ Initialize. """
        if val == "OFF":
            val = "Off"
        if val == "ON":
            val = "On"
        self.value = val
        self.time = time
        self.active = active
        self.enabled = enabled
        self.applicable = True
        if applicable is not None:
            self.applicable = applicable


class PresetChange:
    """ Track the time and value of a preset change. """

    def __init__(self, idx: str, label: str, time: datetime):
        """ Initialize. """
        self.value = idx
        self.label = label
        self.time = time
        self.applicable = True


def init_preset_list(group_id: str, key: str = None, name: str = None, is_label: bool = False):
    """
    Generate a dictionary to store appropriate preset values.
    :param group_id: Preset group ID.
    :param key: Parameter ID.
    :param name: Parameter name.
    :param is_label: Indicates these are preset labels ane must be initialized.
    :return: Preset group
    """
    
    # Get preset group
    if group_id == "5001":
        group = ve.PresetIDs.NEB_SUC_SYS
    elif group_id == "5002":
        group = ve.PresetIDs.VENTILATOR
    elif group_id == "5003":
        group = ve.PresetIDs.VENTILATOR
    elif group_id == "5004":
        group = ve.PresetIDs.OXYGEN
    elif group_id == "5005":
        group = ve.PresetIDs.COUGH

    # No grouping found
    else:
        return {"0": None}

    # Construct dict and return
    presets = {}
    for preset in group:
        init_val = None
        if is_label:
            init_val = EventValue(key, name, None, "Preset {}".format(preset))
        presets[preset] = init_val
    return presets
