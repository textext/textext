.. |TexText| replace:: **TexText 0.11 for Inkscape 0.92**

.. role:: bash(code)
   :language: bash
   :class: highlight

.. role:: latex(code)
   :language: latex
   :class: highlight

.. _tt0x-linux-install:

==================
|TexText| on Linux
==================

To install |TexText| on Linux do the following steps:

#. `Install dependencies <tt0x-linux-install-dependencies_>`_ of |TexText|

    - `Install inkscape <tt0x-linux-install-inkscape_>`_
    - `Install python2.7 <tt0x-linux-install-python27_>`_
    - `Install GUI library (PyGTK2 or TkInter) <tt0x-linux-install-gui-library_>`_
    - `Install pdflatex/lualatex/xelatex <tt0x-linux-install-latex_>`_
    - `Install pdf->svg converter (pdf2svg or pstoedit) <tt0x-linux-install-pdf-to-svg-converter_>`_

#. `Install TexText <tt0x-linux-install-textext_>`_

.. _tt0x-linux-install-dependencies:

Install dependencies
====================

.. _tt0x-linux-install-inkscape:

Install inkscape
~~~~~~~~~~~~~~~~

.. important::

    Do not use Inkscape from Canonical's :bash:`snap` package management! If you
    have it installed via :bash:`snap` uninstall it via :bash:`snap remove inkscape`
    and install it via the classic way: :bash:`sudo apt-get install inkscape`.
    This problem affects ALL Inkscape extensions!

To install on Ubuntu/Debian:

.. code-block:: bash

    sudo apt-get install inkscape

.. _tt0x-linux-install-python27:

Install python2.7
~~~~~~~~~~~~~~~~~

Make sure that a Python 2.7 distribution is installed and found by
your system (usually installed by the package ``python2.7``).

To install on Ubuntu/Debian:

.. code-block:: bash

    sudo apt-get install python2.7


.. warning::

    On recent systems default Python interpreter is ``python3`` which is incompatible with current version of |TexText|
    (and other Inkscape extensions). You need to configure Inkscape such that it still uses python2. To check which is
    your default Python interpreter run ``python --version`` in a terminal. If this command does not return Python
    version 2.7.x consult instructions to configure Inkscape properly:
    :ref:`tt0x-faq-set-inskscape-python-interpreter-to-python2`.



.. _tt0x-linux-install-gui-library:

Install GUI library
~~~~~~~~~~~~~~~~~~~

Install the Python bindings for the graphical user interface of
|TexText|. You have two options: ``PyGTK2`` (recommended) or ``Tkinter``:

.. _tt0x-linux-install-pygtk2:

Install PyGTK2 (recommended)
----------------------------
Install the following packages using your favorite package manager:

-  ``python-gtk2``
-  ``python-gtksourceview2`` (enables syntax highlighting)


To install on Ubuntu/Debian:

.. code-block:: bash

    sudo apt-get install python-gtk2 python-gtksourceview2

.. _tt0x-linux-install-tkinter:

Install Tkinter (not recommended)
---------------------------------

Tkinter is functioning but has a limited interface compared to PyGTK2 version, so it's not recommended.
To use ``Tkinter`` install the  ``python-tk`` pacage using your favorite package manager.

To install on Ubuntu/Debian:

.. code-block:: bash

    sudo apt-get install python-tk

.. _tt0x-linux-install-pdf-to-svg-converter:

Install a pdf->svg converter
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Again you have two options: ``pdf2svg`` (recommended) or ``pstoedit + ghostscript``:

.. _tt0x-linux-install-pdf2svg:

Install pdf2svg (recommended)
----------------------------------
Install the ``pdf2svg`` package

To install on Ubuntu/Debian:

.. code-block:: bash

    sudo apt-get install pdf2svg

.. _tt0x-linux-install-pstoedit:

Install pstoedit (not recommended)
----------------------------------

``pstoedit`` fails to produce `svg` with some versions of ``ghostscript`` so it's
preferable to use ``pdf2svg``.

To use ``pstoedit`` converter install the ``pstoedit`` package and check versions of
installed versions of ``pstoedit`` and ``ghostscript``

To install on Ubuntu/Debian:

.. code-block:: bash

    sudo apt-get install pstoedit

To check versions run:

.. code-block:: bash

    pstoedit --version
    ghostscript --version

.. warning::
    Those combinations of ``pstoedit`` and ``ghostscript`` versions fails to produce `svg` on
    most distributions (see  `bb issue 48 <https://bitbucket.org/pitgarbe/textext/issues/48/ghostscript-still-bug-under-linux>`_):

    +--------------+-----------------+
    | ``pstoedit`` | ``ghostscript`` |
    +--------------+-----------------+
    |     3.70     |      9.22       |
    +--------------+-----------------+
    |   <= 3.74    |      9.27       |
    +--------------+-----------------+

    Please report any observations or problems in :issue:`126`.

.. _tt0x-linux-install-latex:

Install pdflatex/lualatex/xelatex
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``pdflatex`` and ``lualatex`` are part of ``texlive-base`` package. The
``xelatex`` resides in ``texlive-xetex`` package

To install ``pdflatex`` and ``lualatex`` on Ubuntu/Debian:

.. code-block:: bash

    sudo apt-get install texlive-base

To install ``xelatex`` on Ubuntu/Debian:

.. code-block:: bash

    sudo apt-get install texlive-xetex

.. warning::

    If you have for some reason the Linux MiKTeX distribution installed make sure
    that automatic package installation is either set to
    ``Never install missing packages on-the-fly`` or set to
    ``Always install missing packages on-the-fly``, see
    `Manage your TeX installation with MiKTeX Console <https://miktex.org/howto/miktex-console>`_.


.. _tt0x-linux-install-textext:

Install TexText
===============

1.  Download the most recent package from :textext_0x_current_release_page:`GitHub release page <release>` (direct links: :textext_0x_download_zip:`.zip <Linux>`, :textext_0x_download_tgz:`.tar.gz <Linux>`)
2.  Extract the package and change to created directory.
3.  Run :bash:`setup.py` from your terminal:

    .. code-block:: bash

        python2 setup.py

    The script will check if all requirements described in :ref:`tt0x-linux-install-dependencies`
    are met. If so, it will install the extension files into the user's Inkscape configuration
    directory (usually this is ``~/.config/inkscape/extensions``). If not, instructions are given
    helping to fix the problem.

    .. note::

        If you would like to skip the requirement checks during installation call the script
        from the command line as follows:

        .. code-block:: bash

            python2 setup.py --skip-requirements-check