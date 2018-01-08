import pickle
import pywikibot

from os import listdir
from os.path import isfile, join

from Page import Page
from ItemPage import ItemPage


class PywikibotFactory:
    def __init__(self, connectivity):
        self.connectivity = connectivity
        if connectivity == "online":
            self.pywikibot = pywikibot
        else:
            self.pywikibot = PywikibotLocal("data/wiki_dumps")

    def get_site(self):
        if self.connectivity == "online":
            site = pywikibot.Site('en', 'wikipedia')  # The site we want to run our bot on
            return site
        return None


class PywikibotLocal:
    def __init__(self, wikidump):
        if not wikidump is None:
            self.dump = self.load_dump(wikidump)
            self.ItemPage = ItemPage()

    def Page(self, site=None, word=None):
        if not word is None:
            for ineer_dump in self.dump:
                if word in ineer_dump:
                    return ineer_dump[word]
        return Page(word)

    def load_dump(self, wiki_dump):
        onlyfiles = []
        for file in listdir(wiki_dump):
            file_path = join(wiki_dump, file)
            if isfile(file_path):
                onlyfiles.append(file_path)

        dump_list = []
        for file in onlyfiles:
            with open(file, "r") as dump:
                dump_list.append(pickle.load(dump))
        return dump_list

    class NoPage(StandardError):
        """ Attribute not found. """
        def __init__(self, *args, **kwargs): # real signature unknown
            pass

        @staticmethod # known case of __new__
        def __new__(S, *more): # real signature unknown; restored from __doc__
            """ T.__new__(S, ...) -> a new object with type S, a subtype of T """
            pass