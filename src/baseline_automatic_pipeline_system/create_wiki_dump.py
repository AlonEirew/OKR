"""
Creates Wiki dumps for a corpus input.
input: comma separated file (TBD-Need to add method to pull the mentions from GS format file)
output: pickled file that represent for each mention the wiki page presented by mention title
        page redirect (if exist) & aliases (if exist)

data is pickled to a file, examples can be found in data/wiki_dumps

Usage: create_wiki_dump --input=INPUT_FILE_PATH --output=OUTPUT_FILE_PATH

Usage example: create_wiki_dump --input=test/out/Acronym_all_news.csv --output=data/wiki_dumps/Acronym_all_news.pickle

"""


import sys, os
import pickle
import pywikibot
import pandas as pd
import json
from docopt import docopt, printable_usage

for pack in os.listdir("src"):
    sys.path.append(os.path.join("src", pack))

from src.baseline_system.data.Page import Page

site = pywikibot.Site('en', 'wikipedia')
result_dump = {}


def generate_wiki_dump(input, output):
    with open(input, "r") as myfile:
        file_lines = myfile.readlines()

    for line in file_lines:
        content = line.strip().split(',')
        word1 = content[0]
        word2 = content[1]

        add_page(word1)
        add_page(word2)
        add_page(word1.title())
        add_page(word2.title())

    with open(output, "w") as myfile:
        pickle.dump(result_dump, myfile)


def generate_wiki_dump_acronym():
    dataframes = pd.read_csv("./data/intel_gs/Acronym_all_news.csv")
    for index, row in dataframes.iterrows():
        group1 = row[1].replace('[', '').replace(']', '').split(',')
        group2 = row[2].replace('[', '').replace(']', '').split(',')
        add_page(group2[0].strip())
        for word1 in group1:
            word1 = word1.strip()
            add_page(word1)
            add_page(word1.title())

    with open('./data/intel_gs/Acronym_all_news_wiki_dump.pickle', "w") as myfile:
        pickle.dump(result_dump, myfile)


def add_page(word):
    if word not in result_dump:
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
        if page is not None:
            print 'adding page-' + page.to_string()


def get_aliases(page):
    """
    Returns page aliases
    :param page: wikidata mention page representation
    :return: Returns page aliases
    """
    if page is not None:
        try:
            item = pywikibot.ItemPage.fromPage(page) # this can be used for any page object
            item.get()  # need to call it to access any data.
            if 'en' in item.aliases:
                aliases = item.aliases['en']
                return aliases
        except (pywikibot.NoPage, AttributeError, TypeError, NameError):
            pass

    return None


if __name__ == '__main__':
    args = docopt(__doc__)
    if len(args) != 2:
        print 'need provide input and output arguments'
        print printable_usage(__doc__)
        sys.exit()

    input = args['--input']
    output = args['--output']
    generate_wiki_dump(input, output)

    print '--- Done Creating Dump Successfully! ---'
