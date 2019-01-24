"""utils.py

A couple of random utilities.

"""

import os, sys
import ansi


def pickle_file_name(fname):
    """Generate the name for the pickle file. We maintain different pickle files
    depending on the Python version."""
    return os.path.join('..', 'data', 'compiled',
                        str(sys.version_info.major),
                        os.path.basename(fname) + '.pickle')


def read_input():
    """Utility method that hides differences between python 2 and 3."""
    return raw_input() if sys.version_info.major == 2 else input()


def kwic_line(left, kw, right, context=50):
    left = '{s: >{width}}'.format(s=left, width=context)
    right = '{s: <{width}}'.format(s=right, width=context)
    kwic_line = "%s %s%s%s %s" % (left, ansi.BLUE, kw, ansi.END, right)
    return kwic_line


class Synset(object):

    """Implements the information that we have for a synset."""

    def __init__(self, lines):
        self.ssid = lines[1].strip()
        self.cat = lines[2].strip()
        self.btypes = lines[3].strip()
        self.description = lines[4].strip()
        self.gloss = lines[5].strip()

    def __str__(self):
        return "{ %s }" % self.description

