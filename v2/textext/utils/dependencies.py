"""
This file is part of TexText, an extension for the vector
illustration program Inkscape.

Copyright (c) 2006-2022 TexText developers.

TexText is released under the 3-Clause BSD license. See
file LICENSE.txt or go to https://github.com/textext/textext
for full license details.

Provides the class DependencyCheck which can be used to check
if all TexText dependencies are met.
"""
import os
import re
import subprocess
import sys
from typing import Tuple, Union

from .log_util import NestedLoggingGuard
from .environment import system_env


class DependencyCheck:

    INKSCAPE_MAJOR_MIN = 1
    INKSCAPE_MINOR_MIN = 2

    def __init__(self, logger: NestedLoggingGuard):
        """

        Args:
            logger (NestedLoggingGuard): The _logger object receiving the log messages
        """
        super().__init__()
        self._logger = logger

    def detect_inkscape(self, inkscape_exe_path: str = None) -> str:
        exe_path = ""
        inkscape_exe_path = self.detect_executable("inkscape", inkscape_exe_path)
        if inkscape_exe_path and self.check_inkscape_version(inkscape_exe_path):
            exe_path = inkscape_exe_path
        return exe_path

    def detect_pdflatex(self, pdflatex_exe_path: str = None) -> str:
        return self.detect_executable("pdflatex", pdflatex_exe_path)

    def detect_xelatex(self, xelatex_exe_path: str = None) -> str:
        return self.detect_executable("xelatex", xelatex_exe_path)

    def detect_lualatex(self, lualatex_exe_path: str = None) -> str:
        return self.detect_executable("lualatex", lualatex_exe_path)

    def check(self, inkscape_exe_path, pdflatex_exe_path, lualatex_exe_path, xelatex_exe_path) -> \
            Union[Tuple[str, str, str, str], None]:
        with self._logger.info("Checking TexText dependencies..."):
            inkscape_exe_path = self.detect_inkscape(inkscape_exe_path)
            gtk_available = self.detect_pygtk3()
            tkinter_available = self.detect_tkinter()
            pdflatex_exe_path = self.detect_pdflatex(pdflatex_exe_path)
            lualatex_exe_path = self.detect_lualatex(lualatex_exe_path)
            xelatex_exe_path = self.detect_xelatex(xelatex_exe_path)

            if inkscape_exe_path and (pdflatex_exe_path or lualatex_exe_path or xelatex_exe_path) and (
                    gtk_available or tkinter_available):
                self._logger.info("All requirements fulfilled!")
                return inkscape_exe_path, pdflatex_exe_path, lualatex_exe_path, xelatex_exe_path
            self._logger.critical("Not all requirements are fulfilled!")
            return None

    def detect_executable(self, prog_name: str, exe_path: str = None) -> str:
        """
        Tries to find an executable at a given location or in the system oath

        Args:
            prog_name (str): The name of the program (key in
                system_env.executable_names (e.g. "inkscape")
            exe_path (str, optional): The path of the executable to
                check. If None, the executable will be searched in the system
                path

        Returns:
            The absolute path of the executable as a string if the executable has been
            found at the specified location or in the system path, otherwise an empty
            string.

        """
        if exe_path:
            with self._logger.info(f"Checking for {prog_name} at given path `{exe_path}`..."):
                if self.check_executable(prog_name, exe_path):
                    self._logger.info(f"{prog_name} is found at `{exe_path}`")
                    return exe_path
                self._logger.error(f"{prog_name} is NOT found at `{exe_path}`.")
                return ""
        else:
            with self._logger.info(f"Trying to find {prog_name} in system path..."):
                found_path = self.find_executable_in_path(prog_name)
                if found_path:
                    self._logger.info(f"{prog_name} is found at `{found_path}`")
                else:
                    self._logger.error(f"{prog_name} is NOT found in system path!")
                return found_path

    def check_executable(self, prog_name: str, exe_path: str) -> bool:
        """
        Checks if specified file exists and is executable.

        Args:
            prog_name (str): The name of the program (e.g. "inkscape", used for logging only)
            exe_path (str): Full path to the executable (e.g. "/usr/bin/inkscape")

        Returns:
            True if the file exists and is executable, otherwise False.

        """
        with self._logger.debug(f"Checking `{prog_name}-executable` = `{exe_path}`..."):
            if os.path.isfile(exe_path) and os.access(exe_path, os.X_OK):
                self._logger.debug(f"{prog_name} is found at `{exe_path}`")
                return True
            self._logger.debug(f"Bad `{prog_name}` executable: `{exe_path}`")
            return False

    def find_executable_in_path(self, prog_name: str) -> str:
        """
        Tries to find an executable of a program in the system path.

        Args:
            prog_name (str): The name of the program (key in system_env.executable_names
                (e.g. "inkscape")

        Returns:
            The absolute path to the executable if it has been found, otherwise an empty string.
        """
        with self._logger.debug(f"Start searching {prog_name} in system path..."):
            for exe_name in system_env.executable_names[prog_name]:
                for path in system_env.system_path:
                    full_path_guess = os.path.join(path, exe_name)
                    with self._logger.debug(f"Looking for `{exe_name}` in `{path}`"):
                        if self.check_executable(prog_name, full_path_guess):
                            self._logger.debug(f"`{exe_name}` is found at `{path}`")
                            return full_path_guess

                self._logger.warning(f"`{exe_name}` is NOT found in PATH")
            return ""

    def check_inkscape_version(self, exe_path: str) -> bool:
        with self._logger.info("Checking Inkscape version..."):
            try:
                stdout, _ = system_env.call_command([exe_path, "--version"])
            except OSError:
                self._logger.critical("Inkscape version command failed!")
                return False

            for stdout_line in stdout.decode("utf-8", 'ignore').split("\n"):
                match = re.search(r"Inkscape ((\d+)\.(\d+)[-\w]*)", stdout_line)

                if match:
                    found_version, major, minor = match.groups()
                    if int(major) >= self.INKSCAPE_MAJOR_MIN and int(minor) >= self.INKSCAPE_MINOR_MIN:
                        self._logger.info(f"Inkscape={found_version} is found at {exe_path}")
                        return True
                    self._logger.error(f"Inkscape>={self.INKSCAPE_MAJOR_MIN}.{self.INKSCAPE_MINOR_MIN} "
                                       f"is not found (but inkscape={found_version} is found)")
                    return False

            self._logger.error("can't determinate inkscape version!")
            return False

    def detect_pygtk3(self) -> bool:
        self._logger.info("Checking for GTK3...")

        executable = sys.executable
        try:
            system_env.call_command([executable, "-c", "import gi;" +
                                     "gi.require_version('Gtk', '3.0');" +
                                     "from gi.repository import Gtk, Gdk, GdkPixbuf"])
        except (KeyError, OSError, subprocess.CalledProcessError):
            self._logger.warning("GTK3 is not found")
            return False

        self._logger.info("GTK3 is found")
        return True

    def detect_tkinter(self) -> bool:
        self._logger.info("Checking for Tkinter...")

        executable = sys.executable
        try:
            system_env.call_command([executable, "-c",
                                     "import tkinter; import tkinter.messagebox; import tkinter.filedialog;"])
        except (KeyError, OSError, subprocess.CalledProcessError):
            self._logger.critical("TkInter is not found")
            return False

        self._logger.info("TkInter is found")
        return True
