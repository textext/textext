import glob
import os

# List of specific test cases to be run, e.g. ["07", "08"].
# To run all tests set to empty list []
SPECIFIC_TESTS = []


def pytest_generate_tests(metafunc):
    if (
            "root" in metafunc.fixturenames and
            "inkscape_version" in metafunc.fixturenames and
            "textext_version" in metafunc.fixturenames and
            "converter" in metafunc.fixturenames and
            "test_case" in metafunc.fixturenames):
        path_to_snippets = "snippets"
        inkscape_versions = glob.glob(os.path.join(path_to_snippets, "inkscape-*.*"))

        args = []
        ids = []
        for inkscape_version in inkscape_versions:
            for folder, _, files in os.walk(inkscape_version):
                test_case = os.path.basename(folder)
                if len(SPECIFIC_TESTS) == 0 or test_case in SPECIFIC_TESTS:
                    if "config.json" in files and \
                            "original.svg" in files and \
                            "modified.svg" in files:
                        textext_version = os.path.dirname(os.path.dirname(folder))
                        converter = os.path.dirname(folder)
                        args.append([path_to_snippets,
                                     os.path.basename(inkscape_version),
                                     os.path.basename(textext_version),
                                     os.path.basename(converter),
                                     test_case
                                     ])
                        ids.append(os.path.relpath(folder, path_to_snippets))

        assert (len(ids) > 0), "No valid test case(s) defined"

        args_with_ids = sorted(list(zip(args,ids)))
        args, ids = zip(*args_with_ids)
        metafunc.parametrize(["root", "inkscape_version", "textext_version", "converter", "test_case"], args, ids=ids)
