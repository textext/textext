Version 1.8.1 (2022-02-23)
~~~~~~~~~~~~~~~~~~~~~~~~~~
- Fixed: When re-installing TexText with diffent paths to latex excutables
  compared to the original setup these new paths are not recognized when
  invoking TexText from Inkscape (:issue_num:`345`).

Version 1.8.0 (2022-02-03)
~~~~~~~~~~~~~~~~~~~~~~~~~~
- New: It is now possible to use the ``\documentclass`` statement in the
  preamble file. This makes it easier to adjust the fontsize. Old preamble
  files without the ``\documentclass`` statement can still be used.
- Changed: Instructions for installation of TexText for Inkscape in
  Windows PortableApps (fixes :issue_num:`288`)

Version 1.7.1 (2022-01-04)
~~~~~~~~~~~~~~~~~~~~~~~~~~
- Fixed: In Inkscape 1.2-dev new nodes are not placed in the center of the view.
  (:issue_num:`338`)

Version 1.7.0 (2021-12-27)
~~~~~~~~~~~~~~~~~~~~~~~~~~
- New: Adjustable font size in LaTeX code editor (GTK GUI only)
- Fixed: distutils deprecation warning when running under Python 3.10
- Open: In Inkscape 1.2-dev new nodes are not placed in the center of the view.
  (:issue_num:`338`)

Version 1.6.1 (2021-11-16)
~~~~~~~~~~~~~~~~~~~~~~~~~~
- Fixed: When LaTeX-code is imported via the `File` - `Open` dialog
  the error message `ResourceWarning: unclosed file <_io.TextIOWrapper name'...'`
  is shown. (:issue_num:`322`)

Version 1.6.0 (2021-10-07)
~~~~~~~~~~~~~~~~~~~~~~~~~~
- Fixed: Generated svg objects appear sometimes flipped or far away from
  the view center (:issue_num:`283`, :issue_num:`313`)

- New: It is now possible to install TexText system wide for all users
  (setup script only, see
  `setup documentation <https://textext.github.io/textext/install/advanced.html>`_,
  :issue_num:`247`, :issue_num:`314`)

Version 1.5.0 (2021-08-19)
~~~~~~~~~~~~~~~~~~~~~~~~~~
- Changed: The feature enabling easy colorization of TexText svg nodes
  containing `\sqrt`, `\frac`, and other commands introducing strokes
  (lines) in Inkscape is now optional, see
  `documentation <https://textext.github.io/textext/usage/gui.html#colorization-of-the-output>`_.
  Reason for this is the increased compilation time (cf. :issue_num:`304`).

- New (experimental): Support of Inkscape extension manager
  (manual install of file downloaded from
  `Inkscape extension site <https://inkscape.org/~jcwinkler/%E2%98%85textext>`_)

- New (Inkscape on MS Windows): User defined locations of Inkscape
  installed via the msi-Installer are correctly identified by the
  setup-script.

Version 1.4.0 (2021-05-31)
~~~~~~~~~~~~~~~~~~~~~~~~~~
- New: TexText svg nodes can be colorized now by a single click even
  if they contain strokes (as, for example, in fractions,
  square-roots or overlines). Just select the node in Inkscape and
  click on the fill color in the color bar as you do it with normal
  Inkscape text (:issue_num:`291`).

  *Note*: Due to this, execution time per node compilation is longer
  compared to previous versions of TexText. However, you do not need to
  colorize strokes manually in Inkscape anymore. On Windows, also
  a slight flickering on the screen might appear while the TeX code
  is compiled.
- Documentation improvements

Version 1.3.1 (2021-02-26)
~~~~~~~~~~~~~~~~~~~~~~~~~~
- Fixed: Setup script fails on Windows if Inkscape has been installed
  via the .msi installer (:issue_num:`280`)
- Fixed: Imprecise instructions regarding location of Inkscape
  executable in Windows setup script (:issue_num:`280`)
- Added: Detailed explanation of setup script options (Linux, MacOS,
  Windows)

Version 1.3.0 (2020-11-27)
~~~~~~~~~~~~~~~~~~~~~~~~~~
- Fixed: Double backslashes and missing line breaks occur when using
  TexText 1.2.0 on nodes created with TexText <= 1.1 (:issue_num:`265`)

  **Note: A one-time manual insertion of line breaks will be necessary
  when opening such nodes. When having saved them again the line breaks
  are kept in the future. Double backslashes are replaced by single ones
  automatically.**
- Fixed: Opening TexText is slow (:issue_num:`263`)
- Fixed: Windows installation script complains about missing
  Python GTK3 bindings (:issue_num:`262`)
- New: Added explanation to the FAQ/ documentation how to
  define a shortcut for opening TexText (:issue_num:`259`). Refer to
  https://textext.github.io/textext/usage/faq.html#defining-keyboard-shortcut-for-opening-textext-dialog

Version 1.2.0 (2020-10-22)
~~~~~~~~~~~~~~~~~~~~~~~~~~
- Fixed: On Windows and Inkscape 1.0.1 TK interface is shown only
  (:issue_num:`253`)
- Fixed: Color of TexText nodes set in Inkscape not kept after
  recompilation (:issue_num:`245`)
- Fixed: `temp.tex` file not encoded in UTF-8 (:issue_num:`241`)
- Fixed: Installation on Windows via batch file fails if path to
  batch file contains spaces (:issue_num:`232`)
- New: TexText group ID is kept after recompilation (:issue_num:`256`)

Version 1.1.0 (2020-07-17)
~~~~~~~~~~~~~~~~~~~~~~~~~~
- New: Possibility to set a white background for preview images (favourably
  for dark mode themes)
- New: Added instructions how to install Inkscape 1.0 on Ubuntu 18.04/ 20.04
  since it is not shipped by default with these distributions

Version 1.0.1 (2020-05-12)
~~~~~~~~~~~~~~~~~~~~~~~~~~
- Fixed: List index out of range if latex compilation fails 
  (:issue_num:`219`)
  
Version 1.0.0 (2020-05-04)
~~~~~~~~~~~~~~~~~~~~~~~~~~
- **Important**: This version is only compatible with Inkscape 1.0. Please
  use TexText 0.11.1 if you use Inkscape 0.92.x

- **Major changes**
    - TexText can now be found in Inkscape menu entry *"Extensions -> Text -> Tex Text"*
      (All extensions are required to be in some submenu)
    - Added shortcut CTRL+P for displaying the preview image
    - TexText does not need *pstoedit*, *ghostscript* and *pdf2svg* as external
      dependencies anymore
    - TexText uses GTK3 user interface now, as Inkscape 1.0 does
    - Full Python 3 compatibility
    - Windows only: setup_win.bat now supports Python like arguments

- **Important Fixes**
    - Lost color after re-compilation of node (:issue_num:`206`)
    - Operand type error (:issue_num:`186`)
    - Gradient fills not properly rendered (e.g. in color bars)
      (:issue_num:`148`)
    - Proper parsing and display of LaTeX compiler errors
    - Fixed: Double ESC-hit closes TexText window without confirmation

Version 0.11.1 (2020-05-04)
~~~~~~~~~~~~~~~~~~~~~~~~~~~
- **Important**: This version is only compatible with Inkscape 0.92.x Please
  use TexText 1.0 if you use Inkscape 1.0
- Modified URLs for help on dependency installation in setup routine

Version 1.0.0-dev.4 (2020-04-15)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- Fixed: Vertical flipping after re-compilation of nodes created with TexText < 1.0
  (:issue_num:`205`)
- Fixed: Lost color after re-compilation of node (:issue_num:`206`)

Version 1.0.0-dev.3 (2020-04-10)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- Compatibility with Inkscape 1.0 Release Candidate 1 modified extension API
  (:issue_num:`188`, :issue_num:`193`, :issue_num:`194`, :issue_num:`196`, :issue_num:`202`, :issue_num:`203`)
- Fixed operand type error (:issue_num:`186`)
- Windows only: setup_win.bat now supports Python like arguments

Version 1.0.0-dev.2 (2020-02-10)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- New: Enabled TkInter GUI under Python 3
- New: Proper parsing and display of LaTeX compiler errors
- Fixed: New nodes were not being placed in the center of the document
- Fixed: Scale factor is ignored in new nodes
- Fixed: Inkscape version never stored in TexText node
- Fixed: Ctrl+P and Ctrl+Q shortcut not working properly under ALL Python interpreters
  required by Inkscape
- Fixed: Setup error URLs do not point to correct issue template
- Several minor/ internal improvements/ fixes. See commit history of develop branch

Version 1.0.0-dev.1 (2019-12-17)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- New: TexText does not need pstoedit, ghostscript and pdf2svg as external
  dependencies anymore
- New: Added shortcut CTRL+P for displaying the preview image
- Fixed: Gradient fills not properly rendered (e.g. in color bars)
  (:issue_num:`148`)
- Fixed: Double ESC-hit closes TexText window without confirmation
- Internal: Improved exception handling
- Open: On Windows source code syntax highlighting is currently not available

Version 0.11.0 (2019-06-22)
~~~~~~~~~~~~~~~~~~~~~~~~~~~
- New (GTK-version only): Possibility to select a shortcut for closing the
  TexText window. You can select between `Escape` (default), `CTRL + Q` and
  `None`.
- New (GTK-version only): TexText asks for confirmation to close the window
  in case you made changes to your text (:issue_num:`127`).
- New: The annoying "Extension is working" window is not shown anymore.
- New: Improved dependency check on incompatible pstoedit and ghostscript
  versions

**Note**: This is the last feature update for TexText on Inkscape 0.92.x. Any new
features will be included in TexText for Inkscape 1.0.

Version 0.10.2 (2019-05-07)
~~~~~~~~~~~~~~~~~~~~~~~~~~~
- New: Disallowed pstoedit 3.73 + ghostscript 9.27 combination during
  installation (:issue_num:`126`)

Version 0.10.1 (2019-04-17)
~~~~~~~~~~~~~~~~~~~~~~~~~~~
- Fixed: Inkscape binary not found during installation on some MacOS
  installations (:issue_num:`120`)

Version 0.10.0 (2019-04-05)
~~~~~~~~~~~~~~~~~~~~~~~~~~~
- New: Possibility to define default math environment when creating new nodes
  (empty, inline math, display math)
- Fixed: Two grey windows appear with no text inside. Inkscape freezes and
  becomes unusable (:issue_num:`114`)
- Fixed: Log file cannot be written in system wide installations of TexText
  (:issue_num:`111`)
- Internal: Automatic CI deployment and documentation upload (thanks to
  Sergei Izmailov)

Version 0.9.1 (2018-12-27)
~~~~~~~~~~~~~~~~~~~~~~~~~~
- Fixed: UnicodeDecodeError in setup.py / setup_win.bat
  (:issue_num:`101`)


Version 0.9.0 (2018-12-20)
~~~~~~~~~~~~~~~~~~~~~~~~~~
- New: Scripted setup procedure with automatic check of the
  dependencies (:issue_num:`54`, :issue_num:`66`)
- New: Added possibility to wrap long lines (:issue_num:`47`)
- New: GUI settings saved to disk and reloaded at next call
  (word wrap, auto-indent, spaces instead of tab, showing line numbers,
  tab-width)
- New: Large preview images do not destroy the editor view anymore. They
  are displayed scaled to the available window size. It is also possible
  to display the preview image in original size with vertical and
  horizontal scrolling enabled.
- New: Improved error dialog
- New: Imagemagick is not necessary anymore (:issue_num:`60`)
- New: Automatic dependency checks during installation (:issue_num:`54`)
- New: More detailed and informative logging (:issue_num:`35`)
- Fixed: TeX compile error messages reappear (:issue_num:`17`)
- Internal: Change extension repository layout (:issue_num:`28`)
- Internal: Store TexText config in extension folder (:issue_num:`69`)
- Internal: Add CI to monitor backward compatibility (:issue_num:`57`)
- Abandoned: Support for Inkscape <= 0.91.x (see :ref:`faq-old-inkscape` for your options)

Very big thanks go to Sergei Izmailov who again contributed a huge bunch of
great improvements for this release of the extension.


Version 0.8.2 (2018-12-12)
~~~~~~~~~~~~~~~~~~~~~~~~~~
v0.8.2:
  - Fixed: pstoedit/pdf2svg interoperability on distorted nodes :issue_num:`56`

Version 0.8.1 (2018-08-23)
~~~~~~~~~~~~~~~~~~~~~~~~~~
- Fixed: Loss of user defined preamble file path when re-editing
  nodes (:issue_num:`40`, thanks to veltsov@github).
- Added file chooser button for selection of preamble file in Tk
  interface

Version 0.8.0 (2018-08-21)
~~~~~~~~~~~~~~~~~~~~~~~~~~
- Fixed bad positioning, improved alignment capabilities
  (Thanks to Sergei Izmailov for implementing this)
- pdf2svg as backend
- xelatex and lualatex support
- Keep colors explicitly set in TeX or set by Inkscape
- Temp directory is safely removed even if it contains additional files
  generated during compilation

Version 0.7.3 (2018-05-17)
~~~~~~~~~~~~~~~~~~~~~~~~~~
- Fixed: Failure when trying to re-edit nodes created with very old versions of
  TexText. (:issue_num:`15`: "Recompiling of nodes created with TexText < 0.5 fails")

- Fixed: :issue_num:`19`: Missing width and height attributes in svg document
  lead to crash

Version 0.7.2 (2018-04-06)
~~~~~~~~~~~~~~~~~~~~~~~~~~
- Fixed: Failure on missing Inkscape version key (:issue_num:`10`: "Error occurred while
  converting text from LaTeX to SVG")


Version 0.7.1 (2018-02-06)
~~~~~~~~~~~~~~~~~~~~~~~~~~
- Fixed:
  Wrong scaling so that text with explicitly defined font size does not match
  size of text with equal font size in Inkscape 0.92.x (:issue_num:`1`)

- Fixed:
  "Zero length field name in format" error in Inkcape <= 0.91 (:issue_num:`6`)


.. note::
    Note: All issue references for version 0.7 and prior refer to https://bitbucket.org/pitgarbe/textext


Version 0.7 (2017-12-15)
~~~~~~~~~~~~~~~~~~~~~~~~
- Fixed:
  Plugin does not run with Inkscape 0.92.2 under Windows

- New:
  Global and local scale factor. This feature enables the user to set the scale
  factor of a node to the value used while editing the previous node (Button
  "Global"). Hence, it is easier to change several nodes to the same scale
  factor. It is always possible to reset the scale factor to the value used for
  creating the node (Button "Reset").

- New:
  Added compatibility to ImageMagick 7 (version 6 is still supported) (:bb_issue_num:`32`, :bb_issue_num:`39`)

- Workaround:
  A message is displayed if pstoedit failed to produce svg output and ghostscript
  < 9.21 is installed on the system (issues :bb_issue_num:`44`, :bb_issue_num:`48`, :bb_issue_num:`50`).


Version 0.6.1 (2017-02-13)
~~~~~~~~~~~~~~~~~~~~~~~~~~
- Fixed:
  "global name 'WindowsError' is not defined" - on Linux when using Preview


- Fixed:
  Typos "lates_messaga" in textext.py

- Improved:
  Readme can be shown after installation of TexText under Windows

- Improved:
  License packaged


Version 0.6 (2017-02-01)
~~~~~~~~~~~~~~~~~~~~~~~~
- Fixed:
  "too many values to unpack"-error in Inkscape 0.92

- Fixed:
  TexText does not work with 64-bit versions of Inkscape under MS Windows

- Improved:
  TexText does not care anymore if 32-bit or 64-bit versions of pstoedit,
  ImageMagick and ghostscript are installed

- Improved:
  Installation of PyGTK simplified


Version 0.5.2 (2017-01-06)
~~~~~~~~~~~~~~~~~~~~~~~~~~
- Fixed:
  If working with Inkscape files stored with older versions of Inkscape or TexText
  it could happen that - after editing of a LaTeX node - the rendered object becomes
  invisible (in fact: transparent) because the fill attribute was not properly set.

- Fixed:
  Installation under MS Windows as non admin user ends up with the plugin installed
  into the wrong directory.

- Fixed:
  Column numbers do not change during editing of the LaTeX-code under Linux and TK.
  The Column-number is nor removed from the dialog if the TK interface is used.

- Fixed:
  setup.py for the Linux installation does not run under Python 3.

- Improved:
  More detailled error information is passed to the user during setup of the
  Linux package.

- Updated:
  The readme-files have been updated to the new version number. Furthermore, links
  for download of the additional software have been added as well as a comment
  that the plugin will only work usign 32bit versions of Inkscape. Furthermore,
  there is only one readme now for both, Linux and Windows.



Version 0.5.1 (2016-10-10)
~~~~~~~~~~~~~~~~~~~~~~~~~~
- Fixed:
  TexText does not work with Inkscape 0.9.1

  It is ensured now that Inkscape works under both, Inkscape 0.48 and Inkscape 0.91.

