"""
Receives a test set and evaluates performance of entity coreference.
We cluster the entity mentions based on simple lexical similarity metrics (e.g., lemma matching and
Levenshtein distance)

Author: Rachel Wities
"""

import sys

from src.baseline_system.data.pywikibot_factoy import PywikibotFactory

sys.path.append('../common')
sys.path.append('../agreement')

import spacy
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

pywikibot_factory = PywikibotFactory("offline")
site = pywikibot_factory.get_site()
pywikibot = pywikibot_factory.pywikibot

dup_dic = {}

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
        curr_scores = eval_clusters(clusters, graph)
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
    return eval_clusters(predicted_clusters, gold_graph)


def eval_clusters(clusters, graph):
    """
    Receives the predicted clusters and the gold standard graph and evaluates (with coref metrics) the entity
    coreferences
    :param clusters: the predicted clusters
    :param graph: the gold standard graph
    :return: the predicate coreference metrics and the number of singletons
    """
    graph1_ent_mentions = [set(map(str, entity.mentions.values())) for entity in graph.entities.values()]
    graph2_ent_mentions = clusters

    # Evaluate
    muc1, bcubed1, ceaf1 = muc(graph1_ent_mentions, graph2_ent_mentions), \
                           bcubed(graph1_ent_mentions, graph2_ent_mentions), \
                           ceaf(graph1_ent_mentions, graph2_ent_mentions)

    mela1 = np.mean([muc1, bcubed1, ceaf1])
    return np.array([muc1, bcubed1, ceaf1, mela1])


def score(mention, cluster):
    """
    Receives an entity mention (mention, head_lemma, head_pos)
    and a cluster of entity mentions, and returns a numeric value denoting the
    similarity between the mention to the cluster (% of similar head lemma mentions in the cluster)
    :param mention: the mention
    :param cluster: the cluster
    :return: a numeric value denoting the similarity between the mention to the cluster
    """
    return len([other for other in cluster if similar_words(other[1], mention[1])]) / (1.0 * len(cluster))


def similar_words(x, y):
    """
    Returns whether x and y are similar
    :param x: the first mention
    :param y: the second mention
    :return: whether x and y are similar
    """
    if x + y not in dup_dic and y + x not in dup_dic:
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

        result = ResultObject(x,y,syn_result, fuzzy_result, partial_result, wikidata_result)

        dup_dic[x+y] = result
        return result.final_result()

    if x+y in dup_dic:
        return dup_dic[x+y].final_result()

    return dup_dic[y+x].final_result()


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
    print "wikidata compare " + word1 + " to " + word2
    page1 = pywikibot.Page(site, word1)
    page2 = pywikibot.Page(site, word2)

    pageRed1 = page1
    pageRed2 = page2

    if pageRed1.isRedirectPage():
        pageRed1 = page1.getRedirectTarget()
    if pageRed2.isRedirectPage():
        pageRed2 = page2.getRedirectTarget()

    if pageRed1.pageid > 0 and pageRed2.pageid > 0:
        if pageRed1.pageid == pageRed2.pageid:
            return True

    return wikidata_aliases(page1, word1, page2, word2)


def wikidata_aliases(page1, word1, page2, word2):
    aliases1 = ret_aliases(page1, word1)
    if is_in_list(word2, aliases1):
        return True
    else:
        aliases2 = ret_aliases(page2, word2)
        if is_in_list(word1, aliases2):
            return True

    return False


def is_in_list(word, aliases):
    if aliases is not None:
        worduni = unicode(word).lower()
        if worduni in (alias.lower() for alias in aliases):
            return True
    return False


def ret_aliases(page, word):
    if page is not None:
        try:
            item = pywikibot.ItemPage.fromPage(page) # this can be used for any page object
            item.get()  # need to call it to access any data.
            if 'en' in item.aliases:
                aliases = item.aliases['en']
                return aliases
        except (pywikibot.NoPage, AttributeError, TypeError, NameError):
            print "no aliases found for word: " + word

    return None