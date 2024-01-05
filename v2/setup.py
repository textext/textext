"""
This file is part of TexText, an extension for the vector
illustration program Inkscape.

Copyright (c) 2006-2023 TexText developers.

TexText is released under the 3-Clause BSD license. See
file LICENSE.txt or go to https://github.com/textext/textext
for full license details.
"""
import argparse
import glob
import os
import shutil
import sys
import tempfile
from typing import Dict, List
from textext.settings import SettingsTexText, Cache, Cmds
from textext.utils.dependencies import DependencyCheck
from textext.utils.environment import system_env
from textext.utils.log_util import install_logger


def query_yes_no(question, default="yes"):
    """
    Ask a yes/no question via raw_input() and return their answer. Returns True for "yes" or False for "no".

    Taken from https://stackoverflow.com/a/3041990/1741477
    """
    valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("Invalid default answer: '{0}'".format(default))

    read_input = input

    while True:
        sys.stdout.write(question + prompt)
        choice = read_input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' (or 'y' or 'n').\n")


class StashFiles(object):
    """
    A context manager copying some files from a source into a target directory upon
    entering and copying them back when exiting. Used to avoid that protected
    files are deleted during an update.

    """
    def __init__(self, stash_from: str, rel_filenames: Dict[str, str], tmp_dir: str, unstash_to: str = None):
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
                    logger.info("Creating directory `{0}`".format(os.path.dirname(dst)))
                    os.makedirs(os.path.dirname(dst))
                logger.info("Stashing `{0}`".format(src))
                shutil.copy2(src, dst)

    def __exit__(self, exc_type, exc_val, exc_tb):
        for old_name, new_name in self.rel_filenames.items():
            src = os.path.join(self.tmp_dir, old_name)
            dst = os.path.join(self.unstash_to, new_name)
            if os.path.isfile(src):
                if not os.path.isdir(os.path.dirname(dst)):
                    logger.info("Creating directory `{0}`".format(os.path.dirname(dst)))
                    os.makedirs(os.path.dirname(dst))
                logger.info("Restoring old `{0}` -> `{1}`".format(old_name, dst))
                shutil.copy2(src, dst)


def remove_previous_installation(dir_path: str):
    """
    Removes directory dir_path and all of its content.
    Silently discards if anything goes wrong.
    """
    if os.path.exists(dir_path):
        with logger.info("Removing `{0}`".format(dir_path)):
            try:
                shutil.rmtree(dir_path)
            except (OSError, PermissionError, NotADirectoryError) as err:
                msg = "Unable to remove {0}. Reason: {1}. Trying to continue, anyway...".\
                    format(dir_path, err.strerror)
                logger.warning(msg)


def copy_extension_files(src: str, dst: str):
    """
    Copies all files and subirs from src to dst. All existing items will be overwritten.
    Raises a RuntimeError if anything fails.
    """

    with logger.info("Trying to copy files into `{0}`".format(dst)):
        try:
            if os.path.exists(dst):
                if not os.path.isdir(dst):
                    msg = "Can't copy files to `{0}`: it's not a directory".format(dst)
                    logger.critical(msg)
                    raise RuntimeError(msg)
            else:
                logger.info("Creating directory `{0}`".format(dst))
                os.makedirs(dst)

            for file in glob.glob(src):
                basename = os.path.basename(file)
                destination = os.path.join(dst, basename)

                if os.path.isfile(file):
                    logger.info("Copying `{0}` to `{1}`".format(file, destination))
                    shutil.copy(file, destination)
                else:
                    if os.path.exists(destination):
                        if not os.path.isdir(destination):
                            os.remove(destination)
                            os.mkdir(destination)
                    else:
                        logger.info("Creating directory `{0}`".format(destination))
                        os.mkdir(destination)

                    copy_extension_files(os.path.join(file, "*"), destination)

        except (FileExistsError, PermissionError, FileNotFoundError, OSError) as err:
            msg = "Last Operation failed. Reason: {0}".format(err.strerror)
            logger.critical(msg)
            raise RuntimeError(msg)

        except RuntimeError as err:
            # catch exceptions from nested loops and re-raise them so we get out of this
            raise


def get_protected_files(inkscape_extension_dir: str, files: Dict[str, str], confirm_keep: bool) -> Dict[str, str]:
    files_found = {}

    for old_filename, new_filename in files.items():
        old_file_path = os.path.join(inkscape_extension_dir, old_filename)
        new_file_path = os.path.join(os.path.dirname(__file__), new_filename)
        if not os.path.isfile(old_file_path):
            logger.info("Candidate `{0}` for protection not found in previous installation.".format(old_filename))
        else:
            logger.info("Candidate `{0}` for protection found".format(old_filename))
            if not os.path.isfile(new_file_path):
                logger.info("Replacement `{0}` is not found in distribution, keep old file" .format(new_filename))
                files_found[old_filename] = new_filename
                continue
            with open(old_file_path) as f_old,  open(new_file_path) as f_new:
                if f_old.read() != f_new.read():
                    if confirm_keep:
                        logger.warning("Existing `{0}` differs from newer version in distribution".
                                       format(old_file_path))
                        if not query_yes_no("Keep `{0}` from previous installation?".format(old_file_path)):
                            logger.debug("   User choice: deleting old version!")
                            continue
                    logger.info("Content of `{0}` is not identical to version in distribution, keeping it.".
                                format(old_file_path))
                    files_found[old_filename] = new_filename
                else:
                    logger.info("Content of `{0}` is identical to distribution".format(old_filename))

    return files_found


def get_user_tex_files(inkscape_extension_dir: str, dirs_to_check: Dict[str, str],
                       excluded_files: List[str]) -> Dict[str, str]:
    user_files = {}
    for old_dir, new_dir in dirs_to_check.items():
        files = glob.glob(os.path.join(inkscape_extension_dir, old_dir, "*.tex"))
        for file in files:
            file = os.path.basename(file)
            if file not in excluded_files:
                user_files[os.path.join(old_dir, file)] = os.path.join(new_dir, file)
    return user_files


if __name__ == "__main__":

    EXIT_SUCCESS = 0
    EXIT_REQUIREMENT_CHECK_UNKNOWN = 64
    EXIT_REQUIREMENT_CHECK_FAILED = 65
    EXIT_FILE_OPERATION_FAILED = 66
    EXIT_BAD_COMMAND_LINE_ARGUMENT_VALUE = 2

    # Directory containing TexText files relative to this script
    TEXTEXT_SOURCE_DIR = "textext"

    # Directory containing TexText files relative to the inkscape extension dir
    TEXTEXT_TARGET_DIR = "textext"

    # Dictionary of files which the user might have modified, so that they should not be
    # overwritten by the installation
    # Key: file in existing installation (rel. to inkscape extension directory)
    # value: candidate for replacement (rel. to this script)
    PROTECTED_FILES = {
        # old layout TexText < 1.0 (default_packages need to go into textext module directory)
        "default_packages.tex": "{0}/default_packages.tex".format(TEXTEXT_SOURCE_DIR),
        # user modified default_packages need to be kept if modified
        "{0}/default_packages.tex".format(TEXTEXT_TARGET_DIR): "{0}/default_packages.tex".format(TEXTEXT_SOURCE_DIR)
    }

    # Dictionary for directories in which user written tex files might reside
    # and which must be kept
    # key: directory relative to the existing installation (rel. to inkscape extension directory)
    # value: directory into which the files should be moved after installation
    USER_TEX_FILE_DIRS = {
        ".": TEXTEXT_TARGET_DIR,
        TEXTEXT_TARGET_DIR: TEXTEXT_TARGET_DIR
    }

    parser = argparse.ArgumentParser(description='Install TexText')

    parser.add_argument(
        "--inkscape-extensions-path",
        default=system_env.inkscape_user_extensions_path,
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
        "--skip-extension-install",
        default=False,
        action='store_true',
        help="Don't install extension"
    )

    parser.add_argument(
        "--keep-previous-installation-files",
        default=False,
        action='store_true',
        help="Keep modified preamble files from previous installation without asking"
    )

    parser.add_argument(
        "--all-users",
        default=None,
        action='store_true',
        help="Install globally for all users"
    )

    args = parser.parse_args()
    logger, _ = install_logger(os.path.dirname(__file__), "textextsetup.log", cached_console_logging=False)
    settings_dir = system_env.textext_config_path

    # Address some portable app specfic stuff
    if args.portable_apps_dir:
        if os.name != "nt":
            logger.error("The --portable-apps-dir argument can only be used under MS Windows!")
            exit(EXIT_REQUIREMENT_CHECK_FAILED)
        elif not os.path.isdir(args.portable_apps_dir):
            logger.error("Path specified for PortableApps is not a valid directory!")
            exit(EXIT_REQUIREMENT_CHECK_FAILED)
        else:
            args.inkscape_executable = os.path.join(args.portable_apps_dir,
                                                    "InkscapePortable\\App\\Inkscape\\bin\\inkscape.exe")
            args.inkscape_extensions_path = os.path.join(args.portable_apps_dir,
                                                         "InkscapePortable\\Data\\settings\\extensions")
            settings_dir = os.path.join(args.portable_apps_dir,
                                        "InkscapePortable\\Data\\settings\\textext")

    # checker-object for dependency checks
    checker = DependencyCheck(logger)

    # Extract possible manually defined paths to executables and check if they really exists
    for executable_name in ["inkscape", "lualatex", "pdflatex", "xelatex"]:
        executable_path = getattr(args, "{0}_executable".format(executable_name))
        if executable_path:
            if not checker.check_executable(executable_name, executable_path):
                logger.error("Bad `{0}` executable provided: `{1}`. Abort installation.".
                             format(executable_name, executable_path))
                exit(EXIT_BAD_COMMAND_LINE_ARGUMENT_VALUE)

    # Check if all dependencies are met
    if not args.skip_requirements_check:

        check_result = checker.check(args.inkscape_executable, args.pdflatex_executable,
                                     args.lualatex_executable, args.xelatex_executable)

        if not check_result:
            logger.error("Automatic requirements check found issue")
            logger.error("Follow instruction above and run install script again")
            logger.error("To bypass requirement check pass `--skip-requirements-check` to setup.py")
            exit(EXIT_REQUIREMENT_CHECK_FAILED)
        else:
            args.inkscape_executable, args.pdflatex_executable, \
                args.lualatex_executable, args.xelatex_executable = check_result

    # Do the installation if requested
    if not args.skip_extension_install:

        # Set the installation directory
        if args.all_users:
            # Query the system extension path
            [args.inkscape_extensions_path, error] = system_env.inkscape_system_extensions_path(
                args.inkscape_executable)
            if args.inkscape_extensions_path is None:
                logger.error("Determination of system extension directory failed (Error message: {0})".format(error))
                exit(EXIT_BAD_COMMAND_LINE_ARGUMENT_VALUE)
            else:
                logger.info("System extensions are in {0}".format(args.inkscape_extensions_path))

            # Check write access in system extension path
            if not os.access(args.inkscape_extensions_path, os.W_OK):
                logger.error(
                    "You do not have write privileges in `{0}`! Please run setup script as administrator/ with sudo.".
                    format(args.inkscape_extensions_path))
                exit(EXIT_BAD_COMMAND_LINE_ARGUMENT_VALUE)
        else:
            # local installation
            args.inkscape_extensions_path = os.path.expanduser(args.inkscape_extensions_path)

        textext_extension_dir = os.path.join(args.inkscape_extensions_path, TEXTEXT_TARGET_DIR)

        # Determine if any files from the previous installation need to be kept
        protected_files_found = get_protected_files(args.inkscape_extensions_path, PROTECTED_FILES,
                                                    not args.keep_previous_installation_files)
        protected_files_found.update(get_user_tex_files(args.inkscape_extensions_path,
                                                        USER_TEX_FILE_DIRS,
                                                        list(PROTECTED_FILES)))

        try:
            with tempfile.TemporaryDirectory(prefix="textext_") as temp_dir:
                with StashFiles(args.inkscape_extensions_path, protected_files_found, temp_dir):
                    remove_previous_installation(textext_extension_dir)
                    copy_extension_files(src=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                          TEXTEXT_SOURCE_DIR),
                                         dst=args.inkscape_extensions_path)
        except RuntimeError as error:
            logger.critical("Setup failed, see messages above for more details!")
            exit(EXIT_FILE_OPERATION_FAILED)
        else:
            settings = SettingsTexText(directory=settings_dir)
            settings.set_executable(Cmds.INKSCAPE, args.inkscape_executable)
            settings.set_executable(Cmds.PDFLATEX, args.pdflatex_executable)
            settings.set_executable(Cmds.XELATEX, args.xelatex_executable)
            settings.set_executable(Cmds.LUALATEX, args.lualatex_executable)
            settings.set_executable(Cmds.TYPST, args.typst_executable)
            settings.save()

            Cache(directory=settings_dir).delete_file()
            logger.info("--> TexText has been SUCCESSFULLY installed on your system <--")

    exit(EXIT_SUCCESS)
