#!/usr/bin/env python

import argparse 
import logging
import os
import glob
import shutil


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
            logger.error("Can't copy files to `%s`: it's not a directory")
            raise CopyFileOverDirectoryError("Can't copy files to `%s`: it's not a directory")
    else:
        logger.info("Creating directory `%s`"%dst)
        os.makedirs(dst)

    for file in glob.glob(src):
        basename = os.path.basename(file)
        destination = os.path.join(dst,basename)
        if os.path.exists(destination):
            if if_already_exists=="raise":
                logger.error("Can't copy `%s`: `%s` already exists"%(file,destination))
                raise CopyFileAlreadyExistsError("Can't copy `%s`: `%s` already exists"%(file,destination))
            elif if_already_exists=="skip":
                logger.info("Skipping `%s`"%file)
                continue
            elif if_already_exists=="overwrite":
                logger.info("Overwriting `%s`"%destination)
                pass

        if os.path.isfile(file):
            logger.info("Copying `%s` to `%s`" % (file,destination) )
            shutil.copy(file, destination)
        else:
            logger.info("Creating directory `%s`"%destination)

            if os.path.exists(destination):
                if not os.path.isdir(destination):
                    os.remove(destination)
                    os.mkdir(destination)
            else:
                os.mkdir(destination)
            copy_extension_files(  os.path.join(file,"*"),
                                   destination,
                                   if_already_exists=if_already_exists)


logger = logging.getLogger('TexText')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
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

    args = parser.parse_args()

    try:
        copy_extension_files(
            src="extension/*",
            dst=args.inkscape_extensions_path,
            if_already_exists=args.if_already_exists
        )
    except CopyFileAlreadyExistsError:
        logger.info("Hint: add `--overwrite-if-exist` option to overwrite existing files and directories")
        logger.info("Hint: add `--skip-if-exist` option to retain existing files and directories")
