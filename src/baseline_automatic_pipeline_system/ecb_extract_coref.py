import os, sys
import xml.etree.ElementTree as ElementTree

for pack in os.listdir("src"):
    sys.path.append(os.path.join("src", pack))

from eval_entity_coref import similar_words_result


def extract():
    coref_list = {}
    file_to_ids = {}
    for subdir, dirs, files in os.walk('data/ecb/xml'):
        print(subdir)
        for file in files:
            if file.endswith('xml'):
                file_key = extract_file_id(file)
                if file_key not in file_to_ids:
                    file_to_ids[file_key] = set()

                file_name = os.path.join(subdir, file)
                ecb_file = open(file_name, 'r')
                tree = ElementTree.parse(ecb_file)
                root = tree.getroot()

                cross_doc_ids = extract_cross_doc_ids(root)
                m_id_tokens = extract_m_id_tokens(root)
                extracted_tokens = extract_text_tokens(root)

                file_to_ids[file_key].update(cross_doc_ids.keys())
                create_final_result(cross_doc_ids, m_id_tokens, extracted_tokens, coref_list)

        if len(file_to_ids) >= 1:
            break

    evaluate_ecb(coref_list, file_to_ids)


def extract_file_id(in_file):
    file_key_spt = os.path.splitext(in_file)[0].split('_')
    if file_key_spt[1].endswith('ecb'):
        file_key = file_key_spt[0] + '_ecb'
    else:
        file_key = file_key_spt[0] + '_ecbplus'
    return file_key


def evaluate_ecb(coref_list, file_to_ids):
    doc_entities = {}
    doc_events = {}
    for key, ment_ids in file_to_ids.iteritems():
        doc_entities[key] = []
        doc_events[key] = []
        for ment_id in ment_ids:
            words = coref_list[ment_id]
            if ment_id.startswith('ACT') or ment_id.startswith('NEG'):
                for word in words:
                    doc_events[key].append((ment_id, word))
            else:
                for word in words:
                    doc_entities[key].append((ment_id, word))

    ent_results = eval_sim_words_and_print(doc_entities, 'entities')
    event_results = eval_sim_words_and_print(doc_events, 'events')

    print 'All Topics Entities Metrics:'
    print_result(ent_results)
    print
    print 'All Topics Events Metrics:'
    print_result(event_results)


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

    return final_results


def print_result(results_dict):
    fuzzy_pos = 0
    fuzzy_neg = 0
    syn_pos = 0
    syn_neg = 0
    partial_pos = 0
    partial_neg = 0
    wiki_pos = 0
    wiki_neg = 0
    positive = 0
    negative = 0

    for res in results_dict:
        if res.final_result() and res.word1_id == res.word2_id:
            positive += 1
            if res.syn_result:
                syn_pos += 1
            elif res.fuzzy_result:
                fuzzy_pos += 1
            elif res.partial_result:
                partial_pos += 1
            elif res.wikidata_result:
                wiki_pos += 1
        elif res.final_result() and res.word1_id != res.word2_id:
            negative += 1
            if res.syn_result:
                syn_neg += 1
            elif res.fuzzy_result:
                fuzzy_neg += 1
            elif res.partial_result:
                partial_neg += 1
            elif res.wikidata_result:
                wiki_neg += 1

    print('total pairs=' + str(len(results_dict)))
    print('true positive values=' + str(positive))
    print('false positive values=' + str(negative))
    print('syn_pos=' + str(syn_pos) + ", fuzzy_pos=" + str(fuzzy_pos) + ', partial_pos=' + str(partial_pos) + ', wiki_pos=' + str(wiki_pos))
    print('syn_neg=' + str(syn_neg) + ", fuzzy_neg=" + str(fuzzy_neg) + ', partial_neg=' + str(partial_neg) + ', wiki_neg=' + str(wiki_neg))


def create_final_result(cross_doc_ids, m_id_tokens, extracted_tokens, coref_list):
    for key, value in cross_doc_ids.iteritems():
        if key not in coref_list:
            coref_list[key] = set()
        for m_id in value:
            text = ''
            tokens = m_id_tokens[m_id[0]]
            for t_id in tokens:
                text += extracted_tokens[t_id] + ' '

            if text not in coref_list[key]:
                coref_list[key].add(text.strip())

    return coref_list


def extract_text_tokens(root):
    tokens_ids = {}
    for token in root.findall('token'):
        token_id = token.attrib['t_id']
        token_text = token.text.encode('ascii', 'ignore')
        tokens_ids[token_id] = token_text

    return tokens_ids


def extract_m_id_tokens(root):
    m_ids_tokens = {}
    m_ids_tokens.fromkeys([])
    for action in root.find('Markables').iter():
        if action.tag == 'Markables':
            continue
        elif 'm_id' in action.attrib:
            cur_mid = action.attrib['m_id']
            words_t_ids = []
            for token in action.findall('token_anchor'):
                words_t_ids.append(token.attrib['t_id'])

            if len(words_t_ids) > 0:
                m_ids_tokens[cur_mid] = words_t_ids

    return m_ids_tokens


def extract_cross_doc_ids(root):
    cross_doc_ids = {}
    cross_doc_ids.fromkeys([])
    for cross_doc_coref in root.find('Relations').findall('CROSS_DOC_COREF'):
        cur_instance_id = ''
        id_list = []
        for child in cross_doc_coref.iter():
            if child.tag == 'CROSS_DOC_COREF':
                cur_instance_id = child.attrib['note']
            else:
                if child.tag == 'source':
                    id_list.append([child.attrib['m_id']])

        cross_doc_ids[cur_instance_id] = id_list

    return cross_doc_ids


if __name__ == '__main__':
    extract()
