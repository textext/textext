# Tex Text - A LaTeX extension for Inkscape

## Prerequisites

- A LaTeX distribution (e.g. Texlive) has to be installed, especially `pdflatex` is needed
- You need Inkscape, of course


## Installation

### Tex Text Extension

To install *Tex Text*, simply run `python setup.py` in your terminal.
All it does, is copying the necessary files to your Inkscape extension directory. If you don't trust this script, you'll have to copy all the files within the `extensions` directory to `~/.config/inkscape/extensions/`.

### Additional required software

You'll need to install GtkSourceView (`python-gtksourceview2` on Ubuntu/Debian) to take advantage of all the GUI features of *Tex Text*.
This package should install `python-gtk2` as well, but if your distribution works differently, make sure you install the Python Gtk+ bindings.

Next, please install `pstoedit`.

Finally, to enable the preview feature of *Tex Text*, you need to install `ImageMagick`.

*(The extension also needs Ghostscript, but this should already be included with your LaTeX distribution.)*

### Congratulations, you're done!

## Usage

The extension menu in Inkscape will now contain a new entry named *Tex Text*.

When you select it, a dialog will appear that lets you enter any LaTeX code you want (presumably your formula). It will highlight the syntax with colors, show you line numbers and more. Above the text field you can choose a scale factor between 0.1 and 10 in increments of 0.1. You can also choose a preamble file from your disk which shall be used for rendering your LaTeX code.

Basically, your LaTeX code will be inserted into this environment:


This will be typeset and the result converted to SVG and inserted in your Inkscape document.

Your LaTeX code you and the accompanying settings (scale factor and optionally a preamble file) will be stored within the new SVG node in the document. This allows you to edit the LaTeX node later by selecting it and running the *Tex Text* extension (which will then show the dialog containing the saved values).

Any applied color or other styles will be kept when you update the LaTeX node using *Tex Text*.

There is a preview button as well, which shortens the feedback cycle from entry to result considerably, so use it! (It requires ImageMagick to be installed.)