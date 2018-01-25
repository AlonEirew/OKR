"""
Receives a test set and evaluates performance of entity coreference.
We cluster the entity mentions based on simple lexical similarity metrics (e.g., lemma matching and
Levenshtein distance)

Author: Rachel Wities
"""

import sys

sys.path.append('../common')
sys.path.append('../agreement')

import spacy
import re
import numpy as np

from okr import *
from munkres import *
from entity_coref import *
from fuzzywuzzy import fuzz
from spacy.lang.en import English
from num2words import num2words
from nltk.corpus import wordnet as wn
from clustering_common import cluster_mentions,cluster_mentions_with_max_cluster
from data.result_object import ResultObject
from data.pywikibot_factoy import PywikibotFactory

# Create an instance of the pywikibot (API to query wikipedia)
# will run by default offline, in case needed to be run online (meaning HTTP calls to wikipedia) just
# pass "online" as input ie- PywikibotFactory("online")
pywikibot_factory = PywikibotFactory("offline")
site = pywikibot_factory.get_site()
pywikibot = pywikibot_factory.pywikibot

# dictionary to save the pairs evaluation (used for skipping mulipule test of same pairs & for testing)
dup_dict = {}

# Don't use spacy tokenizer, because we originally used NLTK to tokenize the files and they are already tokenized
nlp = English()


def is_stop(w):
    return w in spacy.lang.en.STOP_WORDS


def replace_tokenizer(nlp):
    old_tokenizer = nlp.tokenizer
    nlp.tokenizer = lambda string: old_tokenizer.tokens_from_list(string.split())

replace_tokenizer(nlp)


def evaluate_entity_coref(test_graphs):
    """
    Receives the OKR test graphs and evaluates them for entity coreference
    :param test_graphs: the OKR test graphs
    :return: the coreference scores: MUC, B-CUBED, CEAF and MELA (CoNLL F1).
    """
    scores = []

    for graph in test_graphs:

        # Cluster the entities
        entities = [(str(mention), unicode(mention.terms)) for entity in graph.entities.values() for mention in
                    entity.mentions.values()]
        clusters = cluster_mentions(entities, score)
        clusters = [set([item[0] for item in cluster]) for cluster in clusters]

        # Evaluate
        graph_ent_mentions, gold_ent_mentions = extract_mentions(clusters, graph)
        curr_scores = eval_clusters(graph_ent_mentions, gold_ent_mentions)
        scores.append(curr_scores)

    scores = np.mean(scores, axis=0).tolist()

    return scores


def eval_entity_coref_between_two_graphs(predicted_graph,gold_graph):
    """
    Receives a predicted graph (after the automatic pipeline) and a gold graph and
    prepare the predicted graph for the evaluation
    :param predicted_graph: Auto-created graph
    :param gold_graph: the gold standard graph
    :return: the entity coreference metrics
    """
    predicted_clusters = [set(map(str, entity.mentions.values())) for entity in predicted_graph.entities.values()]
    graph_ent_mentions, gold_ent_mentions = extract_mentions(predicted_clusters, gold_graph)
    return eval_clusters(graph_ent_mentions, gold_ent_mentions)


def eval_clusters(graph_ent_mentions, gold_ent_mentions):
    """
    Receives the predicted clusters and the gold standard graph and evaluates (with coref metrics) the entity
    coreferences
    :param clusters: the predicted clusters
    :param graph: the gold standard graph
    :return: the predicate coreference metrics and the number of singletons
    """
    # Evaluate
    muc1, bcubed1, ceaf1 = muc(graph_ent_mentions, gold_ent_mentions), \
                           bcubed(graph_ent_mentions, gold_ent_mentions), \
                           ceaf(graph_ent_mentions, gold_ent_mentions)

    mela1 = np.mean([muc1, bcubed1, ceaf1])
    return np.array([muc1, bcubed1, ceaf1, mela1])


def extract_mentions(clusters, graph):
    graph_ent_mentions = clusters
    gold_ent_mentions = [set(map(str, entity.mentions.values())) for entity in graph.entities.values()]
    return graph_ent_mentions, gold_ent_mentions


def score(mention, cluster):
    """
    Receives an entity mention (mention, head_lemma, head_pos)
    and a cluster of entity mentions, and returns a numeric value denoting the
    similarity between the mention to the cluster (% of similar head lemma mentions in the cluster)
    :param mention: the mention
    :param cluster: the cluster
    :return: a numeric value denoting the similarity between the mention to the cluster
    """
    return len([other for other in cluster if similar_words(other, mention)]) / (1.0 * len(cluster))


def similar_words(other, mention):
    """
    Returns whether x and y are similar
    :param other: the first mention
    :param mention: the second mention
    :return: whether x and y are similar
    """
    x = other[1]
    x_id = other[0]
    y_id = mention[0]
    y = mention[1]
    key_list = [x, y]
    sorted(key_list)
    dictionary_key = ''.join(key_list)
    if dictionary_key not in dup_dict:
        syn_result = same_synset(x, y)
        fuzzy_result = False;
        partial_result = False;
        wikidata_result = False;
        if not syn_result:
            fuzzy_result = fuzzy_fit(x, y)
            if not fuzzy_result:
                partial_result = partial_match(x,y)
                if not partial_result:
                    wikidata_result = wikidata_check(x,y)

        result = ResultObject(
            x_id,
            x,
            y_id,
            y,
            syn_result,
            fuzzy_result,
            partial_result,
            wikidata_result,
            None)

        dup_dict[dictionary_key] = result
        return result.final_result()

    return dup_dict[dictionary_key].final_result()


def same_synset(x, y):
    """
    Returns whether x and y share a WordNet synset
    :param x: the first mention
    :param y: the second mention
    :return: whether x and y share a WordNet synset
    """
    x_synonyms = set([lemma.lower().replace('_', ' ') for synset in wn.synsets(x) for lemma in synset.lemma_names()])
    y_synonyms = set([lemma.lower().replace('_', ' ') for synset in wn.synsets(y) for lemma in synset.lemma_names()])

    return len([w for w in x_synonyms.intersection(y_synonyms) if not is_stop(w)]) > 0


def fuzzy_fit(x, y):
    """
    Returns whether x and y are similar in fuzzy string matching
    :param x: the first mention
    :param y: the second mention
    :return: whether x and y are similar in fuzzy string matching
    """
    if fuzz.ratio(x, y) >= 90:
        return True

    # Convert numbers to words
    x_words = [num2words(int(w)).replace('-', ' ') if w.isdigit() else w for w in x.split()]
    y_words = [num2words(int(w)).replace('-', ' ') if w.isdigit() else w for w in y.split()]

    return fuzz.ratio(' '.join(x_words), ' '.join(y_words)) >= 85


def partial_match(x, y):
    """
    Return whether these two mentions have a partial match in WordNet synset.
    :param x: the first mention
    :param y: the second mention
    :return: Whether they are aligned
    """

    # Allow partial matching
    if fuzz.partial_ratio(' ' + x + ' ', ' ' + y + ' ') == 100:
        return True

    x_words = [w for w in x.split() if not is_stop(w)]
    y_words = [w for w in y.split() if not is_stop(w)]

    if len(x_words) == 0 or len(y_words) == 0:
        return False

    x_synonyms = [set([lemma.lower().replace('_', ' ') for synset in wn.synsets(w) for lemma in synset.lemma_names()])
                  for w in x_words]
    y_synonyms = [set([lemma.lower().replace('_', ' ') for synset in wn.synsets(w) for lemma in synset.lemma_names()])
                  for w in y_words]

    # One word - check whether there is intersection between synsets
    if len(x_synonyms) == 1 and len(y_synonyms) == 1 and \
                    len([w for w in x_synonyms[0].intersection(y_synonyms[0]) if not is_stop(w)]) > 0:
        return True

    # More than one word - align words from x with words from y
    cost = -np.vstack([np.array([len([w for w in s1.intersection(s2) if not is_stop(w)]) for s1 in x_synonyms])
                       for s2 in y_synonyms])
    m = Munkres()
    cost = pad_to_square(cost)
    indices = m.compute(cost)

    # Compute the average score of the alignment
    average_score = np.mean([-cost[row, col] for row, col in indices])

    if average_score >= 0.75:
        return True

    return False


def wikidata_check(word1, word2):
    """
    Returns whether word1 and word1 share a wikidata redirect page or one is alias of the other
    :param word1: first mention
    :param word2: second mention
    :return: True if word1 and word2 share a wikidata redirect page or one is alias of the other, False otherwise
    """
    # print "wikidata compare " + word1 + " to " + word2
    page1 = get_word_page_by_casing(word1)
    page2 = get_word_page_by_casing(word2)

    pageRed1 = page1
    pageRed2 = page2

    if pageRed1.isRedirectPage():
        pageRed1 = page1.getRedirectTarget()
    if pageRed2.isRedirectPage():
        pageRed2 = page2.getRedirectTarget()

    if pageRed1.pageid > 0 and pageRed2.pageid > 0:
        if pageRed1.pageid == pageRed2.pageid:
            return True

    item1 = get_page_item(pageRed1)
    item2 = get_page_item(pageRed2)

    if wikidata_aliases(item1, word1, item2, word2):
        return True

    is1_disambiguate = is_disambiguate(item1)
    is2_disambiguate = is_disambiguate(item2)

    if is1_disambiguate and not is2_disambiguate:
        is_in_categories1 = is_disambiguate_categories(pageRed1.text, word2.lower())
        if is_in_categories1:
            return True
    elif not is1_disambiguate and is2_disambiguate:
        is_in_categories2 = is_disambiguate_categories(pageRed2.text, word1.lower())
        if is_in_categories2:
            return True

    return False


def get_word_page_by_casing(word):
    word = word.replace('-', ' ')
    page = pywikibot.Page(site, word)
    if page.pageid == 0:
        word = word.title()
        page = pywikibot.Page(site, word)
        if page.pageid == 0:
            word = word.upper()
            page = pywikibot.Page(site, word)
    return page


def is_disambiguate_categories(text, word):
    text_lines = text.split('\n')
    categories = []
    for line in text_lines:
        category = re.findall('\[\[([\w\s\-]+)\]\]', line)
        for cat in category:
            categories.append(cat)
            if cat.lower().replace('-', ' ') == word:
                return True

    return False


def is_disambiguate(item):
    if item is not None:
        dic = item.get()
        if dic is not None and 'descriptions' in dic:
            desc = dic['descriptions']
            if desc is not None and 'en' in desc:
                return True if desc['en'].lower() == 'wikimedia disambiguation page' else False

    return False


def get_page_item(page):
    if page is not None:
        try:
            item = pywikibot.ItemPage.fromPage(page) # this can be used for any page object
            item.get()  # need to call it to access any data.
            return item
        except (pywikibot.NoPage, AttributeError, TypeError, NameError):
            pass

    return None


def wikidata_aliases(item1, word1, item2, word2):
    """
    Returns whether word1 and word2 aliases of each other
    :param page1: first wikidata mention page representation
    :param word1: first mention
    :param page2: second wikidata mention page representation
    :param word2: second mention
    :return: whether word1 and word2 aliases of each other
    """
    if item1 is not None and item2 is not None:
        aliases1 = get_aliases(item1)
        if is_in_list(word2, aliases1):
            return True
        else:
            aliases2 = get_aliases(item2)
            if is_in_list(word1, aliases2):
                return True

    return False


def is_in_list(word, aliases):
    """
    Check's if word is in aliases list
    :param word: mention to check
    :param aliases: other mention aliases list
    :return: Returns True if word exist in aliases, False otherwise
    """
    if aliases is not None:
        worduni = unicode(word).lower()
        if worduni in (alias.lower() for alias in aliases):
            return True
    return False


def get_aliases(item):
    """
    Returns page aliases
    :param page: wikidata mention page representation
    :return: Returns page aliases
    """
    if 'en' in item.aliases:
        aliases = item.aliases['en']
        return aliases

    return None
