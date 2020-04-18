"""utils.py

A couple of random utilities.

"""

import os, sys, time
import ansi


def pickle_file_name(fname):
    """Generate the name for the pickle file. We used to maintain different pickle
    files depending on the Python version, but now we assume Python3."""
    return os.path.join('..', 'data', 'compiled', '3',
                        os.path.basename(fname) + '.pickle')


def read_input():
    """Utility method that hides differences between python 2 and 3."""
    return raw_input() if sys.version_info.major == 2 else input()


def kwic_line(left, kw, right, context=50):
    left = '{s: >{width}}'.format(s=left, width=context)
    right = '{s: <{width}}'.format(s=right, width=context)
    kwic_line = "%s %s%s%s %s" % (left, ansi.BLUE, kw, ansi.END, right)
    return kwic_line


def keep_time(func):
    """Decorator function to print time elapsed."""
    def wrapper(*args, **kwargs):
        t0 = time.time()
        func(*args, **kwargs)
        time_elapsed = time.time() - t0
        print("Time elapsed in %s is %.2f seconds" % (func.__name__, time_elapsed))
    return wrapper


class Synset(object):

    """Implements the information that we have for a synset."""

    def __init__(self, lines):
        self.ssid = lines[1].strip()
        self.cat = lines[2].strip()
        self.btypes = lines[3].strip()
        self.description = lines[4].strip()
        self.gloss = lines[5].strip()

    def __str__(self):
        return "%s %s { %s }" % (self.ssid, self.cat, self.description)

