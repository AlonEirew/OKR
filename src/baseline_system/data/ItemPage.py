class Item:
    def __init__(self, page):
        self.aliases = page.aliases

    @staticmethod
    def get():
        return


class ItemPage():
    def __init__(self):
        return

    @staticmethod
    def fromPage(page):
        return Item(page)
