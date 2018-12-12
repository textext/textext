Version 0.9.0 (t.b.a.)
~~~~~~~~~~~~~~~~~~~~~~
- New: GUI settings saved to disk and reloaded at next call
- New: Improved error dialog
- New: Added possibility to wrap long lines (:issue_num:`47`)
- New: Imagemagick is not necessary anymore (:issue_num:`60`)
- New: Automatic dependency checks during installation (:issue_num:`54`)
- New: More detailed and informative logging (:issue_num:`35`)
- Fixed: TeX compile error messages reappear (:issue_num:`17`)
- Internal: Change extension layout (:issue_num:`28`)
- Internal: Store TexText config in extension folder (:issue_num:`69`)
- Internal: Add CI to monitor backward compatibility (:issue_num:`57`)

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
  
