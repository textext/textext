.. |TexText| replace:: **TexText 0.11 for Inkscape 0.92**

.. role:: bash(code)
   :language: bash
   :class: highlight

.. role:: latex(code)
   :language: latex
   :class: highlight

.. _tt0x-windows-install:

====================
|TexText| on Windows
====================

To install |TexText| on Windows do the following steps:

#. `Install dependencies <tt0x-windows-install-dependencies_>`_ of |TexText|

    - `Install inkscape <tt0x-windows-install-inkscape_>`_
    - `Install GUI library (PyGTK2 or TkInter) <tt0x-windows-install-gui-library_>`_
    - `Install pdflatex/lualatex/xelatex <tt0x-windows-install-latex_>`_
    - `Install pdf->svg converter (pdf2svg or pstoedit) <tt0x-windows-install-pdf-to-svg-converter_>`_

#. `Install TexText <tt0x-windows-install-textext_>`_

.. _tt0x-windows-install-dependencies:

Install dependencies
====================

.. _tt0x-windows-install-inkscape:

Install inkscape
~~~~~~~~~~~~~~~~

Download and install Inkscape 0.92.x from https://inkscape.org/release/

.. warning::

    Please ensure that the Python 2.7 interpreter has been selected during the installation of Inkscape (by default this is the case).


.. _tt0x-windows-install-gui-library:

Install GUI library
~~~~~~~~~~~~~~~~~~~

Install the Python bindings for the graphical user interface of
|TexText|. You have two options: ``PyGTK2`` (recommended) or ``Tkinter``:

.. _tt0x-windows-install-pygtk2:

Install PyGTK2 (recommended)
----------------------------

.. _inkscape-0.92.4-64-bit: https://github.com/textext/pygtk-for-inkscape-windows/releases/download/0.92.4/Install-PyGTK-2.24-Inkscape-0.92.4-64bit.exe
.. _inkscape-0.92.4-32-bit: https://github.com/textext/pygtk-for-inkscape-windows/releases/download/0.92.4/Install-PyGTK-2.24-Inkscape-0.92.4-32bit.exe
.. _inkscape-0.92.3-64-bit: https://github.com/textext/pygtk-for-inkscape-windows/releases/download/0.92.3/Install-PyGTK-2.24-Inkscape-0.92.3-64bit.exe
.. _inkscape-0.92.3-32-bit: https://github.com/textext/pygtk-for-inkscape-windows/releases/download/0.92.3/Install-PyGTK-2.24-Inkscape-0.92.3-32bit.exe
.. _inkscape-0.92.2-64-bit: https://github.com/textext/pygtk-for-inkscape-windows/releases/download/0.92.2/Install-PyGTK-2.24-Inkscape-0.92.2-64bit.exe
.. _inkscape-0.92.2-32-bit: https://github.com/textext/pygtk-for-inkscape-windows/releases/download/0.92.2/Install-PyGTK-2.24-Inkscape-0.92.2-32bit.exe
.. _inkscape-0.92.0-0.92.1-multi: https://github.com/textext/pygtk-for-inkscape-windows/releases/download/0.92.0%2B0.92.1/Install-PyGTK-2.24-Inkscape-0.92.exe

Install the package that matches your Inkscape version:

 - Inkscape 0.92.4 **and** 0.92.5 (`32-bit <inkscape-0.92.4-32-bit_>`_ , `64-bit <inkscape-0.92.4-64-bit_>`_)
 - Inkscape 0.92.3 (`32-bit <inkscape-0.92.3-32-bit_>`_ , `64-bit <inkscape-0.92.3-64-bit_>`_)
 - Inkscape 0.92.2 (`32-bit <inkscape-0.92.2-32-bit_>`_ , `64-bit <inkscape-0.92.2-64-bit_>`_)
 - Inkscape 0.92.0 - 0.92.1 (`32-bit and 64-bit <inkscape-0.92.0-0.92.1-multi_>`_)

.. _tt0x-windows-install-tkinter:

Install Tkinter (not recommended)
---------------------------------

Tkinter is already included in the Python installation shipped with Inkscape.

.. warning::

    Tk support is broken in Inkscape 0.92.2, fixed since 0.92.3

.. _tt0x-windows-install-pdf-to-svg-converter:

Install a pdf->svg converter
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Again you have two options: ``pdf2svg`` or ``pstoedit + ghostscript`` (recommended):

.. _tt0x-windows-install-pdf2svg:

Install pdf2svg (recommended)
-----------------------------

.. _pdf2svg-installer-64bit: https://github.com/textext/pdf2svg/releases/download/v0.2.3/Install-pdf2svg-0.2.3-64bit.exe
.. _pdf2svg-installer-32bit: https://github.com/textext/pdf2svg/releases/download/v0.2.3/Install-pdf2svg-0.2.3-32bit.exe

Download and install the ``pdf2svg`` package from https://github.com/textext/pdf2svg/releases (`32-bit <pdf2svg-installer-32bit_>`_, `64-bit <pdf2svg-installer-64bit_>`_)

.. _tt0x-windows-install-pstoedit:

Install pstoedit (not recommended)
----------------------------------

.. _pstoedit-installer-64bit: https://sourceforge.net/projects/pstoedit/files/pstoedit/3.73/pstoeditsetup_x64.exe
.. _pstoedit-installer-32bit: https://sourceforge.net/projects/pstoedit/files/pstoedit/3.73/pstoeditsetup_win32.exe

.. _gs-installer-32bit: https://github.com/ArtifexSoftware/ghostpdl-downloads/releases/download/gs926/gs926aw32.exe
.. _gs-installer-64bit: https://github.com/ArtifexSoftware/ghostpdl-downloads/releases/download/gs926/gs926aw64.exe

1. Download and install ``pstoedit`` version **3.73** (`32-bit <pstoedit-installer-32bit_>`_, `64-bit <pstoedit-installer-64bit_>`_)
2. Download and install ``ghostscript`` version **9.26**  (`32-bit <gs-installer-32bit_>`_, `64-bit <gs-installer-64bit_>`_)

.. warning::

    The most recent versions of ghostscript (9.50) and pstoedit (3.74) are NOT
    compatible with |TexText|. They do not work at all or produce false results.
    This is an error between both packages and cannot be handled by |TexText|,
    see issue :issue_num:`126`.

.. _tt0x-windows-install-latex:

Install pdflatex/lualatex/xelatex
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Download and install MiKTeX distribution https://miktex.org/download

.. warning::

    Make sure that automatic package installation is either set to
    ``Never install missing packages on-the-fly`` or set to
    ``Always install missing packages on-the-fly``. You can configure this
    feature during installation of MiKTeX or later in the `MiKTeX console <https://miktex.org/howto/miktex-console>`_.

.. _tt0x-windows-install-textext:

Install TexText
===============

You have two options: A setup script or a GUI based installer.

Setup script (recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Download the most recent package from :textext_0x_current_release_page:`GitHub release page <release>` (direct links: :textext_0x_download_zip:`.zip <Windows>`)
2. Extract the package and change into the created directory.
3. Double click on the file :bash:`setup_win.bat`. The script will check if all requirements
   described in :ref:`tt0x-windows-install-dependencies` are met. If so, it will install the extension
   files into the user's Inkscape configuration directory (usually this is
   ``%USERPROFILE%\AppData\Roaming\Inkscape``). If not, instructions are given helping to
   fix the problem. Unfortunately, the output of the script will not be colored on
   Windows versions < 10 18.03.

.. note::

    If you would like to skip the requirement checks during installation call the script
    from the command line as follows:

    .. code-block:: bash

        setup_win.bat /p:"--skip-requirements-check"

Installer
~~~~~~~~~

If you have trouble with the setup script you can use a GUI based installer:

1. Download the most recent installer from :textext_0x_current_release_page:`GitHub release page <release>` (direct links: :textext_0x_download_exe:`.exe <Windows>`)
2. Use the installer and follow the instructions. It will copy the required files into the user's Inkscape
   configuration directory (usually this is ``%USERPROFILE%\AppData\Roaming\Inkscape``).

.. note::

    The installer does not perform any requirement checks. This means that the extension might
    fail to run if you did not install the programs mentioned in
    :ref:`tt0x-windows-install-dependencies` correctly.


