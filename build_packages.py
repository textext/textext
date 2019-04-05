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


if __name__ == "__main__":

    TexTextVersion = open("extension/textext/VERSION").readline().strip()

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
            versioned_subdir = os.path.join(tmpdir,"textext-%s" % TexTextVersion)
            os.mkdir(versioned_subdir)
            shutil.copytree("./extension",
                            os.path.join(versioned_subdir, "extension"),
                            ignore=git_ignore_patterns  # exclude .gitignore files
                            )
            shutil.copy("setup.py", versioned_subdir)
            shutil.copy("LICENSE.txt", versioned_subdir)
            if platform == "windows":
                shutil.copy("setup_win.bat", versioned_subdir)
            if platform == "inkscape":
                shutil.copy("setup_win.bat", versioned_subdir)
                shutil.copy("INSTALL.txt", versioned_subdir)
            for fmt in formats:
                filename = shutil.make_archive(PackageName, fmt, tmpdir)
                print("Successfully created %s" % os.path.basename(filename))
