#!/usr/bin/env python
"""
This file is part of TexText, an extension for the vector
illustration program Inkscape.

Copyright (c) 2006-2025 TexText developers.

TexText is released under the 3-Clause BSD license. See
file LICENSE.txt or go to https://github.com/textext/textext
for full license details.
"""

import argparse
import logging
import os
import glob
import shutil
import sys
import stat
import tempfile
import fnmatch

from textext.requirements_check import \
    set_logging_levels, \
    TexTextRequirementsChecker, \
    defaults, \
    TexTextLogFormatter, \
    SUCCESS

from textext.utility import Settings, Cache


# Hotfix for Inkscape 1.0.1 on Windows: HarfBuzz-0.0.typelib is missing
# in the Inkscape installation Python subsystem, hence we ship
# it manually and set the search path accordingly here
# ToDo: Remove this hotfix when Inkscape 1.0.2 is released and mark
#       Inkscape 1.0.1 as incompatible with TexText
if os.name == "nt":
    os.environ['GI_TYPELIB_PATH'] = os.path.abspath(os.path.join(os.path.dirname(__file__), "textext"))


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
    read_input = input
    while True:
        sys.stdout.write(question + prompt)
        choice = read_input().lower()
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
        for old_name, new_name in self.rel_filenames.items():
            src = os.path.join(self.stash_from, old_name)
            dst = os.path.join(self.tmp_dir, old_name)
            if os.path.isfile(src):
                if not os.path.isdir(os.path.dirname(dst)):
                    logger.debug("Creating directory `%s`" % os.path.dirname(dst) )
                    os.makedirs(os.path.dirname(dst))
                logger.debug("Stashing `%s`" % dst)
                shutil.copy2(src, dst)

    def __exit__(self, exc_type, exc_val, exc_tb):
        for old_name, new_name in self.rel_filenames.items():
            src = os.path.join(self.tmp_dir, old_name)
            dst = os.path.join(self.unstash_to, new_name)
            if os.path.isfile(src):
                if not os.path.isdir(os.path.dirname(dst)):
                    logger.debug("Creating directory `%s`" % os.path.dirname(dst) )
                    os.makedirs(os.path.dirname(dst))
                logger.debug("Restoring old `%s` -> `%s`" % (old_name, dst))
                shutil.copy2(src, dst)


class CopyFileOverDirectoryError(RuntimeError):
    pass


class CopyFileAlreadyExistsError(RuntimeError):
    pass


_ignore_patterns = [
    '__pycache__',
    '*.pyc',
    '*.log',
]


def is_ignored(filename):
    for pattern in _ignore_patterns:
        if fnmatch.fnmatch(filename, pattern):
            return True

    return False


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
        logger.debug("Creating directory `%s`" % dst)
        os.makedirs(dst)

    for file in glob.glob(src):
        basename = os.path.basename(file)
        destination = os.path.join(dst, basename)

        if is_ignored(basename):
            continue

        if os.path.exists(destination):
            if if_already_exists == "raise":
                logger.critical("Can't copy `%s`: `%s` already exists" % (file, destination))
                raise CopyFileAlreadyExistsError("Can't copy `%s`: `%s` already exists" % (file, destination))
            elif if_already_exists == "skip":
                logger.debug("Skipping `%s`" % file)
                continue
            elif if_already_exists == "overwrite":
                logger.debug("Overwriting `%s`" % destination)
                pass

        if os.path.isfile(file):
            logger.debug(f"Copying '{file}' to '{destination}'")
            shutil.copy(file, destination)
        else:
            logger.debug("Creating directory '{destination}'")

            if os.path.exists(destination):
                if not os.path.isdir(destination):
                    os.remove(destination)
                    os.mkdir(destination)
            else:
                os.mkdir(destination)
            copy_extension_files(os.path.join(file, "*"),
                                 destination,
                                 if_already_exists=if_already_exists)


def remove_previous_installation(extension_dir):
    previous_installation_files_and_folders = [
        "textext",                  # <- Whole textext directory (more recent versions of TexText)
        "asktext.py",               # <- Files directly in the extension directory (old versions of TexText)
        "default_packages.tex",
        "latexlogparser.py",
        "textext.inx",
        "textext.py",
        "typesetter.py",
        "win_app_paths.py",
    ]
    for file_or_dir in previous_installation_files_and_folders:
        file_or_dir = os.path.abspath(os.path.join(extension_dir, file_or_dir))
        if os.path.isfile(file_or_dir) or os.path.islink(file_or_dir):
            logger.debug("Removing `%s`" % file_or_dir)
            os.remove(file_or_dir)
        elif os.path.isdir(file_or_dir):
            logger.debug("Removing `%s`" % file_or_dir)
            shutil.rmtree(file_or_dir)
        else:
            logger.debug("`%s` is not found" % file_or_dir)


if __name__ == "__main__":

    EXIT_SUCCESS = 0
    EXIT_REQUIREMENT_CHECK_FAILED = 65
    EXIT_BAD_COMMAND_LINE_ARGUMENT_VALUE = 2

    parser = argparse.ArgumentParser(description='Install TexText')

    parser.add_argument(
        "--inkscape-extensions-path",
        default=None,
        type=str,
        help="Path to inkscape extensions directory"
    )

    parser.add_argument(
        "--inkscape-executable",
        default=None,
        type=str,
        help="Full path to inkscape executable"
    )

    parser.add_argument(
        "--pdflatex-executable",
        default=None,
        type=str,
        help="Full path to pdflatex executable"
    )

    parser.add_argument(
        "--lualatex-executable",
        default=None,
        type=str,
        help="Full path to lualatex executable"
    )

    parser.add_argument(
        "--xelatex-executable",
        default=None,
        type=str,
        help="Full path to xelatex executable"
    )

    parser.add_argument(
        "--typst-executable",
        default=None,
        type=str,
        help="Full path to typst executable"
    )

    parser.add_argument(
        "--portable-apps-dir",
        default=None,
        type=str,
        help="PortableApps installation directory (Windows only)"
    )

    parser.add_argument(
        "--skip-requirements-check",
        default=False,
        action='store_true',
        help="Bypass minimal requirements check"
    )

    parser.add_argument(
        "--use-tk",
        default=False,
        action='store_true',
        help="Use the Tk Interface (tkinter) for the user interface instead of the GTK3 UI"
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
        help="Keep files from previous installation which maybe modified by the user "
             "(e.g. preamble files) without prompting the user"
    )

    parser.add_argument(
        "--all-users",
        default=None,
        action='store_true',
        help="Install globally for all users"
    )

    parser.add_argument(
        "--color",
        default=defaults.console_colors,
        choices=("always", "never"),
        help="Enables/disable console colors"
    )

    parser.add_argument(
        "--verbose",
        default=False,
        action="store_true",
        help="Print additional messages during setup"
    )

    # Files which maybe modified by the user and which, be default, should
    # be kept upon user request
    files_to_keep = {  # old_name : new_name
        "default_packages.tex": "textext/default_packages.tex",  # old layout
        "textext/default_packages.tex": "textext/default_packages.tex",
        "textext/default_preamble_typst.typ": "textext/default_preamble_typst.typ"
    }

    args = parser.parse_args()

    if args.inkscape_extensions_path is None:
        args.inkscape_extensions_path = defaults.inkscape_user_extensions_path

    if args.color == "always":
        TexTextLogFormatter.enable_colors = True
    elif args.color == "never":
        TexTextLogFormatter.enable_colors = False

    set_logging_levels()
    logger = logging.getLogger('TexText')
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO if not args.verbose else logging.DEBUG)
    ch_formatter = TexTextLogFormatter("%(message)s")
    ch.setFormatter(ch_formatter)
    logger.addHandler(ch)

    # Explicit path spec since on Windows working directory must be the python.exe directory
    # which is usually read-only for standard users
    fh = logging.FileHandler(os.path.join(os.path.dirname(__file__), "textextsetup.log"), mode="w")
    fh.setLevel(logging.DEBUG)
    fh_formatter = logging.Formatter("[%(name)s][%(levelname)6s]: %(message)s")
    fh.setFormatter(fh_formatter)
    logger.addHandler(fh)

    logger.info("Installing TexText with the following arguments:")
    logger.info("".join(f"{key}: {value}, " for key, value in vars(args).items())[:-2])

    # Address special Portable Apps directory structure
    if args.portable_apps_dir:
        if not os.path.isdir(args.portable_apps_dir):
            logger.error("Path specified for PortableApps is not a valid directory!")
            exit(EXIT_REQUIREMENT_CHECK_FAILED)
        if os.name != "nt":
            logger.error("The --portable-apps-dir argument can only be used under MS Windows!")
            exit(EXIT_REQUIREMENT_CHECK_FAILED)
        args.inkscape_executable = os.path.join(args.portable_apps_dir,
                                                "InkscapePortable\\App\\Inkscape\\bin\\inkscape.exe")
        args.inkscape_extensions_path = os.path.join(args.portable_apps_dir,
                                                     "InkscapePortable\\Data\\settings\\extensions")
        settings = Settings(directory=os.path.join(args.portable_apps_dir, "InkscapePortable\\Data\\settings\\textext"))
    else:
        settings = Settings(directory=defaults.textext_config_path)

    CachedSettings = Cache(directory=settings.directory)
    CachedSettings.delete_file()

    checker = TexTextRequirementsChecker(logger, settings)

    for executable_name in ["inkscape", "lualatex", "pdflatex", "xelatex", "typst"]:
        executable_path = getattr(args, "%s_executable" % executable_name)
        if executable_path is not None:
            if not checker.check_executable(executable_path):
                logger.error("Bad `%s` executable provided: `%s`. Abort installation." % (executable_name, executable_path))
                exit(EXIT_BAD_COMMAND_LINE_ARGUMENT_VALUE)

            settings["%s-executable" % executable_name] = executable_path
        else:
            settings["%s-executable" % executable_name] = None

    if not args.skip_requirements_check:

        check_result = checker.check()
        if not check_result:
            logger.error("Automatic requirements check found issue")
            logger.error("Follow instruction above and run install script again")
            logger.error("--> To bypass requirement check and force installation of TexText")
            logger.error("--> pass the `--skip-requirements-check` option to setup.py:")
            logger.error("--> setup.py --skip-requirements-check")
            exit(EXIT_REQUIREMENT_CHECK_FAILED)

    if not args.skip_extension_install:
        if args.all_users:
            # Determine path of global installation if requested
            logger.info("Global installation requested, trying to find system extension path...")

            if args.inkscape_executable is not None:
                logger.info("Inkscape executable given as `%s`" % args.inkscape_executable)
                inkscape_executable = args.inkscape_executable
            else:
                # This is quite complicated and in fact only necessary on Windows.
                # In Windows inkscape.exe is not in the system path so we use the
                # tweaked path return by default.get_system_path() and iterate
                # over its elements
                # ToDo: Make this smarter and more intuitive!
                logger.info("Trying to find Inkscape executable automatically...")
                inkscape_executable = None
                for inkscape_exe_name in defaults.executable_names["inkscape"]:
                    for path in defaults.get_system_path():
                        test_path = os.path.join(path, inkscape_exe_name)
                        if os.path.isfile(test_path) and os.access(test_path, os.X_OK):
                            inkscape_executable = test_path
                            logger.info("Inkscape executable found as `%s`" % inkscape_executable)
                            break
                if inkscape_executable is None:
                    logger.error("No Inkscape executable found in system path.")
                    exit(EXIT_BAD_COMMAND_LINE_ARGUMENT_VALUE)

            # Query the system extension path
            [args.inkscape_extensions_path, err] = defaults.inkscape_system_extensions_path(
                inkscape_executable)
            if args.inkscape_extensions_path is None:
                logger.error("Determination of system extension directory failed (Error message: %s)" % err)
                exit(EXIT_BAD_COMMAND_LINE_ARGUMENT_VALUE)
            else:
                logger.info("System extensions are in %s" % args.inkscape_extensions_path)

            # Check write access in system extension path
            if not os.access(args.inkscape_extensions_path, os.W_OK):
                logger.error(
                    "You do not have write privileges in `%s`! Please run setup script as administrator/ with sudo."
                    % args.inkscape_extensions_path)
                exit(EXIT_BAD_COMMAND_LINE_ARGUMENT_VALUE)
        else:
            # local installation
            args.inkscape_extensions_path = os.path.expanduser(args.inkscape_extensions_path)

        if args.keep_previous_installation_files is None:
            logger.debug("Checking for previous installation files which have been modified by the user")
            found_files_to_keep = {}
            for old_filename, new_filename in files_to_keep.items():
                if not os.path.isfile(os.path.join(args.inkscape_extensions_path, old_filename)):
                    logger.debug("%s not found" % old_filename)
                else:
                    logger.debug("%s found" % old_filename)
                    if not os.path.isfile(os.path.join("extension", new_filename)):
                        logger.debug("`%s` is not found in distribution, keep old file" % new_filename)
                        found_files_to_keep[old_filename] = new_filename
                        continue
                    with open(os.path.join(args.inkscape_extensions_path, old_filename)) as f_old, \
                            open(new_filename) as f_new:
                        if f_old.read() != f_new.read():
                            logger.debug("Content of `%s` are not identical version in distribution" % old_filename)
                            found_files_to_keep[old_filename] = new_filename
                        else:
                            logger.debug("Content of `%s` is identical to distribution" % old_filename)

            files_to_keep = {}

            if len(found_files_to_keep) > 0:
                file_s = "file" if len(found_files_to_keep) == 1 else "files"
                for old_filename, new_filename in found_files_to_keep.items():
                    if os.path.isfile(os.path.join("extension", new_filename)):
                        logger.warning("Existing `%s` differs from newer version in distribution" % old_filename)
                        if query_yes_no("Keep `%s` from previous installation?" % old_filename):
                            files_to_keep[old_filename] = new_filename

                args.keep_previous_installation_files = True
            else:
                args.keep_previous_installation_files = False

        if not args.keep_previous_installation_files:
            files_to_keep = {}

        with TemporaryDirectory() as tmp_dir, \
                StashFiles(stash_from=args.inkscape_extensions_path,
                           rel_filenames=files_to_keep,
                           tmp_dir=tmp_dir
                           ):
            logger.info(f"Starting installation of TexText into {args.inkscape_extensions_path}...")
            source_path = os.path.dirname(os.path.abspath(__file__))
            if os.path.dirname(source_path) == args.inkscape_extensions_path:
                logger.error("Can't install extension from itself")
                exit(EXIT_BAD_COMMAND_LINE_ARGUMENT_VALUE)
            remove_previous_installation(args.inkscape_extensions_path)
            copy_extension_files(
                src=os.path.join(source_path, "textext"),
                dst=args.inkscape_extensions_path,
                if_already_exists="overwrite"
            )

        if args.use_tk:
            logger.info("Force usage of Tk Interface (tkinter), setting 'gui_toolkit' to 'tk'")
            settings["gui"]["toolkit"] = "tk"
        else:
            try:
                del(settings["gui"]["toolkit"])
            except (KeyError, TypeError) as _:
                pass

        settings.save()

    logger.log(SUCCESS, "--> TexText has been SUCCESSFULLY installed on your system <--")

    exit(EXIT_SUCCESS)
