"""

Code to browse Semcor.

Should run in both Python 2 and Python 3.

Usage:

$ python browse.py

This assumes that sources have been compiled (see semcor.py).


Browser requirements

- give me the documents/sentences where those two senses co-occur
- search for a synset
x- search for a word
- search for occurrences of pairs of basic types
- display a document
- display a paragraph
x- display a sentence
x- statistics on all senses for a word


TODO:

- the browser itself
- most of the above requirements
    - requires several more indexes
- bundle semcor into this repository
- for compiled sources maintain both python 2 and python 3 versions of pickle files
    - compile into data/brownN/python_version
- semcor is now initialized on one corpus, should perhaps be a list
- when loading, print warning if sources have not been compiled yet
    - include note that python version matters
- make sentences a linked list

"""

from __future__ import print_function

import sys

from semcor import Semcor, SemcorFile, BROWN1, BROWN2
from utils import read_input
from ansi import BLUE, BOLD, END


class Browser(object):

    def __init__(self, semcor):
        self.semcor = semcor
        self.userloop()

    def userloop(self):
        while True:
            print('*> ', end='')
            user_input = read_input()
            if user_input.strip() == 'q':
                break
            elif user_input == 'h':
                print('h - help')
                print('n LEMMA - search for noun LEMMA')
            elif user_input == 't':
                # convenience option for testing
                self.show_stats('walk')
            elif user_input.startswith('stats '):
                lemma = get_lemma(user_input)
                self.show_stats(lemma)
            elif user_input.startswith('s '):
                lemma = get_lemma(user_input)
                self.show_lemma(lemma)

    def get_lemmas(self, lemma):
        return self.semcor.lemma_idx.get(lemma, [])
        
    def show_lemma(self, lemma):
        idx = index_lemmas(self.get_lemmas(lemma))
        for pos in idx:
            for sense in idx[pos]:
                print('\n', BOLD + BLUE, idx[pos][sense][0], END, '\n', sep='')
                for wf in idx[pos][sense]:
                    wf.sent.pp(highlight=wf.position)
        print()

    def show_stats(self, lemma):
        print()
        lemmas = self.get_lemmas(lemma)
        lemma_idx = index_lemmas(lemmas)
        print('Lemma occurs', len(lemmas), 'times\n')
        for pos in lemma_idx:
            print(pos)
            for sense in lemma_idx[pos]:
                print("   wnsn=%s lexsn=s%s  -- %s occurrences" % \
                          (sense[0], sense[1], len(lemma_idx[pos][sense])))
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


if __name__ == '__main__':

    # this assumes that sources have been compiled
    semcor = Semcor(BROWN1)
    semcor.load(5)
    Browser(semcor)
    
