#!/usr/bin/env python
"""
This module contains functions to load common resources.

    Version Notes:
        1.0.0.0 - 07/28/2019 - Created file with load_font function.

"""

__author__ = "John Dorian for Sai Systems Technologies"
__copyright__ = "Copyright 2019"
__version__ = "1.0.0.0"


# Built-in libraries
import os

# ReportLab libraries
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def load_fonts(directory: str):
    """
    Load common fonts.
    :param directory: Environment directory.
    """

    # Avenir family
    avenir_path = os.path.join(directory, "resources", "fonts", "Avenir.ttc")
    pdfmetrics.registerFont(TTFont("Avenir-Light", avenir_path, subfontIndex=6))
    pdfmetrics.registerFont(TTFont("Avenir-RegLight", avenir_path, subfontIndex=0))
    pdfmetrics.registerFont(TTFont("Avenir-Regular", avenir_path, subfontIndex=11))
    pdfmetrics.registerFont(TTFont("Avenir-Medium", avenir_path, subfontIndex=8))
    pdfmetrics.registerFont(TTFont("Avenir-Heavy", avenir_path, subfontIndex=4))
    pdfmetrics.registerFont(TTFont("Avenir-ExtraHeavy", avenir_path, subfontIndex=2))
    pdfmetrics.registerFont(TTFont("Avenir-Light-I", avenir_path, subfontIndex=7))
    pdfmetrics.registerFont(TTFont("Avenir-RegLight-I", avenir_path, subfontIndex=1))
    pdfmetrics.registerFont(TTFont("Avenir-Regular-I", avenir_path, subfontIndex=10))
    pdfmetrics.registerFont(TTFont("Avenir-Medium-I", avenir_path, subfontIndex=9))
    pdfmetrics.registerFont(TTFont("Avenir-Heavy-I", avenir_path, subfontIndex=5))
    pdfmetrics.registerFont(TTFont("Avenir-ExtraHeavy-I", avenir_path, subfontIndex=3))
