#!/usr/bin/env python
"""
Settings summary with usage/alarm graph and settings table.

    Version Notes:
        1.0.0.0 - 10/04/2019 - Created with settings_summary function.
        1.0.0.1 - 10/31/2019 - Added settings chart.
        1.0.0.2 - 11/04/2019 - Improved settings display logic.
        1.0.0.3 - 11/05/2019 - Moved things down to accommodate the multi-view logo.
        1.0.1.0 - 11/06/2019 - Reworked settings chart to render its own lines and remove label characters instead of
                               masking.
        1.0.1.1 - 11/07/2019 - Excluded preset dots for system preset because it doesn't change.
        1.0.1.2 - 11/14/2019 - Restructured suction, nebulizer, and system settings.
        1.0.1.3 - 11/17/2019 - Corrected preset group filter to allow cough preset display.
        1.0.1.4 - 11/22/2019 - Multiple changes to support proper settings average calculations. Darkened O2 Colors.
        1.0.2.0 - 11/24/2019 - Created a strings wrapper for settings labels, expanded data area, added vertical
                               subdivisions, aligned alarm graph to settings chart, and added alarm graph so later pates
        1.0.2.1 - 11/27/2019 - Updated code to properly suppress settings for inactive therapies.
        1.0.2.2 - 11/29/2019 - Referenced proper source for suction units.
        1.0.2.3 - 12/05/2019 - Implemented patient reset, excluded preset labels from settings chart.
        1.0.2.4 - 12/06/2019 - Renamed therapy section titles.
        1.0.2.5 - 12/09/2019 - Switched from setting 55 to suction-pressure.
        1.0.3.0 - 12/12/2019 - Reworked section name management. Added grouping to the first few settings per group.
        1.0.3.1 - 12/13/2019 - Added section linking. Added workaround for duplicate names. Fixed strings wrapping.
        1.0.3.2 - 12/14/2019 - Created a workaround to ensure the first settings dots appear. (ReportLab has a bug?)
        1.0.4.0 - 12/16/2019 - Added settings chart line order to settings file.
        1.0.4.1 - 12/19/2019 - Moved preset values to their own line.
        1.0.4.2 - 01/11/2020 - Adapted to align independently from calendar days.
        1.0.4.3 - 01/12/2020 - Moved data container references for general and alarm templates.
        1.0.4.4 - 01/19/2020 - Added protection against duplicate n/a values.
        1.0.4.5 - 01/24/2020 - Extended grid lines into margin between final settings.
        1.0.4.6 - 02/05/2020 - Added preset label lines to settings chart. Changed display logic for therapy sections.
        1.0.4.7 - 02/07/2020 - Specified the correct parameter ID for suction.
        1.0.4.8 - 04/01/2020 - Adjusted logic for disabled value label override.
        1.0.5.0 - 04/03/2020 - Modified logic to support new models.

"""

__author__ = "John Dorian for Sai Systems Technologies"
__copyright__ = "Copyright 2019"
__version__ = "1.0.5.0"

# Built-in modules
from datetime import datetime

# ReportLab libraries
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import Spacer
from reportlab.platypus import PageBreak
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus.tables import Table
from reportlab.platypus import BaseDocTemplate
from reportlab.platypus import NextPageTemplate
from reportlab.platypus.flowables import Flowable

# VOCSN modules
from modules.models import report as r
from modules.models import vocsn_enum as ve
from modules.models import vocsn_data as vd
from reports.elements import footers as foot
from modules.models.errors import ErrorManager
from reports.elements.styles import Styles as s
from reports.elements.templates import Bookmark
from reports.elements.utilization_graph import UtilizationGraph
from reports.elements.templates import FormattedPage
from reports.elements.headers import standard as header
from modules.processing.settings import Setting, SettingsChange
from reports.elements.general import general_template, alarm_template

# Global variables
SECTION_NAME = "Settings Summary"
REPORT = None
DATA = None
DIR = ""


def _first_page(c: FormattedPage, _: BaseDocTemplate):
    """
    First page template.
    :param c: Canvas reference passed from page constructor.
    :param _: Document reference passed from page constructor.
    """
    global REPORT, DATA, DIR

    # Header
    header(c, DIR, DATA.errors)

    # Footer
    foot.section(c, REPORT, SECTION_NAME)


class DummySetting:
    """ Dummy setting to quickly reuse the LabelCell function. """
    def __init__(self, name):
        self.id = "0"
        self.name = name
        self.definition = {"displayUnits": ""}


class LabelCell(Flowable):
    """ Draw a calendar day. """

    def __init__(self, setting, width: float, height: float, color: colors = None):
        """
        Create a flowable canvas and fill with settings markers.
        :param width: Row canvas width.
        :param height: Row canvas height.
        :param color: Dot color.
        """
        global DIR, DATA, REPORT
        Flowable.__init__(self)

        # References
        r_range = REPORT.range
        self.dir = DIR
        self.data = DATA
        self.range = r_range
        self.color = color

        # Settings data
        self.setting = setting
        self.units = setting.definition["displayUnits"]
        if setting.id == "suction-pressure":
            self.units = setting.tracker.session_vals["suction-pressure"].units
        if not self.units:
            self.units = ""

        # Label converters
        labels = DATA.label_strings
        if setting.id in labels:
            self.label = labels[setting.id]["short"]
        else:
            self.label = setting.name
            self.label = self.label.replace('Peep', 'PEEP')
            self.label = self.label.replace('Pc', 'PC')
            self.label = self.label.replace('Ipap', 'IPAP')
            self.label = self.label.replace('Epap', 'EPAP')
            self.label = self.label.replace('Fio2', 'FiO2')
            if setting.id == "98":
                self.label = "High Flow Patient Circuit Discon."

        # Properties
        self.indent = 0.1 * inch
        self.label_size = 9.5
        self.units_size = 8
        self.white_margin = 4
        self.width = width - 0.5
        self.height = height - 0.5

        # Determine line splits to strings wrap the combined label, units
        c = Canvas("temp.pdf")
        sizing = True
        wrap_mode = 0
        multi_lines = ["", ""]
        c.setFont(s.Fonts.light, self.label_size)
        label_width = c.stringWidth(self.label + " ")
        c.setFont(s.Fonts.light, self.units_size)
        units_width = c.stringWidth(("(" + self.units + ")") if self.units else "")
        while sizing:
            width_result = 0

            # Mode 0: One line
            if wrap_mode == 0:
                width_result += label_width + units_width

            # Mode 1: Label on line 1, units on line 2
            elif wrap_mode == 1:
                width_result = max(label_width, units_width)

            # Mode 2: Wrap label to next line
            elif wrap_mode == 2:
                space = " "
                words = self.label.split(' ')
                split_index = len(words)
                label_width = 0
                for x in range(0, split_index):
                    label_width = c.stringWidth(self.label + space)
                c.setFont(s.Fonts.light, self.label_size)
                while label_width > self.width - 2*self.indent and split_index > 0:
                    split_index -= 1
                    label_width = 0
                    for x in range(0, split_index):
                        label_width = c.stringWidth(words[x] + space)
                for x in range(0, len(words)):
                    if x < split_index - 1:
                        multi_lines[0] += "" if multi_lines[0] == "" else " "
                        multi_lines[0] += words[x]
                    else:
                        multi_lines[1] += "" if multi_lines[1] == "" else " "
                        multi_lines[1] += words[x]

            # Check width and escalate wrap mode if needed
            if width_result <= self.width - 2*self.indent:
                sizing = False
            else:
                wrap_mode += 1
            if wrap_mode > 2:
                break

        # Resize canvas
        if wrap_mode > 0:
            self.height += self.label_size + 0.5

        # Store results and cleanup
        self.wrap_mode = wrap_mode
        self.multi_lines = multi_lines
        del c

    def wrap(self, *args):
        """ Make internal sizes available to build engine. """
        return self.width, self.height

    def draw(self):
        """ Construct block. """

        # References
        c = self.canv
        wrap_mode = self.wrap_mode
        multi_lines = self.multi_lines

        # Prepare canvas
        c.setLineWidth(0.5)
        c.scale(1, 1)
        
        # Dimensions
        bottom = self.label_size * 0.3
        middle = bottom + self.label_size + 1.5

        # Draw main label
        x_pos = self.indent
        color = self.color if self.color else colors.black
        c.setFillColor(color)
        c.setFont(s.Fonts.light, self.label_size)
        if wrap_mode == 0:
            c.drawString(x_pos, bottom, self.label)
            x_pos += c.stringWidth(self.label + " ")
        elif wrap_mode == 1:
            c.drawString(x_pos, middle, self.label)
        else:
            c.drawString(x_pos, middle, multi_lines[0])
            c.drawString(x_pos, bottom, multi_lines[1])
            x_pos += c.stringWidth(multi_lines[1] + " ")

        # Draw units
        if self.units != "":
            c.setFillColor(s.Colors.med_gray)
            c.setFont(s.Fonts.light, self.units_size)
            c.drawString(x_pos, bottom, "(" + self.units + ")")


class SettingRow(Flowable):
    """ Draw a calendar day. """

    def __init__(self, em: ErrorManager, setting, width: float, height: float, color: colors = colors.black, 
                 left: float = 0, key: str = "value"):
        """
        Create a flowable canvas and fill with settings markers.
        :param em: Error manager.
        :param width: Row canvas width.
        :param height: Row canvas height.
        :param color: Dot color.
        :param key: Specify a preset attribute name.
        """
        global DIR, DATA, REPORT
        Flowable.__init__(self)

        # References
        r_range = REPORT.range
        self.em = em
        self.key = key
        self.dir = DIR
        self.data = DATA
        self.color = color
        self.range = r_range

        # Settings data
        self.setting = setting
        self.precision = None
        if type(setting) is Setting:
            self.precision = setting.definition["precision"]

        # Properties
        self.left = left
        self.diameter = 2.5
        self.label_size = 8
        self.white_margin = 4
        self.width = width - 0.5
        self.height = height - 0.5

        # Render variables
        self.last_x = -100

    def wrap(self, *args):
        """ Make internal sizes available to build engine. """
        return self.width, self.height

    def draw(self):
        """ Construct block. """

        # References
        c = self.canv
        # w = self.width
        r = self.range
        h = self.height

        # Prepare canvas
        c.setFont(s.Fonts.light, self.label_size)
        c.scale(1, 1)

        # Draw trend area
        if r.use_trend:
            c.setFillColor(s.Colors.trend)
            x1 = self.x_pos(r.trend_start, use_margin=False)
            x2 = self.x_pos(r.end, use_margin=False)
            p = c.beginPath()
            p.moveTo(x1, 0)
            p.lineTo(x1, h)
            p.lineTo(x2, h)
            p.lineTo(x2, 0)
            p.close()
            c.drawPath(p, stroke=0, fill=1)

        # Draw tick lines
        # These must be drawn rather than use table lines to force them in the background
        tx = self.range.tick_times
        tx_label = self.range.tick_labels
        bottom = 0 if self.left == 0 else -5
        c.setLineWidth(0.25)
        for idx, tick in enumerate(tx):

            # Labeled tick
            x_pos = self.x_pos(tick, use_margin=False)
            if tx_label[idx] is not None:
                if not r.use_trend or tick < r.trend_start:
                    color = s.Colors.med_light_gray if idx == 0 else s.Colors.light_gray
                else:
                    color = s.Colors.med_light_light_gray
                c.setStrokeColor(color)

            # Sub-tick
            else:
                if not r.use_trend or tick < r.trend_start:
                    color = s.Colors.med_light_gray if idx == 0 else s.Colors.x_light_gray
                else:
                    color = s.Colors.light_gray
                c.setStrokeColor(color)

            # Draw tick
            p = c.beginPath()
            p.moveTo(x_pos, bottom)
            p.lineTo(x_pos, h + 0.5)
            p.close()
            c.drawPath(p)

        # No data
        if not self.setting:
            return

        # Filter history to only show changes
        c.setLineWidth(0.5)
        setting = self.setting
        if type(setting) is Setting:
            changes = []
            last_val = None
            last_state = None
            last_applicable = None
            for item in setting.history:
                if (item.value != last_val or item.enabled != last_state or item.enabled != last_state or
                    item.applicable != last_applicable) and not \
                        (last_applicable is False and item.applicable is False) and not \
                        (last_val == "Off" and not item.enabled) and not \
                        (last_state is False and item.value == "Off"):
                    last_val = item.value
                    last_state = item.enabled
                    last_applicable = item.applicable
                    changes.append(item)
        else:
            changes = setting["preset_history"]

        # No marks if no data available
        if len(DATA.events_all) == 0:
            return

        # Populate setting marks
        dots = []
        col_split = col_end = None
        changes.sort(key=lambda a: a.time)
        override_disabled = True if type(setting) is not Setting else setting.display_type != "OnOffSetting"
        if r.use_trend:
            col_split = self.x_pos(r.trend_start, use_margin=False) - 0.125
            col_end = self.x_pos(r.end, use_margin=False) + 0.125
        for x, change in enumerate(changes):
            next_change = changes[x+1] if x+1 < len(changes) else None
            if change.value is None:
                e = Exception("Generated invalid event detail")
                self.em.log_error(ve.Programs.REPORTING, ve.ErrorCat.MID_ERROR, ve.ErrorSubCat.INTERNAL_ERROR,
                                  "Could not show a settings change.", e)
                continue
            dots.append([change, next_change])
            width = self.label(change, next_change, size_only=True, disable_override=override_disabled)
            if width:
                self.margin(change, width, col_split, col_end)
            self.label(change, next_change, disable_override=override_disabled)
        for x, changes in enumerate(dots):
            # At one point Reportlab multiBuild engine dropped the 1st circle per canvas.
            # It may have been fixed by a reboot, but this is here just in case. to draw twice.
            # if x == 0:
            #     self.dot(change, first)
            self.dot(changes[0], changes[1])

    def dot(self, change: SettingsChange, next_change: SettingsChange):
        """ Draw a notification dot on a problematic record. """
        c = self.canv
        diameter = self.diameter
        y = self.height * 0.5
        x = self.x_pos(change.time)
        if next_change:
            next_x = self.x_pos(next_change.time)
            if next_x - x < 0.25:
                self.last_x = x
                return
        self.last_x = x
        if change.applicable:
            c.setFillColor(self.color)
            c.circle(x, y, diameter, stroke=0, fill=1)
        else:
            c.setFillColor(s.Colors.white)
            c.setStrokeColor(s.Colors.med_gray)
            c.circle(x, y, diameter, stroke=1, fill=1)

    def margin(self, change: SettingsChange, width: int = None, split: int = None, end: int = None):
        """ Draw a notification dot on a problematic record. Split colors over trend area """
        c = self.canv
        dot_size = self.diameter
        h = 14
        m = self.white_margin
        y = (self.height - h) * 0.5
        x = self.x_pos(change.time) + dot_size + 0.3*m
        c.setFillColor(colors.white)
        full_w = width if width else 150
        full_w += 0.9*m
        right = x + full_w
        if end is None or x < end:
            if split is None or right < split:
                c.rect(x, y, full_w, h, stroke=0, fill=1)
            elif x < split:
                w = split - x
                c.rect(x, y, w, h, stroke=0, fill=1)
                x = split
                w = min(full_w - w, end - x)
                c.setFillColor(s.Colors.trend)
                c.rect(x, y, w, h, stroke=0, fill=1)
            else:
                w = min(full_w, end - x)
                c.setFillColor(s.Colors.trend)
                c.rect(x, y, w, h, stroke=0, fill=1)

    def label(self, change: SettingsChange, next_change: SettingsChange = None, size_only: bool = False,
              disable_override: bool = False):
        """ Draw a setting label on the canvas. """

        # Dimensions
        c = self.canv
        h = self.label_size
        m = self.white_margin
        dot_size = self.diameter
        y = self.height * 0.5 - h * 0.5 + 1.5
        x = self.x_pos(change.time) + dot_size * 0.5 + m
        limit = self.width + 0.25*inch

        # Prepare label value
        if not change.applicable:
            label = "n/a"
        else:
            label = getattr(change, self.key)
            if type(label) in [int, float]:
                precision = self.precision
                if self.precision is None or self.precision == "":
                    precision = 0
                label = "{0:.{1}f}".format(label, precision)
            if disable_override and hasattr(change, "enabled") and not change.enabled:
                label = "Off"
            if type(change.value) is bool:
                label = str(change.value) if change.value is not None else None

        # Determine available space and constrain label
        next_x = (self.x_pos(next_change.time) - dot_size - 2) if next_change else limit
        space = min(next_x - x, limit - x)
        while c.stringWidth(label) > space and len(label) > 0:
            label = label[0:-1]
            if len(label) > 0:
                label = label[0:-1] + "…"
            else:
                label = ""

        # Width measurement only
        if size_only:
            return c.stringWidth(label) if label else 0

        # Draw label
        if label != "":
            if change.applicable:
                c.setFillColor(colors.black)
            else:
                c.setFillColor(s.Colors.med_gray)
            c.drawString(x, y, label)

    def x_pos(self, time: datetime, use_margin: bool = True):
        """ Determine x-position from datetime. """
        rng = self.range
        time_width = rng.duration
        pos = self.width * ((time - rng.start) / time_width)
        if use_margin:
            pos = max(self.diameter + 2, pos)
        return pos


def settings_table(em: ErrorManager):
    """ Table/graph hybrid showing changes to settings/presets over time. """
    global REPORT, DATA, DIR

    # References
    presets = DATA.settings_presets

    # ----- Setup table data ----- #

    # Styles
    styles = [
        ('LINEABOVE', (0, 0), (-1, 0), 0.25, s.Colors.med_light_gray),
        ('LINEBELOW', (0, 0), (-1, -1), 0.25, s.Colors.med_light_gray),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (1, 0), (-1, -1), 0)
    ]

    # Sizes
    first_col = 1.5 * inch
    last_col = 0.25 * inch
    data_width = 7.5*inch - first_col - last_col
    widths = [first_col, data_width, last_col]
    row_height = 0.25 * inch
    heights = []

    # ----- Render table ----- #

    # Variables
    story = []
    row_idx = 0
    first_row = 0
    last_row = 0

    # Populate settings from preset group
    def add_group_settings(em: ErrorManager, idx_ref: list, name, color_dark: colors, preset_group=None, 
                           show_preset: bool = False, id_list: list = None):
        row_x, first_x, last = idx_ref
        if name:
            styles.append(('TEXTCOLOR', (0, row_x), (0, row_x), color_dark))
            styles.append(('FONT', (0, row_x), (0, row_x), s.Fonts.heavy))
            label_name = name
            if show_preset:
                label_name = name + " Settings"
            chart = SettingRow(em, [], data_width, row_height)
            data.append([label_name, chart, ""])
            heights.append(row_height)
            row_x += 1
            first_x = row_x
            if show_preset:
                group = presets[preset_group]
                t_name = "ventilator" if name == "Ventilation" else name.lower()
                shade = "_dark" if t_name == "oxygen" else ""
                color = getattr(s.Colors, t_name + shade)
                preset_attrs = ["value", "label"]
                line_labels = ["Preset", "Preset Label"]
                for i in range(0, 2):
                    setting = DummySetting(line_labels[i])
                    chart = SettingRow(em, group, data_width, row_height, color, key=preset_attrs[i])
                    label = LabelCell(setting, first_col, row_height, None)
                    data.append([label, chart, ""])
                    heights.append(row_height)
                    row_x += 1
        # items = preset
        if id_list:
            items = {}
            for item in id_list:
                items[item] = DATA.settings_all[item]
            for s_id, setting in items.items():
                # Settings only, not setting group values
                if type(setting) != Setting:
                    continue
                # Skip settings that don't apply for this model
                if not setting.model_applicability:
                    continue
                # Not preset labels
                if s_id in ["9100", "14502", "14503", "14504"]:
                    continue
                # Exclude start/stop values
                if setting.start_stop and s_id != "suction-pressure":
                    continue
                therapy = DATA.therapy_lookup(s_id).name.lower()
                shade = "_dark" if therapy == "oxygen" else ""
                color = getattr(s.Colors, therapy + shade)
                label = LabelCell(setting, first_col, row_height, None)
                this_row = label.height + 0.5
                heights.append(this_row)
                chart = SettingRow(em, setting, data_width, this_row, color)
                data.append([label, chart, ""])
                last = row_x
                row_x += 1
        return [row_x, first_x, last]

    # Add settings for each preset group
    data = []
    min_group = 2
    lists = REPORT.settings["display"]["settings_chart"]["settings_groups"]
    x_ref = [row_idx, first_row, last_row]

    # Ventilation
    x_ref = add_group_settings(em, x_ref, "Ventilation", s.Colors.ventilator, ve.PresetMIDs.VENTILATOR.value[0],
                               show_preset=True)
    x_ref = add_group_settings(em, x_ref, None, s.Colors.ventilator, id_list=lists["ventilation"])
    styles.append(("NOSPLIT", (0, x_ref[1]-1), (-1, min(x_ref[0]-1, x_ref[1] + min_group))))
    styles.append(("BACKGROUND", (0, x_ref[1]-1), (0, x_ref[2]), s.Colors.ventilator_xx_light))

    # Oxygen
    if DATA.model_id not in [ve.Models.VC]:
        first = x_ref[0]
        x_ref = add_group_settings(em, x_ref, "Oxygen", s.Colors.oxygen_dark, ve.PresetMIDs.OXYGEN.value[0],
                                   show_preset=True)
        x_ref = add_group_settings(em, x_ref, None, s.Colors.oxygen_dark, id_list=lists["oxygen"])
        styles.append(("NOSPLIT", (0, x_ref[1]-1), (-1, min(x_ref[0]-1, first + min_group))))
        styles.append(("BACKGROUND", (0, x_ref[1]-1), (0, x_ref[2]), s.Colors.oxygen_xx_light))

    # Cough
    if DATA.model_id not in [ve.Models.V_PRO]:
        first = x_ref[0]
        x_ref = add_group_settings(em, x_ref, "Cough", s.Colors.cough, ve.PresetMIDs.COUGH.value[0], show_preset=True)
        x_ref = add_group_settings(em, x_ref, None, s.Colors.cough, id_list=lists["cough"])
        styles.append(("NOSPLIT", (0, x_ref[1]-1), (-1, min(x_ref[0]-1, first + min_group))))
        styles.append(("BACKGROUND", (0, x_ref[1] - 1), (0, x_ref[2]), s.Colors.cough_xx_light))

    # Suction
    if DATA.model_id in [ve.Models.VOCSN_PRO, ve.Models.VOCSN, ve.Models.VCSN_PRO]:
        first = x_ref[0]
        x_ref = add_group_settings(em, x_ref, "Suction Settings", s.Colors.suction, id_list=[])
        x_ref = add_group_settings(em, x_ref, None, s.Colors.suction_dark, id_list=["55"])
        styles.append(("NOSPLIT", (0, first), (-1, min(x_ref[0]-1, first + min_group))))
        styles.append(("BACKGROUND", (0, x_ref[1] - 1), (0, x_ref[2]), s.Colors.suction_xx_light))

    # Nebulizer
    if DATA.model_id in [ve.Models.VOCSN_PRO, ve.Models.VOCSN, ve.Models.VCSN_PRO]:
        first = x_ref[0]
        x_ref = add_group_settings(em, x_ref, "Nebulizer Settings", s.Colors.nebulizer, id_list=[])
        x_ref = add_group_settings(em, x_ref, None, s.Colors.nebulizer, id_list=lists["nebulizer"])
        styles.append(("NOSPLIT", (0, first), (-1, min(x_ref[0]-1, first + min_group))))
        styles.append(("BACKGROUND", (0, x_ref[1] - 1), (0, x_ref[2]), s.Colors.nebulizer_xx_light))

    # System
    first = x_ref[0] + 1
    x_ref = add_group_settings(em, x_ref, "Device Settings", s.Colors.system, id_list=[])
    x_ref = add_group_settings(em, x_ref, None, s.Colors.cough_dark, id_list=lists["system"])
    styles.append(("NOSPLIT", (0, first), (-1, min(x_ref[0]-1, first + min_group))))
    styles.append(("BACKGROUND", (0, x_ref[1] - 1), (0, x_ref[2]), s.Colors.xx_light_gray))

    # ----- Assemble table ----- #

    # Add elements
    story.insert(0, Spacer(1, -0.5 * inch))
    # story.insert(1, title)
    story.append(Table(data=data, colWidths=widths, rowHeights=heights, style=styles, spaceBefore=0.5*inch,
                       repeatRows=0))
    return story


def settings_summary_section(em: ErrorManager, w_dir: str, doc: BaseDocTemplate, report: r.Report, data: vd.VOCSNData,
                             story: list):
    """
    Create settings summary report section.
    :param em: Error manager.
    :param w_dir: Working directory.
    :param doc: Reference to main report document.
    :param report: Report definitions.
    :param data: VOCSN data container.
    :param story: List of flowable elements.
    :return: PageTemplate class to be integrated into main DocTemplate.
    """

    # Set global variables
    global REPORT, DATA, DIR
    REPORT = report
    DATA = data
    DIR = w_dir

    # Assemble page template
    link_name_arrive = "section_settings_summary"
    bottom_link_away = "section_configuration_log" if report.sections.config_log else None
    first_template = general_template(SECTION_NAME, doc, bottom_link=bottom_link_away)
    later_template = alarm_template(SECTION_NAME, doc, bottom_link=bottom_link_away)
    doc.addPageTemplates(first_template)
    doc.addPageTemplates(later_template)

    # Add flowable elements
    story.append(NextPageTemplate(first_template.id))
    story.append(PageBreak())
    story.append(NextPageTemplate(later_template.id))

    # Section title
    story.extend(s.section_title_flow("Therapy Use and Settings Overview"))

    # Add bookmark destination
    story.append(Bookmark(link_name_arrive))

    # Utilization/alarm graph
    height = 2 * inch
    story.append(Spacer(1, 0.5 * inch))
    story.append(UtilizationGraph(DIR, REPORT, DATA, height, 1.139 * inch, 6.021 * inch))
    story.extend(settings_table(em))
