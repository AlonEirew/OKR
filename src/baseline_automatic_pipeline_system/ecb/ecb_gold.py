import os, sys, json

for pack in os.listdir("src"):
    sys.path.append(os.path.join("src", pack))

from src.baseline_system.eval_entity_coref import similar_words_result


def eval_sim_words_and_print(doc_mentions, cat):
    directory = "data/baseline/gs_test_coref/ecb/" + cat
    final_results = []
    for key, values in doc_mentions.iteritems():
        if not os.path.exists(directory):
            os.makedirs(directory)

        with open(directory + "/" + key + '_topic.csv', "w") as myfile:
            for ment_id1, value1 in values:
                value1 = value1.replace("'", "").replace('"', "").replace('\\', "")
                for ment_id2, value2 in values:
                    value2 = value2.replace("'", "").replace('"', "").replace('\\', "")
                    other = [ment_id1, value1]
                    mention = [ment_id2, value2]
                    sim_result = similar_words_result(other, mention)
                    if ment_id1 == ment_id2:
                        sim_result.expected = True
                    else:
                        sim_result.expected = False

                    myfile.write(sim_result.to_string() + '\n')
                    final_results.append(sim_result)

            print 'All ' + cat + ' in topic ' + key + ' metrics:'
            print_result(final_results)
            print
            del final_results[:]


def print_result(results_dict):
    fuzzy_pos = 0
    fuzzy_neg = 0
    syn_pos = 0
    syn_neg = 0
    partial_pos = 0
    partial_neg = 0
    wiki_pos = 0
    wiki_neg = 0
    total_expected_positive = 0
    positive = 0
    negative = 0

    for res in results_dict:
        if res.expected:
            total_expected_positive += 1
            if res.final_result():
                positive += 1
                if res.syn_result:
                    syn_pos += 1
                elif res.fuzzy_result:
                    fuzzy_pos += 1
                elif res.partial_result:
                    partial_pos += 1
                elif res.wikidata_result:
                    if res.word1.lower() != res.word2.lower():
                        print 'NA,[' + res.word1 + '],[' + res.word2 + '],Y'
                    wiki_pos += 1
        elif res.final_result():
            negative += 1
            if res.syn_result:
                syn_neg += 1
            elif res.fuzzy_result:
                fuzzy_neg += 1
            elif res.partial_result:
                partial_neg += 1
            elif res.wikidata_result:
                if res.word1.lower() != res.word2.lower():
                    print 'NA,[' + res.word1 + '],[' + res.word2 + '],N'
                wiki_neg += 1

    print('total pairs=' + str(len(results_dict)))
    print('total expected positive pairs=' + str(total_expected_positive))
    print('true positive values=' + str(positive))
    print('false positive values=' + str(negative))
    print('syn_pos=' + str(syn_pos) + ", fuzzy_pos=" + str(fuzzy_pos) + ', partial_pos=' + str(partial_pos) + ', wiki_pos=' + str(wiki_pos))
    print('syn_neg=' + str(syn_neg) + ", fuzzy_neg=" + str(fuzzy_neg) + ', partial_neg=' + str(partial_neg) + ', wiki_neg=' + str(wiki_neg))


if __name__ == '__main__':
    doc_entities = {}
    doc_events = {}
    with open('data/intel_gs/ecb_entities.json', "r") as entity_file:
        doc_entities = json.load(entity_file)

    with open('data/intel_gs/ecb_events.json', "r") as event_file:
        doc_events = json.load(event_file)

    eval_sim_words_and_print(doc_entities, 'entities')
    eval_sim_words_and_print(doc_events, 'events')

    print '--- Done Successfully! ---'
