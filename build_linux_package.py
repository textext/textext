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

    TexTextVersion = "0.8.1"
    PackageName = "TexText-Linux-"+TexTextVersion

    parser = argparse.ArgumentParser("Build TexText distribution archive for Linux")
    available_formats = [fmt for fmt, desc in shutil.get_archive_formats()]
    parser.add_argument('formats',
                        type=str,
                        nargs="+",
                        choices=available_formats,
                        help="archive formats [%s]"%", ".join(available_formats))

    args = parser.parse_args()

    git_ignore_patterns = shutil.ignore_patterns(*open(".gitignore").read().split("\n"))

    with TmpDir() as tmpdir:
        shutil.copytree("./extension",
                        os.path.join(tmpdir,"extension"),
                        ignore= git_ignore_patterns  # exclude .gitignore files
                        )
        shutil.copy("setup.py",tmpdir)
        shutil.copy("LICENSE.txt",tmpdir)
        for fmt in args.formats:
            shutil.make_archive(PackageName,fmt,tmpdir)



