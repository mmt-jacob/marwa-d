#!/usr/bin/env python
"""
A tool to duplicate a tar file, processing each CSV therein, overwriting sequence numbers to be consecutive, and
creating valid CRCs.

    Version Notes:
        1.0.0.0 - 02/29/2020 - Created file.
        1.0.0.1 - 03/24/2020 - Added extra comma filter.
        1.0.0.2 - 03/29/2020 - Corrected sequence count across files.

"""

__author__ = "John Dorian for Sai Systems Technologies"
__copyright__ = "Copyright 2019"
__version__ = "1.0.0.2"

# Built-in modules
import io
import os
import sys
import crc16
import pathlib
import tarfile
import argparse


def process_tar(file: str, strip: bool):
    """
    Open a TAR file, enumerate constituent CSV files, and doctor each with valid sequence and CRC numbers.
    :param file: TAR file path and name.
    :param strip: Strip non-tar files from output.
    """

    # Open file
    file_path = pathlib.Path(file)
    path = file_path.parent
    stem = file_path.stem
    name = file_path.name

    # Create output tar
    out_file = os.path.join(path, stem + "_doctored.tar")
    new_tar = tarfile.open(out_file, "w")

    # Read existing tar
    print("Opening", name)
    with tarfile.open(file_path) as tar:

        # Search for CSV files
        sequence = 0
        for member in tar.getmembers():

            # Check file type and keep CSV files
            name = member.name
            ext = member.name.split('.')[-1]

            # Process CSV files
            if ext.lower() == "csv":

                # Read file
                print("  Doctoring", name)
                open_file = tar.extractfile(name)
                csv_data = open_file.read()

                # Read each line
                new_data = b''
                for line in csv_data.split(b'\n'):

                    # Strip extra commas
                    line = line.replace(b'\r', b'')
                    line = line.replace(b', ', b',')
                    while len(line) > 0:
                        if line[-1] == 44:
                            line = line[:-1]
                        else:
                            break

                    # Process line parts
                    parts = line.split(b',')
                    sequence += 1
                    parts[0] = bytes(str(sequence), 'UTF8')
                    parts[-1] = b''
                    new_line = b','.join(parts)
                    crc_new = crc16.crc16xmodem(new_line, 0xffff)
                    new_line += bytes("{:05d}".format(crc_new), 'UTF8') + b'\n'
                    if len(new_line) > 20:
                        new_data += new_line
                    else:
                        sequence -= 1

                # Write file to new tar
                new_file = io.BytesIO(new_data)
                member.size = len(new_data)
                new_tar.addfile(member, new_file)

            # Preserve other files
            elif not strip:
                print("  Adding", name, member.size)
                new_tar.addfile(member, tar.extractfile(name))

    # Close new tar file
    print("Created", out_file)
    new_tar.close()


if __name__ == "__main__":
    """
    Entry point from command line.

    Optional Parameters:
        file   (str): Path and filename for TAR file to read.
    """

    # Define arguments and options
    parser = argparse.ArgumentParser(prog="csv_doctor.py",
                                     description="Duplicate TAR file with consecutive sequence numbers and valid CRCs.")
    parser.add_argument('file', type=str, help="Path and name of TAR file to doctor.")
    parser.add_argument('-s', '--strip', action='store_true', help="Strip non-tar files.")

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
    process_tar(a.file, a.strip)
