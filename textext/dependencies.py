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

from .log_util_new import NestedLoggingGuard
from .environment import system_env


class DependencyCheck(object):

    INKSCAPE_MAJOR_MIN = 1
    INKSCAPE_MINOR_MIN = 2

    def __init__(self, logger: NestedLoggingGuard):
        """

        Args:
            logger (NestedLoggingGuard): The _logger object receiving the log messages
        """
        super(DependencyCheck, self).__init__()
        self._logger = logger

    def detect_inkscape(self, inkscape_exe_path: str = None, no_path_check: bool = False) -> str:
        exe_path = ""
        inkscape_exe_path = self.detect_executable("inkscape", inkscape_exe_path, no_path_check)
        if inkscape_exe_path and self.check_inkscape_version(inkscape_exe_path):
            exe_path = inkscape_exe_path
        return exe_path

    def detect_pdflatex(self, pdflatex_exe_path: str = None, no_path_check: bool = False) -> str:
        return self.detect_executable("pdflatex", pdflatex_exe_path, no_path_check)

    def detect_xelatex(self, xelatex_exe_path: str = None, no_path_check: bool = False) -> str:
        return self.detect_executable("xelatex", xelatex_exe_path, no_path_check)

    def detect_lualatex(self, lualatex_exe_path: str = None, no_path_check: bool = False) -> str:
        return self.detect_executable("lualatex", lualatex_exe_path, no_path_check)

    def check(self, inkscape_exe_path, pdflatex_exe_path, lualatex_exe_path, xelatex_exe_path):
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
            else:
                self._logger.critical("Not all requirements are fulfilled!")
                return None

    def detect_executable(self, prog_name: str, exe_path: str = None, no_path_check: bool = False) -> str:
        """
        Tries to find an executable at given location or/ and in system oath

        This method tries to locate an executable of a program in the system path.
        Additionally, it offers the possibility to check the existance of the
        executable at a specified location.

        Args:
            prog_name (str): The name of the program. It is used as a key
                in the executable_names property of the system_env object
                imported from the environment module (e.g. "inkscape")
            exe_path (str, optional): The guessed path of the executable (e.g.
                "C:\\Program Files\\Inkscape\\bin\\inkscape.exe")
            no_path_check (bool): Set this to True if you would like to avoid the
                automatic check in the system path if the specified path in
                exe_path is not valid.

        Returns:
            The absolute path of the executable as a string if the executable has been
            found at the specified location or in the system path, otherwise an empty
            string.

        """
        with self._logger.info("Trying to detect executbale of {0}...".format(prog_name)):
            if exe_path:
                with self._logger.info("Checking for {0} at given path `{1}`...".format(prog_name, exe_path)):
                    if self.check_executable(prog_name, exe_path):
                        self._logger.info("{0} is found at `{1}`".format(prog_name, exe_path))
                        return exe_path
                    else:
                        if no_path_check:
                            self._logger.error("{0} is NOT found at `{1}`.".format(prog_name, exe_path))
                            return ""
                        else:
                            self._logger.warning("{0} is NOT found at `{1}`, trying to find in system path now...".
                                                 format(prog_name, exe_path))

            with self._logger.info("Trying to find {0} in system path...".format(prog_name)):
                found_path = self.find_executable_in_path(prog_name)
                if found_path:
                    self._logger.info("{0} is found at `{1}`".format(prog_name, found_path))
                else:
                    self._logger.error("{0} is NOT found in system path!".format(prog_name))
                return found_path

    def check_executable(self, prog_name: str, exe_path: str) -> bool:
        """
        Checks if specified file exists and is executable. Corresponding messages
        will be written into the logfile.

        Args:
            prog_name (str): The name of the program (e.g. "inkscape", used for logging only)
            exe_path (str): Full path to the executable (e.g. "/usr/bin/inkscape")

        Returns:
            True if the file exists and is executable, otherwise False.

        """
        with self._logger.debug("Checking `{0}-executable` = `{1}`...".format(prog_name, exe_path)):
            if os.path.isfile(exe_path) and os.access(exe_path, os.X_OK):
                self._logger.debug("{0} is found at `{1}`".format(prog_name, exe_path))
                return True
            else:
                self._logger.debug("Bad `{0}` executable: `{1}`".format(prog_name, exe_path))
                return False

    def find_executable_in_path(self, prog_name: str) -> str:
        """
        Tries to find an executable of a program in the system path. Corresponding messages
        are written into the logfile

        Args:
            prog_name (str): The name of the program. It is used as a key in the executable_names
                property of the system_env object imported from the environment module

        Returns:
            The absolute path to the executable if it has been found, otherwise an empty string.
        """
        with self._logger.debug("Start searching {0} in system path...".format(prog_name)):
            for exe_name in system_env.executable_names[prog_name]:
                for path in system_env.get_system_path():
                    full_path_guess = os.path.join(path, exe_name)
                    with self._logger.debug("Looking for `{0}` in `{1}`".format(exe_name, path)):
                        if self.check_executable(prog_name, full_path_guess):
                            self._logger.debug("`{0}` is found at `{1}`".format(exe_name, path))
                            return full_path_guess

                self._logger.warning("`{0}` is NOT found in PATH".format(exe_name))
            return ""

    def check_inkscape_version(self, exe_path: str) -> bool:
        with self._logger.info("Checking Inkscape version..."):
            try:
                stdout, stderr = system_env.call_command([exe_path, "--version"])
            except OSError:
                self._logger.critical("Inkscape version command failed!")
                return False

            for stdout_line in stdout.decode("utf-8", 'ignore').split("\n"):
                m = re.search(r"Inkscape ((\d+)\.(\d+)[-\w]*)", stdout_line)

                if m:
                    found_version, major, minor = m.groups()
                    if int(major) >= self.INKSCAPE_MAJOR_MIN and int(minor) >= self.INKSCAPE_MINOR_MIN:
                        self._logger.info("Inkscape={0} is found at {1}".format(found_version, exe_path))
                        return True
                    else:
                        self._logger.error("Inkscape>={0}.{1} is not found (but inkscape={2} is found)".
                                           format(self.INKSCAPE_MAJOR_MIN, self.INKSCAPE_MINOR_MIN, found_version))
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
