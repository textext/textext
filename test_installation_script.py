"""

This script creates fake executables (pdflatex, python2.7, etc...)
to test requirements check in setup.py

All fake executables are created in temporary directory and safely deleted at the end.

setup.py is running with PATH set to temporary directory, so actual environment
does not affect this test

"""
import os
import shutil
import sys
import subprocess
import tempfile


class TempDirectory(object):
    def __init__(self):
        self.name = None

    def __enter__(self):
        self.name = tempfile.mkdtemp()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.name is not None:
            shutil.rmtree(self.name)


class FakeExecutablesMaker(object):
    def __init__(self, dirname):
        assert os.path.isdir(dirname)
        self.dirname = dirname

    def __call__(self, name, output="", channel='stdout'):
        assert channel in ["stdout", "stderr"]
        command_name = os.path.join(self.dirname, name)
        with open(command_name, "w") as fout:
            fout.write("#!%s\n" % sys.executable)
            fout.write("from __future__ import print_function\n")
            fout.write("import sys\n")
            fout.write("print(%s, file=sys.%s)" % (repr(output), channel))
        os.chmod(command_name, 0o755)


def test_configuration(fake_commands, expected_exit_code):
    with TempDirectory() as f:
        env = dict(os.environ, PATH=f.name)
        make_fake_executable = FakeExecutablesMaker(f.name)
        for args in fake_commands:
            make_fake_executable(*args)

        ret_code = subprocess.call([sys.executable,
                                    'setup.py',
                                    "--skip-extension-install"],
                                   env=env
                                   )
        assert ret_code == expected_exit_code, '%d != %d' % (ret_code, expected_exit_code)


REQUIREMENT_CHECK_SUCCESS = 0
REQUIREMENT_CHECK_UNKNOWN = 64
REQUIREMENT_CHECK_ERROR = 65

good_configurations = []
for pdf2png in [("convert",), ("magick",)]:
    for pdf2svg in [[("pstoedit", "version 1.1", "stderr"),
                     ("ghostscript", "9.25")
                     ],
                    [("pdf2svg",)]
                    ]:
        for latex in [("pdflatex",), ("lualatex",), ("xelatex",)]:
            good_configurations.append([
                                           ("python2.7",),
                                           pdf2png,
                                           latex
                                       ] + pdf2svg)

for good_configuration in good_configurations:
    test_configuration(good_configuration, REQUIREMENT_CHECK_SUCCESS)

for good_configuration in good_configurations:
    for i in range(len(good_configuration)):
        # good configuration without one element is bad
        bad_configuration = good_configuration[:i] + good_configuration[i + 1:]
        test_configuration(bad_configuration, REQUIREMENT_CHECK_ERROR)

test_configuration([
    ("python2.7",)
], REQUIREMENT_CHECK_ERROR)

test_configuration([
    ("python2.7",),
    ("pdflatex",),
    ("convert",),
    ("pstoedit", "version 3.70", "stderr"),
    ("ghostscript", "9.22")
], REQUIREMENT_CHECK_ERROR)

test_configuration([
    ("python2.7",),
    ("pdflatex",),
    ("convert",),
    ("pstoedit",),
    ("ghostscript",)
], REQUIREMENT_CHECK_UNKNOWN)
