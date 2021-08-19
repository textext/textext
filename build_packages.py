"""
This file is part of TexText, an extension for the vector
illustration program Inkscape.

Copyright (c) 2006-2021 TexText developers.

TexText is released under the 3-Clause BSD license. See
file LICENSE.txt or go to https://github.com/textext/textext
for full license details.

Builds the assets.
"""
import shutil
import argparse
import tempfile
import os


class TmpDir:
    def __init__(self):
        self.path = None

    def __enter__(self):
        self.path = tempfile.mkdtemp()
        return self.path

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.path:
            shutil.rmtree(self.path)


def copy_textext_files(target_dir):
    shutil.copytree("./textext",
                    target_dir,
                    ignore=git_ignore_patterns  # exclude .gitignore files
                    )
    shutil.copy("LICENSE.txt", target_dir)


if __name__ == "__main__":

    TexTextVersion = open("textext/VERSION").readline().strip()

    parser = argparse.ArgumentParser(description="Build TexText distribution archive for selected platforms."
                                                 "If not otherwise specified zip and tgz packages are built "
                                                 "for Linux and a zip package for Windows.")
    available_formats = [fmt for fmt, desc in shutil.get_archive_formats()]
    parser.add_argument('--linux',
                        type=str,
                        nargs="+",
                        choices=available_formats,
                        default=['zip', 'gztar'],
                        help="Build package for Linux with archive formats [%s]" % ", ".join(available_formats))
    parser.add_argument('--windows',
                        type=str,
                        nargs="+",
                        choices=available_formats,
                        default=['zip'],
                        help="Build package for Windows with archive formats [%s]" % ", ".join(available_formats))
    parser.add_argument('--macos',
                        type=str,
                        nargs="+",
                        choices=available_formats,
                        default=['zip'],
                        help="Build package for MacOS with archive formats [%s]" % ", ".join(available_formats))
    parser.add_argument('--inkscape',
                        type=str,
                        nargs="+",
                        choices=available_formats,
                        default=['zip'],
                        help="Build All-OS package for Inkscape Add-On homepage with archive formats [%s]" % ", ".join(available_formats))

    args = vars(parser.parse_args())

    if os.path.exists("assets"):
        shutil.rmtree("assets")

    os.mkdir("assets")

    for platform, formats in {p: f for p, f in args.items() if f}.items():
        PackageName = "assets/TexText-%s-" % platform.capitalize() + TexTextVersion
        git_ignore_patterns = shutil.ignore_patterns(*open(".gitignore").read().split("\n"))

        with TmpDir() as tmpdir:
            # Platform dependent packages have the content
            # textext-x.y.z
            #    textext (module dir)
            #    setup.py
            # Package for package manager has the content
            # textext  (module dir)
            if platform != "inkscape":
                versioned_subdir = os.path.join(tmpdir,"textext-%s" % TexTextVersion)
                extension_subdir = os.path.join(versioned_subdir, "textext")
                copy_textext_files(extension_subdir)
                shutil.copy("setup.py", versioned_subdir)
                if platform == "windows":
                    shutil.copy("setup_win.bat", versioned_subdir)
            else:
                copy_textext_files(os.path.join(tmpdir, "textext"))

            for fmt in formats:
                filename = shutil.make_archive(PackageName, fmt, tmpdir)
                print("Successfully created %s" % os.path.basename(filename))
