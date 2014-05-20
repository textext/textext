#!/usr/bin/env python
__author__ = 'Pit Garbe'


def main():
    """
    Installing TexText. Basically just copying the files to the user's Inkscape extension folder
    """
    import os
    import shutil

    success = "Installation successful. Enjoy! :)"
    failure = "Installation Failed :("

    red = "\033[01;31m{0}\033[00m"
    green = "\033[92m{0}\033[00m"

    success = green.format(success)
    failure = red.format(failure)

    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "extension")
    destination = os.path.expanduser("~/.config/inkscape/extensions")

    num_copied_files = 0

    for (dirpath, dirnames, filenames) in os.walk(path):
        for filename in filenames:
            filepath = os.path.join(path, filename)
            try:
                os.makedirs(destination)
            except StandardError:
                pass

            try:
                shutil.copy(filepath, destination)
                num_copied_files += 1
            except StandardError:
                print failure
                SystemExit(1)
        # we only care for the top directory level
        break
    if num_copied_files > 0:
        print success
    else:
        print failure

if __name__ == "__main__":
    main()