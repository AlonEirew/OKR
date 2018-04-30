import os, sys, json
import xml.etree.ElementTree as ElementTree


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

        # if len(file_to_ids) >= 1:
        #     break

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

    extract_ecb_to_file(doc_entities, doc_events)


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


def extract_ecb_to_file(doc_entities, doc_events):
    with open('data/intel_gs/ecb_entities.json', "w+") as myfile:
        json.dump(doc_entities, myfile)

    with open('data/intel_gs/ecb_events.json', "w+") as myfile:
        json.dump(doc_events, myfile)


if __name__ == '__main__':
    extract()
    print '--- Done Creating Dump Successfully! ---'
