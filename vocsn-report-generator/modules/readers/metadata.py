#!/usr/bin/env python
"""
Process and organize contents of VOCSN metadata file.

    Version Notes:
        1.0.0.0 - 10/05/2019 - Created file with read_metadata.
        1.0.0.1 - 10/17/2019 - Added parameter reference.
        1.0.0.2 - 10/23/2019 - Read software version from metadata.
        1.0.0.3 - 10/29/2019 - Added event synonyms.
        1.0.0.4 - 11/01/2019 - Moved creation of monitor trackers to data initialization area
        1.0.0.5 - 11/07/2019 - Added custom metadata to handle therapy start/stop values.
        1.0.0.6 - 11/19/2019 - Added a temporary unit format converter.
        1.0.1.0 - 12/10/2019 - Added metadata lookup for therapy start/stop and control change type definitions.
        1.0.1.1 - 12/20/2019 - Changed to reading metadata from local copy, imported here. Changed "C" source to last.
        1.0.1.2 - 12/26/2019 - Added unknown record type warning.
        1.0.1.3 - 01/05/2020 - Changed terminal output.
        1.0.1.4 - 01/24/2020 - Moved to generalized version number
        1.0.1.5 - 02/01/2020 - Updated to new log format.
        1.0.1.6 - 02/18/2020 - Updated with faster monitor indexing.
        1.0.2.0 - 03/03/2020 - Adapted to use backward-looking metadata files.

"""

__author__ = "John Dorian for Sai Systems Technologies"
__copyright__ = "Copyright 2019"
__version__ = "1.0.2.0"

# Built-in modules
import os
import json

# VOCSN modules
from modules.models import vocsn_enum as ve
from modules.models.errors import ErrorManager
from modules.models.vocsn_data import VOCSNData


def read_metadata(em: ErrorManager, data: VOCSNData, use_int_md: bool):
    """
    Parse metadata and organize for efficient retrieval.
    :param em: Error manager.
    :param data: VOCSN data container.
    :param use_int_md: If true, use internal copy of metadata, otherwise use metadata from file, stored in TarManager.
    """

    # Catch errors
    val = None
    try:

        # Check that metadata file exists for version
        if not data.gen_version:
            raise Exception("No valid VOCSN version found")

        # Import metadata JSON
        if use_int_md:
            ver = data.gen_version
            fn = os.path.join("definitions", "metadata", "TrendMetaData_{}.json".format(ver))
            if not os.path.exists(fn):
                fn = os.path.join("..", fn)
            if not os.path.exists(fn):
                raise Exception("No metadata file for version")
            with open(fn, 'r') as file:
                md = json.load(file)
        else:
            raw_md = data.tar_manager.metadata
            md = json.loads(raw_md)

        # Validate required sections
        for section in ["Groupings", "METADATA_VERSION", "Messages", "Parameters"]:
            if section not in md:
                val = section
                raise Exception("Metadata is missing section")

        # Store pre-organized records
        data.metadata_raw = md
        data.metadata_grouping = md['Groupings']
        data.metadata_messages = md['Messages']
        data.metadata_parameters = md['Parameters']

        # Add custom definitions to parameter list
        for key, val in ve.custom_metadata_parameters.items():
            data.metadata_parameters[key] = val

        # Lookup therapy start definitions
        start_keys = data.metadata_messages[ve.EventIDs.THERAPY_START]["KeyID"]
        start_defs = None
        for x in range(0, len(start_keys)):
            if type(start_keys[x]) is dict:
                start_defs = start_keys[x]
        if not start_defs or "TherapyStartTypes" not in start_defs:
            raise Exception("Unable to locate therapy start definitions in metadata")
        data.metadata_t_start = start_defs["TherapyStartTypes"]

        # Lookup therapy stop definitions
        stop_keys = data.metadata_messages[ve.EventIDs.THERAPY_END]["KeyID"]
        stop_defs = None
        for x in range(0, len(stop_keys)):
            if type(stop_keys[x]) is dict:
                stop_defs = stop_keys[x]
        if not stop_defs or "TherapyStopTypes" not in stop_defs:
            raise Exception("Unable to locate therapy stop definitions in metadata")
        data.metadata_t_stop = stop_defs["TherapyStopTypes"]

        # Lookup control data types
        ctrl_def = data.metadata_messages[ve.EventIDs.SETTINGS_CHANGE]["KeyID"]
        ctrl_type_defs = None
        for x in range(0, len(ctrl_def)):
            if type(ctrl_def[x]) is dict:
                ctrl_type_defs = ctrl_def[x]
        if not ctrl_type_defs or "ControlChangeTypes" not in ctrl_type_defs:
            raise Exception("Unable to locate control data type definitions in metadata")
        data.metadata_ctrl_types = ctrl_type_defs["ControlChangeTypes"]

        # Organize data definitions
        for key, defs in md['Parameters'].items():
            data_class = defs['data_class']
            if data_class == "Monitor":
                data.metadata_monitors[key] = defs
            elif data_class in ["Setting", "Alarm"]:
                data.metadata_settings[key] = defs
            elif data_class == "Alarm":
                data.metadata_alarms[key] = defs
            elif data_class == "ParamSynonym":
                data.metadata_synonyms[key] = defs
            else:
                em.log_warning("Unexpected parameter class", val=data_class)

        # Populate 7201 parameter list index
        for key in data.metadata_messages["7201"]["KeyID"]:
            if "_" not in key or "_N" in key:
                key = key.split('_')[0]
                data.metadata_7201[key] = data.metadata_parameters[key]

    # Handle errors
    except Exception as e:
        message = "Error reading metadata"
        em.log_error(ve.Programs.REPORTING, ve.ErrorCat.PROCESS_ERROR, ve.ErrorSubCat.METADATA_ERROR, message, e,
                     val=val)
