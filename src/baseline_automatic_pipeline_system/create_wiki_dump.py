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
from entity_matching.obj.Page import Page

for pack in os.listdir("src"):
    sys.path.append(os.path.join("src", pack))

from src.common.okr import load_graphs_from_folder, load_graph_from_file
from docopt import docopt, printable_usage

site = pywikibot.Site('en', 'wikipedia')
result_dump = {}


def generate_wiki_dump_from_gs(input, output):
    if os.path.isdir(input):
        gold_graphs = load_graphs_from_folder(input)
    else:  # single gold file
        gold_graphs = [load_graph_from_file(input)]

    for gold_val in gold_graphs:
        for key, val in gold_val.ent_mentions_by_key.iteritems():
            add_all_pages(val.terms)

    with open(output, "w") as myfile:
        pickle.dump(result_dump, myfile)


def generate_wiki_dump_acronym(input=None, output=None):
    dataframes = pd.read_csv("./data/intel_gs/Acronym_all_news.csv")
    for index, row in dataframes.iterrows():
        group1 = row[1].replace('[', '').replace(']', '').split(',')
        group2 = row[2].replace('[', '').replace(']', '').split(',')
        add_all_pages(group2[0])
        for word1 in group1:
            add_all_pages(word1)

    with open('./data/wiki_dumps/change_to_whatever.pickle', "w") as myfile:
        pickle.dump(result_dump, myfile)


def generate_wiki_dump_from_dict(input, output):
    for key, values in input.iteritems():
        for words in values:
            add_all_pages(words)

    with open(output, "w") as myfile:
        pickle.dump(result_dump, myfile)


def add_all_pages(word):
    word = word.strip()
    add_page(word)
    add_page(word.lower())
    add_page(word.title())
    add_page(word.upper())


def add_page(word):
    try:
        if word not in result_dump:
            page = pywikibot.Page(site, word)
            pageid = page.pageid
            page_has_redirect = page.isRedirectPage()
            redirect = None
            aliases, description = get_aliases_and_description(page)
            word = unicode(word)
            text = page.text

            if page_has_redirect:
                red_page = page.getRedirectTarget()
                red_title = red_page.title.im_self._link.title
                red_aliases, ret_description = get_aliases_and_description(red_page)
                red_text = red_page.text
                redirect = Page(red_title, red_page.pageid, False, None, red_aliases, ret_description, red_text)
                if red_title not in result_dump:
                    result_dump[red_title] = redirect

            page = Page(word, pageid, page_has_redirect, redirect, aliases, description, text)
            result_dump[word] = page
            if page is not None:
                print 'adding page-' + page.to_string()
    except:
        print "could not extract wiki info from word-" + word


def get_aliases_and_description(page):
    """
    Returns page aliases
    :param page: wikidata mention page representation
    :return: Returns page aliases
    """
    aliases = None
    description = {}
    if page is not None:
        try:
            item = pywikibot.ItemPage.fromPage(page) # this can be used for any page object
            item_desc = item.get()  # need to call it to access any data.
            if 'en' in item.aliases:
                aliases = item.aliases['en']
            if 'en' in item_desc['descriptions']:
                dict([("age", 25)])
                description['descriptions'] = dict([('en', item_desc['descriptions']['en'])])
        except (pywikibot.NoPage, AttributeError, TypeError, NameError):
            pass

    return aliases, description


if __name__ == '__main__':
    args = docopt(__doc__)
    if len(args) != 2:
        print 'need provide input and output arguments'
        print printable_usage(__doc__)
        sys.exit()

    input = args['--input']
    output = args['--output']
    generate_wiki_dump_from_gs(input, output)

    print '--- Done Creating Dump Successfully! ---'
