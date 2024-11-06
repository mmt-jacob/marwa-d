#!/usr/bin/env python
"""
Load string definitions from file.

    Version Notes:
        1.0.0.0 - 12/15/2019 - Created with label loader.
        1.0.0.1 - 12/21/2019 - Integrated error management.
        1.0.0.2 - 01/24/2020 - Changed to generalized form of version.
        1.0.0.3 - 02/01/2020 - Updated to new log format.

"""

__author__ = "John Dorian for Sai Systems Technologies"
__copyright__ = "Copyright 2019"
__version__ = "1.0.0.3"

# Built-in modules
import os
import json

# VOCSN modules
from modules.models import vocsn_enum as ve
from modules.models.errors import ErrorManager


def load_labels(em: ErrorManager, data, new_ver: str = None):
    """
    Load label strings from definition file.
    :param em: Error manager.
    :param data: VOCSN data container.
    :param new_ver: Optionally specify a version.
    """

    # Catch errors
    val = None
    try:

        # Lookup version
        ver = new_ver if new_ver else data.gen_version

        # Construct expected file name
        fn = os.path.join("definitions", "strings", "labels_{}.json".format(str(ver)))

        # Contextualize
        if not os.path.exists(fn):
            fn = os.path.join("..", fn)

        # File missing
        if not os.path.exists(fn):
            val = data.version
            raise Exception("No string definition file for version")

        # Access file
        with open(fn, 'r') as file:
            strings = json.load(file)

        # Reference JSON definition
        data.label_strings = strings["ParameterLabel"]

    # Handle exceptions
    except Exception as e:
        message = "Unable to load report string definitions"
        em.log_error(ve.Programs.REPORTING, ve.ErrorCat.PROCESS_ERROR, ve.ErrorSubCat.METADATA_ERROR, message, e,
                     val=val)
