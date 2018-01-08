import os, sys, json


for pack in os.listdir("src"):
    sys.path.append(os.path.join("src", pack))

import eval_entity_coref
import coreference


def test_similar_word_full():
    coreference.main()

    with open("test/out/EntityCoreRefResultBaseLine.txt", "w") as myfile:
        for key in eval_entity_coref.dup_dic:
            myfile.write(eval_entity_coref.dup_dic[key].to_string() + '\n')


def test_similar_word():
    word1 = 'IBM'
    word2 = 'international business machines'
    eval_entity_coref.similar_words(word1, word2)
    print eval_entity_coref.dup_dic[word1+word2].to_string()


def test_wiki():
    word1 = 'prime minister'
    word2 = 'pm'
    result = eval_entity_coref.wikidata_check(word1, word2)
    print result


if __name__ == '__main__':
    test_similar_word_full()