#!/usr/bin/env python


import argparse
import logging
import os
import glob
import shutil
import sys
import stat
import tempfile

sys.path.append(os.path.join(
    os.path.dirname(__file__),
    "extension",
    "textext"
))

from requirements_check import \
    set_logging_levels, \
    TexTextRequirementsChecker, \
    defaults, \
    LoggingColors


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
        default=defaults.inkscape_extensions_path,
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
        default=defaults.console_colors,
        choices=("always", "never"),
        help="Enables/disable console colors"
    )

    files_to_keep = {  # old_name : new_name
        "default_packages.tex": "textext/default_packages.tex",  # old layout
        "textext/default_packages.tex": "textext/default_packages.tex"  # new layout
    }

    args = parser.parse_args()
    args.inkscape_extensions_path = os.path.expanduser(args.inkscape_extensions_path)

    if args.color == "always":
        LoggingColors.enable_colors = True
    elif args.color == "never":
        LoggingColors.enable_colors = False

    set_logging_levels()
    logger = logging.getLogger('TexText')
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('[%(name)s][%(levelname)6s]: %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    if not args.skip_requirements_check:
        check_result = TexTextRequirementChecker(logger).check()
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
                args.keep_previous_installation_files = query_yes_no(
                    "Keep above %s from previous installation?" % file_s)
            else:
                args.keep_previous_installation_files = False

        if not args.keep_previous_installation_files:
            files_to_keep = {}

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
