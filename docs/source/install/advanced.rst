.. |TexText| replace:: **TexText for Inkscape 1.x**
.. |Inkscape| replace:: **Inkscape 1.x**

.. role:: bash(code)
   :language: bash
   :class: highlight


.. _advanced-install:

=============================
Advanced installation options
=============================

The :bash:`setup.py` / :bash:`setup_win.bat` installation script offers several
options to adapt the installation process to your system configuration:

-h, --help
    Show help message and exit.

--inkscape-extensions-path INKSCAPE_EXTENSIONS_PATH
    Path to inkscape extensions directory. Use this if the user
    extensions are installed in an unusual place, e.g. when using |Inkscape|
    in PortableApps on Windows.

--inkscape-executable INKSCAPE_EXECUTABLE
    Full path to inkscape executable.  Use this if |Inkscape| is not found
    automatically by the setup script (Test- or Beta-installations, Portable
    Apps on Windows).

--pdflatex-executable PDFLATEX_EXECUTABLE
    Full path to pdflatex executable.

--lualatex-executable LUALATEX_EXECUTABLE
    Full path to lualatex executable.

--xelatex-executable XELATEX_EXECUTABLE
    Full path to xelatex executable.

--skip-requirements-check
    Bypass minimal requirements check. |TexText| will be installed even if
    the requirements for running it are not meat.

--skip-extension-install
    Don't install extension (just check the requirements).

--keep-previous-installation-files
    Keep/discard files from previous installation, suppress prompt.

--all-users
    Install globally for all users (sudo/ admin privileges required)

    .. caution::
        Usually, this works well. However, you should keep in mind that the
        |TexText| files are copied into Inkscape's global extension folder,
        hence cluttering your Inkscape installation. You may need to remove these
        files manually when you uninstall Inkscape.

--color always, --color never
    Enables/disable console colors.
