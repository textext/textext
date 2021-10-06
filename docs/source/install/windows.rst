.. |TexText| replace:: **TexText for Inkscape 1.x**
.. |Inkscape| replace:: **Inkscape 1.x**
.. |InkscapeOld| replace:: **Inkscape 0.92.x**

.. role:: bash(code)
   :language: bash
   :class: highlight

.. role:: latex(code)
   :language: latex
   :class: highlight

.. _gtksourceview-windows-64-bit: https://github.com/textext/gtksourceview-for-inkscape-windows/releases/download/1.0.0/Install-GtkSourceView-3.24-Inkscape-1.0-64bit.exe
.. _gtksourceview-windows-32-bit: https://github.com/textext/gtksourceview-for-inkscape-windows/releases/download/1.0.0/Install-GtkSourceView-3.24-Inkscape-1.0-32bit.exe
.. _gtksourceview-inkscape-site: https://github.com/textext/gtksourceview-for-inkscape-windows/releases


.. _windows-install:

====================
|TexText| on Windows
====================

.. _windows-install-preparation:

Preparation
===========
1. Make sure that Inkscape version 1.0 or later is installed on your system and you checked
   the ``Python`` option in ``Program Files`` as well as the ``Extensions`` options in
   ``Inkscape Data`` during the installation of Inkscape (by default this is the case).

    .. figure:: ../images/inkscape-install-options-windows.png
       :alt: Necessary installation options in Inkscape


2. Make sure that an operational LaTeX distribution is installed on your system. You can verify
   this by invoking at least one of :bash:`pdflatex --version`, :bash:`xelatex --version`, and
   :bash:`lualatex --version` in a command or power shell window.

   .. warning::

       Make sure that automatic package installation is either set to
       ``Never install missing packages on-the-fly`` or set to
       ``Always install missing packages on-the-fly``. You can configure this
       feature during installation of MiKTeX or later in the `MiKTeX console <https://miktex.org/howto/miktex-console>`_.


3. Optional: If you whish to have syntax highlighting and some other :ref:`nice features <usage-gui-config>`
   enabled in the |TexText|-Gui install GtkSourceView. For that purpose download the GtkSourceView package
   that matches your Inkscape installation type

   - `GtkSourceview 3 for Inkscape 1.0 64-bit <gtksourceview-windows-64-bit_>`_
   - `GtkSourceview 3 for Inkscape 1.0 32-bit <gtksourceview-windows-32-bit_>`_

   and run the corresponding installer. It will add a small amount of files into your |Inkscape|
   installation. You need administrator privileges for this step. If you do not trust the installer
   you will find zip packages on the `GtkSourceView for Inkscape project site <gtksourceview-inkscape-site_>`_
   for manual installation.

.. important::

    Compared to previous versions |TexText| does not need any conversion utilities like ghostscript,
    pstoedit or pdfsvg. Furthermore, the required Python bindungs for the GTK3-GUI
    are already included in the windows version of |Inkscape|.

.. _windows-install-textext:

Download and install |TexText|
==============================

You have two options: A setup script or a GUI based installer.

Setup script (recommended)
--------------------------

1. Download the most recent package from :textext_current_release_page:`GitHub release page <release>` (direct links: :textext_download_zip:`.zip <Windows>`)
2. Extract the package and change into the created directory.
3. Double click on the file :bash:`setup_win.bat`. The script will check if all requirements
   described :ref:`above <windows-install-preparation>` are met. If so, it will install the extension
   files into the user's Inkscape configuration directory (usually this is
   ``%USERPROFILE%\AppData\Roaming\Inkscape``).

See :ref:`advanced-install` for further options provided by
:bash:`setup_win.bat`.

.. note::

    In case of installation problems refer to the :ref:`trouble_installation` in the :ref:`troubleshooting` section!




Installer
---------

You can also use a GUI based installer:

1. Download the most recent installer from :textext_current_release_page:`GitHub release page <release>` (direct links: :textext_download_exe:`.exe <Windows>`)
2. Use the installer and follow the instructions. It will copy the required files into the user's Inkscape
   configuration directory (usually this is ``%USERPROFILE%\AppData\Roaming\Inkscape``).

.. note::

    The installer does not perform any requirement checks. This means that the extension might
    fail to run if you did not install the programs mentioned
    :ref:`above <windows-install-preparation>` correctly.


You are done. Now you can consult the :ref:`usage instructions <gui>`.

.. _windows-install-library:
.. _windows-install-gtk3:
.. _windows-install-tkinter:

Problems with the GUI framework
-------------------------------

The GUI framework should already be included in the Inkscape installation on Windows.
Hence, if the |TexText| installer complains about missing GTK3 or TkInter bindings
please file a bug report on `github <https://github.com/textext/textext/issues/new/choose>`_