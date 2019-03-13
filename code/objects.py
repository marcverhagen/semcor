"""

"""

from __future__ import print_function

import os

from ansi import BOLD, BLUE, GREEN, GREY, END


class SemcorObject(object):

    def is_paragraph(self):
        return False

    def is_sentence(self):
        return False

    def is_word_form(self):
        return False

    def is_punctuation(self):
        return False


class Paragraph(SemcorObject):

    def __init__(self, pid):
        self.pid = pid         # <string>
        self.sentences = []

    def add_sentence(self, sent):
        self.sentences.append(sent)

    def is_paragraph(self):
        return True

    def collect_forms(self, forms):
        """Collect all instances of WordForm that have a sense."""
        for s in self.sentences:
            s.collect_forms(forms)
        
    def pp(self):
        print("<para %s>" % self.pid)
        for s in self.sentences:
            s.pp()


class Sentence(SemcorObject):

    def __init__(self, semcor_file, para, sid):
        self.fname = os.path.basename(semcor_file.fname)
        self.para = para
        self.pid = para.pid     # <string>
        self.sid = sid          # <string>
        self.wfs = []

    def __str__(self):
        return "<Sentence %s:%s with %d wfs>" % (self.fname, self.sid, len(self.wfs))

    def is_sentence(self):
        return True

    def get_element(self, n):
        """Returns the WordForm or the Punctuation instance at position n of the list of
        elements in the sentence, returns None if there is no such index."""
        try:
            return self.wfs[n]
        except IndexError:
            return None

    def add_wf(self, wf):
        # note that a wf will either be an instance of WordForm or an instance
        # of Punctuation
        self.wfs.append(wf)

    def collect_forms(self, forms):
        for wf in self.wfs:
            if wf.is_word_form() and wf.has_sense():
                forms.append(wf)

    def as_string(self):
        return ' '.join([t.text for t in self.wfs])
    
    def pp(self, highlight=None):
        print("%s%s%s-%s%s: " % (GREY, GREEN, self.fname, self.sid, END), end='')
        for wf in self.wfs:
            if wf.is_word_form() and highlight == wf.position:
                print(BOLD + BLUE + wf.text + END, end=' ')
            #elif wf.has_sense():
            #    print(BLUE+wf.text+END, end=' ')
            else:
                print(wf.text, end=' ')
        print()


class WordForm(SemcorObject):

    """Semcor word forms have a lemma, a part-of-speech, a wordnet sense and a
    lexical sense (we are for now ignoring other attributes). Word forms are
    initiated from a tag like the following.
    
       <wf cmd=done pos=VB lemma=say wnsn=1 lexsn=2:32:00::>said</wf>

    Note that these word forms can have multiple tokens and those are not just
    for names, for example primary_election is a word form. Some word forms do
    not have senses associated with them, for them we just have POS and the
    text."""

    def __init__(self, para, sent, position, tag):
        self.para = para                  # instance of Paragraph
        self.sent = sent                  # instance of Sentence
        self.position = position          # position in the sentence
        self.pid = para.pid
        self.sid = sent.sid
        self.pos = tag.get('pos')
        self.rdf = tag.get('rdf')
        self.pn = tag.get('pn')
        self.lemma = tag.get('lemma')
        self.wnsn = tag.get('wnsn')
        self.lexsn = tag.get('lexsn')
        self.text = tag.getText()
        self.synset = None
        self.keys = tuple(tag.__dict__['attrs'].keys())  # for statistics

    def __str__(self):
        if self.wnsn is None:
            return "<wf %s %s>" % (self.pos, self.text)
        else:
            return "<wf %s %s %s %s>" % (self.pos, self.lemma, self.wnsn, self.lexsn)

    def sense(self):
        return "%s%%%s" % (self.lemma, self.lexsn) if self.has_sense() else None

    def is_word_form(self):
        return True

    def is_nominal(self):
        return self.pos.startswith('NN')

    def is_common_noun(self):
        return self.pos in ('NN', 'NNS')

    def has_sense(self):
        return self.wnsn is not None and self.lexsn is not None

    def kwic(self, context):
        kw = self.sent.wfs[self.position].text
        left = self.sent.wfs[:self.position]
        right = self.sent.wfs[self.position+1:]
        left = ' '.join([t.text for t in left])
        right = ' '.join([t.text for t in right])
        left = left[-context:]
        right = right[:context]
        return (left, kw, right)
    

class Punctuation(SemcorObject):

    def __init__(self, tag):
        self.text = tag.getText()
        self.keys = tuple()

    def __str__(self):
        return "<Punctuation %s>" % self.text

    def is_punctuation(self):
        return True

    def has_sense(self):
        return False

    def sense(self):
        return None
