"""analyze.py

Some analysis of the wf tags in semcor.

Usage:

$ python3 analyze.py MAXFILES?

The optional argument determines how many files are used for analysis, the
default is to use all files. This assumes that files have been compiled with
semcor.py. Results are printed to standard output and to a file weird-rdfs.txt,
the latter contains some ANSI espace sequences and to see the contents you
should just do a "cat weird-rdfs.txt" (those escape sequences are no good for
Windows or when you want to open the file in an editor, this will be changed at
some point).

There are a couple of funky parts to semcor. One is that the lemma value of
proper names is set to the the entity type. This script analyzes what happens
for those cases, which seems to be that the value of the lemma, pn, and rdf
attributes are all set to the entity type.

However, there are word forms that have an rdf attribute but that are not proper
names. Not sure exactly what they exactly are, but they are printed to the file
weird-rdfs.txt. It should also be noted that those cases are not the same as the
cases where the lemma is different from the actual text of the wf tag, that
group is much bigger (more than half of all forms, it includes all inflections).

TODO:
- add argument to suppress ANSI escape sequences in output file
- analyze what is going on in weird-rdfs.txt

"""


import sys
from collections import Counter
from semcor import Semcor, SemcorFile
from ansi import BLUE, GREY, END
from utils import kwic_line


def collect_data(sc, raw_attributes, attributes, attribute_index,
                 groups, weird_rdfs):
    
    for scfile in sc.files:
        for wf in scfile.forms:
            raw_attributes['list'].extend(wf.keys)
            # counting the attributes
            for attr in attributes:
                val = getattr(wf, attr)
                if val is not None:
                    attribute_index[attr]['count'] += 1
                    attribute_index[attr]['values'].append(val)
            # the case where we have a pn and the lemma is actually set to it
            if wf.lemma == wf.pn == wf.rdf:
                groups['count'] += 1
                groups['tag'].append(wf.pos)
                groups['pn_value'].append(wf.pn)
                groups['rdf_value'].append(wf.rdf)
            # there are rdf attributes used for something else
            if wf.rdf is not None and wf.pn is None:
                weird_rdfs.append(wf)
    # make dictionaries of all the lists
    raw_attributes['dict'] = Counter(raw_attributes['list'])
    for key in ('tag', 'pn_value', 'rdf_value'):
        groups[key] = Counter(groups[key])
    for attr in attributes:
        attribute_index[attr]['values'] = Counter(attribute_index[attr]['values'])


def print_attr_info(raw_attributes, attribute_index):
    # for now just printing the raw counts
    print("ATTRIBUTES\n")
    for attr in sorted(raw_attributes['dict']):
        print("  %6d  %s" % (raw_attributes['dict'][attr], attr))


def print_pn_info(pns):
    print("\nPROPER NAMES")
    print("\n   COUNT = %s" % pns['count'])
    for key in ('tag', 'pn_value', 'rdf_value'):
        print()
        for subkey, count in pns[key].items():
            print("     %4d  %s=%s" % (count, key, subkey))
    print()


def print_weird_rdfs(forms):
    lemmas = {}
    context = 50
    for wf in forms:
        (left, kw, right) = wf.kwic(context)
        lemmas.setdefault(wf.rdf, []).append((left, kw, right, wf.sent.as_string()))
    with open('weird-rdfs.txt', 'w') as fh:
        for lemma in sorted(lemmas):
            for (left, kw, right, sent) in lemmas[lemma]:
                width = (2 * context) + 30
                line = kwic_line(left, kw, right, context)
                line = '{s: <{width}}'.format(s=line, width=width)
                fh.write("%s %s%s%s\n" % (line, GREY, lemma, END))


def count_basic_types(sc):
    """Counts how often noun tokens go with a particular count of basic types."""
    instances = 0
    btypes_count = []
    word_sets_per_btype_size = []
    for i in range(21):
        word_sets_per_btype_size.append(set())
    for file in sc.files:
        for wf in file.forms:
            if wf.pos != 'NN':
                continue
            btypes = []
            synsets = sc.synset_idx.get(wf.lemma,{}).values()
            synsets = [ss for ss in synsets if ss.cat == 'noun']
            for synset in synsets:
                btypes.extend(synset.btypes.split())
            instances += 1
            btypes_count.append(len(set(btypes)))
            word_sets_per_btype_size[len(set(btypes))].add(wf.lemma)
            if len(set(btypes)) > 8:
                print(len(set(btypes)), wf.lemma)
    print("INSTANCES: %d" % instances)
    print("TYPE_COUNT: %s" % Counter(btypes_count))
    print("\nWORD_SET_PER_COUNT:")
    for i in range(21):
        words = word_sets_per_btype_size[i]
        print(i, len(words), list(words)[:5])


if __name__ == '__main__':

    maxfiles = int(sys.argv[1]) if len(sys.argv) > 1 else 999

    sc = Semcor(maxfiles)

    # basic statistics on all attributes
    raw_attributes = { 'list': [], 'dict': None }
    attributes = ('pos', 'rdf', 'pn', 'lemma', 'wnsn', 'lexsn')
    attribute_index = {}
    for attr in attributes:
        attribute_index[attr] = { 'count': 0, 'values': [] }

    # keeping track of what happens when there is a pn attribute attribute
    pns = { 'count': 0, 'tag': [], 'pn_value': [], 'rdf_value': [] }

    # those forms with an rdf attribute that do not have a group attribute
    weird_rdfs = []

    collect_data(sc, raw_attributes, attributes, attribute_index, pns, weird_rdfs)

    print_attr_info(raw_attributes, attribute_index)
    print_pn_info(pns)
    print_weird_rdfs(weird_rdfs)

    count_basic_types(sc)
