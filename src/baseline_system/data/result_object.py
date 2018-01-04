class ResultObject:
    def __init__(self, word1, word2, syn_result, fuzzy_result, partial_result, wikidata_result):
        self.word1 = word1
        self.word2 = word2
        self.syn_result = syn_result
        self.fuzzy_result = fuzzy_result
        self.partial_result = partial_result
        self.wikidata_result = wikidata_result

    def final_result(self):
        return self.syn_result or self.fuzzy_result or self.partial_result or self.wikidata_result

    def to_string(self):
        return self.word1 + ',' + self.word2 + ',' + str(
            self.syn_result) + ',' + str(self.fuzzy_result) + ',' + str(
            self.partial_result) + ',' + str(self.wikidata_result)
