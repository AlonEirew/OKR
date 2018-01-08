import json

class Page:
    def __init__(self, word=None, pageid=0, is_redirect=False, redirect_page=None, aliases=None):
        self.title = word
        self.pageid = pageid
        self.is_redirect = is_redirect
        self.redirect_page = redirect_page
        self.aliases = aliases

    def isRedirectPage(self):
        return self.is_redirect

    def getRedirectTarget(self):
        return self.redirect_page

    def get(self):
        return