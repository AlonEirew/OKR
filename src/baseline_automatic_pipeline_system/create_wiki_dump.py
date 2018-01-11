"""
Creates Wiki dumps for a corpus input.
input: comma separated file (TBD-Need to add method to pull the mentions from GS format file)
output: pickled file that represent for each mention the wiki page presented by mention title
        page redirect (if exist) & aliases (if exist)

data is pickled to a file, examples can be found in data/wiki_dumps

Usage: create_wiki_dump --input=INPUT_FILE_PATH --output=OUTPUT_FILE_PATH

Usage example: create_wiki_dump --input=test/out/WhitneyHeichelPairs.txt --output=data/wiki_dumps/WhitneyHeichelWikiDump.pickle

"""


import sys, os
import pickle
import pywikibot
from docopt import docopt, printable_usage

for pack in os.listdir("src"):
    sys.path.append(os.path.join("src", pack))

from src.baseline_system.data.Page import Page
from src.baseline_system.eval_entity_coref import get_aliases

site = pywikibot.Site('en', 'wikipedia')
result_dump = {}


def generate_wiki_dump(input, output):
    with open(input, "r") as myfile:
        file_lines = myfile.readlines()

    for line in file_lines:
        content = line.strip().split(',')
        word1 = content[0]
        word2 = content[1]

        if word1 not in result_dump:
            add_page(word1)

        if word2 not in result_dump:
            add_page(word2)

        if word1.title() not in result_dump:
            add_page(word1.title())

        if word2.title() not in result_dump:
            add_page(word2.title())

    with open(output, "w") as myfile:
        pickle.dump(result_dump, myfile)


def add_page(word):
    page = pywikibot.Page(site, word)
    pageid = page.pageid
    page_has_redirect = page.isRedirectPage()
    redirect = None
    aliases = get_aliases(page)
    word = unicode(word)

    if page_has_redirect:
        red_page = page.getRedirectTarget()
        red_title = red_page.title.im_self._link.title
        red_aliases = get_aliases(red_page)
        redirect = Page(red_title, red_page.pageid, False, None, red_aliases)
        if red_title not in result_dump:
            result_dump[red_title] = redirect

    page = Page(word, pageid, page_has_redirect, redirect, aliases)
    result_dump[word] = page


if __name__ == '__main__':
    args = docopt(__doc__)
    if len(args) != 2:
        print 'need provide input and output arguments'
        print printable_usage(__doc__)
        sys.exit()

    input = args['--input']
    output = args['--output']
    generate_wiki_dump(input, output);

    print '--- Done Creating Dump Successfully! ---'
