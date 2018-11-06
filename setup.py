#!/usr/bin/env python

import argparse
import logging
import re
import os
import glob
import shutil
import subprocess
import sys
import stat
import tempfile


# taken from https://stackoverflow.com/a/3041990/1741477
def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")


class TemporaryDirectory(object):
    """ Mimic tempfile.TemporaryDirectory from python3 """
    def __init__(self):
        self.dir_name = None

    def __enter__(self):
        self.dir_name = tempfile.mkdtemp("textext_")
        return self.dir_name

    def __exit__(self, exc_type, exc_val, exc_tb):

        def retry_with_chmod(func, path, exec_info):
            os.chmod(path, stat.S_IWRITE)
            func(path)

        if self.dir_name:
            shutil.rmtree(self.dir_name, onerror=retry_with_chmod)


class StashFiles(object):
    def __init__(self, stash_from, rel_filenames, tmp_dir, unstash_to=None):
        self.stash_from = stash_from
        self.unstash_to = stash_from if unstash_to is None else unstash_to
        self.rel_filenames = rel_filenames
        self.tmp_dir = tmp_dir

    def __enter__(self):
        for old_name, new_name in self.rel_filenames.iteritems():
            src = os.path.join(self.stash_from, old_name)
            dst = os.path.join(self.tmp_dir, old_name)
            if os.path.isfile(src):
                if not os.path.isdir(os.path.dirname(dst)):
                    logger.info("Creating directory `%s`" % os.path.dirname(dst) )
                    os.makedirs(os.path.dirname(dst))
                logger.info("Stashing `%s`" % dst)
                shutil.copy2(src, dst)

    def __exit__(self, exc_type, exc_val, exc_tb):
        for old_name, new_name in self.rel_filenames.iteritems():
            src = os.path.join(self.tmp_dir, old_name)
            dst = os.path.join(self.unstash_to, new_name)
            if os.path.isfile(src):
                if not os.path.isdir(os.path.dirname(dst)):
                    logger.info("Creating directory `%s`" % os.path.dirname(dst) )
                    os.makedirs(os.path.dirname(dst))
                logger.info("Restoring old `%s` -> `%s`" % (old_name, dst))
                shutil.copy2(src, dst)


class LoggingColors(object):

    enable_colors = True

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
            COLOR_RESET,
            BG_DEFAULT + FG_LIGHT_BLUE,
            BG_DEFAULT + FG_YELLOW,
            BG_DEFAULT + FG_RED,
            BG_DEFAULT + FG_GREEN,
            BG_DEFAULT + FG_YELLOW,
            BG_RED + FG_WHITE,
        ]
        if not LoggingColors.enable_colors:
            colors = [""]*len(colors)
            COLOR_RESET=""
        return {name: (level, color) for level, name, color in zip(levels, names, colors)}, COLOR_RESET


get_levels_colors = LoggingColors()

def colorize_logging():
    level_colors, COLOR_RESET = get_levels_colors()
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
        self.is_critical = None

    @property
    def color(self):
        if self.value == True:
            return get_levels_colors()[0]["SUCCESS "][1]
        elif self.value == False:
            return get_levels_colors()[0]["ERROR   "][1]
        else:
            return get_levels_colors()[0]["UNKNOWN "][1]

    def print_to_logger(self, offset=0, prefix="", parent=None):
        _, reset_color = get_levels_colors()

        if self.is_critical:
            lvl = logging.CRITICAL
        elif self.value == True:
            lvl = logging.ERROR + 1  # success
        elif self.value == False:
            lvl = logging.INFO
        else:
            lvl = logging.ERROR + 2  # unknown

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

    check_result.mark_critical_errors()

    check_result.print_to_logger()

    return check_result.value


def remove_previous_installation(extension_dir):
    previous_installation_files_and_folders = [
        "asktext.py",
        "default_packages.tex",
        "inkex45.py",
        "latexlogparser.py",
        "scribus_textext.py",
        "textext",
        "textext.inx",
        "textext.py",
        "typesetter.py",
        "win_app_paths.py",
    ]
    for file_or_dir in previous_installation_files_and_folders:
        file_or_dir = os.path.abspath(os.path.join(extension_dir, file_or_dir))
        if os.path.isfile(file_or_dir):
            logger.info("Removing `%s`" % file_or_dir)
            os.remove(file_or_dir)
        elif os.path.isdir(file_or_dir):
            logger.info("Removing `%s`" % file_or_dir)
            shutil.rmtree(file_or_dir)
        else:
            logger.debug("`%s` is not found" % file_or_dir)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Install TexText')

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

    parser.add_argument(
        "--keep-previous-installation-files",
        default=None,
        action='store_true',
        help="Keep/discard files from previous installation, suppress prompt"
    )

    parser.add_argument(
        "--color",
        default="always",
        choices=("always", "never"),
        help="Enables/disable console colors"
    )

    colorize_logging()
    logger = logging.getLogger('TexText')
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('[%(name)s][%(levelname)6s]: %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    files_to_keep = {  # old_name : new_name
        "default_packages.tex": "textext/default_packages.tex",  # old layout
        "textext/default_packages.tex": "textext/default_packages.tex"  # new layout
    }

    args = parser.parse_args()
    args.inkscape_extensions_path = os.path.expanduser(args.inkscape_extensions_path)

    if args.keep_previous_installation_files is None:
        found_files_to_keep = {}
        for old_filename, new_filename in files_to_keep.iteritems():
            if not os.path.isfile(os.path.join(args.inkscape_extensions_path, old_filename)):
                logger.debug("%s not found" % old_filename)
            else:
                logger.debug("%s found" % old_filename)
                with open(os.path.join(args.inkscape_extensions_path, old_filename)) as f_old, \
                        open(os.path.join("extension", new_filename)) as f_new:
                    if f_old.read() != f_new.read():
                        logger.debug("Content of `%s` are not identical version in distribution" % old_filename)
                        found_files_to_keep[old_filename] = new_filename
                    else:
                        logger.debug("Content of `%s` is identical to distribution" % old_filename)

        files_to_keep = found_files_to_keep

        if len(files_to_keep) > 0:
            file_s = "file" if len(files_to_keep) == 1 else "files"
            for old_filename in files_to_keep.keys():
                logger.warn("Existing `%s` differs from newer version in distribution" % old_filename)
            args.keep_previous_installation_files = query_yes_no("Keep above %s from previous installation?" % file_s)
        else:
            args.keep_previous_installation_files = False

    if not args.keep_previous_installation_files:
        files_to_keep = {}

    if args.color == "always":
        LoggingColors.enable_colors = True
    elif args.color == "never":
        LoggingColors.enable_colors = False

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

        with TemporaryDirectory() as tmp_dir, \
                StashFiles(stash_from=args.inkscape_extensions_path,
                           rel_filenames=files_to_keep,
                           tmp_dir=tmp_dir
                           ):
            remove_previous_installation(args.inkscape_extensions_path)

            copy_extension_files(
                src="extension/*",
                dst=args.inkscape_extensions_path,
                if_already_exists="overwrite"
            )

    exit(0)
