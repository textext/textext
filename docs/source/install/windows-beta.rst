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

.. warning::
    |Inkscape| builds for Windows are in fact nightly builds. Hence, operability of |TexText| might
    fail from one day to another. If you need a stable environment you are strongly encouraged
    to use :ref:`Inkscape 0.92<windows-install>`. Please report any issues.

.. important::

    1. Compared to previous versions of **TexText** for |InkscapeOld| |TexText| does
       not need any conversion utilities like ghostscript, pstoedit or pdfsvg.
       Furthermore, the required Python bindungs for the GTK-GUI are already included
       in the windows version of |Inkscape|.

    2. Currently, GTKSourceView is not available in the Windows version of |TexText|,
       hence syntax highlighting is not enabled. An installer will be provided soon.

The procedure depends on the Windows version you
are using

    - :ref:`ttwin10`

    - :ref:`ttwin78`

.. _ttwin10:

Installation on recent Windows 10 (>= 1703) systems
===================================================

.. note::

    Several of the following actions take place in a **power shell window**. To open a
    power shell from the Windows Explorer ``right click`` while pressing the
    ``SHIFT`` key in the directory you want to open it. Then select ``Open power shell window here``.
    The power shell opens which usually has a **blue** background.

Preparation
-----------
In a power shell window execute the following steps:

1. Backup your existing Inkscape extension directory:

    .. code-block:: powershell

        cmd /r xcopy /S /E /Y %APPDATA%\inkscape\extensions %APPDATA%\inkscape\extensions.backup\

2. Remove the old TexText installation:

    .. code-block:: powershell

        cmd /r del /S /Q %APPDATA%\inkscape\extensions\textext
        cmd /r del /Q %APPDATA%\inkscape\extensions\textext.inx


Download and install the |Inkscape| package
-------------------------------------------

1. Download |Inkscape| from https://inkscape.org/release/1.0beta2/.

2. Extract the zip package to a folder of your choice, e.g. ``C:\InkscapeBeta``.

3. Veryify that you are able to launch |Inkscape| by double clicking on ``inkscape.exe``
   in ``C:\InkscapeBeta\bin``.


Download and install |TexText|
------------------------------

1. Download the most recent **preview** package from :textext_current_release_page:`GitHub release page <release>`
2. Extract the package and change into the created directory.
3. In a power shell window run :bash:`setup_win.bat` with (**Important!!**) specification of the path to your
   |Inkscape| executable from your terminal:

    .. code-block:: powershell

        ./setup_win.bat --inkscape-executable "C:\InkscapeBeta\bin\inkscape.exe"

    Setup will inform you if some of the prerequisites needed by |TexText| are missing.
    Install them.

Now you can launch |Inkscape| by double clicking on ``inkscape.exe`` in ``C:\InkscapeBeta``
and work with |TexText|

**Please report any issues!** Thank you!


Switching back to Inkscape |InkscapeOld|
----------------------------------------

In a power shell window execute:

.. code-block:: powershell

    cmd /r move /Y %APPDATA%\inkscape\extensions %APPDATA%\inkscape\extensions.beta\
    cmd /r xcopy /S /E /Y %APPDATA%\inkscape\extensions.backup %APPDATA%\inkscape\extensions\


.. _ttwin78:

Installation on Windows 7, Windows 8 and older Windows 10 system
================================================================

.. note::

    Several of the following actions take place in a **command window**. To open a
    command window from the Windows Explorer ``right click`` while pressing the
    ``SHIFT`` key in the directory you want to open it. Then select ``Open command window here``.
    The command window opens which usually has a **black** background.

Preparation
-----------
In a power shell/ command window execute the following steps:

1. Backup your existing Inkscape extension directory:

    .. code-block:: winbatch

        xcopy /S /E /Y %APPDATA%\inkscape\extensions %APPDATA%\inkscape\extensions.backup\

2. Remove the old TexText installation:

    .. code-block:: winbatch

        del /S /Q %APPDATA%\inkscape\extensions\textext
        del /Q %APPDATA%\inkscape\extensions\textext.inx


Download and install the |Inkscape| package
-------------------------------------------

1. Download |Inkscape| from https://inkscape.org/release/1.0beta2/.

2. Extract the zip package to a folder of your choice, e.g. ``C:\InkscapeBeta``.

3. Veryify that you are able to launch |Inkscape| by double clicking on ``inkscape.exe``
   in ``C:\InkscapeBeta\bin``.


Download and install |TexText|
------------------------------

1. Download the most recent **preview** package from :textext_current_release_page:`GitHub release page <release>`
2. Extract the package and change into the created directory.
3. If you are on older Windows 10 systems, Windows 8, or Windows 7: In a command window run
   :bash:`setup_win.bat` with (**Important!!**) specification of the path to your |Inkscape| executable
   from your terminal:

    .. code-block:: winbatch

        setup_win.bat --inkscape-executable "C:\InkscapeBeta\bin\inkscape.exe"

    Setup will inform you if some of the prerequisites needed by |TexText| are missing.
    Install them.

Now you can launch |Inkscape| by double clicking on ``inkscape.exe`` in ``C:\InkscapeBeta``
and work with |TexText|

**Please report any issues!** Thank you!


Switching back to Inkscape |InkscapeOld|
----------------------------------------

In a command window execute:

.. code-block:: winbatch

    move /Y %APPDATA%\inkscape\extensions %APPDATA%\inkscape\extensions.beta\
    xcopy /S /E /Y %APPDATA%\inkscape\extensions.backup %APPDATA%\inkscape\extensions\
