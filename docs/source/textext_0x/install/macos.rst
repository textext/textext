.. |TexText| replace:: **TexText 0.11 for Inkscape 0.92**

.. role:: bash(code)
   :language: bash
   :class: highlight

.. role:: latex(code)
   :language: latex
   :class: highlight

.. _tt0x-macos-install:

==================
|TexText| on MacOS
==================

.. note::

    These instrcuctions refer to an installation of Inkscape via Homebrew. Please report any
    issues, comments or hints to https://github.com/textext/textext/issues/new

To install |TexText| on MacOS do the following steps:

#. `Install dependencies <tt0x-macos-install-dependencies_>`_ of |TexText|

    - `Install inkscape <tt0x-macos-install-inkscape_>`_
    - `Install pdflatex/lualatex/xelatex <tt0x-macos-install-latex_>`_
    - `Install pdf->svg converter (pdf2svg or pstoedit) <tt0x-macos-install-pdf-to-svg-converter_>`_

#. `Install TexText <tt0x-macos-install-textext_>`_

.. _tt0x-macos-install-dependencies:

Install dependencies
====================

.. _tt0x-macos-install-inkscape:

Install inkscape
~~~~~~~~~~~~~~~~

To install using homebrew:

.. code-block:: bash

    brew cask install inkscape

The Python modules required for the TexText GUI are already included in this
Inkscape installation, see :ref:`tt0x-macos-install-python27`.

.. _tt0x-macos-install-pdf-to-svg-converter:

Install a pdf->svg converter
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You have two options: ``pdf2svg`` (recommended) or ``pstoedit + ghostscript``:

.. _tt0x-macos-install-pdf2svg:

Install pdf2svg (recommended)
----------------------------------
Install the ``pdf2svg`` package

To install using homebrew:

.. code-block:: bash

    brew install pdf2svg

.. _tt0x-macos-install-pstoedit:

Install pstoedit (not recommended)
----------------------------------

Some versions ``pstoedit`` fails to produce `svg` so it's preferable to use ``pdf2svg``.

To use ``pstoedit`` converter install the ``pstoedit`` package and check versions of
installed versions of ``pstoedit`` and ``ghostscript``

To install using homebrew:

.. code-block:: bash

    brew install ghostscript
    brew install pstoedit

To check versions run:

.. code-block:: bash

    pstoedit --version
    gs --version

.. warning::
    Those combinations of ``pstoedit`` and ``ghostscript`` versions fails to produce `svg` on
    most distributions (see  `bb issue 48 <https://bitbucket.org/pitgarbe/textext/issues/48/ghostscript-still-bug-under-linux>`_):

    +--------------+-----------------+
    | ``pstoedit`` | ``ghostscript`` |
    +--------------+-----------------+
    |     3.70     |      9.22       |
    +--------------+-----------------+

    Please report any observations or problems in :issue:`30`.

.. _tt0x-macos-install-latex:

Install pdflatex/lualatex/xelatex
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``pdflatex``, ``lualatex`` and ``xelatex`` are part of ``mactex`` package.

To install using homebrew:

.. code-block:: bash

    brew cask install mactex


.. _tt0x-macos-install-textext:

Install TexText
===============

1.  Download the most recent package from :textext_current_release_page:`GitHub release page <release>` (direct links: :textext_download_zip:`.zip <MacOS>`)
2.  Extract the package and change to created directory.
3.  Run :bash:`setup.py` from your terminal:

    .. code-block:: bash

        python setup.py

    The script will check if all requirements described in :ref:`tt0x-macos-install-dependencies`
    are met. If so, it will install the extension files into the user's Inkscape configuration
    directory (usually this is ``~/.config/inkscape/extensions``). If not, instructions are given
    helping to fix the problem.

    .. important::

        Ignore any messages about missing PyGTK packages! (Issue :issue_num:`31`)

    .. note::

        If you would like to skip the requirement checks during installation call the script
        from the command line as follows:

        .. code-block:: bash

            python setup.py --skip-requirements-check


.. (Multiple labels to catch links from failed requirement check!)
.. _tt0x-macos-install-python27:
.. _tt0x-macos-install-tkinter:
.. _tt0x-macos-install-gui-library:
.. _tt0x-macos-install-pygtk2:


Information with respect to Python installation
===============================================

.. note::

    Homebrew's Inkscape uses MacOS's system Python interpreter in ``/usr/bin`` independently of any other installed
    Python interpreter (e.g. from Homebrew). The packages required for the GUI of TexText are already included in
    the Homebrew installation of Inkscape.

    If the extension does not work despite this fact or installation fails please report this
    to https://github.com/textext/textext/issues/new

    Thank you!