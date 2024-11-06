#!/usr/bin/env python
"""
Generate a Usage report with manually created sample data. This replaces the normal workflow where data is automatically
populated from the web portal.

    Version Notes:
        1.0.0.0 - 07/22/2019 - Created file with sample data for Usage report.
        1.0.0.1 - 07/28/2019 - Added custom font and report section field.
        1.0.0.2 - 09/07/2019 - Added JSON settings file to provide report formatting parameters.
        1.0.2.0 - 01/05/2019 - Cleaned up for deployment validation.

"""

__author__ = "John Dorian for Sai Systems Technologies"
__copyright__ = "Copyright 2019"
__version__ = "1.0.2.0"

# Built-in modules
import os
import sys
from datetime import datetime, timedelta

# Contextualize
sys.path.append("..")

# VOCSN Modules
from reports import usage
from modules.models import report as r
from modules.models.errors import ErrorManager
from modules.models.vocsn_enum import ReportType


def demo_usage_report():
    """Create a demo usage report"""

    # Institution
    inst_name = "University Medical Center"
    inst = r.Institute(inst_name)

    # Physician
    phys_name_fst = "Julian"
    phys_name_mid = "S"
    phys_name_lst = "Bashir"
    phys_title = "Dr."
    phys_cred = "MD"
    phys = r.Physician(phys_name_fst, phys_name_mid, phys_name_lst, phys_title, phys_cred)

    # Patient
    pat_db_id = "987654"
    pat_dob = datetime(year=1961, month=6, day=21)
    pat_ref_num = "A45678"
    pat_name_fst = "Gillian"
    pat_name_mid = "M"
    pat_name_lst = "Taylor"
    patient = r.Patient(pat_db_id, pat_dob, pat_ref_num, pat_name_fst, pat_name_mid, pat_name_lst)

    # Report Range in hours
    # 1  Hour   = 1
    # 3  Hours  = 3
    # 6  Hours  = 6
    # 12 Hours  = 12
    # 1  Day    = 24
    # 3  Days   = 72
    # 7  Days   = 168
    # 30 Days   = 720
    # 60 Days   = 1440
    # 90 Days   = 2160
    # 180 Days  = 4320
    # duration = 72
    # start = datetime(year=2019, month=12, day=27, hour=18, minute=12)
    duration = 72
    start = datetime(year=2020, month=1, day=11, hour=12, minute=54)

    # Derived datetimes
    duration_td = timedelta(hours=duration)
    export = start + duration_td

    # Assemble report
    label = "Test"
    r_type = ReportType.USAGE
    notes = "Description of patient condition, notes, instructions, or equipment usage details." * 4
    report = r.Report("SAMPLE", r_type, start, duration, export, inst, phys, patient, notes, label=label)
    report.report_date = datetime.utcnow()

    # Report sections
    report.sections.cover = True
    report.sections.trend_summary = True
    report.sections.alarm_summary = True
    report.sections.settings_summary = True
    report.sections.monitor_details = True
    report.sections.therapy_log = True
    report.sections.alarm_log = True
    report.sections.config_log = True
    report.sections.event_log = True

    # Generate report
    # sample_tar = os.path.join("0001_SN113830_Date2019y12m31d_Time07h57m17s.tar")
    sample_tar = os.path.join("0004_SN112848_Date2020y01m14d_Time08h54m00s.tar")

    diag = False
    now = datetime.utcnow()
    log_name = "SAMPLE_{}-{:02}-{:02}_{:02}-{:02}-{:02}"\
        .format(now.year, now.month, now.day, now.hour, now.minute, now.second)
    em = ErrorManager("Sample Usage Report", log_name, diag)
    usage.usage_report(em, report, "output", sample_tar, diag=diag)
    em.write_log()


# Run demo report
demo_usage_report()
