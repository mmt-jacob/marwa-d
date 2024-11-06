#!/usr/bin/env python
"""
Functions for looking up and selecting version specific definition files.

    Version Notes:
        1.0.0.0 - 10/05/2019 - Created file with read_metadata.
        1.0.0.1 - 04/07/2020 - Added working directory context.
        1.0.0.2 - 04/10/2020 - Override default version mapping for v4.08.XX until proper metadata is available.

"""

__author__ = "John Dorian for Sai Systems Technologies"
__copyright__ = "Copyright 2019"
__version__ = "1.0.0.2"

# Built-in modules
import os

# VOCSN modules
from modules.models.errors import ErrorManager


def check_ver(em: ErrorManager, ver: str, w_dir: str = ""):
    """
    Checks if version is valid, defined as:
      1) Definition is available
      2) Version is a recognizable number greater than last available 4.00.00 series definition file.
    Return both the closest available version name and a boolean indicating if local metadata can be used.
    :param em: Error manager.
    :param ver: Version name, and bool to allow use of local metadata.
    :param w_dir: Working directory
    :return: Available version name or None if invalid.
    """

    # Function to extract numeric form of version if applicable
    def get_ver_num(ver_str: str):
        try:
            if len(ver_str) >= 5:
                ver_str = int(ver_str)
                return ver_str if ver_str > 40000 else None
        except (TypeError, ValueError):
            return None

    # Variables
    use_ver = None
    latest_ver = 0
    use_int_md = False

    # Catch errors
    try:

        # Try converting name to number
        ver_num = get_ver_num(ver)

        # Check for specific version
        # Identify latest available version
        md_path = os.path.join(w_dir, "definitions", "metadata")
        for filename in os.listdir(md_path):
            filename = str(filename)
            if filename.endswith(".json") and "TrendMetaData" in filename:
                file_ver_name = filename.replace('TrendMetaData_', '').split('.')[0]
                if ver == file_ver_name:
                    use_int_md = True
                    use_ver = ver
                    break
                check = get_ver_num(file_ver_name)
                if check and check > latest_ver:
                    latest_ver = check

        # If a match wasn't found, use latest defined version
        if not use_ver and ver_num and latest_ver and ver_num >= latest_ver:
            em.log_warning("Using {} version definitions for {}".format(latest_ver, ver_num))
            use_ver = str(latest_ver)
        elif not use_ver:
            em.log_warning("Unknown version: {}".format(ver))

        # Temporarily override source for v4.09.XX software until final metadata is available for local storage.
        if 40900 <= ver_num < 41000:
            use_ver = 40900
            use_int_md = False

    # Unable to lookup valid version definitions
    except Exception as e:
        em.log_warning("Encountered invalid VOCSN version", val=type(e).__name__)

    # Return version and metadata source
    return use_ver, use_int_md
