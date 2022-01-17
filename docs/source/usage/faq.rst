.. |TexText| replace:: **TexText**

.. role:: bash(code)
   :language: bash
   :class: highlight

.. role:: latex(code)
   :language: latex
   :class: highlight

.. _faq:

Frequently Asked Questions (FAQ)
--------------------------------

.. contents:: :local:

.. _define-keyboard-shortcut:

Defining keyboard shortcut for opening |TexText| dialog
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. In Inkscape open :bash:`Edit` -> :bash:`Preferences` ->
   :bash:`Interface` -> :bash:`Keyboard Shortcuts`

2. Find the |TexText| entry in the :bash:`Extensions` category

3. Within the :bash:`Shortcut` column click next to the |TexText| entry.
   An entry `New accelerator` appears in the :bash:`Shortcut` column.

4. Now type the keyboard shortcut you intend to use, e.g. :bash:`CTRL` + :bash:`T`.
   Inkscape informs you if the shortcut is already in use.

.. _faq-font-size:

Explicit setting of font size
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you want the font size of your compiled LaTeX code to be of a
specific size then you have to do two things:

1. Set the scale factor of the node to 1.0

2. Enter your code as following if you want to have a ``14pt`` sized font
   for the text `This is my Text`\:

.. code-block:: latex

    \fontsize{14pt}{1em}{\selectfont This is my Text.}


The resulting text should be of equal height as if has been typeset directly in Inkscape.

.. figure:: ../images/texttext-fontsize-example.png
   :alt: Font size example

If you want to change the default font size you can do that by specifying it in the
:ref:`usage-preamble-file`.

.. code-block:: latex

    \documentclass[12pt]{article}
    % ***rest of the preamble file***

This is convenient, e.g., if you want to create multiple nodes with the same,
specific font size.

.. _faq-font-custom-font:

Selection of special fonts
~~~~~~~~~~~~~~~~~~~~~~~~~~

Usually your code is typeset in the LaTeX standard fonts. As usual, you
can use commands like :latex:`\textbf{}`, :latex:`\textsf{}` etc. in your code. If
you want to select a special font, e.g. the beloved *Times New Roman*
from MS Word, then proceed as follows:


1. Open the file ``default_packages.tex`` which resides in the extension
   subdirectory (``%USERPROFILE%\AppData\Roaming\Inkscape\extensions\textext`` on Windows,
   ``~/.config/inkscape/extensions/textext`` on Linux) and enter the following
   two lines:

.. code-block:: latex

    \usepackage{fontspec}
    \setmainfont{Times New Roman}

2. Save the file and recompile your node. You can also define different
   preamble files and load them dependent on your node, see :ref:`usage-dialog-overview`.


.. _faq-utf8:

Using special characters like German Umlaute (äüö) etc.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you want to use special characters which are not understood by plain LaTeX
in your nodes you have two options:

1. Include the directive ``\usepackage[utf-8]{inputenc}`` in the preamble file,
   see :ref:`usage-preamble-file`.

2. Use ``xelatex`` or ``lualatex`` as TeX command, see :ref:`usage-tex-compilers`.

.. _faq-old-inkscape:

Using TexText with Inkscape 0.92.x
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Please use |TexText| 0.11.x, see :ref:`tt0x-installation-toc`

Extension not shown in the Inkscape Extension menu
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If the the |TexText| entry is not shown in the ``Extension --> Text`` menu of Inkscape proceed with
the following checks:

1. Make sure that the setup procedure completed successfully. Double check its final output.

2. Launch Inkscape, open the ``Edit`` menu, select ``Preferences``, then select ``System`` in
   the tree-view to the left and check the entry ``User exentsions`` in the right part of
   the window. Its entry should be

   - on Linux/ MacOS: ``/home/[your user name]/.config/inkscape/extensions``

   - on Windows: ``C:\Users\[Your user name]\AppData\Roaming\inkscape\extensions``

   If you use different locations you must run the setup script with the
   ``--inkscape-extensions-path`` option.

   Linux/ MacOS:

   .. code-block:: bash

        python setup.py --inkscape-extensions-path /path/to/your/extensions

   Windows

   .. code-block:: bash

        setup_win.bat --inkscape-extensions-path "C:\Path\to your extensions"

   Alternatively you can select the correct directory in the GUI installer.

Error message "GUI framework cannot be initialized"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The reason for this error might be related to a missing package in your
TeX distribution, see :ref:`faq_missing_packages` just below.
In that case the error message is quite misleading.


.. _faq_missing_packages:

Windows with MiKTeX: Compilation fails with empty error dialog
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If the compilation of your LaTeX code fails with an empty error dialog and the expanded
view of ``stderr`` (see :ref:`trouble_latex`) shows an entry like

.. code-block:: bash

    Sorry, but pdflatex.exe did not succeed.

    The log file hopefully contains the information to get MiKTeX going again:

the most likely reason is that MiKTeX tries to install a package on the fly and fails to
do so. Manually compile your code as described in :ref:`trouble_manual_compile`. Then
you will see what goes wrong so you can fix it. See also the warning in :ref:`windows-install-preparation`.
