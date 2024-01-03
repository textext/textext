"""
This file is part of TexText, an extension for the vector
illustration program Inkscape.

Copyright (c) 2006-2023 TexText developers.

TexText is released under the 3-Clause BSD license. See
file LICENSE.txt or go to https://github.com/textext/textext
for full license details.
"""
import os
import platform
import subprocess
from typing import List
from utils.errors import TexTextCommandNotFound, TexTextCommandFailed, TexTextConversionError
from utils.log_util import logger
from utils.texoutparse import LatexLogParser


class TexToPdfConverter:
    """ Class which provides methods for the conversion from tex -> pdf -> svg

    Takes some TexText metadata, compiles the code and produces a svg or png
    file from it.

    This is the most sensitive part of TexText. Hence, we need a lot of error
    handling and logging here.

    """

    DEFAULT_DOCUMENT_CLASS = r"\documentclass{article}"
    DOCUMENT_TEMPLATE = r"""
    {0}
    \pagestyle{{empty}}
    \begin{{document}}
    {1}
    \end{{document}}
    """
    LATEX_OPTIONS = ['-interaction=nonstopmode',
                     '-halt-on-error']

    def __init__(self, inkscape_exe: str, latex_exe: str):
        """ Instantiates the converter

        :param inkscape_exe: The full path to the inkscape executable used for
                             conversion from pdf to svg / png
        :param latex_exe: The full path to the tex executable used for compilation
                          of the tex code.
        """
        self.tmp_base = 'tmp'
        self._inkscape_exe = inkscape_exe
        self._latex_exe = latex_exe

    def tex_to_pdf(self, latex_text: str, preamble_file: str):
        """ Create a PDF file from latex text.

        :param latex_text: The text to be compiled
        :param preamble_file: Full path to preamble file. If the preamble file does not exist
                              DEFAULT_DOCUMENT_CLASS is inserted before latex_text.

        :raises: TexTextConversionError
        """
        with logger.debug("Converting .tex to .pdf"):
            # Read preamble
            preamble = ""
            if os.path.isfile(preamble_file):
                with open(preamble_file, 'r', encoding="utf-8") as f_handle:
                    logger.debug(f"Reading preamble file {preamble_file}")
                    preamble += f_handle.read()
            else:
                logger.debug(f"Preamble file {preamble_file} not found.")

            # Add default document class to preamble if there is no one
            # (by purpose or if preamble_file does not exist)
            if not self._contains_document_class(preamble):
                logger.debug("Using default document class.")
                preamble = self.DEFAULT_DOCUMENT_CLASS + preamble

            # Options pass to LaTeX-related commands
            texwrapper = self.DOCUMENT_TEMPLATE.format(preamble, latex_text)

            # Write tex
            with open(self.tmp('tex'), mode='w', encoding='utf-8') as f_tex:
                f_tex.write(texwrapper)

            # Exec tex_command: tex -> pdf
            try:
                cmd = [self._latex_exe, self.tmp('tex')] + self.LATEX_OPTIONS
                with logger.debug(f"Calling {cmd} in {os.getcwd()}..."):
                    self._exec_command(cmd)
            except (TexTextCommandFailed, TexTextCommandNotFound) as error:
                if os.path.exists(self.tmp('log')):
                    logger.debug(f"TeX-compilation failed, parsing log file {self.tmp('log')}...")
                    parsed_log = self._parse_pdf_log()
                    raise TexTextConversionError(parsed_log, error.return_code, error.stdout, error.stderr) from error
                logger.debug(f"TeX-compilation failed, no log file found!")
                raise TexTextConversionError(str(error), error.return_code, error.stdout, error.stderr) from error

            if not os.path.exists(self.tmp('pdf')):
                raise TexTextConversionError(f"{self._latex_exe} didn't produce output {self.tmp('pdf')}")

    def pdf_to_svg(self):
        """ Convert the PDF file into an SVG file.

        :raises: TexTextConversionError
        """
        cmd = [self._inkscape_exe,
               "--pdf-poppler",
               "--pages=1",
               "--export-type=svg",
               "--export-text-to-path",
               "--export-area-drawing",
               "--export-filename",
               self.tmp('svg'),
               self.tmp('pdf')]
        with logger.debug(f"Calling {cmd} in {os.getcwd()}..."):
            try:
                self._exec_command(cmd)
            except (TexTextCommandNotFound, TexTextCommandFailed) as error:
                logger.debug(f"pdf -> svg conversion failed. Reason: {str(error)}!")
                raise TexTextConversionError(str(error), error.return_code, error.stdout, error.stderr) from error

    def pdf_to_png(self, white_bg: bool):
        """Convert the PDF file to a SVG file

        :param white_bg: If the png should have a white background instead of
                         a transparent one.

        :raises: TexTextConversionError
        """
        cmd = [
            self._inkscape_exe,
            "--pdf-poppler",
            "--pages=1",
            "--export-type=png",
            "--export-area-drawing",
            "--export-dpi=300",
            "--export-filename",
            self.tmp('png'),
            self.tmp('pdf')
        ]

        if white_bg:
            cmd.extend([
                "--export-background=#FFFFFF",
                "--export-background-opacity=1.0"
            ])

        with logger.debug(f"Calling {cmd} in {os.getcwd()}..."):
            try:
                self._exec_command(cmd)
            except (TexTextCommandNotFound, TexTextCommandFailed) as error:
                logger.debug(f"pdf -> png conversion failed. Reason: {str(error)}!")
                raise TexTextConversionError(str(error), error.return_code, error.stdout, error.stderr) from error

    def stroke_to_path(self):
        """ Convert stroke elements to path elements for easier colorization and scaling in Inkscape

        E.g. $\\overline x$ -> the line above x is converted from stroke to path
        """
        try:
            self._exec_command([
                self._inkscape_exe,
                "-g",
                "--batch-process",
                f"--actions=EditSelectAll;StrokeToPath;export-filename:{self.tmp('svg')};export-do;EditUndo;FileClose",
                self.tmp('svg')
            ]
            )
        except (TexTextCommandNotFound, TexTextCommandFailed):
            pass

    def tmp(self, ext: str) -> str:
        """ Returns temporary base filename plus file ext

        :param ext: The extension added to the file name.

        :return: str
        """
        return self.tmp_base + '.' + ext

    @staticmethod
    def _contains_document_class(preamble: str):
        """Return True if `preamble` contains a documentclass-like command.

        :param preamble: A string holding the content of the preamble.

        Also, checks and considers if the command is commented out or not.
        """
        lines = preamble.split("\n")
        document_commands = [r"\documentclass{", r"\documentclass[",
                             r"\documentstyle{", r"\documentstyle["]
        for line in lines:
            for document_command in document_commands:
                if document_command in line and "%" not in line.split(document_command)[0]:
                    return True
        return False

    def _parse_pdf_log(self) -> str:
        """ Strip down tex output to only the first error etc. discard all the noise

        :return: string containing the error message and some context lines after it
        ToDo: Re-think exception catching (specific exceptions?)
        """
        with logger.debug("Parsing LaTeX log file"):
            parser = LatexLogParser()

            # noinspection PyBroadException
            try:
                with open(self.tmp('log'), mode='r', encoding='utf8') as f_handle:
                    parser.process(f_handle)
                return parser.errors[0]
            except Exception:  # pylint: disable=broad-except
                return "TeX compilation failed. See stdout output for more details"

    @staticmethod
    def _exec_command(cmd: List[str], ok_return_value: int = 0) -> bytes:
        """
        Run given command, check return value, and return
        concatenated stdout and stderr.
        :param cmd: Command to execute (as a list of tokens)
        :param ok_return_value: The expected return value after successful completion
        :raises: TexTextCommandNotFound, TexTextCommandFailed
        """

        try:
            # hides the command window for cli tools that are run (in Windows)
            info = None
            if platform.system() == "Windows":
                info = subprocess.STARTUPINFO()
                info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                info.wShowWindow = subprocess.SW_HIDE
            with subprocess.Popen(cmd,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE,
                                  stdin=subprocess.PIPE,
                                  startupinfo=info) as proc:
                out, err = proc.communicate()

        except OSError as err:
            raise TexTextCommandNotFound(f"Command {' '.join(cmd)} failed: {err}.\n"
                                         f"Ensure that {cmd[0]} is correct or in the system path!") from err

        if ok_return_value is not None and proc.returncode != ok_return_value:
            raise TexTextCommandFailed(message=f"Command {' '.join(cmd)} failed (code {proc.returncode})",
                                       return_code=proc.returncode,
                                       stdout=out,
                                       stderr=err)
        return out + err
