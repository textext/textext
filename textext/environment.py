"""
This file is part of TexText, an extension for the vector
illustration program Inkscape.

Copyright (c) 2006-2022 TexText developers.

TexText is released under the 3-Clause BSD license. See
file LICENSE.txt or go to https://github.com/textext/textext
for full license details.

This file provides an system_env object which TexText can query
for information about executable locations, tempdir-paths, executable
names and other stuff. See the AbstractEnvironment class for the
set of available methods. For each of the three operating systems
a class is derived from this abstract base class. Depending on
the OS this module is executed the variable system_env is instanciated
with the correct class.
"""
from abc import ABCMeta, abstractmethod
import subprocess as sp
import sys
import os
import ctypes as ct


class AbstractEnvironment:
    __metaclass__ = ABCMeta

    @property
    @abstractmethod
    def os_name(self):
        pass

    @property
    @abstractmethod
    def console_colors(self):
        pass

    @property
    @abstractmethod
    def executable_names(self):
        pass

    @property
    @abstractmethod
    def inkscape_user_extensions_path(self):
        pass

    def inkscape_system_extensions_path(self, inkscape_exe_path):
        try:
            stdout, _ = self.call_command([inkscape_exe_path, "--system-data-directory"])
            path = os.path.join(stdout.decode("utf-8", 'ignore').rstrip(), "extensions")
            err = None
        except sp.CalledProcessError as excpt:
            path = None
            err = f"Command `{excpt.cmd}` failed, stdout: `{excpt.stdout}`, stderr: `{excpt.stderr}`"
        except UnicodeDecodeError as excpt:
            path = None
            err = excpt.reason

        return [path, err]

    @property
    @abstractmethod
    def textext_config_path(self):
        pass

    @property
    @abstractmethod
    def textext_logfile_path(self):
        pass

    @property
    @abstractmethod
    def system_path(self):
        pass

    @staticmethod
    @abstractmethod
    def call_command(command, return_code=0):
        pass


class LinuxEnvironment(AbstractEnvironment):
    os_name = "linux"
    console_colors = "always"
    executable_names = {"inkscape": ["inkscape"],
                        "pdflatex": ["pdflatex"],
                        "lualatex": ["lualatex"],
                        "xelatex": ["xelatex"]
                        }

    @property
    def inkscape_user_extensions_path(self):
        return os.path.expanduser("~/.config/inkscape/extensions")

    @property
    def textext_config_path(self):
        return os.path.expanduser("~/.config/textext")

    @property
    def textext_logfile_path(self):
        return os.path.expanduser("~/.cache/textext")

    @property
    def system_path(self):
        return os.environ["PATH"].split(os.path.pathsep)

    @staticmethod
    def call_command(command, return_code=0):
        with sp.Popen(command, stdout=sp.PIPE, stderr=sp.PIPE) as proc:
            stdout, stderr = proc.communicate()
        if return_code is not None and proc.returncode != return_code:
            raise sp.CalledProcessError(proc.returncode, command)
        return stdout, stderr


class MacEnvironment(LinuxEnvironment):
    os_name = "macos"
    executable_names = {"inkscape": ["inkscape", "inkscape-bin"],
                        "pdflatex": ["pdflatex"],
                        "lualatex": ["lualatex"],
                        "xelatex": ["xelatex"]
                        }

    @property
    def system_path(self):
        path = ["/Applications/Inkscape.app/Contents/Resources"]
        path += os.environ["PATH"].split(os.path.pathsep)
        return path

    @property
    def inkscape_user_extensions_path(self):
        return os.path.expanduser("~/Library/Application Support/org.inkscape.Inkscape/config/inkscape/extensions")

    @property
    def textext_config_path(self):
        return os.path.expanduser("~/Library/Preferences/textext")

    @property
    def textext_logfile_path(self):
        return os.path.expanduser("~/Library/Preferences/textext")


class WindowsEnvironment(AbstractEnvironment):

    os_name = "windows"
    console_colors = "never"
    executable_names = {"inkscape": ["inkscape.exe"],
                        "pdflatex": ["pdflatex.exe"],
                        "lualatex": ["lualatex.exe"],
                        "xelatex": ["xelatex.exe"],
                        }

    def __init__(self):
        super().__init__()
        from .win_app_paths import get_non_syspath_dirs  # pylint: disable=import-outside-toplevel
        self._tweaked_syspath = get_non_syspath_dirs() + os.environ["PATH"].split(os.path.pathsep)

        # Windows 10 supports colored output since anniversary update (build 14393)
        # so we try to use it (it has to be enabled since it is always disabled by default!)
        try:
            wininfo = sys.getwindowsversion()
            if wininfo.major >= 10 and wininfo.build >= 14393:
                h_kernel32 = ct.windll.kernel32

                #  STD_OUTPUT_HANDLE = -11
                # -> https://docs.microsoft.com/en-us/windows/console/getstdhandle
                h_stdout = h_kernel32.GetStdHandle(-11)

                # ENABLE_PROCESSED_OUTPUT  | ENABLE_WRAP_AT_EOL_OUTPUT | ENABLE_VIRTUAL_TERMINAL_PROCESSING = 7
                # -> https://docs.microsoft.com/en-us/windows/console/setconsolemode
                h_kernel32.SetConsoleMode(h_stdout, 7)

                self.console_colors = "always"
        except (ImportError, AttributeError):
            pass

    @property
    def inkscape_user_extensions_path(self):
        return os.path.join(os.getenv("APPDATA"), "inkscape", "extensions")

    @property
    def textext_config_path(self):
        return os.path.join(os.getenv("APPDATA"), "textext")

    @property
    def textext_logfile_path(self):
        return os.path.join(os.getenv("APPDATA"), "textext")

    @property
    def system_path(self):
        return self._tweaked_syspath

    @staticmethod
    def call_command(command, return_code=0):
        """
        Safely execute a system command.

        Args:
            command (list(str)): The command as a list of tokens
            return_code (int): The return code which is interpreted as successfull

        Returns:
            A tuple of two strings, the first containing stdout, the second stderr
        """
        # Ensure that command window does not pop up on Windows!
        info = sp.STARTUPINFO()
        info.dwFlags |= sp.STARTF_USESHOWWINDOW
        info.wShowWindow = sp.SW_HIDE
        with sp.Popen(command, stdout=sp.PIPE, stderr=sp.PIPE, startupinfo=info) as proc:
            stdout, stderr = proc.communicate()
        if return_code is not None and proc.returncode != return_code:
            raise sp.CalledProcessError(proc.returncode, command)
        return stdout, stderr


if sys.platform.startswith("win"):
    system_env = WindowsEnvironment()
elif sys.platform.startswith("darwin"):
    system_env = MacEnvironment()
else:
    system_env = LinuxEnvironment()
