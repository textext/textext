"""
This file is part of TexText, an extension for the vector
illustration program Inkscape.

Copyright (c) 2006-2024 TexText developers.

TexText is released under the 3-Clause BSD license. See
file LICENSE.txt or go to https://github.com/textext/textext
for full license details.
"""
"""
This file defines some constants used in several components of TexText.

This is the only place where we define these strings!
"""

CMD_PDFLATEX = "pdflatex"
CMD_XELATEX = "xelatex"
CMD_LUALATEX = "lualatex"
CMD_TYPST = "typst"
CMD_INKSCAPE = "inkscape"
TEX_COMMANDS = [CMD_PDFLATEX, CMD_XELATEX, CMD_LUALATEX, CMD_TYPST]

HAL_LEFT = "left"
HAL_CENTER = "center"
HAL_RIGHT = "right"
VAL_TOP = "top"
VAL_MIDDLE = "middle"
VAL_BOTTOM = "bottom"
