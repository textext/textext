.. |TexText| replace:: **TexText**

.. role:: bash(code)
   :language: bash
   :class: highlight

.. role:: latex(code)
   :language: latex
   :class: highlight

.. _troubleshooting:

Troubleshooting
---------------

There are three main reasons why something may went wrong:

1. Your LaTeX code contains invalid commands or syntax errors

2. The installed toolchain for the conversion of your code to a valid SVG element
   is for some reason broken.

3. |TexText| contains a bug and you are the person who discovers it!

|TexText| helps you to resolve such issues by offering detailed error and logging information.

.. contents:: :local:

LaTeX and toolchain errors
~~~~~~~~~~~~~~~~~~~~~~~~~~

If compilation of your LaTeX code fails |TexText| opens a dialog displaying the
cause of the failure. In most cases a syntax error in your code will be the reason.
|TexText| filters the relevant information from the compiler output and displays
it:

.. figure:: ../images/textext-error-dialog-simple.png
   :scale: 50 %
   :alt: Simple error dialog

If you would like to see the full output of the LaTeX processor, click on the ``+``
left to te ``stdout`` label:

.. figure:: ../images/textext-error-dialog-stdout.png
   :scale: 50 %
   :alt: Error dialog with stdout

Sometimes nothing meaningful can be stripped from the LaTeX processor output, or
nothing has been produced by LaTeX which can be parsed by |TexText|:

.. figure:: ../images/textext-error-dialog-empty.png
   :scale: 50 %
   :alt: empty error dialog

Most likely something serious failed during compilation and you may find additional
information under ``stderr``.

.. figure:: ../images/textext-error-dialog-stderr.png
   :scale: 50 %
   :alt: Error dialog with stderr

.. important::
   The ``stderr`` option is only available when errors have been piped by the
   failed command.

Bugs in |TexText|
~~~~~~~~~~~~~~~~~

Of course, |TexText| may contain bugs which may crash the plugin. If this happens
an Inkscape error dialog is opened that will show something like this:

.. figure:: ../images/textext-error-dialog-python-error-1.png
    :scale: 50 %
    :alt: Error dialog after failed execution

Note the advice at the end of the text view: You should run the extension again.
Then, a logging mechanism is started which writes its result into the Inkscape
error dialog:

.. figure:: ../images/textext-error-dialog-python-error-2.png
    :scale: 50 %
    :alt: Error dialog after failed execution, second run

You can use this information to further analyze the problem or to
open an issue on GitHub asking for help: https://github.com/textext/textext/issues/new

.. important::
    Please carefully read the instructions in the issue template on GitHub so you
    pass all the required information to the developer team.