TexText - A Tex extension for Inkscape
======================================

TexText is a Python plugin for the vector graphics editor
`Inkscape <http://www.inkscape.org/>`__ providing the possibility to add
LaTeX generated SVG elements to your drawing.

.. figure:: images/textext-with-inkscape.png
   :alt: TexText dialog with Inkscape


Key features
------------

-  Multi-line editor with syntax highlighting (see :ref:`§ <usage-dialog-overview>`)
-  Compilation with **PdfLaTeX**, **XeLaTeX** or **LuaLaTex** (see :ref:`§ <usage-tex-compilers>`)
-  Interoperable scaling in TexText and Inkscape (see :ref:`§ <usage-scaling>`)
-  Font size match with Inkscape text (see :ref:`§ <usage-font>`)
-  Customizable TeX preamble (additional packages, parskip, parindent, etc.) (see :ref:`§ <usage-preamble-file>`)
-  Colorization via TeX commands/Inkscape is kept after re-editing (see :ref:`§ <usage-colorization>`)
-  Alignment anchor of the produced output (see :ref:`§ <usage-alignment>`)
-  Compatibility with TexText down to version 0.4.x

.. toctree::
    :caption: Installation
    :maxdepth: 2
    :glob:

    install/*

.. toctree::
    :caption: Usage
    :maxdepth: 3
    :glob:

    usage.rst

History
-------

This repository continues the development of the plugin which took place
at https://bitbucket.org/pitgarbe/textext until January 2018.
Originally, TexText had been developed by `Pauli
Virtanen <http://www.iki.fi/pav/software/textext/>`__ based on the
plugin InkLaTeX written by Toru Araki.



.. include:: changelog.rst

