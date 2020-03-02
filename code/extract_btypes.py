"""extract_btypes.py

Extracts all nominal word forms from SemCor and print them in text order with
the associated synset and basic type. If we cannnot find a synset just print
None and None.

Usage:

$ python3 extract_btypes.py

Results are written to semcor-types.tab, which can be used as a gold standard
for a method on CoreLex or WordNet in https://github.com/marcverhagen/corelex
that provides a base line for basic type extraction.

"""


import sys

from semcor import Semcor, SemcorFile
 
sc = Semcor()

fh = open(sys.argv[1], 'w')

for file in sc.files:
    for form in file.forms:
        if form.pos != 'NN':
            continue
        synset = form.synset
        if synset is None:
            fh.write("%s\tNone\tNone\n" % form.lemma)
        else:
            fh.write("%s\t%s\t%s\n" % (form.lemma, synset.ssid, synset.btypes))

