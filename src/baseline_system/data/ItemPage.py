class Item:
    def __init__(self, page):
        self.aliases = dict([('en', page.aliases)])
        self.description = page.description

    def get(self):
        return self.description


class ItemPage():
    def __init__(self):
        return

    @staticmethod
    def fromPage(page):
        return Item(page)
