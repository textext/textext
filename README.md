[![Build Status](https://travis-ci.com/textext/textext.svg?branch=develop)](https://travis-ci.com/textext/textext)

# TexText - A LaTeX/ XeLaTex/ LuaLaTex extension for Inkscape (releases 0.92, 0.91 and 0.48)

TexText is a Python plugin for the vector graphics editor [Inkscape](http://www.inkscape.org/) providing the possibility to add LaTeX generated SVG elements to your drawing.

![TexText dialog with Inkscape](docs/wiki-resources/textext-with-inkscape.png)

## Key features

- Multi-line editor, optionally with syntax highlighting
- Compatibility with TexText down to version 0.4.x
- Compilation of TeX code using PdfLaTeX, XeLaTeX or LuaLaTex
- Free scaling of the produced output either by dragging with the mouse in Inkscape or by setting a scale factor manually in the TexText GUI. Both approaches are compatible to each other. Scaling is kept after re-editing the code or can be adjusted later.
- Possibility of exact font size matching with Inkscape text
- TeX preamble file can be freely configured (additional packages, parskip, parindent, etc.)
- Colorization of the produced output via TeX commands or directly by Inkscape. Colorization is kept after re-editing the TeX code.
- It is possible to specify the alignment anchor of the produced output. By this it is possible to fix e.g. the top left corner of the produced svg output from compilation to compilation.
-   TeXText uses either pdf2svg or pstoedit+ghostscript as converter for producing svg code from the generated pdf.

## Download

See [TexText release area](https://github.com/textext/textext/releases) on GitHub for the latest release.

## Installation and usage

Detailed information about **installation** and **usage** can be found in the [Wiki](https://github.com/textext/textext/wiki).

## History

This repository continues the development of the plugin which took place at [https://bitbucket.org/pitgarbe/textext](https://bitbucket.org/pitgarbe/textext) until January 2018. Originally, TexText had been developed by [Pauli Virtanen](http://www.iki.fi/pav/software/textext/) based on the plugin InkLaTeX written by Toru Araki.
