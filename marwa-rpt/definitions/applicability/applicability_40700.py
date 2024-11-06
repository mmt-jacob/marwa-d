#!/usr/bin/env python
"""
Applicability logic definitions.

    Instructions:
        1) Make a copy of this file.
        2) Rename it with the precise VOCSN software version, excluding '.' characters from the name.
        3) Modify the logic here as needed.

"""

# VOCSN modules
from modules.models.vocsn_enum import Models
from modules.processing.applicability import ApplicabilityStack


class ApplicabilityTracker:
    """ Provides temporary state indexing to accelerate applicability determination for parameters. """

    def __init__(self):
        """ Initialize. """

        # References
        self.data = None
        self.model = None

        # Processing flag - reset when new events are created
        self.up_to_date = False

        # Dependee values
        self.mode = None
        self.circuit_type = None
        self.cough_active = None
        self.suction_active = None
        self.nebulizer_active = None
        self.oxygen_mode = None
        self.oxygen_source = None
        self.fio2_monitor = None
        self.volume_targeted = None
        self.pres_cont_flow_term = None

        # Update stack
        # Objects placed here will be updated at end of read loop with final applicability state
        # Objects must have "applicability" field
        self.stack = ApplicabilityStack()

    def setup(self, data):
        """
        Setup function available after initialization so data container can be accessed directly after this class is
        initialized from an exec call.
        :param data: VOCSN data container.
        """

        # References
        self.data = data
        self.model = data.model_id

        # One-time mode applicability determination
        for _, setting in data.settings_all.items():
            self.model_applicability(setting)

    def model_applicability(self, param):
        """
        Determine if a parameter is applicable for the specified model.
        :param param: Parameter model class. (MonitorChannel or Setting)
        """

        # NOTE: Matched IDs are subtractive, so being listed here means the parameter is n/a.

        # Variables
        a = True
        p_id = param.id
        model = self.model
        d_class = param.definition["data_class"]

        # Settings
        if d_class == "Setting":

            # VC Model
            if model == Models.VC:
                # O2 Concentrator Activate
                # Suction Activate
                # Nebulizer Activate
                # FiO2 Control
                # FiO2 Monitor
                # O2 Flow Equivalent
                # Cough and Suction
                # Suction Vacuum
                if p_id in {"3", "5", "6", "41", "72", "45", "54", "55"}:
                    a = False

            # VC Pro Model
            elif model == Models.VC_PRO:
                # O2 Concentrator Activate
                # Suction Activate
                # Nebulizer Activate
                # O2 Flow Equivalent
                # Cough and Suction
                # Suction Vacuum
                if p_id in {"3", "5", "6", "45", "54", "55"}:
                    a = False

            # VOCSN Model
            elif model == Models.VOCSN:
                # FiO2 Control
                # FiO2 Monitor
                if p_id in {"41", "72"}:
                    a = False

            # VCSN Pro Model
            elif model == Models.VCSN_PRO:
                # O2 Concentrator Activate
                if p_id in {"3"}:
                    a = False

            # V Pro Model
            elif model == Models.V_PRO:
                # O2 Concentrator Activate
                # Cough Assist
                # Suction Activate
                # Nebulizer Activate
                # O2 Flow Equivalent
                # Cough and Suction
                # Suction Vacuum
                if p_id in {"3", "4", "5", "6", "45", "54", "55"}:
                    a = False

            # VOCSN Pro Model - All parameters applicable

        # Monitors
        elif d_class == "Monitor":

            # VC Model
            if model == Models.VC:
                # VPSA Usage
                # Pump Usage
                # O2 Concentrator Usage
                # FiO2
                # Calc. FiO2
                if p_id in {"12002", "12003", "14506", "9411", "9412"}:
                    a = False

            # VC Pro Model
            elif model == Models.VC_PRO:
                # VPSA Usage
                # Pump Usage
                # O2 Concentrator Usage
                # Calc. FiO2
                if p_id in {"12002", "12003", "14506", "9412"}:
                    a = False

            # VCSN Pro Model
            elif model == Models.VCSN_PRO:
                # VPSA Usage
                # O2 Concentrator Usage
                if p_id in {"12002", "14506"}:
                    a = False

            # V Pro Model
            elif model == Models.V_PRO:
                # VPSA Usage
                # Pump Usage
                # O2 Concentrator Usage
                # Calc. FiO2
                if p_id in {"12002", "12003", "14506", "9412"}:
                    a = False

            # VOCSN Model - All parameters applicable
            # VOCSN Pro Model - All parameters applicable

        # Alarms
        elif d_class == "Alarm":

            # VC Model
            if model == Models.VC:
                # Service Concentrator Soon
                # High FiO2
                # Low FiO2
                # Very Low FiO2
                # Check O2 Source
                # O2 Concentrator Fault
                if p_id in {"12072", "61", "66", "12063", "99", "12065"}:
                    a = False

            # VC Pro Model
            elif model == Models.VC_PRO:
                # Service Concentrator Soon
                if p_id in {"12072"}:
                    a = False

            # VOCSN Model
            elif model == Models.VOCSN:
                # High FiO2
                # Low FiO2
                # Very Low FiO2
                # Check O2 Source
                if p_id in {"61", "66", "12063", "99"}:
                    a = False

            # V Pro Model
            elif model == Models.V_PRO:
                # Service Concentrator Soon
                if p_id in {"12072"}:
                    a = False

            # VCSN Pro Model
            elif model == Models.VCSN_PRO:
                # Service Concentrator Soon
                if p_id in {"12072"}:
                    a = False

            # VOCSN Pro Model - All parameters applicable

        # Store result
        param.model_applicability = a

    def _index_dependees(self):
        """ Look up logical conditions once to accelerate processing. """

        # Data container references
        s = self.data.settings_all
        t = self.data.events_tracker

        # Value lookup
        self.mode = s["24"].current_enum()
        self.circuit_type = s["13"].current_enum()
        self.cough_active = t.cough.calendar.active
        self.suction_active = t.suction.calendar.active
        self.nebulizer_active = t.nebulizer.calendar.active
        self.cough_active = True
        self.suction_active = True
        self.nebulizer_active = True
        self.oxygen_mode = s["87"].current_enum()
        self.oxygen_source = s["88"].current_enum()
        self.fio2_monitor = s["72"].current_enum() in {"2026", "2152"}
        self.volume_targeted = s["27"].current_enum() in {"0", "2150", "2152"}
        self.pres_cont_flow_term = s["35"].current_enum() in {"0", "2150", "2152"}

        # Common reference values
        self.hi_flow = self.mode == "95"
        self.active = self.circuit_type in ["2050", "2054"]
        self.passive = self.circuit_type in ["2051", "2053", "2055", "2056"]

        # Mark indexed states as up to date
        self.up_to_date = True

    def update_all(self):
        """ Update all settings, monitors, and alarms with current applicability. """
        from modules.processing.settings import Setting
        from modules.models.vocsn_data import MonitorChannel

        # Variables
        changed = False

        # Settings and Alarms
        for _, setting in self.data.settings_all.items():
            if type(setting) is Setting:
                changed = self._check_applicability(setting) or changed

        # Monitors
        for _, monitor in self.data.monitors_all.items():
            if type(monitor) is MonitorChannel:
                changed = self._check_applicability(monitor) or changed

        # Update queued historical records with current state
        self.stack.update()

        # Return change value
        return changed

    def _check_applicability(self, param):
        """
        Check if parameter is applicable given the current settings states.
        :param param: Parameter ID model class.
        """

        # Check starting value
        start = param.applicable

        # Model applicability takes precedent
        if not param.model_applicability:
            param.applicable = False
            return

        # Index dependee values
        if not self.up_to_date:
            self._index_dependees()

        # Variables
        a = True
        p_id = param.id
        d_class = param.definition["data_class"][0]

        # Settings
        if d_class == "S":

            # Humidification OK
            if p_id == "14":
                a = self.circuit_type != "2052"

            # Breath Rate OK
            # PEEP OK
            # Apnea Rate OK
            elif p_id in {"25", "30", "39"}:
                a = not self.hi_flow and (self.active or self.passive)

            # Leak Compensation OK
            elif p_id == "40":
                a = not self.hi_flow and self.active

            # Tidal Volume OK
            elif p_id == "28":
                a = self.mode not in {"95", "2225", "2226", "2227"}

            # Min. Inspiratory Pressure OK
            # Pressure Adjustment Rate OK
            elif p_id in {"100", "101"}:
                a = self.mode in {"2222", "2223", "2224"}

            # Pressure Control - Is this right? (listed as never applicable)
            elif p_id == "29":
                a = False

            # IPAP OK
            elif p_id == "32":
                a = self.mode in {"2225"}

            # Flow Cycle OK
            elif p_id == "36":
                a = (self.mode in {"2226", "2223"} and self.pres_cont_flow_term) or \
                    (self.mode in {"2222", "2224", "2225", "2227", "2229"})

            # O2 Flow Equivalent OK
            elif p_id == "45":
                a = not self.hi_flow and self.oxygen_mode == "3076"

            # Inspiratory Time OK
            # Flow Trigger OK
            elif p_id in {"26", "34"}:
                a = not self.hi_flow

            # Volume Targeted - Should this stay? (not listed)
            elif p_id == "27":
                a = False

            # Pressure Support OK+
            # High Flow - is this the right parameter?
            elif p_id in {"33", "14508"}:
                a = self.mode in {"2224", "2227", "2229"}

            # Pressure Control Flow Termination OK
            elif p_id == "35":
                a = self.mode in {"2223", "2224", "2226", "2227"}

            # Time Cycle OK
            elif p_id == "37":
                a = self.mode in {"2222", "2224", "2225", "2227", "2229"}

            # Rise Time OK
            elif p_id == "38":
                a = self.mode not in {"2228", "95"}

            # Sigh OK+
            elif p_id == "42":
                a = self.mode in {"2228", "2229"}

            # Flow OK
            elif p_id == "96":
                a = self.hi_flow

            # Cough + Suction - OK to map to therapy active state instead of setting?
            elif p_id == "54":
                a = self.cough_active and self.suction_active

            # FiO2 OK
            elif p_id == "41":
                a = self.oxygen_mode == "3075"

            # Insufflation Pressure - (all OK to map to therapy active state instead of setting?)
            # Exsufflation Pressure
            # Insufflation Time
            # Exsufflation Time
            # Pause Time
            # Insufflation Rise Time
            # Cough Cycles
            # Breath Sync
            elif p_id in {"46", "47", "48", "49", "50", "51", "52", "53"}:
                a = self.cough_active

            # Vacuum - OK to map to therapy active state instead of setting?
            elif p_id == "55":
                a = self.suction_active

            # Nebulizer Duration - OK to map to therapy active state instead of setting?
            elif p_id == "57":
                a = self.nebulizer_active

            # Always Applicable (not counting model applicability)
                # Alarm Volume
                # Mode
                # High Pressure Alarm Delay
                # Oxygen Source
                # Oxygen Delivery Mode

        # Monitors
        elif d_class == "M":

            # Vte OK
            # Minute Volume OK
            # Leak OK
            if p_id in {"9406", "9407", "9409"}:
                a = not self.hi_flow and (self.active or self.passive)

            # FiO2 OK
            if p_id == "9411":
                a = (self.hi_flow and self.fio2_monitor) or \
                    (self.oxygen_mode == "3075" and self.fio2_monitor)

            # MAP OK
            # PIP OK
            # PEEP OK
            # I:E Ratio OK
            # Breath Rate OK
            # % Patient Triggered OK
            if p_id in {"9402", "9403", "9404", "9405", "9408", "9410"}:
                a = not self.hi_flow

            # Flow Setting - Not available?
            if p_id == "95":
                a = self.hi_flow

            # Calculated FiO2 OK
            if p_id == "9412":
                a = self.oxygen_mode == "3076"

            # Airway Pressure OK
            if p_id == "9401":
                a = not self.cough_active

            # Cough Airway Pressure OK
            # Peak Cough Flow OK
            # Cough Volume OK
            # Cough Cycles OK
            if p_id in {"12023", "12024", "12025", "12026"}:
                a = self.cough_active

            # Vacuum - Not available?
            if p_id == "55":
                a = self.suction_active

            # Always Applicable (not counting model applicability)
                # System Usage
                # VPSA Usage
                # Pump Usage
                # Hours Until PM Required
                # Internal Battery Capacity
                # Removable Battery 1 Capacity
                # Removable Battery 2 Capacity
                # Concentrator Usage

            # Not available data
                # Date
                # Time
                # Patient Effort
                # Pressure Waveform
                # Flow Waveform
                # Volume Waveform
                # Nebulizer Minutes Remaining

        # Alarms
        elif d_class == "A":

            # High Minute Volume OK
            # Low Minute Volume OK
            if p_id in {"60", "65"}:
                a = not self.hi_flow and (self.active or self.passive)

            # High FiO2 OK
            # Low FiO2 OK
            if p_id in {"61", "66"}:
                a = self.fio2_monitor and (self.oxygen_mode == "3075" or self.hi_flow)

            # O2 Concentration - "Concentrator or FiO2 in use"?
            if p_id == "12065":
                a = not self.hi_flow and (self.oxygen_mode == "3075" or self.oxygen_source == "3126")

            # Apnea Rate OK
            # High Breath Rate OK
            # High PEEP OK
            # Low Breath Rate OK
            # Low Inspiratory Pressure OK
            # Low PEEP OK
            # Patient Circuit Disconnect - Is this right?
            if p_id in {"58", "59", "63", "64", "67", "70", "68"}:
                a = not self.hi_flow

            # High Flow Patient Circuit Disconnect - Is this right?
            if p_id == "98":
                a = self.hi_flow or self.active or self.passive

            # Very Low FiO2 OK
            if p_id == "12063":
                a = self.fio2_monitor

            # Always Applicable (not counting model applicability)
                # Battery Use
                # Device Maintenance Required
                # Inop
                # Internal Battery Low
                # Internal Battery Critically Low
                # System Fault
                # Service Concentrator Soon
                # High Pressure
                # Check Patient Circuit
                # Check O2 Source

        # Store result
        param.applicable = a

        # Return changed value
        return start == a
