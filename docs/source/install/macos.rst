.. |TexText| replace:: **TexText for Inkscape 1.x**
.. |Inkscape| replace:: **Inkscape 1.x**
.. |InkscapeOld| replace:: **Inkscape 0.92.x**


.. role:: bash(code)
   :language: bash
   :class: highlight

.. role:: latex(code)
   :language: latex
   :class: highlight

.. _macos-install:

==================
|TexText| on MacOS
==================

.. _macos-install-preparation:

.. attention::
   Inkscape for MacOS is shipped as a :bash:`dmg`-file from the Inkscape
   website. However, on some systems the extensions and Python subsystem
   shipped together with this installer seems to be broken. This is a problem
   of Inkscape development, not of |TexText|. Hence, two
   alternative approaches are shown here together with some steps how to
   setup a Python installation which works together with the Inkscape extension
   system.

   Help us and other MacOS users by posting an
   `issue on github <https://github.com/textext/textext/issues/new/choose>`_
   if something goes wrong or you have ideas how to improve the procedure!

Method 1: Use Inkscape DMG installer (optionally together with Homebrew Python)
-------------------------------------------------------------------------------

1. Install Inkscape: Download the installer from the
   `Inkscape download site <https://inkscape.org/release>`_.

2. Install Inkscape. Verify that Inkscape launches and is of version
   1.x.

3. Download the most recent package of |TexText| from
   :textext_current_release_page:`GitHub release page <release>`
   (direct link: :textext_download_zip:`.zip <MacOS>`)

   Extract the package and change into the created directory.

4. Next we try to install and run |TexText|. If the installation or the launch
   of |TexText| fails a method is shown how to fix the problem.

   Run:

   .. code-block:: bash

        python3 setup.py --pdflatex-executable=$(which pdflatex) --skip-requirements-check

   or

   .. code-block:: bash

        python setup.py --pdflatex-executable=$(which pdflatex) --skip-requirements-check

   The script  will copy the required files into the user's Inkscape
   configuration directory (usually this is ``~/Library/Application Support/org.inkscape.Inkscape/config/inkscape/extensions``)

   See :ref:`advanced-install` for further options provided by
   :bash:`setup.py`.

5. Launch Inkscape and try to run |TexText| (Consult the :ref:`usage instructions <gui>`).
   If |TexText| fails to launch go to step 6. Otherwise you are done.

6. The Python installation shipped together with Inkscape seems to be broken. Hence,
   we need to install one manually. Assuming you have Homebrew installed, install
   Python 3.9:

   .. code-block:: bash

        brew install python@3.9

7. Then install the Tkinter GUI-library, NumPy and PyGObject:

   .. code-block:: bash

        brew install python-tk@3.9
        brew install numpy
        brew install pygobject3

8. Install the lxml-tools required by the Inkscape extensions:

   .. code-block:: bash

        $(brew --prefix)/opt/python@3.9/libexec/bin/pip install lxml


9. Determine the path of the Homebrew python3 executable:

   .. code-block:: bash

        which $(brew --prefix)/opt/python@3.9/libexec/bin/python3


10. Navigate into the directory
    :bash:`/Users/<your username>/Library/Application Support/org.inkscape.Inkscape/config/inkscape`.
    (Replace <your username> by your MacOS user name)

11. Open the file :bash:`preferences.xml` and navigate to the line that says
    :bash:`id="extensions"`. Add a line :bash:`python-interpreter="<python path>"`
    where :bash:`<python path>` has to be replaced by the path determined in step 9.
    After this operation the entry should look like this:

    .. code-block:: xml

        <group
            id="extensions"
            python-interpreter="<python path>"
        />

12. If the installation of |TexText| in step 4 failed try to install it with the
    following command, otherwise go to step 13:

    .. code-block:: bash

        $(brew --prefix)/opt/python@3.9/libexec/bin/python3 setup.py --pdflatex-executable=$(which pdflatex) --skip-requirements-check

13. Launch Inkscape and try to run |TexText|. In case of success you should see at least
    the Tkinter GUI which is a simplified version of the GTK gui described in the
    :ref:`usage instructions <gui>`.

.. note::

    In case of installation problems refer to the :ref:`trouble_installation` in the :ref:`troubleshooting` section!
    If this still does not help open an `issue on github <https://github.com/textext/textext/issues/new/choose>`_.
    However, please note the the TexText-maintainers do not have access to a MacOS system. So
    we need your direct cooperation to improve the installation instructions.


Method 2: Use Homebrew Inkscape
-------------------------------

Preparation
===========

1. Install inkscape

   .. code-block:: bash

        brew install --cask inkscape

   Verify that inkscape launches and is of version >= 1.x.

.. _macos-install-textext:

Download and install |TexText|
==============================

1. Download the most recent package from :textext_current_release_page:`GitHub release page <release>`
   (direct link: :textext_download_zip:`.zip <MacOS>`)

2. Extract the package and change into the created directory.

3. Run:

   .. code-block:: bash

        python3 setup.py --pdflatex-executable=$(which pdflatex) --skip-requirements-check

   or

   .. code-block:: bash

        python setup.py --pdflatex-executable=$(which pdflatex) --skip-requirements-check

   The script  will copy the required files into the user's Inkscape
   configuration directory (usually this is ``~/Library/Application Support/org.inkscape.Inkscape/config/inkscape/extensions``)

   If installation fails or TexText does not launch proceed with step 6 in method 1.

See :ref:`advanced-install` for further options provided by
:bash:`setup.py`.

Now you can consult the :ref:`usage instructions <gui>`.
