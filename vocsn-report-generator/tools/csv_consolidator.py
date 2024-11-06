#!/usr/bin/env python
"""
A tool to append successive CSV files into a single file to aid with data verification and forensics.

    Version Notes:
        1.0.0.0 - 01/07/2020 - Created file.

"""

__author__ = "John Dorian for Sai Systems Technologies"
__copyright__ = "Copyright 2019"
__version__ = "1.0.0.0"

# Built-in modules
import os
import sys
import pathlib
import tarfile
import argparse


def process_tar(file: str):
    """
    Open a TAR file, enumerate constituent CSV files, and combine them into one CSV.
    :param file: TAR file path and name.
    """

    # Open file
    combined = b''
    file_path = pathlib.Path(file)
    path = file_path.parent
    stem = file_path.stem
    csv_files = []
    with tarfile.open(file_path) as tar:

        # Search for CSV files
        for member in tar.getmembers():

            # Check file type and keep CSV files
            name = member.name
            ext = member.name.split('.')[-1]
            if ext.lower() == "csv":
                csv_files.append(name)

        # Process CSV files
        for csv in csv_files:

            # Read file
            print("  Reading", csv)
            open_file = tar.extractfile(csv)
            csv_data = open_file.read()
            combined += csv_data

    # Create output file
    out_file = os.path.join(path, stem + ".csv")
    with open(out_file, "wb+") as file:
        file.write(combined)


if __name__ == "__main__":
    """
    Entry point from command line.

    Optional Parameters:
        file   (str): Path and filename for TAR file to read.
    """

    # Define arguments and options
    parser = argparse.ArgumentParser(prog="CSV Consolidator",
                                     description="Consolidate successive CSV files into a single file for analysis.")
    parser.add_argument('file', type=str, help="Path and name of TAR file containing CSV files.")

    # Process arguments and options
    a = parser.parse_args(sys.argv[1:])

    # Check input
    if not a.file:
        print("Please specify a tar file")

    # Validate file
    if ".tar" not in a.file.lower():
        print("Only TAR files are accepted.")

    # Check file exists
    if not os.path.exists(a.file):
        print("File not found")

    # Pass arguments
    process_tar(a.file)
