|Build Status|

TexText - A TeX extension for Inkscape
======================================

TexText is a Python plugin for the vector graphics editor
`Inkscape <http://www.inkscape.org/>`__ providing the possibility to add
and re-edit LaTeX generated SVG elements to your drawing.

.. figure:: docs/source/images/textext-with-inkscape.png
    :alt: TexText dialog with Inkscape

Key features
------------

-  Windows/ Linux/ MacOS support
-  LaTeX generated SVG elements can be re-edited later
-  Multi-line editor with syntax highlighting (see `§ <usage-dialog-overview_>`_)
-  Compilation with **PdfLaTeX**, **XeLaTeX** or **LuaLaTex** (see `§ <usage-tex-compilers_>`_)
-  Interoperable scaling in TexText and Inkscape (see `§ <usage-scaling_>`_)
-  Font size match with Inkscape text (see `§ <usage-font_>`_)
-  Customizable TeX preamble (additional packages, parskip, parindent, etc.) (see `§ <usage-preamble-file_>`_)
-  Colorization via TeX commands/Inkscape is kept after re-editing (see `§ <usage-colorization_>`_)
-  Alignment anchor of the produced output (see `§ <usage-alignment_>`_)
-  Preview images  (see `§ <usage-preview_>`_)
-  Compatibility with TexText down to version 0.4.x

Download
--------

Download of the most recent version (and older ones): https://github.com/textext/textext/releases


Documentation
-------------

Documentation hosted at https://textext.github.io/textext
It contains `installation <installation-toc_>`_ and `usage <usage-toc_>`_ instructions


History
-------

This repository continues the development of the plugin which took place
at https://bitbucket.org/pitgarbe/textext until January 2018.
Originally, TexText had been developed by `Pauli
Virtanen <http://www.iki.fi/pav/software/textext/>`__ based on the
plugin InkLaTeX written by Toru Araki.

.. |Build Status| image:: https://travis-ci.com/textext/textext.svg?branch=develop
   :target: https://travis-ci.com/textext/textext

.. _documentation:         https://textext.github.io/textext
.. _installation-toc:      https://textext.github.io/textext#installation-toc
.. _usage-toc:             https://textext.github.io/textext#usage-toc
.. _usage-dialog-overview: https://textext.github.io/textext/usage/gui.html#usage-dialog-overview
.. _usage-tex-compilers:   https://textext.github.io/textext/usage/gui.html#usage-tex-compilers
.. _usage-scaling:         https://textext.github.io/textext/usage/gui.html#scaling-of-the-output
.. _usage-font:            https://textext.github.io/textext/usage/faq.html#explicit-setting-of-font-size
.. _usage-preamble-file:   https://textext.github.io/textext/usage/gui.html#usage-preamble-file
.. _usage-colorization:    https://textext.github.io/textext/usage/gui.html#usage-colorization
.. _usage-alignment:       https://textext.github.io/textext/usage/gui.html#usage-alignment
.. _usage-preview:         https://textext.github.io/textext/usage/gui.html#preview-button