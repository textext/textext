
import abc
import logging
import os
import re
import subprocess
import sys


class Defaults(object):
    __metaclass__ = abc.ABCMeta
    @abc.abstractproperty
    def python(self): pass

    @abc.abstractproperty
    def inkscape(self): pass

    @abc.abstractproperty
    def ghostscript(self): pass

    @abc.abstractproperty
    def pstoedit(self): pass

    @abc.abstractproperty
    def pdflatex(self): pass

    @abc.abstractproperty
    def lualatex(self): pass

    @abc.abstractproperty
    def xelatex(self): pass

    @abc.abstractproperty
    def console_colors(self):pass

    @abc.abstractproperty
    def inkscape_extensions_path(self): pass


class LinuxDefaults(Defaults):
    python = "python2.7"
    inkscape = "inkscape"
    ghostscript = "ghostscript"
    pstoedit = "pstoedit"
    pdflatex = "pdflatex"
    lualatex = "lualatex"
    xelatex = "xelatex"
    pdf2svg = "pdf2svg"
    console_colors = "always"

    @property
    def inkscape_extensions_path(self):
        return os.path.expanduser("~/.config/inkscape/extensions")


class WindowsDefaults(Defaults):

    def __init__(self):
        # Append the location of our apps to the system path
        sys.path.append("extension/textext")
        import win_app_paths as wap

        paths = os.environ.get('PATH', '').split(os.path.pathsep)
        for result in [wap.get_pstoedit_dir(), wap.get_ghostscript_dir()]:
            if result and result is not wap.IS_IN_PATH:
                paths += [os.path.join(result)]

        result = wap.get_imagemagick_command()
        if result:
            paths += [os.path.join(os.path.dirname(result))]

        os.environ['PATH'] = os.path.pathsep.join(paths)

    python = "python.exe"
    inkscape = "inkscape.exe"
    ghostscript = "gs.exe"
    pstoedit = "pstoedit.exe"
    pdflatex = "pdflatex.exe"
    lualatex = "lualatex.exe"
    xelatex = "xelatex.exe"
    pdf2svg = "pdf2svg.exe"
    console_colors = "never"

    @property
    def inkscape_extensions_path(self):
        return os.path.join(os.getenv("APPDATA"), "inkscape\extensions")


class LoggingColors(object):

    enable_colors = False

    def __call__(self):
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

        levels = [
            VERBOSE,          # 5
            logging.DEBUG,    # 10
            logging.INFO,     # 20
            logging.WARNING,  # 30
            logging.ERROR,    # 40
            SUCCESS,          # 41
            UNKNOWN,          # 42
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
            COLOR_RESET,
            COLOR_RESET,
            BG_DEFAULT + FG_LIGHT_BLUE,
            BG_YELLOW + FG_WHITE,
            BG_DEFAULT + FG_RED,
            BG_DEFAULT + FG_GREEN,
            BG_DEFAULT + FG_YELLOW,
            BG_RED + FG_WHITE,
        ]
        if not LoggingColors.enable_colors:
            colors = [""]*len(colors)
            COLOR_RESET=""
        return {name: (level, color) for level, name, color in zip(levels, names, colors)}, COLOR_RESET


def set_logging_levels():
    level_colors, COLOR_RESET = get_levels_colors()
    for name, (level,color) in level_colors.items():
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
    def __init__(self, value, messages, nested=None, is_and_node=False, is_or_node=False, is_not_node=False):
        self.value = TrinaryLogicValue(value)
        self.messages = messages
        self.nested = nested if nested is not None else []

        self.is_and_node = is_and_node
        self.is_or_node = is_or_node
        self.is_not_node = is_not_node
        self.is_critical = None

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
                tail = parent.color+"/-and-"+self.color+nest_symbol+reset_color
            elif parent.is_or_node:
                tail = parent.color+"/--or-"+self.color+nest_symbol+reset_color
            elif parent.is_not_node:
                tail = parent.color+"/-not-"+self.color+nest_symbol+reset_color
            else:
                tail = parent.color+"/-----"+self.color+nest_symbol+reset_color
        else:
            tail = self.color+nest_symbol+reset_color

        if not parent:
            suffix = ""
        elif parent.nested[-1] is self:
            suffix = "      "
        else:
            suffix = parent.color+"|"+reset_color+"     "

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
            nst.print_to_logger(logger, offset + 1, prefix=prefix+suffix, parent=self)

    def flatten(self):
        if len(self.nested) == 0:
            return self

        for i, nst in enumerate(self.nested):
            self.nested[i] = nst.flatten()

        if self.nested[0].is_or_node and self.is_or_node:
            return RequirementCheckResult(
                self.value,
                self.nested[0].messages + self.messages,
                self.nested[0].nested + self.nested[1:],
                is_or_node=True
            )

        if self.nested[0].is_and_node and self.is_and_node:
            return RequirementCheckResult(
                self.value,
                self.nested[0].messages + self.messages,
                self.nested[0].nested + self.nested[1:],
                is_and_node=True
            )

        if self.nested[-1].is_or_node and self.is_or_node:
            return RequirementCheckResult(
                self.value,
                self.messages + self.nested[-1].messages,
                self.nested[:-1] + self.nested[-1].nested,
                is_or_node=True
            )

        if self.nested[-1].is_and_node and self.is_and_node:
            return RequirementCheckResult(
                self.value,
                self.messages + self.nested[-1].messages,
                self.nested[:-1] + self.nested[-1].nested,
                is_and_node=True
            )

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


class Requirement(object):
    def __init__(self, criteria, *args, **kwargs):
        self.criteria = lambda: criteria(*args, **kwargs)
        self._prepended_messages = {"ANY": [], "SUCCESS": [], "ERROR": [], "UNKNOWN": []}
        self._appended_messages = {"ANY": [], "SUCCESS": [], "ERROR": [], "UNKNOWN": []}
        self._overwrite_messages = None

    def check(self):
        result = self.criteria()
        # print(self,self._overwrite_messages)
        if self._overwrite_messages:
            result.messages = self._overwrite_messages
        result.messages = self._prepended_messages["ANY"] + result.messages
        if result.value == TrinaryLogicValue(True):
            result.messages = self._prepended_messages["SUCCESS"] + result.messages
        if result.value == TrinaryLogicValue(False):
            result.messages = self._prepended_messages["ERROR"] + result.messages
        if result.value == TrinaryLogicValue(None):
            result.messages = self._prepended_messages["UNKNOWN"] + result.messages

        result.messages += self._appended_messages["ANY"]
        if result.value == TrinaryLogicValue(True):
            result.messages += self._appended_messages["SUCCESS"]
        if result.value == TrinaryLogicValue(False):
            result.messages += self._appended_messages["ERROR"]
        if result.value == TrinaryLogicValue(None):
            result.messages += self._appended_messages["UNKNOWN"]
        # print(self,result.messages)
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


class TexTextRequirementsChecker(object):

    def __init__(self, logger):
        self.logger = logger
        pass

    def find_executable(self, executable_name):
        messages = []
        for path in os.environ["PATH"].split(os.path.pathsep):
            full_path_guess = os.path.join(path, executable_name)
            self.logger.log(VERBOSE, "Looking for `%s` in `%s`" % (executable_name, path))
            if os.path.isfile(full_path_guess):
                self.logger.log(VERBOSE, "`%s` is found at `%s`" % (executable_name, path))
                messages.append("`%s` is found at `%s`" % (executable_name, path))
        if len(messages) > 0:
            return RequirementCheckResult(True, messages)
        messages.append("`%s` is NOT found in PATH" % (executable_name))
        return RequirementCheckResult(False, messages)

    def find_PyGtk2(self):
        try:
            subprocess.check_call([defaults.python, "-c", "import pygtk; pygtk.require('2.0'); import gtk;"],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except (OSError, subprocess.CalledProcessError):
            return RequirementCheckResult(False, ["PyGTK2 is not found"])

        return RequirementCheckResult(True, ["PyGTK2 is found"])

    def find_TkInter(self):
        try:
            subprocess.check_call([defaults.python, "-c", "import TkInter; import tkMessageBox; import tkFileDialog;"],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except (OSError, subprocess.CalledProcessError):
            return RequirementCheckResult(False, ["TkInter is not found"])

        return RequirementCheckResult(True, ["TkInter is found"])

    def find_ghostscript(self, version):
        try:
            p = subprocess.Popen([defaults.ghostscript, "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = p.communicate()
        except (OSError, subprocess.CalledProcessError):
            return RequirementCheckResult(False, ["ghostscript=%s is not found" % version])

        first_stdout_line = stdout.decode("utf-8").split("\n")[0]
        m = re.search(r"(\d+.\d+)", first_stdout_line)
        if m:
            found_version = m.group(1)
            if version == found_version:
                return RequirementCheckResult(True, ["ghostscript=%s is found" % version])
            else:
                return RequirementCheckResult(False, [
                    "ghostscript=%s is not found (but ghostscript=%s is found)" % (version, found_version)])
        return RequirementCheckResult(None, ["Can't determinate ghostscript version"])

    def find_pstoedit(self, version):
        try:
            p = subprocess.Popen([defaults.pstoedit], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = p.communicate()
        except (OSError, subprocess.CalledProcessError):
            return RequirementCheckResult(False, ["pstoedit=%s is not found" % version])

        first_stderr_line = stderr.decode("utf-8").split("\n")[0]
        m = re.search(r"version (\d+.\d+)", first_stderr_line)
        if m:
            found_version = m.group(1)
            if version == found_version:
                return RequirementCheckResult(True, ["pstoedit=%s is found" % version])
            else:
                return RequirementCheckResult(False, [
                    "pstoedit=%s is not found (but pstoedit=%s is found)" % (version, found_version)])
        return RequirementCheckResult(None, ["Can't determinate pstoedit version"])

    def check(self):

        textext_requirements = (
                Requirement(self.find_executable, defaults.inkscape).prepend_message("ANY", 'Detect inkscape')
                &
                Requirement(self.find_executable, defaults.python).prepend_message("ANY", 'Detect `python2.7`')
                &
                (
                        Requirement(self.find_executable, defaults.pdflatex) |
                        Requirement(self.find_executable, defaults.lualatex) |
                        Requirement(self.find_executable, defaults.xelatex)
                ).overwrite_check_message("Detect *latex")
                &
                (
                        Requirement(self.find_PyGtk2) |
                        Requirement(self.find_TkInter)
                ).overwrite_check_message("Detect GUI library")
                &
                (
                        (
                                ~(
                                        Requirement(self.find_pstoedit, "3.70") &
                                        Requirement(self.find_ghostscript, "9.22")
                                ).overwrite_check_message("Detect incompatible versions of psedit+ghostscript")
                                &
                                (
                                        Requirement(self.find_executable, defaults.pstoedit) &
                                        Requirement(self.find_executable, defaults.ghostscript)
                                )
                        ).overwrite_check_message("Detect compatible psedit+ghostscript versions")
                        |
                        (
                            Requirement(self.find_executable, defaults.pdf2svg)
                        ).prepend_message("ANY", "Detect pdf2svg:")
                ).overwrite_check_message("Detect pdf->svg conversion utility")
        ).overwrite_check_message("TexText requirements")

        check_result = textext_requirements.check()

        check_result = check_result.flatten()

        check_result.mark_critical_errors()

        check_result.print_to_logger(self.logger)

        return check_result.value


get_levels_colors = LoggingColors()

if sys.platform.startswith("win"):
    defaults = WindowsDefaults()
else:
    defaults = LinuxDefaults()


VERBOSE = 5
SUCCESS = 41
UNKNOWN = 42