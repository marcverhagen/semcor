import sys, bs4

from objects import Paragraph, Sentence, WordForm, Punctuation


def parse(semcor_file):
    library = 'lxml' if sys.version_info.major == 2 else 'html5lib'
    soup = bs4.BeautifulSoup(open(semcor_file.fname), library)
    for p in soup.findAll('p'):
        parse_paragraph(semcor_file, p)
    return semcor_file


def parse_paragraph(semcor_file, p):
    pid = p.get('pnum')
    paragraph = Paragraph(pid)
    semcor_file.add_paragraph(paragraph)
    for s in p.findAll('s'):
        parse_sentence(semcor_file, paragraph, s)


def parse_sentence(semcor_file, paragraph, s):
    sid = s.get('snum')
    sentence = Sentence(semcor_file, paragraph, sid)
    paragraph.add_sentence(sentence)
    position = 0
    for dtr in s.children:
        if dtr.name == 'wf':
            wf = WordForm(paragraph, sentence, position, dtr)
            sentence.add_element(wf)
            position += 1
        elif dtr.name == 'punc':
            punct = Punctuation(dtr)
            sentence.add_element(punct)
            position += 1
        elif dtr.name is None:
            pass
        else:
            print('WARNING, unexpected daughter:', dtr)
            

