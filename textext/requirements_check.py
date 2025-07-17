"""
This file is part of TexText, an extension for the vector
illustration program Inkscape.

Copyright (c) 2006-2025 TexText developers.

TexText is released under the 3-Clause BSD license. See
file LICENSE.txt or go to https://github.com/textext/textext
for full license details.

Classes for handling and checking of the dependencies required
to successfully run TexText.
"""
from abc import ABCMeta, abstractmethod
import logging
import os
import re
import subprocess
import sys

VERBOSE = 5
SUCCESS = 41
UNKNOWN = 42


class Defaults(object):
    __metaclass__ = ABCMeta

    # ToDo: Change to @property @abstractmethod when discarding Python 2.7 support
    @property
    @abstractmethod
    def os_name(self): pass

    @property
    @abstractmethod
    def console_colors(self): pass

    @property
    @abstractmethod
    def executable_names(self): pass

    @property
    @abstractmethod
    def inkscape_user_extensions_path(self): pass

    def inkscape_system_extensions_path(self, inkscape_exe_path):
        try:
            stdout, stderr = self.call_command([inkscape_exe_path, "--system-data-directory"])
            path = os.path.join(stdout.decode("utf-8", 'ignore').rstrip(), "extensions")
            err = None
        except subprocess.CalledProcessError as excpt:
            path = None
            err = "Command `%s` failed, stdout: `%s`, stderr: `%s`" % (excpt.cmd, excpt.stdout, excpt.stderr)
        except UnicodeDecodeError as excpt:
            path = None
            err = excpt.reason

        return [path, err]

    @property
    @abstractmethod
    def textext_config_path(self): pass

    @property
    @abstractmethod
    def textext_logfile_path(self): pass

    @property
    @abstractmethod
    def get_system_path(self): pass

    @staticmethod
    @abstractmethod
    def call_command(command, return_code=0): pass

    @property
    @abstractmethod
    def example_path(self): pass

    @property
    @abstractmethod
    def setup_script(self): pass

class LinuxDefaults(Defaults):
    os_name = "linux"
    console_colors = "always"
    executable_names = {"inkscape": ["inkscape"],
                        "pdflatex": ["pdflatex"],
                        "lualatex": ["lualatex"],
                        "xelatex": ["xelatex"],
                        "typst": ["typst"]
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

    def get_system_path(self):
        return os.environ["PATH"].split(os.path.pathsep)

    @staticmethod
    def call_command(command, return_code=0):
        p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        if return_code is not None and p.returncode != return_code:
            raise subprocess.CalledProcessError(p.returncode,command)
        return stdout, stderr

    @property
    def example_path(self):
        return "/path/to/your/"

    @property
    def setup_script(self):
        return "python3 setup.py"

class MacDefaults(LinuxDefaults):
    os_name = "macos"
    executable_names = {"inkscape": ["inkscape", "inkscape-bin"],
                        "pdflatex": ["pdflatex"],
                        "lualatex": ["lualatex"],
                        "xelatex": ["xelatex"],
                        "typst": ["typst"]
                        }

    def get_system_path(self):
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

    @property
    def example_path(self):
        return "/path/to/your/"

    @property
    def setup_script(self):
        return "python3 setup.py"


class WindowsDefaults(Defaults):

    os_name = "windows"
    console_colors = "never"
    executable_names = {"inkscape": ["inkscape.exe"],
                        "pdflatex": ["pdflatex.exe"],
                        "lualatex": ["lualatex.exe"],
                        "xelatex": ["xelatex.exe"],
                        "typst": ["typst.exe"]
                        }

    def __init__(self):
        super(WindowsDefaults, self)
        from .win_app_paths import get_non_syspath_dirs
        self._tweaked_syspath = get_non_syspath_dirs() + os.environ["PATH"].split(os.path.pathsep)

        # Windows 10 supports colored output since anniversary update (build 14393)
        # so we try to use it (it has to be enabled since it is always disabled by default!)
        try:
            wininfo = sys.getwindowsversion()
            if wininfo.major >= 10 and wininfo.build >= 14393:

                import ctypes as ct
                h_kernel32 = ct.windll.kernel32

                #  STD_OUTPUT_HANDLE = -11
                # -> https://docs.microsoft.com/en-us/windows/console/getstdhandle
                h_stdout = h_kernel32.GetStdHandle(-11)

                # ENABLE_PROCESSED_OUTPUT  | ENABLE_WRAP_AT_EOL_OUTPUT | ENABLE_VIRTUAL_TERMINAL_PROCESSING = 7
                # -> https://docs.microsoft.com/en-us/windows/console/setconsolemode
                result = h_kernel32.SetConsoleMode(h_stdout, 7)

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

    def get_system_path(self):
        return self._tweaked_syspath

    @staticmethod
    def call_command(command, return_code=0): # type: (List,Optional[int]) -> Tuple[str, str]
        # Ensure that command window does not pop up on Windows!
        info = subprocess.STARTUPINFO()
        info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        info.wShowWindow = subprocess.SW_HIDE
        p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=info)
        stdout, stderr = p.communicate()
        if return_code is not None and p.returncode != return_code:
            raise subprocess.CalledProcessError(p.returncode, "{0}, stderr: {1}".format(command, stderr),
                                                output=stdout, stderr=stderr)
        return stdout, stderr

    @property
    def example_path(self):
        return "C:\\Path\\To\\Your\\"

    @property
    def setup_script(self):
        return "setup_win.bat"


class TexTextLogFormatter(logging.Formatter):

    enable_colors = False

    COLOR_RESET = "\033[0m"
    FG_DEFAULT = "\033[39m"
    FG_BLACK = "\033[30m"
    FG_RED = "\033[31m"
    FG_GREEN = "\033[32m"
    FG_YELLOW = "\033[33m"
    FG_BLUE = "\033[34m"
    FG_MAGENTA = "\033[35m"
    FG_CYAN = "\033[36m"
    FG_LIGHT_GRAY = "\033[37m"
    FG_DARK_GRAY = "\033[90m"
    FG_LIGHT_RED = "\033[91m"
    FG_LIGHT_GREEN = "\033[92m"
    FG_LIGHT_YELLOW = "\033[93m"
    FG_LIGHT_BLUE = "\033[94m"
    FG_LIGHT_MAGENTA = "\033[95m"
    FG_LIGHT_CYAN = "\033[96m"
    FG_WHITE = "\033[97m"

    BG_DEFAULT = "\033[49m"
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_LIGHT_GRAY = "\033[47m"
    BG_DARK_GRAY = "\033[100m"
    BG_LIGHT_RED = "\033[101m"
    BG_LIGHT_GREEN = "\033[102m"
    BG_LIGHT_YELLOW = "\033[103m"
    BG_LIGHT_BLUE = "\033[104m"
    BG_LIGHT_MAGENTA = "\033[105m"
    BG_LIGHT_CYAN = "\033[106m"
    BG_WHITE = "\033[107m"

    UNDERLINED = "\033[4m"

    LEVELS = [
        VERBOSE,  # 5
        logging.DEBUG,  # 10
        logging.INFO,  # 20
        logging.WARNING,  # 30
        logging.ERROR,  # 40
        SUCCESS,  # 41
        UNKNOWN,  # 42
        logging.CRITICAL  # 50
    ]
    NAMES = [
        "VERBOSE ",
        "DEBUG   ",
        "INFO    ",
        "WARNING ",
        "ERROR   ",
        "SUCCESS ",
        "UNKNOWN ",
        "CRITICAL"
    ]
    colors = [
        COLOR_RESET,  # VERBOSE
        COLOR_RESET,  # DEBUG
        BG_DEFAULT + FG_LIGHT_BLUE,  # INFO
        BG_DEFAULT + FG_YELLOW,  # WARNING
        BG_DEFAULT + FG_RED,  # ERROR
        BG_DEFAULT + FG_GREEN,  # SUCCESS
        BG_DEFAULT + FG_YELLOW,  # UNKNOWN
        BG_RED + FG_WHITE,  # CRITICAL
    ]

    @classmethod
    def get_levels(cls):
        return [x for x in zip(cls.LEVELS, cls.NAMES)]

    def format(self, record):
        logger_name = record.name
        log_level = self.LEVELS.index(record.levelno)
        level_name = self.NAMES[log_level]
        color = self.colors[log_level] if self.enable_colors else ""
        reset_color = self.COLOR_RESET if self.enable_colors else ""
        message = super().format(record)
        return f"[{logger_name}][{color}{level_name}{reset_color}]: {message}"


def set_logging_levels():
    for log_level, level_name in TexTextLogFormatter.get_levels():
        logging.addLevelName(log_level, level_name)


class TexTextRequirementsChecker(object):
    MINIMUM_REQUIRED_INKSCAPE_VERSION = "1.4.0"

    def __init__(self, logger, config):
        self.logger = logger
        self.config = config
        self.available_tex_to_pdf_converters = {}
        self.available_pdf_to_svg_converters = {}

        self.inkscape_prog_name = "inkscape"
        self.pdflatex_prog_name = "pdflatex"
        self.lualatex_prog_name = "lualatex"
        self.xelatex_prog_name = "xelatex"
        self.typst_prog_name = "typst"

        self.inkscape_executable = None

        self.pygtk_is_found = False
        self.tkinter_is_found = False

        pass

    def find_gtk3(self) -> bool:
        self.logger.info("Checking if GTK is available...")
        try:
            executable = sys.executable
            defaults.call_command([executable, "-c", "import gi;"+
                                                     "gi.require_version('Gtk', '3.0');"+
                                                     "from gi.repository import Gtk, Gdk, GdkPixbuf"])
        except (KeyError, OSError, subprocess.CalledProcessError):
            self.logger.warning(f"   ...GTK3 is not found (but TkInter maybe available as a fall back...).")
            self.logger.info(f"      GTK3 offers the best user experience. You may refer to the installation")
            self.logger.info(f"      instructions to make it available:")
            self.logger.info(f"      https://textext.github.io/textext/install/{defaults.os_name}.html")
            return False
        self.logger.log(SUCCESS, "   ...GTK3 is found.")
        return True

    def find_tkinter(self) -> bool:
        self.logger.info("Checking if Tk interface (tkinter) is available...")
        try:
            defaults.call_command(
                [sys.executable, "-c", "import tkinter; import tkinter.messagebox; import tkinter.filedialog;"])
        except (KeyError, OSError, subprocess.CalledProcessError):
            self.logger.warning("   ...tkinter is not found (but maybe GTK3 is available).")
            return False
        self.logger.log(SUCCESS, "   ...tkinter is found.")
        return True

    def find_inkscape(self) -> bool:
        req_maj, req_min, req_rel = [int(item) for item in self.MINIMUM_REQUIRED_INKSCAPE_VERSION.split(".")]
        self.logger.info(f"Checking for Inkscape {self.MINIMUM_REQUIRED_INKSCAPE_VERSION}...")
        try:
            # When we call this from Inkscape we need this call
            import inkex.command as iec
            stdout_line = iec.inkscape("", version=True)
            executable = iec.which("inkscape")
        except (ImportError, IOError):
            executable = ""
            try:
                executable = self.find_executable('inkscape')
                stdout, stderr = defaults.call_command([executable, "--version"])
                stdout_line = stdout.decode("utf-8", 'ignore')
            except (FileNotFoundError, OSError):
                self.logger.error(f"   ...Inkscape (as {executable}) is not found!")
                self.logger.info(f"      Ensure that Inkscape is in the system path or pass the path to")
                self.logger.info(f"      the setup via the --inkscape-executable command line option:")
                self.logger.info(f"      {defaults.setup_script} --inkscape-executable {defaults.example_path}inkscape")

                return False

        m = re.search(r"Inkscape ((\d+)\.(\d+)\.*(\d+)?[-\w]*)", stdout_line)
        if m:
            try:
                found_version, major, minor, release = m.groups()
                if not release:
                    release = "9999999"
            except ValueError as _:
                found_version, major, minor = m.groups()
                release = "9999999"

            if int(major) >= req_maj and int(minor) >= req_min and int(release) >= req_rel:
                self.logger.log(SUCCESS, f"   ...Inkscape = {found_version} is found at {executable}")
                self.inkscape_executable = executable
                return True
            else:
                self.logger.error(f"   ...Inkscape >= {self.MINIMUM_REQUIRED_INKSCAPE_VERSION} "
                                     f"is not found (but Inkscape = {found_version} is found "
                                     f"at {executable}).")
                return False
        self.logger.error("   ...can't determinate Inkscape version!")
        return False

    def find_executable(self, prog_name) -> str:
        # try value from config
        executable_path = self.config.get(prog_name + "-executable", None)
        if executable_path is not None:
            if self.check_executable(executable_path):
                self.logger.info(f"   ...using '{prog_name}-executable' = '{executable_path}' from settings.")
                return executable_path
            else:
                self.logger.warning(f"   ...bad '{prog_name}' executable in settings: '{executable_path}'" )
                self.logger.warning(f"   ...fall back to automatic detection of '{prog_name}' in system path" )

        # look for executable in path
        try:
            return self._find_executable_in_path(prog_name)
        except FileNotFoundError as _:
            raise

    def _find_executable_in_path(self, prog_name) -> str:
        for exe_name in defaults.executable_names[prog_name]:
            first_path = None
            for path in defaults.get_system_path():
                full_path_guess = os.path.join(path, exe_name)
                self.logger.debug(f"   ...Looking for '{exe_name}' in '{path}'")
                if self.check_executable(full_path_guess):
                    self.logger.debug(f"   ...'{exe_name}' is found at '{path}'")
                    if first_path is None:
                        first_path = path

            if first_path is not None:
                return os.path.join(first_path, exe_name)

            self.logger.debug(f"   ...'{exe_name}' is NOT found in PATH")

        raise FileNotFoundError(f"'{prog_name}' is NOT found in PATH")

    @staticmethod
    def check_executable(filename) -> bool:
        return filename is not None and os.path.isfile(filename) and os.access(filename, os.X_OK)

    def check(self):

        def add_latex(name, exe):
            self.available_tex_to_pdf_converters.update({name: exe})

        self.logger.info(f"Python interpreter: {sys.executable}")
        self.logger.info(f"Python version: {sys.version}")

        # Check availability of Inkscape and its version
        inkscape_found = self.find_inkscape()

        # Check availability of GTK, GTKSourceView, TkInter
        self.pygtk_is_found = self.find_gtk3()
        self.tkinter_is_found = self.find_tkinter()
        gui_toolkit_found = self.pygtk_is_found or self.tkinter_is_found
        if not gui_toolkit_found:
            self.logger.error("Neither GTK nor TkInter has been found! Without such a GUI framework TexText")
            self.logger.error("will not work. Refer to the messages above for any details.")

        # Check availability of LaTeX compilers
        latex_compilers_found = False
        for latex_compiler_name in [self.pdflatex_prog_name, self.lualatex_prog_name, self.xelatex_prog_name]:
            self.logger.info(f"Checking if {latex_compiler_name} is available...")
            try:
                compiler_exe_path = self.find_executable(latex_compiler_name)
            except FileNotFoundError:
                self.logger.warning(f"   ...{latex_compiler_name} not found, but other LaTeX compilers or typst may")
                self.logger.info(f"      be available. If you want to use {latex_compiler_name}: Ensure that the")
                self.logger.info(f"      {latex_compiler_name} executable is in the system path or pass the path to")
                self.logger.info(f"      the setup via the --{latex_compiler_name}-executable command line option:")
                self.logger.info(f"      {defaults.setup_script} --{latex_compiler_name}-executable {defaults.example_path}{latex_compiler_name}")
            else:
                self.logger.log(SUCCESS, f"   ...{latex_compiler_name} is found at {compiler_exe_path}.")
                latex_compilers_found = True
                add_latex(latex_compiler_name, compiler_exe_path)

        # Check availability of typst compiler
        typst_compiler_found = False
        self.logger.info(f"Checking if {self.typst_prog_name} is available...")
        try:
            compiler_exe_path = self.find_executable(self.typst_prog_name)
        except FileNotFoundError:
            if latex_compilers_found:
                self.logger.warning(f"   ...{self.typst_prog_name} not found, but latex compilers are available.")
                self.logger.info(f"      If you want to use typst: Ensure that the  typst executable is in the system")
                self.logger.info(f"      path or pass the path to the setup via the --typst-executable command line")
                self.logger.info(f"      option: {defaults.setup_script} --typst-executable {defaults.example_path}typst")
            else:
                self.logger.error(f"   ...{self.typst_prog_name} not found, and no LaTeX compilers are available.")
                self.logger.error(f"At least one LaTeX compiler or typst must be available for TexText to work.")
        else:
            self.logger.log(SUCCESS, f"   ...{self.typst_prog_name} is found at {compiler_exe_path}.")
            typst_compiler_found = True
            add_latex(self.typst_prog_name, compiler_exe_path)

        return inkscape_found and gui_toolkit_found and (latex_compilers_found or typst_compiler_found)


if sys.platform.startswith("win"):
    defaults = WindowsDefaults()
elif sys.platform.startswith("darwin"):
    defaults = MacDefaults()
else:
    defaults = LinuxDefaults()
