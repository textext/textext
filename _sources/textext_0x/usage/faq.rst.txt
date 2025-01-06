.. |TexText| replace:: **TexText 0.11**

.. role:: bash(code)
   :language: bash
   :class: highlight

.. role:: latex(code)
   :language: latex
   :class: highlight

.. _tt0x-faq:

Frequently Asked Questions (FAQ, TexText 0.11)
----------------------------------------------

.. contents:: :local:

.. _tt0x-faq-font-size:

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

.. _tt0x-faq-font-custom-font:

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
   preamble files and load them dependent on your node, see :ref:`tt0x-usage-dialog-overview`.


.. _tt0x-faq-utf8:

Using special characters like German Umlaute (äüö) etc.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you want to use special characters which are not understood by plain LaTeX
in your nodes you have two options:

1. Include the directive ``\usepackage[utf-8]{inputenc}`` in the preamble file,
   see :ref:`tt0x-usage-preamble-file`.

2. Use ``xelatex`` or ``lualatex`` as TeX command, see :ref:`tt0x-usage-tex-compilers`.

.. _tt0x-faq-old-inkscape:

Using TexText with older Inkscape versions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. _inkscape-0.48.x-0.91.x-multi: https://github.com/textext/pygtk-for-inkscape-windows/releases/download/0.48%2B0.91/Install-PyGTK-2.24-Inkscape-0.48+0.91.exe

Unfortunately the current |TexText| release does not work with Inkscape versions 0.91.x
and 0.48.x, at least under Windows. The reason is the underlying Python interpreter
which must be of version 2.7. If you need to work with an older Inkscape version you are
encouraged to use |TexText| 0.8.x. You can download it from here
https://github.com/textext/textext/releases .

These are the required PyGTK-Packages (Windows):

 - Inkscape 0.48.x - 0.91.x (`32-bit and 64-bit <inkscape-0.48.x-0.91.x-multi_>`_)

Installation instructions:

 - https://github.com/textext/textext/wiki/Installation-instructions

.. note::
    If you manage to run Inkscape < 0.92 with Python 2.7 you can use the most recent
    version of |TexText|.


Extension not shown in the Inkscape Extension menu
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If the the |TexText| entry is not shown in the ``Extension`` menu of Inkscape proceed with
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

        setup_win.bat /p:"--inkscape-extensions-path 'C:\Path\to your extensions'"

   Alternatively you can select the correct directory in the GUI installer.

Windows with MiKTeX: Compilation fails with empty error dialog
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If the compilation of your LaTeX code fails with an empty error dialog and the expanded
view of ``stderr`` (see :ref:`tt0x-trouble_latex`) shows an entry like

.. code-block:: bash

    Sorry, but pdflatex.exe did not succeed.

    The log file hopefully contains the information to get MiKTeX going again:

the most likely reason is that MiKTeX tries to install a package on the fly and fails to
do so. Manually compile your code as described in :ref:`tt0x-trouble_manual_compile`. Then
you will see what goes wrong so you can fix it. See also the warning in :ref:`tt0x-windows-install-latex`.

.. _tt0x-faq-set-inskscape-python-interpreter-to-python2:

Set Inkscape python interpreter to Python2
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Inkscape by default uses ``python`` executable to run python extension. On recent systems ``python`` defaults to be ``python3``.
To run |TexText| you need to change inkscape `python-interpreter` to ``python2``:

..
    The steps are taken from
    http://wiki.inkscape.org/wiki/index.php/Extension_Interpreters#Selecting_a_specific_interpreter_version_.28via_preferences_file.29


1. Quit all running Inkscape processes

2. Open your ``perferences.xml`` file with a text editor (usually ``~/.config/inkscape/preferences.xml``)

   .. note::

        Find the exact location of preference file by going to :kbd:`Edit|Preferences|System|User Preferences`

3. Search the group which holds settings for the extension system itself and options of various extensions:

   .. code-block:: xml

      <group
         id="extensions"

         org.ekips.filter.gears.teeth="24"
         org.ekips.filter.gears.pitch="20"
         org.ekips.filter.gears.angle="20" />

4. Insert a key for the interpreter, for example ``python-interpreter`` for setting the program that should be used to
   run python extensions, and set the string to the absolute path to the python binary which is compatible with Inkscape's
   current extension scripts (in the example below, the path is ``/usr/bin/python2.7``, you can determine it in a
   terminal via the command ``which python2.7`` or ``which python2``):

    .. code-block:: xml

       <group
          id="extensions"
          python-interpreter="/usr/bin/python2.7"

          org.ekips.filter.gears.teeth="24"
          org.ekips.filter.gears.pitch="20"
          org.ekips.filter.gears.angle="20" />
