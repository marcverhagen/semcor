import os, sys


def pickle_file_name(fname):
    """Generate the name for the pickle file. We maintain different pickle files
    depending on the Python version."""
    return os.path.join('data',
                        'compiled',
                        str(sys.version_info.major),
                        os.path.basename(fname) + '.pickle')


def read_input():
    return raw_input() if sys.version_info.major == 2 else input()
