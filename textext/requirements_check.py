"""
This file is part of TexText, an extension for the vector
illustration program Inkscape.

Copyright (c) 2006-2021 TexText developers.

TexText is released under the 3-Clause BSD license. See
file LICENSE.txt or go to https://github.com/textext/textext
for full license details.

Classes for handling and checking of the dependencies required
to successfully run TexText.
"""
import abc
import logging
import os
import re
import subprocess
import sys


class Defaults(object):
    __metaclass__ = abc.ABCMeta

    # ToDo: Change to @property @abstractmethod when discarding Python 2.7 support
    @abc.abstractproperty
    def os_name(self): pass

    @abc.abstractproperty
    def console_colors(self): pass

    @abc.abstractproperty
    def executable_names(self): pass

    @abc.abstractproperty
    def inkscape_extensions_path(self): pass

    @abc.abstractmethod
    def get_system_path(self): pass

    @staticmethod
    @abc.abstractmethod
    def call_command(command, return_code=0): pass


class LinuxDefaults(Defaults):
    os_name = "linux"
    console_colors = "always"
    executable_names = {"inkscape": ["inkscape.beta", "inkscape"],   # BETA-TEST only #
                        "pdflatex": ["pdflatex"],
                        "lualatex": ["lualatex"],
                        "xelatex": ["xelatex"]
                        }

    @property
    def inkscape_extensions_path(self):
        return os.path.expanduser("~/.config/inkscape/extensions")

    def get_system_path(self):
        return os.environ["PATH"].split(os.path.pathsep)

    @staticmethod
    def call_command(command, return_code=0):
        p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        if return_code is not None and p.returncode != return_code:
            raise subprocess.CalledProcessError(p.returncode,command)
        return stdout, stderr


class MacDefaults(LinuxDefaults):
    os_name = "macos"
    executable_names = {"inkscape": ["inkscape", "inkscape-bin"],
                        "pdflatex": ["pdflatex"],
                        "lualatex": ["lualatex"],
                        "xelatex": ["xelatex"]
                        }

    def get_system_path(self):
        path = ["/Applications/Inkscape.app/Contents/Resources"]
        path += os.environ["PATH"].split(os.path.pathsep)
        return path

    @property
    def inkscape_extensions_path(self):
        return os.path.expanduser("~/Library/Application Support/org.inkscape.Inkscape/config/inkscape/extensions")


class WindowsDefaults(Defaults):

    os_name = "windows"
    console_colors = "never"
    executable_names = {"inkscape": ["inkscape.exe"],
                        "pdflatex": ["pdflatex.exe"],
                        "lualatex": ["lualatex.exe"],
                        "xelatex": ["xelatex.exe"],
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
    def inkscape_extensions_path(self):
        return os.path.join(os.getenv("APPDATA"), "inkscape", "extensions")

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
            raise subprocess.CalledProcessError(p.returncode, command)
        return stdout, stderr



class LoggingColors(object):
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

    def __call__(self):
        levels = [
            VERBOSE,  # 5
            logging.DEBUG,  # 10
            logging.INFO,  # 20
            logging.WARNING,  # 30
            logging.ERROR,  # 40
            SUCCESS,  # 41
            UNKNOWN,  # 42
            logging.CRITICAL  # 50
        ]
        names = [
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
            self.COLOR_RESET,
            self.COLOR_RESET,
            self.BG_DEFAULT + self.FG_LIGHT_BLUE,
            self.BG_YELLOW + self.FG_WHITE,
            self.BG_DEFAULT + self.FG_RED,
            self.BG_DEFAULT + self.FG_GREEN,
            self.BG_DEFAULT + self.FG_YELLOW,
            self.BG_RED + self.FG_WHITE,
        ]
        if not LoggingColors.enable_colors:
            colors = [""] * len(colors)
            self.COLOR_RESET = ""
        return {name: (level, color) for level, name, color in zip(levels, names, colors)}, self.COLOR_RESET


def set_logging_levels():
    level_colors, COLOR_RESET = get_levels_colors()
    for name, (level, color) in level_colors.items():
        logging.addLevelName(level, color + name + COLOR_RESET)


class TrinaryLogicValue(object):
    def __init__(self, value=None):
        if isinstance(value, TrinaryLogicValue):
            self.value = value.value
        else:
            self.value = value

    def __and__(self, rhs):
        if rhs.value == False or self.value == False:
            return TrinaryLogicValue(False)
        if rhs.value is None or self.value is None:
            return TrinaryLogicValue(None)
        return TrinaryLogicValue(True)

    def __or__(self, rhs):
        if rhs.value == True or self.value == True:
            return TrinaryLogicValue(True)
        if rhs.value is None or self.value is None:
            return TrinaryLogicValue(None)
        return TrinaryLogicValue(False)

    def __invert__(self):
        if self.value is None:
            return TrinaryLogicValue(None)
        return TrinaryLogicValue(not self.value)

    def __eq__(self, rhs):
        if isinstance(rhs, TrinaryLogicValue):
            return self.value is None and rhs.value is None or self.value == rhs.value
        return self.value is None and rhs is None or self.value == rhs

    def __ne__(self, rhs):
        return not self.__eq__(rhs)

    def __str__(self):
        return "TrinaryLogicValue(%s)" % self.value


class RequirementCheckResult(object):
    def __init__(self, value, messages, nested=None, is_and_node=False, is_or_node=False, is_not_node=False, **kwargs):
        self.value = TrinaryLogicValue(value)
        self.messages = messages
        self.nested = nested if nested is not None else []

        self.is_and_node = is_and_node
        self.is_or_node = is_or_node
        self.is_not_node = is_not_node
        self.is_critical = None
        self.kwargs = kwargs

    @property
    def color(self):
        if self.value == True:
            return get_levels_colors()[0]["SUCCESS "][1]
        elif self.value == False:
            return get_levels_colors()[0]["ERROR   "][1]
        else:
            return get_levels_colors()[0]["UNKNOWN "][1]

    def print_to_logger(self, logger, offset=0, prefix="", parent=None):
        _, reset_color = get_levels_colors()

        if self.is_critical:
            lvl = logging.CRITICAL
        elif self.value == True:
            lvl = SUCCESS
        elif self.value == False:
            lvl = logging.INFO
        else:
            lvl = UNKNOWN

        value_repr = {
            True: "Succ",
            False: "Fail",
            None: "Ukwn"
        }
        if self.nested:
            nest_symbol = "+ [%s]" % value_repr[self.value.value]
        else:
            nest_symbol = "* [%s]" % value_repr[self.value.value]

        if parent:
            if parent.is_and_node:
                tail = parent.color + "/-and-" + self.color + nest_symbol + reset_color
            elif parent.is_or_node:
                tail = parent.color + "/--or-" + self.color + nest_symbol + reset_color
            elif parent.is_not_node:
                tail = parent.color + "/-not-" + self.color + nest_symbol + reset_color
            else:
                tail = parent.color + "/-----" + self.color + nest_symbol + reset_color
        else:
            tail = self.color + nest_symbol + reset_color

        if not parent:
            suffix = ""
        elif parent.nested[-1] is self:
            suffix = "      "
        else:
            suffix = parent.color + "|" + reset_color + "     "

        if not self.messages:
            messages = [""]
        else:
            messages = self.messages
        for msg in messages:
            line = ""
            line += prefix + tail
            line += " " + msg

            logger.log(lvl, line)

            tail = suffix
        for nst in self.nested:
            nst.print_to_logger(logger, offset + 1, prefix=prefix + suffix, parent=self)

    def flatten(self):
        if len(self.nested) == 0:
            return self

        for i, nst in enumerate(self.nested):
            self.nested[i] = nst.flatten()

        if self.nested[0].is_or_node and self.is_or_node:
            kwargs = dict(self.kwargs)
            kwargs.update(self.nested[0].kwargs)
            return RequirementCheckResult(
                self.value,
                self.nested[0].messages + self.messages,
                self.nested[0].nested + self.nested[1:],
                is_or_node=True,
                **kwargs
            )

        if self.nested[0].is_and_node and self.is_and_node:
            kwargs = dict(self.kwargs)
            kwargs.update(self.nested[0].kwargs)
            return RequirementCheckResult(
                self.value,
                self.nested[0].messages + self.messages,
                self.nested[0].nested + self.nested[1:],
                is_and_node=True,
                **kwargs
            )

        if self.nested[-1].is_or_node and self.is_or_node:
            kwargs = dict(self.kwargs)
            kwargs.update(self.nested[-1].kwargs)
            return RequirementCheckResult(
                self.value,
                self.messages + self.nested[-1].messages,
                self.nested[:-1] + self.nested[-1].nested,
                is_or_node=True,
                **kwargs
            )

        if self.nested[-1].is_and_node and self.is_and_node:
            kwargs = dict(self.kwargs)
            kwargs.update(self.nested[-1].kwargs)
            return RequirementCheckResult(
                self.value,
                self.messages + self.nested[-1].messages,
                self.nested[:-1] + self.nested[-1].nested,
                is_and_node=True,
                **kwargs
            )

        if self.nested[-1].is_not_node:
            self.kwargs.update(self.nested[-1].kwargs)

        return self

    def mark_critical_errors(self, non_critical_value=True):
        if self.value == non_critical_value:
            return
        if self.value == None:
            return

        self.is_critical = True

        if self.is_and_node or self.is_or_node:
            for nst in self.nested:
                if nst.value != non_critical_value:
                    nst.mark_critical_errors(non_critical_value)

        if self.is_not_node:
            for nst in self.nested:
                nst.mark_critical_errors(not non_critical_value)

    def __getitem__(self, item):
        return self.kwargs[item]


class Requirement(object):
    def __init__(self, criteria, *args, **kwargs):
        self.criteria = lambda: criteria(*args, **kwargs)
        self._prepended_messages = {"ANY": [], "SUCCESS": [], "ERROR": [], "UNKNOWN": []}
        self._appended_messages = {"ANY": [], "SUCCESS": [], "ERROR": [], "UNKNOWN": []}
        self._overwrite_messages = None

        self._on_unknown_callbacks = []
        self._on_success_callbacks = []
        self._on_failure_callbacks = []

    def check(self):
        result = self.criteria()
        if not isinstance(result.messages,list):
            result.messages = [result.messages]
        if self._overwrite_messages:
            result.messages = self._overwrite_messages
        result.messages = self._prepended_messages["ANY"] + result.messages
        if result.value == TrinaryLogicValue(True):
            result.messages = self._prepended_messages["SUCCESS"] + result.messages
            for callback in self._on_success_callbacks:
                callback(result)
        if result.value == TrinaryLogicValue(False):
            result.messages = self._prepended_messages["ERROR"] + result.messages
            for callback in self._on_failure_callbacks:
                callback(result)
        if result.value == TrinaryLogicValue(None):
            result.messages = self._prepended_messages["UNKNOWN"] + result.messages
            for callback in self._on_unknown_callbacks:
                callback(result)

        result.messages += self._appended_messages["ANY"]
        if result.value == TrinaryLogicValue(True):
            result.messages += self._appended_messages["SUCCESS"]
        if result.value == TrinaryLogicValue(False):
            result.messages += self._appended_messages["ERROR"]
        if result.value == TrinaryLogicValue(None):
            result.messages += self._appended_messages["UNKNOWN"]
        return result

    def prepend_message(self, result_type, message):
        assert result_type in self._prepended_messages.keys()
        if not isinstance(message, list):
            message = [message]
        self._prepended_messages[result_type].extend(message)
        return self

    def overwrite_check_message(self, message):
        if not isinstance(message, list):
            message = [message]
        self._overwrite_messages = message
        return self

    def append_message(self, result_type, message):
        assert result_type in self._appended_messages.keys()
        if not isinstance(message, list):
            message = [message]
        self._appended_messages[result_type].extend(message)
        return self

    def __and__(self, rhs):
        # type: (Requirement) -> Requirement
        def and_impl():
            L = self.check()
            R = rhs.check()
            return RequirementCheckResult(L.value & R.value,
                                          [],
                                          [L, R],
                                          is_and_node=True
                                          )

        return Requirement(and_impl)

    def __or__(self, rhs):
        # type: (Requirement) -> Requirement
        def or_impl():
            L = self.check()
            R = rhs.check()
            return RequirementCheckResult(L.value | R.value,
                                          [],
                                          [L, R],
                                          is_or_node=True
                                          )

        return Requirement(or_impl)

    def __invert__(self):
        # type: (Requirement) -> Requirement
        def invert_impl():
            L = self.check()
            return RequirementCheckResult(~L.value,
                                          [],
                                          [L],
                                          is_not_node=True
                                          )

        return Requirement(invert_impl)

    def on_success(self, callback):
        self._on_success_callbacks.append(callback)
        return self

    def on_failure(self, callback):
        self._on_failure_callbacks.append(callback)
        return self

    def on_unknown(self, callback):
        self._on_unknown_callbacks.append(callback)
        return self


class TexTextRequirementsChecker(object):

    def __init__(self, logger, config):
        self.logger = logger
        self.config = config
        self.available_tex_to_pdf_converters = {}
        self.available_pdf_to_svg_converters = {}

        self.inkscape_prog_name = "inkscape"
        self.pdflatex_prog_name = "pdflatex"
        self.lualatex_prog_name = "lualatex"
        self.xelatex_prog_name = "xelatex"

        self.inkscape_executable = None

        self.pygtk_is_found = False
        self.tkinter_is_found = False

        pass

    def find_pygtk3(self):
        try:
            executable = sys.executable
            defaults.call_command([executable, "-c", "import gi;"+
                                                     "gi.require_version('Gtk', '3.0');"+
                                                     "from gi.repository import Gtk, Gdk, GdkPixbuf"])
        except (KeyError, OSError, subprocess.CalledProcessError):
            return RequirementCheckResult(False, ["GTK3 is not found"])
        return RequirementCheckResult(True, ["GTK3 is found"])

    def find_tkinter(self):
        executable = sys.executable
        if sys.version_info[0] == 3:
            import_tk_script = "import tkinter; import tkinter.messagebox; import tkinter.filedialog;"
        else:
            import_tk_script = "import Tkinter; import tkMessageBox; import tkFileDialog;"
        try:
            defaults.call_command(
                [executable, "-c", import_tk_script])
        except (KeyError, OSError, subprocess.CalledProcessError):
            return RequirementCheckResult(False, ["TkInter is not found"])

        return RequirementCheckResult(True, ["TkInter is found"])

    def find_inkscape_1_0(self):
        from distutils.version import LooseVersion
        try:
            executable = self.find_executable('inkscape')['path']
            stdout, stderr = defaults.call_command([executable, "--version"])
        except (KeyError, OSError):
            return RequirementCheckResult(False, ["inkscape is not found"])
        for stdout_line in stdout.decode("utf-8", 'ignore').split("\n"):
            m = re.search(r"Inkscape (\d+.\d+[-\w]*)", stdout_line)

            if m:
                found_version = m.group(1)
                if LooseVersion(found_version) >= LooseVersion("1.0"):
                    return RequirementCheckResult(True, ["inkscape=%s is found" % found_version], path=executable)
                else:
                    return RequirementCheckResult(False, [
                        "inkscape>=1.0 is not found (but inkscape=%s is found)" % (found_version)])
        return RequirementCheckResult(None, ["Can't determinate inkscape version"])

    def find_executable(self, prog_name):
        # try value from config
        executable_path = self.config.get(prog_name+"-executable", None)
        if executable_path is not None:
            if self.check_executable(executable_path):
                self.logger.info("Using `%s-executable` = `%s`" % (prog_name, executable_path))
                return RequirementCheckResult(True, "%s is found at `%s`" % (prog_name, executable_path),
                                              path=executable_path)
            else:
                self.logger.warning("Bad `%s` executable: `%s`" % (prog_name, executable_path))
                self.logger.warning("Fall back to automatic detection of `%s`" % prog_name)
        # look for executable in path
        return self._find_executable_in_path(prog_name)

    def _find_executable_in_path(self, prog_name):
        messages = []
        for exe_name in defaults.executable_names[prog_name]:
            first_path = None
            for path in defaults.get_system_path():
                full_path_guess = os.path.join(path, exe_name)
                self.logger.log(VERBOSE, "Looking for `%s` in `%s`" % (exe_name, path))
                if self.check_executable(full_path_guess):
                    self.logger.log(VERBOSE, "`%s` is found at `%s`" % (exe_name, path))
                    messages.append("`%s` is found at `%s`" % (exe_name, path))
                    if first_path is None:
                        first_path = path
            if first_path is not None:
                return RequirementCheckResult(True, messages, path=os.path.join(first_path,exe_name))
            messages.append("`%s` is NOT found in PATH" % (exe_name))
        return RequirementCheckResult(False, messages)

    def check_executable(self, filename):
        return filename is not None and os.path.isfile(filename) and os.access(filename, os.X_OK)

    def check(self):

        def set_inkscape(exe):
            self.inkscape_executable = exe

        def add_latex(name, exe):
            self.available_tex_to_pdf_converters.update({name: exe})

        def set_pygtk(result):
            self.pygtk_is_found = True

        def set_tkinter(result):
            self.tkinter_is_found= True

        def help_message_with_url(section_name, executable_name=None):
            user = "textext"
            url_template = "https://{user}.github.io/textext/install/{os_name}.html#{os_name}-install-{section}"
            url = url_template.format(
                user=user,
                os_name=defaults.os_name,
                section=section_name
            )

            if defaults.console_colors == "always":
                url_line = "       {}%s{}".format(LoggingColors.FG_LIGHT_BLUE + LoggingColors.UNDERLINED,
                                                     LoggingColors.COLOR_RESET)
            else:
                url_line = "       {}%s{}".format("", "")

            result = [
                "Please follow installation instructions at ",
                url_line % url
            ]
            if executable_name:
                result += [
                    "If %s is installed in custom location, specify it via " % executable_name,
                    "       --{name}-executable=<path-to-{name}>".format(name=executable_name),
                    "and run setup.py again",
                ]
            return result

        textext_requirements = (
            Requirement(self.find_inkscape_1_0)
            .prepend_message("ANY", 'Detect inkscape>=1.0')
            .append_message("ERROR", help_message_with_url("preparation","inkscape"))
            .on_success(lambda result: set_inkscape(result["path"]))
            & (
                    Requirement(self.find_executable, self.pdflatex_prog_name)
                    .on_success(lambda result: add_latex("pdflatex", result["path"]))
                    .append_message("ERROR", help_message_with_url("preparation", "pdflatex"))
                    | Requirement(self.find_executable, self.lualatex_prog_name)
                    .on_success(lambda result: add_latex("lualatex", result["path"]))
                    .append_message("ERROR", help_message_with_url("preparation", "lualatex"))
                    | Requirement(self.find_executable, self.xelatex_prog_name)
                    .on_success(lambda result: add_latex("xelatex", result["path"]))
                    .append_message("ERROR", help_message_with_url("preparation", "xelatex"))
            ).overwrite_check_message("Detect *latex")
            .append_message("ERROR", help_message_with_url("preparation"))
            & (
                    Requirement(self.find_pygtk3).on_success(set_pygtk)
                    .append_message("ERROR", help_message_with_url("gtk3"))
                    | Requirement(self.find_tkinter).on_success(set_tkinter)
                    .append_message("ERROR", help_message_with_url("tkinter"))
            ).overwrite_check_message("Detect GUI library")
            .append_message("ERROR", help_message_with_url("gui-library"))
        ).overwrite_check_message("TexText requirements")

        check_result = textext_requirements.check()

        check_result = check_result.flatten()

        check_result.mark_critical_errors()

        check_result.print_to_logger(self.logger)

        return check_result.value


get_levels_colors = LoggingColors()

if sys.platform.startswith("win"):
    defaults = WindowsDefaults()
elif sys.platform.startswith("darwin"):
    defaults = MacDefaults()
else:
    defaults = LinuxDefaults()

VERBOSE = 5
SUCCESS = 41
UNKNOWN = 42
