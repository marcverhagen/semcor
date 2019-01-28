"""index.py

All code associated with the various indexes used.

"""

import os, sys
import ansi, utils


class IndexedWordForms(object):

    """Class that provides an interface to a set of WordForms. This is in
    addition to the lemma_idx on Semcor, which is a simple index from lemmas to
    WordForm lists, which contains all WordForms in the corpus. This class is
    intended to store the results of specific searches and has more than one way
    to access the data.

    Attributes:

    lemma_idx : dict ( string -> list of WordForms )

    lemma_fname_idx : dict ( string -> dict ( string -> list of WordForms ) )

    fname_lemma_idx : dict ( string -> dict ( string -> list of WordForms ) )

    btypes_idx : BTypePairDictionary
       Index to store wordforms that go with pairs of basic types (btypes). The
       key is always an ordered pair of btypes and excludes btypes with spaces
       in them (meaning a sense is associated with two basic types, for now we
       avoid dealing with these).

    """

    def __init__(self, semcor, wfs):
        self.semcor = semcor
        self.wfs = wfs
        self.lemma_idx = create_lemma_index(wfs)
        self.lemma_fname_idx = {}
        for lemma, wfs in self.lemma_idx.items():
            self.lemma_fname_idx[lemma] = create_fname_index(wfs)
        self.fname_lemma_idx = invert_index(self.lemma_fname_idx)
        self.btypes_idx = {}

    def filter_lemmas_with_only_one_sense_per_document(self):
        """This filters lemma_fname_idx, keeping only those lemmas that have at
        least two senses in a document. It thus checks the list of wordforms for
        each lemma/document pair and removes the list if it only has one
        sense. In addition it updates fname_lemma_idx so that it is in sync with
        lemma_fname_idx. Note that after filtering the two indexes changed do
        not contains all word forms in self.wfs and self.lemma_idx anymore, that
        is, wfs and lemma_idx are not changed."""
        self.lemma_fname_idx = filter_lemma_fname_index(self.lemma_fname_idx)
        self.fname_lemma_idx = invert_index(self.lemma_fname_idx)

    def initialize_btypes_index(self):
        self.btypes_idx = BTypePairDictionary(self)

    def get_pairs(self, min_lemmas=1, min_instances=1):
        pairs = self.btypes_idx.keys()
        pairs = [pair for pair in pairs
                 if len(self.btypes_idx[pair]['ALL']) >= min_instances
                 and len(self.btypes_idx[pair]['LEMMAS']) >= min_lemmas]
        return pairs

    def print_lemma_fname_index(self):
        for lemma in sorted(self.lemma_fname_idx):
            fname_idx = self.lemma_fname_idx[lemma]
            wf_count = sum([len(wfs) for wfs in fname_idx.values()])
            print("\n%s (%d)" % (lemma, wf_count))
            for fname, wfs in fname_idx.items():
                base = os.path.basename(fname)
                btypes = set([wf.synset.btypes for wf in wfs])
                for wf in wfs:
                    print('  ', base, wf.synset.btypes, wf)
        print()

    def print_btypes_index(self, n=None):
        self.btypes_idx.print_index(n)

    def print_btypes_index_summary(self):
        self.btypes_idx.print_summary()


class BTypePairDictionary(object):

    def __init__(self, wordforms_idx):
        self.data = {}
        for lemma in wordforms_idx.lemma_fname_idx:
            for fname in wordforms_idx.lemma_fname_idx[lemma]:
                wfs = wordforms_idx.lemma_fname_idx[lemma][fname]
                btypes = set([wf.synset.btypes for wf in wfs])
                btypes = tuple(sorted(bt for bt in btypes if not ' ' in bt))
                btype_pairs = pairs(btypes)
                for btype_pair in btype_pairs:
                    self.add_wordforms(lemma, btype_pair, wfs)

    def __getitem__(self, key):
        return self.data[key]

    def __iter__(self):
        return self.data.__iter__()

    def keys(self):
        return self.data.keys()

    def add_wordforms(self, lemma, btype_pair, wfs):
        self.data.setdefault(btype_pair, { 'ALL': [], 'LEMMAS': {} })
        self.data[btype_pair]['LEMMAS'].setdefault(lemma, [])
        # this makes sure that only the wordforms with a basic type
        # that is part of the pair are included
        filterd_wfs = [wf for wf in wfs if wf.synset.btypes in btype_pair]
        self.data[btype_pair]['ALL'].extend(filterd_wfs)
        self.data[btype_pair]['LEMMAS'][lemma].extend(filterd_wfs)

    def print_summary(self):
        for btypes in sorted(self.data):
            wfs = self.data[btypes]['ALL']
            lemmas = self.data[btypes]['LEMMAS']
            print("%s%s%s" % (ansi.BOLD, ' - '.join(btypes), ansi.END), end='  ')
            print("{ lemmas: %d, instances: %d }" % (len(lemmas), len(wfs)))
        print("\nTOTAL NUMBER OF PAIRS: %d\n" % len(self.data))

    def print_index(self, n=None):
        if n is not None:
            count = 0
        for btypes in sorted(self.data):
            if n is not None:
                count += 1
                if count > n:
                    break
            print("\n%s%s%s\n" % (ansi.BOLD, ' - '.join(btypes), ansi.END))
            for lemma in self.data[btypes]['LEMMAS']:
                wfs = self.data[btypes]['LEMMAS'][lemma]
                wfs.sort(key=lambda x: x.synset.btypes)
                for wf in wfs:
                    (left, kw, right) = wf.kwic(50)
                    line = utils.kwic_line(left, kw, right, 50)
                    print("   %s %s%s %s" % (ansi.GREEN, wf.synset.btypes, ansi.END, line))


def create_lemma_index(wordforms):
    """Return an index of the list of WordForms given. The keys are lemmas and
    the values are lists of WordForms."""
    idx = {}
    for wf in wordforms:
        idx.setdefault(wf.lemma, []).append(wf)
    return idx


def create_fname_index(wordforms):
    """Return an index of the list of WordForms given. The keys are file names and
    the values are lists of WordForms."""
    idx = {}
    for wf in wordforms:
        idx.setdefault(wf.sent.fname, []).append(wf)
    return idx


def invert_index(idx):
    """Returns a new index with the same values, but structured differently in that
    in the output top-level keys switch place with embedded keys. For example,
    "k1 -> k2 -> value" will be turned into "k2 -> k1 -> value". The values
    themselves do not change."""
    result = {}
    for fname in idx:
        for lemma in idx[fname]:
            result.setdefault(lemma, {})
            result[lemma][fname] = idx[fname][lemma]
    return result


def filter_lemma_fname_index(idx):
    """Return a new index that only has those lemmas-fname pairs that are
    associated with a list of WordForms that have at least two different basic
    types."""

    def filter_sub_index(idx):
        """Return a new index that only has those lemmas that are associated with a
        list of WordForms that have at least two different basic types. Include only
        those WordForms that have a synset value. Input index has file namess as
        keys and lists of WordForms as values."""
        filtered_idx = {}
        for fname, wfs in idx.items():
            wfs = [wf for wf in wfs if wf.synset is not None]
            if len(set([wf.synset.btypes for wf in wfs])) > 1:
                filtered_idx[fname] = wfs
        return filtered_idx

    idx = { lemma: filter_sub_index(idx) for lemma, idx in idx.items() }
    return { lemma: idx for lemma, idx in idx.items() if idx }


def pairs(sequence):
    """Returns the list of pairs that you can create from the sequence. The results
    are ordered and no duplicates will be included, also, if <a,b> is in the result
    then <b,a> won't be."""
    sequence = sorted(list(set(sequence)))
    indices = list(range(len(sequence)))
    return [(sequence[i], sequence[j]) for i in indices for j in indices if i < j]
