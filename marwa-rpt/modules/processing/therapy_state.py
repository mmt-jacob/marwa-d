#!/usr/bin/env python
"""
Classes and functions for handling TAR files.

    Version Notes:
        1.0.0.0 - 12/08/2019 - Created file for handling therapy state message.
        1.0.0.1 - 12/12/2019 - Added information needed in logs.
        1.0.0.2 - 02/09/2020 - Improved error management and log clarity.
        1.0.0.3 - 02/26/2020 - Fixed flaws in backup procedure for capturing preset change from 7203 record.

"""

__author__ = "John Dorian for Sai Systems Technologies"
__copyright__ = "Copyright 2019"
__version__ = "1.0.0.3"

# VOCSN modules
from modules.models.report import Report
from modules.models import vocsn_enum as ve
from modules.models.errors import ErrorManager
from modules.models.vocsn_data import VOCSNData
from modules.processing.utilities import dt_to_ts
from modules.models.vocsn_enum import EventIDs as eID
from modules.models.event_types import EventTherapyState
from modules.processing.events import create_event_record
from modules.processing.utilities import current_preset_label


def set_therapy_states(em: ErrorManager, data: VOCSNData, report: Report, e: EventTherapyState,
                       last_start_code: str = None):
    """
    Update therapy activation states, preset selections, and nebulizer mode.
    :param em: Error manager.
    :param data: VOCSN data container.
    :param report: Report definition.
    :param e: Therapy state event.
    :param last_start_code: Last ventilator start condition encountered.
    """

    # Variables and references
    r_range = report.range
    settings = data.settings_tracker

    # ---------- Ventilator ---------- #

    # Update ventilator preset
    group = ve.PresetMIDs.VENTILATOR.value[0]
    tracker = data.events_tracker.ventilator
    preset_group = data.settings_presets[group]
    preset = preset_group["current_preset"]
    e_preset = e.ventilator_preset
    if preset != e_preset:

        # Vent preset values
        def vent_preset_id(val):
            if val == "1":
                return "2175"
            if val == "2":
                return "2176"
            if val == "3":
                return "2177"
            else:
                return ""

        # Convert to corresponding 22-parameter index value
        preset_22 = vent_preset_id(e_preset)

        # Simulate a setting change event
        if preset_22:

            old_preset_num = data.settings_presets[ve.PresetMIDs.VENTILATOR.value[0]]["current_preset"]
            old_preset = vent_preset_id(old_preset_num)
            line = ["-1", dt_to_ts(e.raw_time), dt_to_ts(e.syn_time), "E", eID.SETTINGS_CHANGE, "22", "0", "9003",
                    old_preset, preset_22, "0"]
            preset_e = create_event_record(em, data, line)

            # Skip if nothing changed
            if old_preset != preset_e.values[1].enum:
                data.settings_tracker.add_event(preset_e)
                tracker.settings_events.append(preset_e)
                data.events_all.append(preset_e)

    # Update ventilator activation state
    if e.ventilator_active != tracker.calendar.active:

        # Simulate a ventilator start or stop event
        if e.ventilator_active:
            line = [e.sequence, dt_to_ts(e.raw_time), dt_to_ts(e.syn_time), "E", eID.VENT_START, last_start_code, "0"]
        else:
            line = [e.sequence, dt_to_ts(e.raw_time), dt_to_ts(e.syn_time), "E", eID.VENT_END, "0"]
        vent_e = create_event_record(em, data, line)
        data.events_tracker.add_event(vent_e)
        data.events_all.append(vent_e)

    # ---------- Oxygen ---------- #

    # Update oxygen preset
    group = ve.PresetMIDs.OXYGEN.value[0]
    tracker = data.events_tracker.oxygen
    preset_group = data.settings_presets[group]
    preset = preset_group["current_preset"]
    preset_label = current_preset_label(data, tracker.therapy, preset)
    e_preset = e.oxygen_preset
    if preset != e_preset:

        # Change preset
        settings.change_preset(tracker, r_range, preset_group, e_preset, None, e.syn_time)
        preset_label = current_preset_label(data, tracker.therapy, e_preset)

    # Update oxygen activation state
    if e.oxygen_active != tracker.calendar.active:

        # Simulate a oxygen start or stop event
        if e.oxygen_active:
            action = ["Starting", "start"]
            line = [e.sequence, dt_to_ts(e.raw_time), dt_to_ts(e.syn_time), 'E', eID.THERAPY_START, preset_label,
                    ve.SubTherapies.OXYGEN.value, "", "", "", "", "", "", "", "", "", "", "", ""]
        else:
            action = ["Stopping", "stop"]
            line = [e.sequence, dt_to_ts(e.raw_time), dt_to_ts(e.syn_time), 'E', eID.THERAPY_END, "",
                    ve.SubTherapies.OXYGEN.value, ""]
        em.log_warning(action[0] + " oxygen therapy from 7203 therapy state message")
        em.disable_tracking()
        try:
            o2_event = create_event_record(em, data, line)
            data.events_tracker.add_event(o2_event)
            data.events_all.append(o2_event)
        except Exception as err:
            em.enable_tracking()
            em.log_warning("Error while synthesizing oxygen {} event: {}".format(action[1], str(err)))
        em.enable_tracking()

    # ---------- Oxygen Flush---------- #

    # Update oxygen activation state
    tracker = data.events_tracker.oxygen
    if e.flush_active != tracker.o2_flush_active:

        # Simulate a oxygen flush start or stop event
        if e.flush_active:
            action = ["Starting", "start"]
            line = [e.sequence, dt_to_ts(e.raw_time), dt_to_ts(e.syn_time), 'E', eID.THERAPY_START, "",
                    ve.SubTherapies.OXYGEN_FLUSH.value, e.flush_mode_id, ""]
        else:
            action = ["Stopping", "stop"]
            line = [e.sequence, dt_to_ts(e.raw_time), dt_to_ts(e.syn_time), 'E', eID.THERAPY_END, "",
                    ve.SubTherapies.OXYGEN_FLUSH.value, ""]
        em.log_warning(action[0] + " O2 flush therapy from 7203 therapy state message")
        em.disable_tracking()
        try:
            o2_event = create_event_record(em, data, line)
            data.events_tracker.add_event(o2_event)
            data.events_all.append(o2_event)
        except Exception as err:
            em.enable_tracking()
            em.log_warning("Error while synthesizing O2 flush {} event: {}".format(action[1], str(err)))
        em.enable_tracking()

    # ---------- Cough ---------- #

    # Update cough preset
    group = ve.PresetMIDs.COUGH.value[0]
    tracker = data.events_tracker.cough
    preset_group = data.settings_presets[group]
    preset = preset_group["current_preset"]
    preset_label = current_preset_label(data, tracker.therapy, preset)
    e_preset = e.cough_preset
    if preset != e.cough_preset:

        # Change preset
        settings.change_preset(tracker, r_range, preset_group, e_preset, None, e.syn_time)

    # Update cough activation state
    if e.cough_active != tracker.calendar.active:

        # Simulate a cough start or stop event
        if e.cough_active:
            action = ["Starting", "start"]
            line = [e.sequence, dt_to_ts(e.raw_time), dt_to_ts(e.syn_time), 'E', eID.THERAPY_START, preset_label,
                    ve.SubTherapies.COUGH.value, "", "", "", "", "", "", "", "", "", ""]
        else:
            action = ["Stopping", "stop"]
            line = [e.sequence, dt_to_ts(e.raw_time), dt_to_ts(e.syn_time), 'E', eID.THERAPY_END, "",
                    ve.SubTherapies.COUGH.value, "", "", "", ""]
        em.log_warning(action[0] + " cough therapy from 7203 therapy state message")
        em.disable_tracking()
        try:
            o2_event = create_event_record(em, data, line)
            data.events_tracker.add_event(o2_event)
            data.events_all.append(o2_event)
        except Exception as err:
            em.enable_tracking()
            em.log_warning("Error while synthesizing cough {} event: {}".format(action[1], str(err)))
        em.enable_tracking()

    # ---------- Suction ---------- #

    # Update suction activation state
    tracker = data.events_tracker.suction
    if e.suction_active != tracker.calendar.active:

        # Simulate a suction start or stop event
        if e.suction_active:
            action = ["Starting", "start"]
            line = [e.sequence, dt_to_ts(e.raw_time), dt_to_ts(e.syn_time), 'E', eID.THERAPY_START, "",
                    ve.SubTherapies.SUCTION.value, "", "", ""]
        else:
            action = ["Stopping", "stop"]
            line = [e.sequence, dt_to_ts(e.raw_time), dt_to_ts(e.syn_time), 'E', eID.THERAPY_END, "",
                    ve.SubTherapies.SUCTION.value, "", "", ""]
        em.log_warning(action[0] + " suction therapy from 7203 therapy state message")
        em.disable_tracking()
        try:
            suction_event = create_event_record(em, data, line)
            data.events_tracker.add_event(suction_event)
            data.events_all.append(suction_event)
        except Exception as err:
            em.enable_tracking()
            em.log_warning("Error while synthesizing suction {} event: {}".format(action[1], str(err)))
        em.enable_tracking()

    # ---------- Nebulizer ---------- #

    # Update nebulizer activation state
    tracker = data.events_tracker.nebulizer
    if e.nebulizer_active != tracker.calendar.active:

        # Simulate a nebulizer start or stop event
        s_id = ve.SubTherapies.NEBULIZER.value if e.nebulizer_mode == "2825" else ve.SubTherapies.NEBULIZER_EXT.value
        if e.suction_active:
            action = ["Starting", "start"]
            line = [e.sequence, dt_to_ts(e.raw_time), dt_to_ts(e.syn_time), 'E', eID.THERAPY_START, "", s_id, "", ""]
        else:
            action = ["Stopping", "stop"]
            line = [e.sequence, dt_to_ts(e.raw_time), dt_to_ts(e.syn_time), 'E', eID.THERAPY_END, "", s_id, ""]
        em.log_warning(action[0] + " nebulizer therapy from 7203 therapy state message")
        em.disable_tracking()
        try:
            suction_event = create_event_record(em, data, line)
            data.events_tracker.add_event(suction_event)
            data.events_all.append(suction_event)
        except Exception as err:
            em.enable_tracking()
            em.log_warning("Error while synthesizing nebulizer {} event: {}".format(action[1], str(err)))
        em.enable_tracking()
