from entity_matching.obj.similarity_type import SimilarityType


class ResultObject:

    def __init__(self, word1_id, word1, word2_id, word2, syn_result, fuzzy_result, partial_result, wikidata_result, expected=None):
        self.word1_id = word1_id
        self.word1 = word1
        self.word2 = word2
        self.word2_id = word2_id
        self.syn_result = syn_result
        self.fuzzy_result = fuzzy_result
        self.partial_result = partial_result
        if wikidata_result != SimilarityType.NOT_SIMILAR:
            self.wikidata_result = True
        else:
            self.wikidata_result = False
        self.expected = expected

    def final_result(self):
        return self.syn_result or self.fuzzy_result or self.partial_result or self.wikidata_result

    def to_string(self):
        # replace comma so result file can be loaded in csv format
        word_ids = self.word1_id + ':' + self.word2_id
        word_rep1 = self.word1.replace(',', '.')
        word_rep2 = self.word2.replace(',', '.')
        return word_ids + ',' + word_rep1 + ',' + word_rep2 + ',' + str(
            self.syn_result) + ',' + str(self.fuzzy_result) + ',' + str(
            self.partial_result) + ',' + str(self.wikidata_result) + "," + str(self.expected)
