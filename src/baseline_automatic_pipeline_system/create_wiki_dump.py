import pickle
import pywikibot

from src.baseline_system.data.Page import Page

site = pywikibot.Site('en', 'wikipedia')
result_dump = {}

def generate_wiki_dump():

    with open("test/out/WhitneyHeichelPairs.txt", "r") as myfile:
        file_lines = myfile.readlines()

    for line in file_lines:
        content = line.strip().split(',')
        word1 = content[0]
        word2 = content[1]

        if word1 not in result_dump:
            add_page(word1)

        if word2 not in result_dump:
            add_page(word2)

    with open("data/wiki_dumps/TestWikiDump.pickle", "w") as myfile:
        pickle.dump(result_dump, myfile)


def add_page(word):
    page = pywikibot.Page(site, word)
    pageid = page.pageid
    page_has_redirect = page.isRedirectPage()
    redirect = None
    aliases = ret_aliases(page, word)
    word = unicode(word)

    if page_has_redirect:
        red_page = page.getRedirectTarget()
        red_title = red_page.title.im_self._link.title
        red_aliases = ret_aliases(red_page, red_title)
        redirect = Page(red_title, red_page.pageid, False, None, red_aliases)
        if red_title not in result_dump:
            result_dump[red_title] = redirect

    page = Page(word, pageid, page_has_redirect, redirect, aliases)
    result_dump[word] = page


def ret_aliases(page, word):
    if page is not None:
        try:
            item = pywikibot.ItemPage.fromPage(page) # this can be used for any page object
            item.get()  # you need to call it to access any data.
            if 'en' in item.aliases:
                aliases = item.aliases['en']
                return aliases
        except (pywikibot.NoPage, AttributeError, TypeError, NameError):
            print "no page found for word: " + word

    return None


if __name__ == '__main__':
    # add_page("International Business Machines")
    generate_wiki_dump();
    print '--- Done Creating Dump Successfully! ---'
