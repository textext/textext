TexText - A Tex extension for Inkscape
======================================

TexText is a Python plugin for the vector graphics editor
`Inkscape <http://www.inkscape.org/>`__ providing the possibility to add
and re-edit LaTeX generated SVG elements to your drawing.

.. figure:: images/textext-with-inkscape.png
   :alt: TexText dialog with Inkscape


Key features
------------

-  Windows/ Linux/ MacOS support
-  LaTeX generated SVG elements can be re-edited later
-  Multi-line editor with syntax highlighting (see :ref:`§ <usage-dialog-overview>`)
-  Compilation with **PdfLaTeX**, **XeLaTeX** or **LuaLaTex** (see :ref:`§ <usage-tex-compilers>`)
-  Interoperable scaling in TexText and Inkscape (see :ref:`§ <usage-scaling>`)
-  Customizable TeX preamble (additional packages, parskip, parindent, etc.) (see :ref:`§ <usage-preamble-file>`)
-  Colorization via TeX commands/ Inkscape is kept after re-editing (see :ref:`§ <usage-colorization>`)
-  Alignment anchor of the produced output (see :ref:`§ <usage-alignment>`)
-  Font size match with Inkscape text (see :ref:`§ <faq-font-size>`)
-  Preview images  (see :ref:`§ <usage-preview>`)
-  Compatibility with TexText down to version 0.4.x


.. _installation-toc:

.. toctree::
    :caption: Installation
    :maxdepth: 2
    :glob:

    install/*

.. _usage-toc:

.. toctree::
    :caption: Usage
    :maxdepth: 2
    :glob:

    usage/gui
    usage/faq
    usage/troubleshooting

.. toctree::
    :caption: Credits
    :maxdepth: 1

    history.rst
    authors.rst

.. toctree::
    :caption: Changelog
    :maxdepth: 2

    changelog.rst
