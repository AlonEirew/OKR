"""
WIP to create base line for core reference mentions evaluation
Script is basically running the coreference script and save the result to a file,
later this file will be used to compare with progressive work to see regressions or progressions
"""

import os, sys

for pack in os.listdir("src"):
    sys.path.append(os.path.join("src", pack))

import eval_entity_coref
import coreference


def test_similar_word():
    word1 = 'IBM'
    word2 = 'international business machines'
    eval_entity_coref.similar_words(word1, word2)
    print eval_entity_coref.dup_dict[word1+word2].to_string()


def test_wiki():
    word1 = 'prime minister'
    word2 = 'pm'
    result = eval_entity_coref.wikidata_check(word1, word2)
    print result


if __name__ == '__main__':
    create_baseline()