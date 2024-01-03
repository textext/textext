"""
This file is part of TexText, an extension for the vector
illustration program Inkscape.

Copyright (c) 2006-2022 TexText developers.

TexText is released under the 3-Clause BSD license. See
file LICENSE.txt or go to https://github.com/textext/textext
for full license details.

Provides some utilities used in the extensions.
"""
import contextlib
import os
import tempfile
import re


@contextlib.contextmanager
def change_to_temp_dir():
    """
    Context manager creating a temporary directory and changes into it.

    Example:
        with change_to_temp_dir()
            do_something_in_temp_dir()
    """
    with tempfile.TemporaryDirectory(prefix="textext_") as temp_dir:
        orig_dir = os.path.abspath(os.path.curdir)
        try:
            os.chdir(temp_dir)
            yield
        finally:
            os.chdir(orig_dir)


def version_greater_or_equal_than(version_str, other_version_str):
    """ Checks if a version number is >= than another version number

    Version numbers are passed as strings and must be of type "N.M.Rarb" where N, M, R
    are non negative decimal numbers < 1000 and arb is an arbitrary string.
    For example, "1.2.3" or "1.2.3dev" or "1.2.3-dev" or "1.2.3 dev" are valid version strings.

    Returns:
        True if the version number is equal or greater then the other version number,
        otherwise false

    """

    def ver_str_to_float(ver_str):
        """ Parse version string and returns it as a floating point value

        Returns The version string as floating point number for easy comparison
        (minor version and release number padded with zeros). E.g. "1.23.4dev" -> 1.023004.
        If conversion fails returns NaN.

        """
        match = re.search(r"(\d+).(\d+).(\d+)[-\w]*", ver_str)
        if match is not None:
            ver_maj, ver_min, ver_rel = match.groups()
            return float(f"{ver_maj}.{ver_min:0>3}{ver_rel:0>3}")
        return float("nan")

    return ver_str_to_float(version_str) >= ver_str_to_float(other_version_str)
