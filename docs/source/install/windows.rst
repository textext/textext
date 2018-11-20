.. |TexText| replace:: **TexText**

.. role:: bash(code)
   :language: bash
   :class: highlight

.. role:: latex(code)
   :language: latex
   :class: highlight

.. _windows-install:

==================
TexText on Windows
==================

To install |TexText| on Windows do the following steps:

#. `Install dependencies <windows-install-dependencies_>`_ of |TexText|

    - `Install inkscape <windows-install-inkscape_>`_
    - `Install GUI library (PyGTK2 or TkInter) <windows-install-gui-library_>`_
    - `Install pdflatex/lualatex/xelatex <windows-install-latex_>`_
    - `Install pdf->svg converter (pdf2svg or pstoedit) <windows-install-pdf-to-svg-converter_>`_

#. `Install TexText <windows-install-textext_>`_

.. _windows-install-dependencies:

Install dependencies
====================

.. _windows-install-inkscape:

Install inkscape
~~~~~~~~~~~~~~~~

Download and install inkscape https://inkscape.org/release/

.. warning::

    Please ensure that the Python 2.7 interpreter has been selected during the installation of Inkscape (by default this is the case).


.. _windows-install-gui-library:

Install GUI library
~~~~~~~~~~~~~~~~~~~

Install the Python bindings for the graphical user interface of
|TexText|. You have two options: ``PyGTK2`` (recommended) or ``Tkinter``:

.. _windows-install-pygtk2:

Install PyGTK2 (recommended)
----------------------------

.. _inkscape-0.92.2-0.92.3-64-bit: https://github.com/textext/textext/releases/download/0.7/Install-PyGTK-2.24-Inkscape-0.92.2-64bit.exe
.. _inkscape-0.92.2-0.92.3-32-bit: https://github.com/textext/textext/releases/download/0.7/Install-PyGTK-2.24-Inkscape-0.92.2-32bit.exe
.. _inkscape-0.92.0-0.92.1-multi: https://github.com/textext/textext/releases/download/0.7/Install-PyGTK-2.24-Inkscape-0.92.exe
.. _inkscape-0.48.x-0.91.x-multi: https://github.com/textext/textext/releases/download/0.7/Install-PyGTK-2.24-Inkscape-0.48+0.91.exe

Install the package that matches your Inkscape version:

 - Inkscape 0.48.x - 0.91.x (`32-bit and 64-bit <inkscape-0.48.x-0.91.x-multi_>`_)
 - Inkscape 0.92.0 - 0.92.1 (`32-bit and 64-bit <inkscape-0.92.0-0.92.1-multi_>`_)
 - Inkscape 0.92.2 - 0.92.3 (`32-bit <inkscape-0.92.2-0.92.3-32-bit_>`_ , `64-bit <inkscape-0.92.2-0.92.3-64-bit_>`_)

.. _windows-install-tkinter:

Install Tkinter (not recommended)
---------------------------------

Tkinter is already included in the Python installation shipped with Inkscape.

.. warning::

    Tk support is broken in Inkscape 0.92.2, fixed in 0.92.3

.. _windows-install-pdf-to-svg-converter:

Install a pdf->svg converter
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Again you have two options: ``pdf2svg`` or ``pstoedit + ghostscript`` (recommended):

.. _windows-install-pdf2svg:

Install pdf2svg (not recommended)
----------------------------------

.. note::

    ``pdf2svg`` support on Windows is in beta

Install the ``pdf2svg`` package from https://github.com/textext/pdf2svg/releases

.. _windows-install-pstoedit:

Install pstoedit (recommended)
----------------------------------


.. _pstoedit-installer-64bit: https://sourceforge.net/projects/pstoedit/files/pstoedit/3.71/pstoeditsetup_x64.exe
.. _pstoedit-installer-32bit: https://sourceforge.net/projects/pstoedit/files/pstoedit/3.71/pstoeditsetup_win32.exe

.. _gs-installer-32bit: https://github.com/ArtifexSoftware/ghostpdl-downloads/releases/download/gs923/gs923w32.exe
.. _gs-installer-64bit: https://github.com/ArtifexSoftware/ghostpdl-downloads/releases/download/gs923/gs923w64.exe

1. Download and install ``pstoedit-3.71`` (`32-bit <pstoedit-installer-32bit_>`_, `64-bit <pstoedit-installer-64bit_>`_)
2. Download and install ``ghostcript-9.23``  (`32-bit <gs-installer-32bit_>`_, `64-bit <gs-installer-64bit_>`_)

.. _windows-install-latex:

Install pdflatex/lualatex/xelatex
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Download and install MiKTeX distribution https://miktex.org/download


.. _windows-install-textext:

Install TexText
=================

1. Download the most recent package from :textext_current_release_page:`GitHub release page <release>` (direct links: :textext_download_exe:`.exe <Windows>`)
2. Use the installer and follow the instructions. It will copy the required files into the user's Inkscape
   configuration directory (usually this is ``%USERPROFILE%\AppData\Roaming\Inkscape``) and put a key into
   the Windows registry which is used to store configuration data of the extension.

