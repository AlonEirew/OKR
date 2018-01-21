class Page:
    def __init__(self, word=None, pageid=0, is_redirect=False, redirect_page=None, aliases=None, description=None, text=None):
        self.title = word
        self.pageid = pageid
        self.is_redirect = is_redirect
        self.redirect_page = redirect_page
        self.aliases = aliases
        self.description = description
        self.text = text

    def isRedirectPage(self):
        return self.is_redirect

    def getRedirectTarget(self):
        return self.redirect_page

    def get(self):
        return

    def to_string(self):
        return str(self.title) + ', ' + str(self.pageid) + ', ' + str(self.is_redirect) + ', ' + \
              str(self.redirect_page) + ', ' + str(self.aliases) + ', ' + str(self.description)
