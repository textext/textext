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

    path = os.path.join(__file__, "extension")
    destination = os.path.expanduser("~/.config/inkscape/extensions")

    try:
        for (dirpath, dirnames, filenames) in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(path, filename)
                try:
                    os.makedirs(destination)
                except StandardError:
                    pass

                shutil.copy(filepath, destination)
            # we only care for the top directory level
            break
        print success
    except StandardError:
        print failure

if __name__ == "__main__":
    main()