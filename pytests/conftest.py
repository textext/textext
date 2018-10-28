import glob
import os


def pytest_generate_tests(metafunc):
    if (
            "root" in metafunc.fixturenames and
            "inkscape" in metafunc.fixturenames and
            "snippet" in metafunc.fixturenames):
        path_to_snippets = "snippets"
        inkscape_versions = glob.glob(os.path.join(path_to_snippets, "inkscape-*.*"))

        args = []
        ids = []
        for inkscape_version in inkscape_versions:
            for folder, _, files in os.walk(inkscape_version):
                if "config.json" in files and \
                        "original.svg" in files and \
                        "modified.svg" in files:
                    args.append([path_to_snippets,
                                 os.path.relpath(inkscape_version, path_to_snippets),
                                 os.path.relpath(folder, inkscape_version)
                                 ])
                    ids.append(os.path.relpath(inkscape_version, path_to_snippets) +
                               "/" + os.path.relpath(folder, inkscape_version))
        args_with_ids = sorted(list(zip(args,ids)))
        args, ids = zip(*args_with_ids)
        metafunc.parametrize(["root", "inkscape", "snippet"], args, ids=ids)
