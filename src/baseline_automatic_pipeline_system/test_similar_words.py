import pickle

import os, sys, json
import pywikibot

for pack in os.listdir("src"):
    sys.path.append(os.path.join("src", pack))

import eval_entity_coref
import coreference
from src.baseline_system.data.Page import Page

site = pywikibot.Site('en', 'wikipedia')

def test_similar_word_full():
    coreference.main()

    with open("test/out/EntityCoreRefResultBaseLine.txt", "a") as myfile:
        for key in eval_entity_coref.dup_dic:
            myfile.write(eval_entity_coref.dup_dic[key].to_string() + '\n')


def test_similar_word():
    word1 = 'IBM'
    word2 = 'international business machines'
    eval_entity_coref.similar_words(word1, word2)
    print eval_entity_coref.dup_dic[word1+word2].to_string()


def test_wiki():
    word1 = 'prime minister'
    word2 = 'pm'
    result = eval_entity_coref.wikidata_check(word1, word2)
    print result


def generate_wiki_dump():
    result_dump = {}

    with open("test/out/test_small.txt", "r") as myfile:
        file_lines = myfile.readlines()

    for line in file_lines:
        content = line.strip().split(',')
        word1 = content[0]
        word2 = content[1]

        if word1 not in result_dump:
            myPage1 = get_page(word1)
            result_dump[word1] = myPage1

        if word2 not in result_dump:
            myPage2 = get_page(word2)
            result_dump[word2] = myPage2

    with open("test/in/test_small.txt", "w") as myfile:
        pickle.dump(result_dump, myfile)

    with open("test/in/test_small.txt", "r") as pickleFile:
        result_from_pickle = pickle.load(pickleFile)
        print 'debug'


def get_page(word1):
    page1 = pywikibot.Page(site, word1)
    page1id = page1.pageid
    page1isredirect = page1.isRedirectPage()
    redirect1Title = None

    if page1isredirect:
        pageRed1 = page1.getRedirectTarget()
        redirect1Title = pageRed1.title.im_self._link.title

    page = Page(word1, page1id, page1isredirect, redirect1Title)
    return page


if __name__ == '__main__':
    generate_wiki_dump();