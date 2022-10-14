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
