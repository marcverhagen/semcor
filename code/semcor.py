"""Interface to Semcor.

Should run in both Python 2 and Python 3, but Python 3 is recommended because
it is much faster for this code.


Usage from command line:

$ python semcor.py --compile (-n MAXFILES)
$ python semcor.py (-n MAXFILES)

The first invocation compiles semcor files, the second loads compiled files. The
default is to compile or load all files, this default can be overruled with the -n
option.

Usage as an imported module:

>>> from semcor import Semcor, SemcorFile
>>> sc = Semcor(10)

The argument sets a limit to the number of files to load, without it all files
are loaded.

If sources have not yet been compiled you first need to do this:

>>> from semcor import compile_semcor
>>> compile_semcor()

Here all files are compiled, you can add an integer-valued argument to restrict
the number of files to compile.

"""

from __future__ import print_function

import os, sys, bs4, pickle, time, glob, getopt

import parser
from utils import pickle_file_name, Synset, keep_time
from index import create_lemma_index, IndexedWordForms


SEMCOR = '../data/semcor3.0'

# The files are all the files in the brown1 and brown2 subcorpora of semcor. The
# brownv subcorpus, which has verbs only, is not included. Files are sorted in
# lexicographic order with the subcorpus as part of the path so brown1/br-j03
# will precede brown2/br-e22.
SEMCOR_FILES = sorted(glob.glob(os.path.join(SEMCOR, 'brown[12]/tagfiles/*')))

# Mappings to wordnet synsets
MAPPINGS = '../data/corelex/corelex-3.1-semcor_lemma2synset.txt'


@keep_time
def compile_semcor(maxfiles=999):
    """Compile semcor files, default is to compile all files but maxfiles can be
    used to restrict the number. Compiling a file means reading it, creating a
    SemcorFile instance for it and saving it to disk as a pickle file. Loading
    from compiled sources with Python 2 is about 2-3 times faster then loading
    and parsing semcor source files, on Python 3 the speed up is a factor 10
    larger, although it takes a bit longer to compile."""
    count = 0
    for fname in SEMCOR_FILES:
        count += 1
        if count > maxfiles:
            break
        print('Compiling', fname)
        semcor_file = SemcorFile(fname)
        parser.parse(semcor_file)
        semcor_file.collect_forms()
        semcor_file.index()
        semcor_file.pickle()


class Semcor(object):

    """Instance variables:

    fnames : list of strings
       all files from the brown1 and brown2 subcorpora of Semcor

    fcount : integer
       number of all files in brown1 and brown2 subcorpora (length of fnames)

    files : list of SemcorFile instances
       list of SemcorFile instances loaded, where the filenames are a
       subset of fnames

    loaded : integer
       number of files loaded, the length of the list in files

    lemma_idx : dict (string -> list of WordForm instances)
       An index of mappings from lemmas like "say" or "walk" to a list of all
       instances of WordForm in the loaded corpus that go with the lemma. The
       WordForms do not all need to have the same parts-of-speech and senses.

    file_idx : dict (string -> SemcorFile)
       An index from file names in semcor to instances of SemcorFile. For
       filenames just the base names are used, so we have "br-a01" and not
       "brown1/br-a01" or "brown1/tagfiles/br-a01. This index includes all
       instance of SemcorFile in the files variable."

    sent_idx : dict (int -> Sentence)
       An index of sentences numbered sequentially to Sentence instances, the
       sentence number starts at 1 and does not reset for each document, that
       is, we have unique sentence identifiers. This list is not initialized
       when loading Semcor, rather it is created later by request using an
       external file with documents sorted in some order.

    synset_idx : dict (string -> dict (string -> Synset))
       An index with mappings to WordNet and Corelex information. The keys are
       lemmas like 'walk' at the top level of the index and Semcor senses like
       'walk%1:04:01::' in the embedded dictionaries, and each semcor sense is
       mapped to one Synset which contains the Wordnet information amended with
       Corelex basic types. The reason that we have both levels is that we want
       to be able to get all senses and synsets for a lemma. The Semcor sense is
       a concatenation of the lemma, the percentage sign and the lexical sense.
       The content for this index is read from the MAPPINGS file.

    noun_idx : IndexedWordForms
       An IndexedWordForms instance with all nominals, but including a WordForm
       only if the document that the WordForm occurs in has another WordForm
       with the same lemma but a different sense.

    """

    # TODO: that noun_idx is a bit weird since it has the weird restriction of
    # not including a ordform if it does no co-occur with another wordform in
    # the same document with the same lemma and a different sense. How am I
    # going to name all those other indexes with different data? Maybe have one
    # index but create seperate views on it (then again, how do I name the
    # views). Or maybe have one index and accessor methods do the filtering (and
    # yes, they could cache results). Will not worry about this till I have more
    # indexes of type IndexedWordForms.

    def __init__(self, maxfiles=999):
        """Initialize attributes, load the semcor files and perform other loads and
        initializations. The maximum number of files to load is defined by the
        optional argument, the default is to load all files."""
        self._initialize_attributes()
        self._load(maxfiles)
        self._load_common_nouns_indexed_on_basic_types()

    def _initialize_attributes(self):
        self.fnames = SEMCOR_FILES
        self.fcount = len(SEMCOR_FILES)
        self.files = []
        self.loaded = 0
        self.lemma_idx = {}
        self.file_idx = {}
        self.sent_idx = {}
        self.synset_idx = {}
        self.noun_idx = None

    def _load(self, maxfiles=999):
        """Load the compiled semcor files, but no more than specified by
        maxfiles. The default is to load all files."""
        t0 = time.time()
        self.files = []
        self.loaded = self.fcount if maxfiles > self.fcount else maxfiles
        print('Loading compiled files...')
        for fname in self.fnames[:maxfiles]:
            pickle_file = pickle_file_name(fname)
            with open(pickle_file, 'rb') as fh:
                self.files.append(pickle.load(fh))
        t1 = time.time()
        self._index()
        t2 = time.time()
        self._load_mappings()
        t3 = time.time()
        print("\nTime elapsed:")
        print("   loading files:    %4.2f seconds" % (t1 - t0))
        print("   indexing files:   %4.2f seconds" % (t2 - t1))
        print("   loading mappings: %4.2f seconds" % (t3 - t2))
        print()

    def _load_common_nouns_indexed_on_basic_types(self):
        wfs = self.get_common_nouns()
        self.noun_idx = IndexedWordForms(self, wfs)
        # now the following two are separate methods made visible to the outside,
        # could also been done by handing flags into the class initialization.
        self.noun_idx.filter_lemmas_with_only_one_sense_per_document()
        self.noun_idx.initialize_btypes_index()

    def _index(self):
        """Create indexes from all individual file-level indexes."""
        self.lemma_idx = {}
        self.file_idx = {}
        for semcor_file in self.files:
            self.file_idx[os.path.basename(semcor_file.fname)] = semcor_file
            for form in semcor_file.forms:
                self.lemma_idx.setdefault(form.lemma,[]).append(form)

    def _load_mappings(self):
        """Load the mappings from lemmas and senses to synsets."""
        # TODO: consider compiling these mappings using pickle
        self.synset_idx = {}
        with open(MAPPINGS) as fh:
            content = fh.read().split(os.linesep + os.linesep)
            for lemma_data in content:
                lines = lemma_data.split(os.linesep)
                lemma = lines.pop(0)
                self.synset_idx[lemma] = {}
                for i in range(0, len(lines), 6):
                    sense = lines[i].strip()
                    ss = Synset(lines[i:i+6])
                    self.synset_idx[lemma][sense] = ss
        self._add_synsets_to_wordforms()

    def _add_synsets_to_wordforms(self):
        for lemma in self.lemma_idx:
            for wf in self.lemma_idx[lemma]:
                wf.synset = self.get_synset_for_lemma(lemma, wf.lexsn)

    def __str__(self):
        return "<Semcor instance with %d files>" % self.loaded

    def create_sentence_index(self, fnames_file):
        """Creates the index in sent_idx, using the list of semcor file names in
        fnames_file. File names should be just the base name and should be put
        in the file separate by any kind of white space, for example, one file
        per line. Any filename that does not correspond to a loaded semcor file
        will be ignored."""
        self.sent_idx = {}
        fnames = open(fnames_file).read().strip().split()
        fnames = [fname for fname in fnames if fname in self.file_idx]
        sentence_number = 0
        for fname in fnames:
            scfile = self.file_idx[fname]
            for s in scfile.get_sentences():
                sentence_number += 1
                self.sent_idx[sentence_number] = s

    def get_file(self, fname):
        return self.file_idx.get(fname)

    def get_synset_for_lemma(self, lemma, sense):
        """Get the synset associated with the lemma and the sense. An example
        lemma-sense combination is 'walk' with '2:38:00::'. Returns None if no
        such synset was found."""
        return self.synset_idx.get(lemma, {}).get(lemma + '%' + sense)

    def get_senses(self):
        senses = set()
        for scfile in self.files:
            for sent in scfile.get_sentences():
                for wf in sent.wfs:
                    if wf.has_sense():
                        senses.add("%s%%%s" % (wf.lemma, wf.lexsn))
        return senses

    def get_common_nouns(self):
        answer = []
        for scfile in self.files:
            answer.extend(scfile.get_common_nouns())
        return answer

    def get_common_noun_index(self):
        idx = {}
        for scfile in self.files:
            nouns = scfile.get_common_nouns()
            sub_idx = create_lemma_index(nouns)
            idx[scfile.fname] = sub_idx
        return idx


class SemcorFile(object):

    """Class that stores all information from Semcor files.

    Instance variables:

    fname : string
       The name of the file, this is the full path starting from the code
       directory

    paragraphs : list of Paragraphs

    forms : list of WordForms
       All the WordForms in the document that have a sense.

    lemma_idx : dict { string -> list of WordForms }
       Dictionary indexed on lemmas where the value is a list of WordForms that
       are associated with the lemma.

    """

    def __init__(self, fname):
        self.fname = fname
        self.paragraphs = []
        self.forms = []
        self.lemma_idx = {}

    def __str__(self):
        # just print the subcorpus and the basename
        subcorpus = self.fname.split(os.sep)[-3]
        basename = os.path.basename(self.fname)
        return "<SemcoreFile %s %s>" % (subcorpus, basename)

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

    def get_sentence(self, sent_id):
        """Return the sentence with sid equal to sent_id or return None if no such
        sentence exists."""
        for par in self.paragraphs:
            for sentence in par.sentences:
                if sentence.sid == sent_id:
                    return sentence
        return None

    def get_sentences(self):
        """Return a list of all sentences in the document."""
        sentences = []
        for para in self.paragraphs:
            sentences.extend(para.sentences)
        return sentences

    def get_nominals(self):
        """Return a list of all nominals in the document."""
        return [wf for wf in self.forms if wf.is_nominal()]

    def get_common_nouns(self):
        """Return the list of all common nouns in the document."""
        return [wf for wf in self.forms if wf.is_common_noun()]


if __name__ == '__main__':

    options, args = getopt.getopt(sys.argv[1:], 'n:', ['compile'])
    options = { name: value for (name, value) in options }
    maxfiles = int(options.get('-n', 999))

    if '--compile' in options:
        compile_semcor(maxfiles)
    else:
        sc = Semcor(maxfiles)
        print(sc)
