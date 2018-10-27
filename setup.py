#!/usr/bin/env python

import argparse
import logging
import re
import os
import glob
import shutil
import subprocess
import sys

COLOR_RESET = "\033[0m"

def get_levels_colors():
    RESET = COLOR_RESET
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
        logging.DEBUG,
        logging.INFO,
        logging.WARNING,
        logging.ERROR,
        logging.ERROR + 1,  # SUCCESS
        logging.ERROR + 2,  # UNKNOWN
        logging.CRITICAL
    ]
    names = [
        "DEBUG   ",
        "INFO    ",
        "WARNING ",
        "ERROR   ",
        "SUCCESS ",
        "UNKNOWN ",
        "CRITICAL"
    ]
    colors = [
        RESET,
        BG_DEFAULT + FG_LIGHT_BLUE,
        BG_DEFAULT + FG_YELLOW,
        BG_DEFAULT + FG_RED,
        BG_DEFAULT + FG_GREEN,
        BG_DEFAULT + FG_YELLOW,
        BG_RED + FG_WHITE,
    ]
    return {name: (level,color) for level, name, color in zip(levels, names, colors)}

def colorize_logging():
    level_colors = get_levels_colors()
    for name, (level,color) in level_colors.items():
        logging.addLevelName(level, color + name + COLOR_RESET)


class CopyFileOverDirectoryError(RuntimeError):
    pass


class CopyFileAlreadyExistsError(RuntimeError):
    pass


def copy_extension_files(src, dst, if_already_exists="raise"):
    """
    src: glob expresion to copy from
    dst: destination directory 
    if_already_exists: action on existing files. One of "raise" (default), "skip", "overwrite"
    """
    if os.path.exists(dst):
        if not os.path.isdir(dst):
            logger.critical("Can't copy files to `%s`: it's not a directory")
            raise CopyFileOverDirectoryError("Can't copy files to `%s`: it's not a directory")
    else:
        logger.info("Creating directory `%s`" % dst)
        os.makedirs(dst)

    for file in glob.glob(src):
        basename = os.path.basename(file)
        destination = os.path.join(dst, basename)
        if os.path.exists(destination):
            if if_already_exists == "raise":
                logger.critical("Can't copy `%s`: `%s` already exists" % (file, destination))
                raise CopyFileAlreadyExistsError("Can't copy `%s`: `%s` already exists" % (file, destination))
            elif if_already_exists == "skip":
                logger.info("Skipping `%s`" % file)
                continue
            elif if_already_exists == "overwrite":
                logger.info("Overwriting `%s`" % destination)
                pass

        if os.path.isfile(file):
            logger.info("Copying `%s` to `%s`" % (file, destination))
            shutil.copy(file, destination)
        else:
            logger.info("Creating directory `%s`" % destination)

            if os.path.exists(destination):
                if not os.path.isdir(destination):
                    os.remove(destination)
                    os.mkdir(destination)
            else:
                os.mkdir(destination)
            copy_extension_files(os.path.join(file, "*"),
                                 destination,
                                 if_already_exists=if_already_exists)


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

    @property
    def color(self):
        if self.value == True:
            return get_levels_colors()["SUCCESS "][1]
        elif self.value == False:
            return get_levels_colors()["ERROR   "][1]
        else:
            return get_levels_colors()["UNKNOWN "][1]

    def print_to_logger(self, offset=0, prefix="", parent=None):
        reset_color = COLOR_RESET
        if self.value == True:
            lvl = logging.ERROR + 1  # success
        elif self.value == False:
            lvl = logging.ERROR
            if offset == 0:
                lvl = logging.CRITICAL
        else:
            lvl = logging.ERROR + 2  # unknown

        if self.nested:
            nest_symbol = "+"
        else:
            nest_symbol = "*"

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
            nst.print_to_logger(offset + 1, prefix=prefix+suffix, parent=self)

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


def check_requirements():
    def find_executable(executable_name):
        messages = []
        for path in os.environ["PATH"].split(":"):
            full_path_guess = os.path.join(path, executable_name)
            logger.debug("Looking for `%s` in `%s`" % (executable_name, path))
            if os.path.isfile(full_path_guess):
                logger.debug("`%s` is found at `%s`" % (executable_name, path))
                messages.append("`%s` is found at `%s`" % (executable_name, path))
        if len(messages) > 0:
            return RequirementCheckResult(True, messages)
        messages.append("`%s` is NOT found in PATH" % (executable_name))
        return RequirementCheckResult(False, messages)

    def find_PyGtk2():
        try:
            subprocess.check_call(["python2.7", "-c", "import pygtk; pygtk.require('2.0'); import gtk;"])
        except (OSError, subprocess.CalledProcessError):
            return RequirementCheckResult(False, ["PyGTK2 is not found"])

        return RequirementCheckResult(True, ["PyGTK2 is found"])

    def find_TkInter():
        try:
            subprocess.check_call(["python2.7", "-c", "import TkInter; import tkMessageBox; import tkFileDialog;"],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except (OSError, subprocess.CalledProcessError):
            return RequirementCheckResult(False, ["TkInter is not found"])

        return RequirementCheckResult(True, ["TkInter is found"])

    def find_ghostscript(version):
        try:
            p = subprocess.Popen(["ghostscript", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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

    def find_pstoedit(version):
        try:
            p = subprocess.Popen(["pstoedit"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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

    textext_requirements = (
            Requirement(find_executable, "python2.7").prepend_message("ANY", 'Detect `pytohn2.7`')
            &
            (
                    Requirement(find_executable, "pdflatex") |
                    Requirement(find_executable, "lualatex") |
                    Requirement(find_executable, "xelatex")
            ).overwrite_check_message("Detect *latex")
            &
            (
                    Requirement(find_PyGtk2) |
                    Requirement(find_TkInter)
            ).overwrite_check_message("Detect GUI library")
            &
            (
                    Requirement(find_executable, "convert") |
                    Requirement(find_executable, "magick")
            ).overwrite_check_message("Detect pdf->png conversion utility")
            &
            (
                    (
                            ~(
                                    Requirement(find_pstoedit, "3.70") &
                                    Requirement(find_ghostscript, "9.22")
                            ).overwrite_check_message("Detect incompatible versions of psedit+ghostscript")
                            &
                            (
                                    Requirement(find_executable, "pstoedit") &
                                    Requirement(find_executable, "ghostscript")
                            )
                    ).overwrite_check_message("Detect compatible psedit+ghostscript versions")
                    |
                    (
                        Requirement(find_executable, "pdf2svg")
                    ).prepend_message("ANY", "Detect pdf2svg:")
            ).overwrite_check_message("Detect pdf->svg conversion utility")
    ).overwrite_check_message("TexText requirements")

    check_result = textext_requirements.check()

    check_result = check_result.flatten()

    check_result.print_to_logger()

    return check_result.value


colorize_logging()
logger = logging.getLogger('TexText')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('[%(name)s][%(levelname)6s]: %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Install TexText')

    if_already_exists = parser.add_mutually_exclusive_group()
    if_already_exists.add_argument(
        "--overwrite-if-exist",
        dest='if_already_exists',
        action='store_const',
        const="overwrite",
        default="raise",
        help="Overwrite already existing extension files"
    )
    if_already_exists.add_argument(
        "--skip-if-exist",
        dest='if_already_exists',
        action='store_const',
        const="skip",
        help="Retain already existing extension files"
    )

    parser.add_argument(
        "--inkscape-extensions-path",
        default=os.path.expanduser("~/.config/inkscape/extensions"),
        help="Path to inkscape extensions directory"
    )

    parser.add_argument(
        "--skip-requirements-check",
        default=False,
        action='store_true',
        help="Bypass minimal requirements check"
    )

    parser.add_argument(
        "--skip-extension-install",
        default=False,
        action='store_true',
        help="Don't install extension"
    )

    args = parser.parse_args()

    if not args.skip_requirements_check:
        check_result = check_requirements()
        if check_result == None:
            logger.info("Automatic requirements check is incomplete")
            logger.info("Please check requirements list manually and run:")
            logger.info(" ".join(sys.argv + ["--skip-requirements-check"]))
            exit(64)

        if check_result == False:
            logger.info("Automatic requirements check found issue")
            logger.info("Follow instruction above and run install script again")
            logger.info("To bypass requirement check pass `--skip-requirements-check` to setup.py")
            exit(65)

    if not args.skip_extension_install:
        try:
            copy_extension_files(
                src="extension/*",
                dst=args.inkscape_extensions_path,
                if_already_exists=args.if_already_exists
            )
        except CopyFileAlreadyExistsError:
            logger.info("Hint: add `--overwrite-if-exist` option to overwrite existing files and directories")
            logger.info("Hint: add `--skip-if-exist` option to retain existing files and directories")
            exit(66)

    exit(0)
