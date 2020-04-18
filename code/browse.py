"""

Code to browse Semcor.

Usage:

$ python3 browse.py [--n MAXFILES]

This assumes that sources have been compiled (see semcor.py).

Current functionality:
- printing statistics for a lemma (all senses)
- searching for a lemma and display results
- include synset identifiers (new style, with lemmas) and glosses
- display a paragraph that contains a given sentence

Further browser requirements
- give me the documents/sentences where those two senses co-occur
- search for a synset
- search for occurrences of pairs of basic types
- display context for a sentence (not the paragraph, but a window of
  neighoring sentences)
- add basic types to statistics on all senses for a word

TODO:
- when loading, print warning if sources have not been compiled yet
- make sentences a linked list
- for each sense only 10 word forms (selected randomly) are printed
  perhaps add code to show more or to change the number of forms

"""

import sys, re, textwrap, random

# SemcorFile needs to be imported for loading the pickled files
from semcor import Semcor, SemcorFile
from utils import read_input, kwic_line
from ansi import BLUE, GREEN, BOLD, GREY, END


class Browser(object):

    def __init__(self, semcor):
        self.semcor = semcor
        self.userloop()

    def userloop(self):
        while True:
            print('*> ', end='')
            user_input = read_input().strip()
            if user_input == 'q':
                break
            elif user_input in ('?', 'h', 'help'):
                print_help()
            elif user_input == 't':
                # convenience option for testing
                self.show_stats('walk')
                self.show_paragraph('br-a11-28')
            elif user_input.startswith('s '):
                self.show_stats(get_lemma(user_input))
            elif user_input.startswith('v '):
                self.show_verb(get_lemma(user_input))
            elif user_input.startswith('n '):
                self.show_noun(get_lemma(user_input))
            elif user_input.startswith('a '):
                self.show_adjective(get_lemma(user_input))
            elif user_input.startswith('r '):
                self.show_adverb(get_lemma(user_input))
            elif user_input.startswith('p '):
                self.show_paragraph(get_sentence(user_input))
            elif user_input == 'bt':
                self.show_basic_types()
            elif user_input.startswith('bt '):
                self.show_basic_type(user_input[2:].strip())
            elif user_input == 'btp':
                self.show_basic_type_pairs()
            elif user_input.startswith('btp '):
                self.show_basic_type_pair(user_input[3:].strip())
            else:
                print('\nUnknown command, available commands:')
                print_help()

    def get_lemmas(self, lemma):
        return self.semcor.get_lemmas(lemma)

    def show_noun(self, lemma):
        idx = index_lemmas(self.get_lemmas(lemma))
        for pos in idx:
            self.show_senses(idx, pos, 'NN')
        print()

    def show_verb(self, lemma):
        idx = index_lemmas(self.get_lemmas(lemma))
        for pos in idx:
            self.show_senses(idx, pos, 'VB')
        print()

    def show_adjective(self, lemma):
        idx = index_lemmas(self.get_lemmas(lemma))
        for pos in idx:
            self.show_senses(idx, pos, 'JJ')
        print()

    def show_adverb(self, lemma):
        idx = index_lemmas(self.get_lemmas(lemma))
        for pos in idx:
            self.show_senses(idx, pos, 'RB')
        print()

    def show_senses(self, idx, pos, tag_prefix):
        if pos.startswith(tag_prefix):
            for sense in idx[pos]:
                # each sense is a word form, the word forms all have identical
                # senses so we use the first one to print as a header
                first_wf = idx[pos][sense][0]
                lemma = first_wf.lemma
                sense_id = first_wf.lexsn
                synset = first_wf.synset
                print('\n', BOLD + BLUE, first_wf, END, '\n', sep='')
                if synset is not None:
                    btypes = synset.btypes if len(synset.btypes) < 12 else ''
                    print(synset, synset.btypes)
                    print('\n', GREEN, synset.gloss, END, '\n', sep='')
                wfs = idx[pos][sense]
                random.shuffle(wfs)
                for wf in wfs[:10]:
                    context = 50
                    (left, kw, right) = wf.kwic(context)
                    sid = wf.sent.fname + '-' + wf.sid
                    line = kwic_line(left, kw, right, context)
                    print("%s%-10s%s %s" % (GREY, sid, END, line))

    def show_stats(self, lemma):
        print()
        lemmas = self.get_lemmas(lemma)
        lemma_idx = index_lemmas(lemmas)
        print('Occurrences:', len(lemmas), '\n')
        for pos in lemma_idx:
            print(pos)
            for sense in lemma_idx[pos]:
                lexsn = "{ lexsn=%s }" % sense[1]
                synset = lemma_idx[pos][sense][0].synset
                occurrences = len(lemma_idx[pos][sense])
                print_string = lexsn
                if synset is not None:
                    print_string = "%s %s" % (lexsn, synset)
                print("  %3d  %s" % (occurrences, print_string))
        print()

    def show_paragraph(self, sentence):
        result = re.match(r"(.*)-(\d+)$", sentence)
        if result is None:
            print("Could not get file name and sentence number from input")
            return
        fname = result.group(1)
        sent = result.group(2)
        semcor_file = self.semcor.get_file(fname)
        if semcor_file is None:
            print("Could not find file %s" % fname)
        else:
            sentence = semcor_file.get_sentence(sent)
            if sentence is None:
                print("Could not find sentence %s" % sent)
            print()
            paragraph = sentence.para.pp()
            print()

    def show_basic_types(self):
        btypes = self.semcor.get_btypes()
        for bt in sorted(btypes):
            print("%s  %2d pairs" % (bt, len(btypes[bt])))

    def show_basic_type(self, bt):
        btypes = self.semcor.get_btypes()
        pairs = sorted(btypes.get(bt, []))
        for pair in pairs:
            print("%s-%s  %3d instances %2d lemmas" %
                  (pair[0], pair[1],
                   len(self.semcor.noun_idx.btypes_idx[pair]['ALL']),
                   len(self.semcor.noun_idx.btypes_idx[pair]['LEMMAS'])))

    def show_basic_type_pairs(self):
        pairs = self.semcor.noun_idx.get_pairs(min_lemmas=2, min_instances=4)
        for pair in pairs:
            print("%s-%s (%d wordforms)" %
                  (pair[0], pair[1],
                   len(self.semcor.noun_idx.btypes_idx[pair]['ALL'])))

    def show_basic_type_pair(self, pair):
        print()
        print(pair)
        pair = tuple(pair.split('-')[:2])
        wfs_idx = self.semcor.noun_idx.btypes_idx.data.get(pair)
        if wfs_idx is None:
            print("No results for %s-%s\n" % (pair[0], pair[1]))
            return
        for lemma in wfs_idx['LEMMAS'].keys():
            wfs = wfs_idx['LEMMAS'][lemma]
            wfs.sort(key=lambda x: x.synset.btypes)
            for wf in wfs:
                context = 40
                (left, kw, right) = wf.kwic(context)
                sid = wf.sent.fname + '-' + wf.sid
                bt = wf.synset.btypes
                line = kwic_line(left, kw, right, context)
                print("%s%s%s %s%-10s%s %s" % (GREEN, bt, END, GREY, sid, END, line))
            print()

def index_lemmas(lemmas):
    lemma_idx = {}
    for lemma in lemmas:
        lemma_idx.setdefault(lemma.pos, {})
        sense = (lemma.wnsn, lemma.lexsn)
        lemma_idx[lemma.pos].setdefault(sense, []).append(lemma)
    return lemma_idx


def get_lemma(user_input):
    if sys.version_info.major == 2:
        lemma = user_input.split()
        return '_'.join(lemma[1:])
    else:
        lemma = user_input.split(maxsplit=1)[1]
        return lemma.replace(' ', '_')

def get_sentence(user_input):
    # This happens to be the same as getting the lemma (but replacing spaces
    # with nderscores will never happen).
    return get_lemma(user_input)


def print_help():
    print()
    print('h          -  help')
    print('s LEMMA    -  show statistics for LEMMA')
    print('n LEMMA    -  search for noun LEMMA')
    print('v LEMMA    -  search for verb LEMMA')
    print('a LEMMA    -  search for adjective LEMMA')
    print('r LEMMA    -  search for adverb LEMMA')
    print('p SID      -  print paragraph with sentence SID')
    print('bt         -  show list of basic types that occur in potentially interesting pairs')
    print('bt NAME    -  show potentially interesting pairs for the basic type')
    print('btp        -  show list of potentially interesting basic type pairs')
    print('btp T1-T2  -  show examples for basic type pair')
    print()


if __name__ == '__main__':

    # this assumes that sources have been compiled
    files_to_load = 999
    if len(sys.argv) > 2 and sys.argv[1] == '-n':
        files_to_load = int(sys.argv[2])
    semcor = Semcor(files_to_load)
    Browser(semcor)
    
