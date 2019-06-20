Version 0.11.0 (2019-06-21)
~~~~~~~~~~~~~~~~~~~~~~~~~~~
- New (GTK-version only): Possibility to select a shortcut for closing the
  TexText window. You can select between `Escape`, `CTRL + Q` and `None`.
  The last on is the default behavior now what means that the window cannot
  be closed by a shortcut or accidently by pressing `Escape`. You can
  define the behavior in the settings menu.
- New: The annoying "Extension is working" window is not shown anymore.
- New: Improved dependency check on incompatible pstoedit and ghostscript
  versions

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
  
