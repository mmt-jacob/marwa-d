#!/usr/bin/env python
"""
Read json data data from VOCSN and load into working memory objects.

    Version Notes:
        1.0.0.0 - 07/29/2019 - Created file, adapted from experimental scripts.

"""

__author__ = "John Dorian for Sai Systems Technologies"
__copyright__ = "Copyright 2019"
__version__ = "1.0.0.0"

# Built-in modules
import sys
import json
import traceback


def read_json(in_file: str) -> list:
    """
    Read and parse contents of JSON file.
    :param in_file: Input file name.
    :return: List generated from JSON file.
    """

    # Vars
    data = None

    # Catch file read errors
    try:

        # Open file
        with open(in_file, 'r') as fd:
            data = fd.read()

    # Handle file read errors
    except Exception as e:
        sys.stderr.write("Unable to read file.\n")
        sys.stderr.write("{}".format(str(e)))
        sys.stderr.write("{}".format(traceback.format_exc()))
        exit(1)

    # Catch JSON parsing errors
    try:

        # Parse data
        return json.loads(data)

    # Handle errors
    except Exception as e:
        sys.stderr.write("Error in JSON data.\n")
        sys.stderr.write("{}".format(str(e)))
        sys.stderr.write("{}".format(traceback.format_exc()))
        exit(1)
