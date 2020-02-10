.. |TexText| replace:: **TexText for Inkscape 1.0 beta**
.. |Inkscape| replace:: **Inkscape 1.0 beta**
.. |InkscapeOld| replace:: **Inkscape 0.92.x**

.. role:: bash(code)
   :language: bash
   :class: highlight

.. role:: latex(code)
   :language: latex
   :class: highlight

.. _windows-beta-install:

====================
|TexText| on Windows
====================

This guide explains how to install and use |TexText| together with |Inkscape| on a system
on which also |InkscapeOld| is installed.

.. note::

    Several of the following actions take place in a command window. To open a
    command window from the Windows Explorer ``right click`` while pressing the ``SHIFT`` key in
    the directory you want to open it. Then select ``Open command window here``.

Preparation
===========
In a command window execute the following steps:

1. Backup your existing Inkscape extension directory:

    .. code-block:: winbatch

        xcopy /S /E /Y %APPDATA%\inkscape\extensions %APPDATA%\inkscape\extensions.backup\

2. Remove the old TexText installation:

    .. code-block:: winbatch

        del /S /Q %APPDATA%\inkscape\extensions\textext
        del /Q %APPDATA%\inkscape\extensions\textext.inx


Download and install the |Inkscape| app image file
==================================================

1. Download |Inkscape| from https://inkscape.org/release/1.0beta2/.

2. Extract the zip package to a folder of your choice, e.g. ``C:\InkscapeBeta``.

3. Veryify that you are able to launch |Inkscape| by double clicking on ``inkscape.exe``
   in ``C:\InkscapeBeta\bin``.


Download and install |TexText|
==============================

1. Download the most recent **preview** package from :textext_current_release_page:`GitHub release page <release>`
2. Extract the package and change into the created directory.
3. In a command window run :bash:`setup_win.bat` with (**Important!!**) specification of the
   path to your |Inkscape| executable from your terminal:

    .. code-block:: winbatch

        setup_win.bat /d:"C:\InkscapeBeta\bin"

    Setup will inform you if some of the prerequisites needed by |TexText| are missing.
    Install them.

    .. important::

        1. Compared to previous versions of **TexText** for |InkscapeOld| |TexText| does
           not need any conversion utilities like ghostscript, pstoedit or pdfsvg.
           Furthermore, the required Python bindungs for the GTK-GUI are already included
           in the windows version of |Inkscape|.

        2. Currently, GTKSourceView is not available in the Windows version of |TexText|,
           hence syntax highlighting is not enabled. An installer will be provided soon.

Now you can launch |Inkscape| by double clicking on ``inkscape.exe`` in ``C:\InkscapeBeta``
and work with |TexText|

**Please report any issues!** Thank you!


Switching back to Inkscape |InkscapeOld|
========================================

In a command window execute:

.. code-block:: winbatch

    move /Y %APPDATA%\inkscape\extensions %APPDATA%\inkscape\extensions.beta\
    xcopy /S /E /Y %APPDATA%\inkscape\extensions.backup %APPDATA%\inkscape\extensions\
