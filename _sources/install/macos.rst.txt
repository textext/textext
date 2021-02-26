.. |TexText| replace:: **TexText for Inkscape 1.0**
.. |Inkscape| replace:: **Inkscape 1.0**
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

   This is highly experimental. Help us and other MacOS users by posting an
   `issue on github <https://github.com/textext/textext/issues/new/choose>`_
   if something goes wrong or you have ideas how to improve the procedure!

Preparation
===========

1. Install inkscape

   .. code-block:: bash

        brew cask install inkscape

   Verify that inkscape launches and is of version >= 1.x.

.. _macos-install-textext:

Download and install |TexText|
==============================

.. important::

   Compared to previous versions |TexText| does not need any conversion utilities like
   ghostscript, pstoedit or pdfsvg.

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
   configuration directory (usually this is ``~/.config/inkscape/extensions``)

.. note::

    In case of installation problems refer to the :ref:`trouble_installation` in the :ref:`troubleshooting` section!


You are done. Now you can consult the :ref:`usage instructions <gui>`.
