.. |TexText| replace:: **TexText**
.. |Inkscape| replace:: **Inkscape 1.x**

.. role:: bash(code)
   :language: bash
   :class: highlight

.. role:: dos(code)
   :language: dos
   :class: highlight


.. _configuration:

=====================
TexText Configuration
=====================

Usually, |TexText| is configured automatically during setup or via selecting
certian options in the GUI. In case of any problems or to address certain
issues one may directly edit the |TexText| configuration file.

.. contents:: :local:
   :depth: 2


The TexText configuration file
==============================

The configuration file ``config.json`` can be found at the following locations:

- Linux: ``~/.config/textext/config.json``
- Winbdows: ``C:\Users\AppData\Roaming\TexText\config.json``
- MacOS: ``~/Library/Preferences/textext``

The top level structure is:

.. code-block:: json

    {
      "preamble": "...",
      "scale": 1.0,
      "previous_tex_command": "...",
      "gui": {
        "toolkit": "...",
        "use_gtk_source": true,
        "confirm_close": true,
        "line_numbers": true,
        "auto_indent": true,
        "insert_spaces": true,
        "tab_width": 2,
        "new_node_content": "...",
        "close_shortcut": "..."
      }
    }

Fields and Allowed Values (toplevel)
------------------------------------

preamble (string, optional)
    Path to a LaTeX preamble file (.tex) or typst preamble file (.typst)
    is included in the document. If this is not set the default files
    (``default_packages.tex`` or ``default_preamble_typst.typ``) from the
    |TexText| installation directory is used.

    Example:

    .. code-block:: json

        "preamble": "C:\\Users\\...\\default_packages.tex"

scale (number, optional)
    Scaling factor for the rendered LaTeX object.

    Default: 1.0

    Example:

    .. code-block:: json

        "scale": 0.8

previous_tex_command (string, optional)
    Last used LaTeX engine. Determines which engine is preselected in the next
    session.

    Allowed values: ``"pdflatex"`` (default), ``"lualatex"``, ``"xelatex"``,
    ``"typst"``


Fields and Allowed Values (``gui`` object)
------------------------------------------

toolkit (string, optional)
    Specifies the GUI toolkit to be used.

    Allowed values: ``"gtk"`` (recommended), ``"tk"``

use_gtk_source (boolean, optional)
    Enable GtkSourceView for syntax highlighting (only valid, if
    ``toolkit="gtk"``.

    Values: ``true`` or ``false``

confirm_close (boolean, optional)
    Whether to show a confirmation prompt when closing the editor.

    Values: ``true`` or ``false``

line_numbers (boolean, optional)
    Display line numbers in the editor.

    Values: ``true`` or ``false``

auto_indent (boolean, optional)
    Enable automatic indentation of LaTeX code.

    Values: ``true`` or ``false``

insert_spaces (boolean, optional)
    Insert spaces instead of tab characters when pressing Tab.

    Values: ``true`` or ``false``

tab_width (integer, optional)
    Number of spaces per tab.

    Example:

    .. code-block:: json

        "tab_width": 2

new_node_content (string, optional)
    Initial content used for new LaTeX nodes.

    Allowed values: ``"Empty"`` (no content), ``"InlineMath"`` (e.g. $$) -
    default, ``"DisplayMath"`` (e.g. \\[\\])

close_shortcut (string, optional)
    Keyboard shortcut to close the editor.

    Allowed values: ``"Escape"``, ``"CtrlQ"``, ``"None"`` (no shortcut)

JSON schema for the configuration file
======================================

.. code-block:: json

    {
      "$schema": "http://json-schema.org/draft-07/schema#",
      "title": "TeXText Configuration Schema",
      "type": "object",
      "properties": {
        "preamble": {
          "type": "string",
          "description": "Path to a LaTeX preamble file (.tex)"
        },
        "scale": {
          "type": "number",
          "description": "Scale factor for the rendered LaTeX content",
          "minimum": 0
        },
        "previous_tex_command": {
          "type": "string",
          "description": "Previously used LaTeX engine",
          "enum": ["pdflatex", "lualatex", "xelatex", "typst"]
        },
        "gui": {
          "type": "object",
          "description": "Graphical user interface configuration",
          "properties": {
            "toolkit": {
              "type": "string",
              "enum": ["gtk", "tk"],
              "description": "GUI toolkit to be used"
            },
            "use_gtk_source": {
              "type": "boolean",
              "description": "Enable GtkSourceView (for syntax highlighting)"
            },
            "confirm_close": {
              "type": "boolean",
              "description": "Ask for confirmation when closing the editor"
            },
            "line_numbers": {
              "type": "boolean",
              "description": "Display line numbers in the code editor"
            },
            "auto_indent": {
              "type": "boolean",
              "description": "Enable automatic indentation"
            },
            "insert_spaces": {
              "type": "boolean",
              "description": "Insert spaces instead of tab characters"
            },
            "tab_width": {
              "type": "integer",
              "minimum": 1,
              "description": "Number of spaces per tab"
            },
            "new_node_content": {
              "type": "string",
              "enum": ["Empty", "InlineMath", "DisplayMath"],
              "description": "Default content for new LaTeX nodes"
            },
            "close_shortcut": {
              "type": "string",
              "enum": ["Escape", "CtrlQ", "None"],
              "description": "Keyboard shortcut for closing the editor"
            }
          },
          "additionalProperties": false
        }
      },
      "additionalProperties": false
    }