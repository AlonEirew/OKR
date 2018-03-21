
"""
Evaluation for entity coreference resolution using gold entity mentions.
Run it from base OKR directory.

Usage: coreference --gold=GOLD_STANDARD

GOLD_STANDARD: can be a folder that contains the gold standard files (XML files) or a single gold file (in XML format)

Usage example: coreference --gold=data/baseline/test

"""

import os
import sys
from docopt import docopt
from os.path import basename

for pack in os.listdir("src"):
    sys.path.append(os.path.join("src", pack))

import clustering_common
import logging
from okr import *
import numpy as np
from eval_entity_coref import eval_clusters
from eval_entity_coref import extract_mentions
from eval_entity_coref import dup_dict
from parsers.spacy_wrapper import spacy_wrapper
from eval_predicate_coref import get_mention_head

#TODO create new algorithm for entity-coreference instead of relying on clustering_common baseline
def cluster_entity_mentions(mention_list):
    """
    currently using clustering_common.
    :param mention_list: the mentions to cluster
    :return: clusters of mentions
    """
    import eval_entity_coref
    return clustering_common.cluster_mentions(mention_list, eval_entity_coref.score)


def cluster_proposition_mentions(mention_list, entities_clustering):
    """
    Receives predicate mentions and entity clusters and perform predicate coreference resolution -
    cluster the predicate mentions in a greedy way: assign each predicate to the first
    cluster with similarity score > 0.5, the score is based on lexical similarity
    and arguments similarity between proposition mentions.
    :param mention_list: the mentions to cluster
    :param entities_clustering: a clustering of entity-mentions to coreference chains. 
        format: list of lists of tuples, each tuple stands for an entity-mention - (mention-id, terms)
    :return: clusters of mentions
    """
    argument_clusters = []
    for cluster in entities_clustering:
        ids_of_cluster = [mention_tuple[0] for mention_tuple in cluster]
        argument_clusters.append(ids_of_cluster)

    return greedy_prop_clustring(mention_list, predicate_score, argument_clusters, lexical_wt=0.75, argument_match_ratio=0.75)


def predicate_score(prop, cluster, argument_clusters, lexical_wt, argument_match_ratio):
    """
    Receives a proposition info (head_lemma, arguments, bare predicate, etc.)
    and a cluster of proposition mentions, and returns a numeric value denoting the
    similarity between the mention to the cluster (based on the lexical similarity and arguments similarity)
    :param prop: the mention
    :param cluster: the cluster
    :param argument_clusters: a clustering of entity-mentions to coreference chains.
    :param lexical_wt: the lexical weight for the scoring function which compares two proposition clusters.
     (the argument weight is 1- lexical_wt)
    :param argument_match_ratio: the minimum argument alignment threshold between propositions
    :return: a numeric value denoting the similarity between the mention to the cluster
    """

    from eval_predicate_coref import some_word_match
    implicit_mentions = 0.0

    # calculate lexical score for explicit predicates
    if prop[1] != 'IMPLICIT':
        prop_terms = prop[1]
        lexical_matches = 0.0
        for other_prop in cluster:
            if other_prop[1] != 'IMPLICIT':
                if some_word_match(other_prop[1], prop_terms):
                    lexical_matches += 1
            else:
                implicit_mentions += 1

        explicit_mentions = 1.0 * (len(cluster) - implicit_mentions)
        lexical_score = lexical_matches / explicit_mentions if explicit_mentions > 0 else 0.0

    else:
        lexical_score = 0
        lexical_wt = 0

    # calculate the ratio of proposition mentions in the cluster who has at
    # least argument_match_ratio percent of arguments corefer with the mention being compared.
    argument_score = len([other for other in cluster if
                            (some_arg_match(other[2], prop[2], argument_clusters, argument_match_ratio))]) / (
                        1.0 * len(cluster))

    return lexical_wt * lexical_score + (1 - lexical_wt) * argument_score


def greedy_prop_clustring(mention_list, score, argument_clusters, lexical_wt, argument_match_ratio):
    """
    Cluster the predicate mentions in a greedy way: assign each predicate to the first
    cluster with similarity score > 0.5. If no such cluster exists, start a new one.
    :param mention_list: the mentions to clustert
    :param score: the score function that receives a mention and a cluster and returns a score
    :param argument_clusters: a clustering of entity-mentions to coreference chains.
    :param lexical_wt: the lexical weight for the scoring function which compares two proposition clusters.
     (the argument weight is 1- lexical_wt)
    :param argument_match_ratio: the minimum argument alignment threshold between propositions
    :return: clusters of mentions
    """
    clusters = []

    for mention in mention_list:
        found_cluster = False
        for cluster in clusters:
            cluster_mention_score = score(mention, cluster, argument_clusters, lexical_wt, argument_match_ratio)
            if cluster_mention_score > 0.5:
                cluster.append(mention)
                found_cluster = True
                break

        if not found_cluster:
            clusters.append([mention])

    return clusters


def some_arg_match(prop_mention1_info, prop_mention2_info, argument_clusters, arg_match_ratio):
    """
    Finds if at least some % of arguments of two propositions are coreferent.
    :param prop_mention1_info: First proposition mention
    :param prop_mention2_info: Second proposition mention
    :param argument_clusters: The clusters of arguments obtained by coreference
    :param arg_match_ratio: criteria of argument overlap = number of aligned arguments / number of arguments(minimum of proposition1 and proposition2)
    :return: True if at least arg_match_ratio of arguments of two propositions are coreferent.
    """

    matched_arguments = 0.0
    prop_mention1_args = [arg_data['sentence_id'] +'_' + arg_key for arg_key,arg_data in
                          prop_mention1_info['Arguments'].iteritems()]

    prop_mention2_args = [arg_data['sentence_id'] +'_' + arg_key for arg_key,arg_data in
                          prop_mention2_info['Arguments'].iteritems() ]

    for m_id1 in prop_mention1_args:
        pair_found = False
        for m_id2 in prop_mention2_args:
            for cluster in argument_clusters:
                if m_id1 in cluster and m_id2 in cluster:
                    matched_arguments += 1
                    pair_found = True
                    break
            if pair_found == True:
                break

    if matched_arguments == 0:
        return False
    elif len(prop_mention1_args) + len(prop_mention2_args) - matched_arguments == 0:
        logging.error('problem here:')
        logging.error('Matched arguments: ' + str(matched_arguments))
        logging.error('Number of arguments in the two propositions: {0}, {1}'.format( str(len(prop_mention1_args)), str(len(prop_mention2_args))))

        return False

    else:
        return (matched_arguments / (len(prop_mention1_args) + len(
            prop_mention2_args) - matched_arguments) >= arg_match_ratio)


def eval_entity_coref_with_gold_graph(gold_graph):
    """
    Evaluating entity coreference with gold mentions, against gold clusters.
    :param gold_graph: OKR object
    :return: MUC, B^3, CEAF_C, MELA
    """
    entity_mentions_for_clustering = [(str(mention), unicode(mention.terms)) for entity in gold_graph.entities.values()
                                      for mention in
                                      entity.mentions.values()]
    entity_clusters = cluster_entity_mentions(entity_mentions_for_clustering)
    entity_clusters_for_eval = [set([item[0] for item in cluster]) for cluster in entity_clusters]

    graph1_ent_mentions, graph2_ent_mentions = extract_mentions(entity_clusters_for_eval, gold_graph)
    curr_entity_scores = eval_clusters(graph1_ent_mentions, graph2_ent_mentions)

    # create base line GS file
    create_gs_test_result(graph2_ent_mentions)

    return curr_entity_scores


def create_gs_test_result(gold_graph):
    """
   Add the expected value (as taken from GS file) to dup_dict result pairs, this information will be then
   dumped to a file representing the Baseline for regression/progression purposes
   :param gold_graph: OKR object
   """
    for value in dup_dict.itervalues():
        for cluster_set in gold_graph:
            if set([value.word1_id, value.word2_id]).issubset(cluster_set):
                value.expected = True
                break
        if not value.expected:
            value.expected = False


def main():
    args = docopt(__doc__)
    gold_path = args["--gold"]
    # checking whether the input is a folder or a single file
    if os.path.isdir(gold_path):
        gold_graphs = load_graphs_from_folder(gold_path)
    else:  # single gold file
        gold_graphs = [load_graph_from_file(gold_path)]
    # evaluate on each file
    entity_coref_scores = []
    for gold_graph in gold_graphs:
        entity_coref_scores.append(eval_entity_coref_with_gold_graph(gold_graph))
    # compute mean of scores above files
    entity_coref_scores = np.mean(entity_coref_scores, axis=0).tolist()
    # report
    entity_muc, entity_b_cube, entity_ceaf_c, entity_mela = entity_coref_scores
    print 'Entity coreference: MUC=%.3f, B^3=%.3f, CEAF_C=%.3f, MELA=%.3f' % \
          (entity_muc, entity_b_cube, entity_ceaf_c, entity_mela)

    file_name = basename(gold_path)
    file_name = os.path.splitext(file_name)[0]
    # input is a directory
    if not file_name:
        file_name = os.path.basename(os.path.normpath(gold_path)) + "_folder"
    with open("data/baseline/gs_test_coref/" + file_name + ".csv", "w") as myfile:
        for key in dup_dict:
            myfile.write(dup_dict[key].to_string() + '\n')
            if dup_dict[key].wikidata_result and not dup_dict[key].expected and dup_dict[key].word1 != dup_dict[key].word2:
                print 'NA,[' + dup_dict[key].word1 + '],[' + dup_dict[key].word2 + '],N'


if __name__ == '__main__':
    main()