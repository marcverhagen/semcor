"""

Interface to Semcor.

Should run in both Python 2 and Python 3.


Usage fron command line:

$ python semcor.py --compile
$ python semcor.py

The first invocation compiles semcor files, the second loads compiled files.

Usage as an imported module:

>>> from semcor import load_semcor
>>> sc = load_semcor(SOME_DIRECTORY)

If sources have not yet been compiled you first need to do this:

>>> from semcor import compile_semcor
>>> compile_semcor(SOME_DIRECTORY)


"""

from __future__ import print_function

import os, sys, bs4, pickle, time

import parser
from utils import pickle_file_name, Synset


SEMCOR = '../data/semcor3.0'

BROWN1 = os.path.join(SEMCOR, 'brown1', 'tagfiles')
BROWN2 = os.path.join(SEMCOR, 'brown2', 'tagfiles')

MAPPINGS = '../data/corelex/corelex-3.1-semcor_lemma2synset.txt'


def load_semcor(directory, maxfiles=999):
    """Load the semcor files in directory and return a Semcor instance. The maximum
    number of files to load is defined by the optional second argument."""
    sc = Semcor(directory)
    sc.load(maxfiles)
    return sc


def compile_semcor(directory, maxfiles=999):
    """Compile maxfiles files from the given semcor directory."""
    sc = Semcor(directory)
    sc.compile(maxfiles)


class Semcor(object):

    def __init__(self, corpus):

        self.corpus = corpus
        self.fnames = []
        self.files = []
        self.lemma_idx = {}
        self.file_idx = {}
        self.mappings = {}
        self._init_files()

    def __str__(self):
        return "<Semcor on %s with %d files>" % \
            (self.corpus.split(os.path.sep)[-2], len(self.files))

    def _init_files(self):
        self.fnames = [os.path.join(BROWN1, fname)
                       for fname in sorted(os.listdir(self.corpus))]

    def compile(self, limit=999):
        """Compile the files in the corpus. Compiling means reading all files,
        creating SemcorFile instances for them and saving them to disk as pickle
        files. The limit argument limits how many files are compiled, default is
        to compile all of them."""
        t0 = time.time()
        count = 0
        for fname in self.fnames:
            count += 1
            if count > limit:
                break
            print('Compiling', fname)
            semcor_file = SemcorFile(fname)
            parser.parse(semcor_file)
            semcor_file.collect_forms()
            semcor_file.index()
            semcor_file.pickle()
        time_elapsed = time.time() - t0
        print("Time elapsed is %.2f seconds" % time_elapsed)

    def load(self, limit=999):
        """Load all compiled files. Loading from compiled sources with Python 2
        is about 2-3 times faster then loading semcor files and parsing them, on
        Python 3 the speed up is a factor 10 bigger, although it takes a bit
        longer to compile."""
        t0 = time.time()
        self.file = []
        for fname in self.fnames[:limit]:
            pickle_file = pickle_file_name(fname)
            print('Loading', pickle_file)
            with open(pickle_file, 'rb') as fh:
                self.files.append(pickle.load(fh))
        t1 = time.time()
        self.index()
        t2 = time.time()
        self.load_mappings()
        t3 = time.time()
        print("\nTime elapsed:")
        print("   loading files:    %4.2f seconds" % (t1 - t0))
        print("   indexing files:   %4.2f seconds" % (t2 - t1))
        print("   loading mappings: %4.2f seconds" % (t3 - t2))
        print()

    def index(self):
        """Create indexes from all individual file-level indexes."""
        self.lemma_idx = {}
        self.file_idx = {}
        for semcor_file in self.files:
            self.file_idx[os.path.basename(semcor_file.fname)] = semcor_file
            for form in semcor_file.forms:
                self.lemma_idx.setdefault(form.lemma,[]).append(form)

    def get_file(self, fname):
        return self.file_idx.get(fname)

    def load_mappings(self):
        """Load the lemma and lemma sense to synset mappings."""
        # TODO: consider compiling these mappings using pickle
        self.mappings = {}
        with open(MAPPINGS) as fh:
            content = fh.read().split(os.linesep + os.linesep)
            for lemma_data in content:
                lines = lemma_data.split(os.linesep)
                lemma = lines.pop(0)
                self.mappings[lemma] = {}
                for i in range(0, len(lines), 6):
                    sense = lines[i].strip()
                    ss = Synset(lines[i:i+6])
                    self.mappings[lemma][sense] = ss

    def get_synset_for_lemma(self, lemma, sense):
        """Get the synset associated with the lemma and the sense. An example
        lemma-sense combination is 'walk' with '2:38:00::'. Returns None if no
        such synset was found."""
        return self.mappings.get(lemma, {}).get(lemma + '%' + sense)


class SemcorFile(object):

    def __init__(self, fname):
        self.fname = fname
        self.paragraphs = []
        self.forms = []

    def __str__(self):
        return "<SemcoreFile %s>" % os.path.basename(self.fname)
    
    def add_paragraph(self, para):
        self.paragraphs.append(para)

    def pp(self):
        print("%s" % self)
        for p in self.paragraphs:
            p.pp()

    def collect_forms(self):
        """Collect all instances of WordForm that have a sense."""
        self.forms = []
        for p in self.paragraphs:
            p.collect_forms(self.forms)

    def index(self):
        """Build various indexes for the forms with senses."""
        self.lemma_idx = {}
        for form in self.forms:
            self.lemma_idx.setdefault(form.lemma,[]).append(form)
    
    def pickle(self):
        """Pickle the file and save it in data/compiled."""
        pickle_file = pickle_file_name(self.fname)
        with open(pickle_file, 'wb') as fh:
            pickle.dump(self, fh)

    def get_sentence(self, sent):
        for par in self.paragraphs:
            for sentence in par.sentences:
                if sentence.sid == sent:
                    return sentence
        return None


if __name__ == '__main__':

    if len(sys.argv) > 1 and sys.argv[1] == '--compile':
        compile_semcor(BROWN1, 10)
    else:
        sc = load_semcor(BROWN1, 10)
        print(sc)
