import json

class Page:
    def __init__(self, word, id, is_redirect, redirect_title):
        self.title = word
        self.id = id
        self.is_redirect = is_redirect
        self.redirect_title = redirect_title

    def isRedirectPage(self):
        return

    def getRedirectTarget(self):
        return

    def get(self):
        return

    def default(self):
        return json.dump(self.__dict__)