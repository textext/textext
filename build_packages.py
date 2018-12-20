import shutil
import argparse
import tempfile
import os


class TmpDir:
    def __init__(self):
        self.path = None

    def __enter__(self):
        self.path = os.path.join(tempfile.mkdtemp(), "textext-%s" % TexTextVersion)
        os.mkdir(self.path)
        return self.path

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.path:
            shutil.rmtree(self.path)


if __name__ == "__main__":

    TexTextVersion = "0.9.0"

    parser = argparse.ArgumentParser(description="Build TexText distribution archive for selected platforms."
                                                 "If not otherwise specified zip and tgz packages are built "
                                                 "for Linux and a zip package for Windows.")
    available_formats = [fmt for fmt, desc in shutil.get_archive_formats()]
    parser.add_argument('--linux',
                        type=str,
                        nargs="+",
                        choices=available_formats,
                        help="Build package for Linux with archive formats [%s]" % ", ".join(available_formats))
    parser.add_argument('--windows',
                        type=str,
                        nargs="+",
                        choices=available_formats,
                        help="Build package for Windows with archive formats [%s]" % ", ".join(available_formats))
    parser.add_argument('--macos',
                        type=str,
                        nargs="+",
                        choices=available_formats,
                        help="Build package for MacOS with archive formats [%s]" % ", ".join(available_formats))

    args = vars(parser.parse_args())
    if not any(args.values()):
        args = {'linux': ['zip', 'gztar'], 'windows': ['zip'], 'macos': ['zip']}

    for platform, formats in {p: f for p, f in args.items() if f}.items():
        PackageName = "TexText-%s-" % platform.capitalize() + TexTextVersion
        git_ignore_patterns = shutil.ignore_patterns(*open(".gitignore").read().split("\n"))

        with TmpDir() as tmpdir:
            shutil.copytree("./extension",
                            os.path.join(tmpdir, "extension"),
                            ignore=git_ignore_patterns  # exclude .gitignore files
                            )
            shutil.copy("setup.py", tmpdir)
            shutil.copy("LICENSE.txt", tmpdir)
            if platform == "windows":
                shutil.copy("setup_win.bat", tmpdir)
            for fmt in formats:
                # Build package in parent dir, i.e. the temporary directory
                filename = shutil.make_archive(PackageName, fmt, os.path.join(tmpdir, os.pardir))
                print("Successfully created %s" % os.path.basename(filename))
