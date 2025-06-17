.. |TexText| replace:: **TexText**
.. |Inkscape| replace:: **Inkscape 1.x**

.. role:: bash(code)
   :language: bash
   :class: highlight

.. role:: dos(code)
   :language: dos
   :class: highlight


.. _commandlineusage:

==========================
TexText Command Line Usage
==========================

Next to the usage from within Inkscape |TexText| can also be invoked from the
command line. This maybe used in third party apps or for debugging
purposes.

.. contents:: :local:
   :depth: 2

Prerequisites
=============

In order to use |TexText| from the command line some prerequisites must be met.
At first, since |TexText| uses the Inkscape executable itself for the required
pdf -> svg conversion, Inkscape must be installed on your system. Additionally,
the path to the Inkscape extension system must be known.

Linux
~~~~~

Since  Inkscape is on your system all required Python libraries are already
available for the system Python interpreter. You only have to ensure that the
``PYTHONPATH`` variable contains the path to the Inkscape extension framework:

.. code-block:: bash

    export PYTHONPATH=${PYTHONPATH}:/usr/share/inkscape/extensions

Windows
~~~~~~~

On Windows Python is bundled within the Inkscape installation. You need to
ensure that the Inkscape binary directory is in the system path so that
``inkscape.exe`` and ``python.exe`` is found. Additionally, the ``PYTHONPATH``
variable must contain the path to the Inkscape extension framework:

.. code-block:: doscon

    set PATH=C:\Program Files\Inkscape\bin;%PATH%
    set PYTHONPATH=%PYTHONPATH%;C:\Program Files\Inkscape\share\inkscape\extensions

.. note::

    If you are unsure where the Inkscape extension subsystem resides in your
    system execute the command

    .. code-block:: bash

        inkscape --system-data-directory

    and add ``/extensions`` (or ``\extensions`` on Windows) to the output.


Usage
=====

On the command line, in principle, |TexText| operates as follows: It takes the
content of an Inkscape SVG-document, does something with it (e.g. inserts a
|TexText| object, modifies an existing |TexText| object, or re-compiles all
existing |TexText| obejcts) and writes the resulting SVG-content into a new file
or to ``stdout``.

The calling syntax is

.. code-block:: bash

    python __main.py__ [-h] [--output OUTPUT] [--id IDS] [--selected-nodes SELECTED_NODES]
                       [--text TEXT] [--preamble-file PREAMBLE_FILE]
                       [--scale-factor SCALE_FACTOR] [--alignment ALIGNMENT]
                       [--recompile-all-entries] [--tex_command TEX_COMMAND] [INPUT_FILE]

The function returns ``0`` in case compilation succeeded. It returns ``1``
(bad setup) or ``60`` (program or compile errors) if execution failed.

Command Line Arguments
======================

-h, --help
    Show help message and exit.

INPUT_FILE:
    The Inkscape SVG-file the content of with is taken and processed by
    |TexText|. This file is not modified. See the ``--output`` argument for
    more details.

--output OUTPUT
    Path of the file into which the output of |TexText| is written. If this
    argument is omitted the output is written to ``stdout``.

--id IDS
    The XML id attribute of the selected |TexText| object (or a list of ids
    if multiple are selected) in the SVG-Document one would like to modify.
    If this argument is omitted it is assumed that a new |TexText| object
    is going to be created and inserted into the SVG document. If the object
    is no |TexText| object nothing happens.

    .. note::

        Currently, |TexText| does only support a single id.

--selected-nodes SELECTED_NODES
    Not used by |TexText| (it is the XML id:subpath:position attribute
    of selected nodes of a path)

--text TEXT
    The LaTeX or typst code to compile. If this argument is omitted the GUI
    opens if ``--recompile-all-entries`` is not set. The GUI will show the
    content of the |TexText| object specified by ``--id`` or nothing if no id
    has been specified.

--preamble-file PREAMBLE_FILE
    Full path to the preamble file one would like to use for
    compilation.

--scale-factor SCALE_FACTOR
    The scale factor one would like to use for compilation. A scale factor
    ``1.0`` means that the compiled LaTeX or typst output is inserted
    "as is" into the document.

--alignment ALIGNMENT
    Only evaluated when a |TexText| object is re-compiled. It controls how a
    modified |TexText| object is aligned with respect to the old object.
    Possible values are: ``top left``, ``top center``, ``top right``,
    ``middle left``, ``middle center``, ``middle-right``, ``bottom left``,
    ``bottom center``, and ``bottom right``.

--recompile-all-entries
    Re-compile all |TexText| objects found in the SVG-document. The
    ``--id`` and ``--text`` arguments are ignored in that case.

--tex_command TEX_COMMAND
    The command used for compilation of the code passed via the ``--text``
    argument. Possible values are ``pdflatex``, ``xelatex``, ``lualatex``,
    and ``typst``. If this argument is omitted the default (``pdflatex``)
    is used.

Examples
========

With showing the GUI
~~~~~~~~~~~~~~~~~~~~

- Take ``empty.svg``, open the GUI, compile the code typed in there and insert
  the generated object into the document. Write the result to ``stdout``:

    .. code-block:: bash

        python __main__.py empty.svg

- From ``nonempty.svg`` take the object the ``id`` attribute of which has the
  value ``7`` and in case this is a |TexText| object pass its LaTeX code to the
  GUI. After modification of the code, compile it and replace the original
  object by the modified one and write the output to ``result.svg``:

    .. code-block:: bash

        python __main__.py --id 7 --output result.svg nonempty.svg

Without showing the GUI
~~~~~~~~~~~~~~~~~~~~~~~

- Take ``empty.svg``, compile the code ``$x \in \mathbb{R}$`` using the preamble
  ``my_preamble.tex`` and insert the result as a |TexText| object scaled by
  ``2.0`` into the document. Write the result into the file ``result.svg``:

    .. code-block:: bash

        python __main__.py --text "$x \in \mathbb{R}$" --preamble-file "my_preamble.tex" --scale-factor 2.0 --output result.svg empty.svg

- Take ``nonempty.svg``, compile the code ``$x \in \mathbb{R}$`` using the preamble
  ``my_preamble.tex``. Then, replace the |TexText| object the XML id attribute
  of which has the value ``7`` by the compiled result in such a way that the
  center of the new object matches the center of the old object. Write the
  result into the file ``result.svg``:

    .. code-block:: bash

        python __main__.py --id 7 --text "$x \in \mathbb{R}$" --preamble-file "my_preamble.tex" --alignment "middle center" --output result.svg empty.svg

- Recompile all |TexText| objects in ``nonempty.svg`` and write the result into
  ``result.svg``:

    .. code-block:: bash

        python __main__.py --recompile-all-entries --output result.svg nonempty.svg
