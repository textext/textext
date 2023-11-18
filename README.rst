|status-ci| |status-downloads|

TexText - A TeX extension for Inkscape
======================================

TexText is a Python plugin for the vector graphics editor
`Inkscape <http://www.inkscape.org/>`__ providing the possibility to add
and re-edit LaTeX and `typst <https://typst.app/>`__ generated SVG elements to your drawing.

.. figure:: docs/source/images/textext-with-inkscape.png
    :alt: TexText dialog with Inkscape

Key features
------------

-  Windows/ Linux/ MacOS support
-  LaTeX/ typst generated SVG elements can be re-edited later
-  Multi-line editor with syntax highlighting (`Read more... <usage-dialog-overview_>`_)
-  Compilation with **PdfLaTeX**, **XeLaTeX**, **LuaLaTex** or **typst** (`Read more... <usage-tex-compilers_>`_)
-  Interoperable scaling in TexText and Inkscape (`Read more...  <usage-scaling_>`_)
-  Font size match with Inkscape text (`Read more... <usage-font_>`_)
-  Customizable TeX preamble for e.g. additional packages, parskip, parindent, etc. (`Read more...  <usage-preamble-file_>`_)
-  Colorization via TeX/ typst commands/ Inkscape is kept after re-editing (`Read more... <usage-colorization_>`_)
-  Alignment anchor of the produced output (`Read more...  <usage-alignment_>`_)
-  Preview images  (`Read more... <usage-preview_>`_)
-  Compatibility with TexText down to version 0.4.x

Download
--------

Download of the most recent version (and older ones): https://github.com/textext/textext/releases

Compatibility chart:

   +---------------------+-------------------------------------------------------------------+
   | Inkscape            | TexText                                                           |
   +=====================+===================================================================+
   | 1.3.x               | `>=1.9.0 <https://github.com/textext/textext/releases>`_          |
   +---------------------+-------------------------------------------------------------------+
   | 1.2.x, 1.1.x, 1.0.x | `1.8.2 <https://github.com/textext/textext/releases/tag/1.8.2>`_  |
   +---------------------+-------------------------------------------------------------------+
   | 0.92.x              |  `0.11 <https://github.com/textext/textext/releases/tag/0.11.0>`_ |
   +---------------------+-------------------------------------------------------------------+

Documentation
-------------

Documentation hosted at https://textext.github.io/textext.
It contains `installation <installation-toc_>`_ and `usage <usage-toc_>`_ instructions.

History
-------

This repository continues the development of the plugin which took place
at https://bitbucket.org/pitgarbe/textext until January 2018.
Originally, TexText had been developed by `Pauli
Virtanen <http://www.iki.fi/pav/software/textext/>`__ based on the
plugin InkLaTeX written by Toru Araki.

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

.. |status-ci| image:: https://github.com/textext/textext/actions/workflows/ci.yaml/badge.svg?branch=master
    :target: https://github.com/textext/textext/actions/workflows/ci.yaml
    :alt: Status of continuous integration tests
.. |status-downloads| image:: https://img.shields.io/github/downloads/textext/textext/total   
    :alt: GitHub all releases    

