import os, json
from phrases_similarity.create_wiki_dump import generate_wiki_dump_from_dict

from src.common.okr import load_graphs_from_folder, load_graph_from_file


def generate_wiki_dump_from_gs(doc_entities, doc_events, output):
    dict_input = {}
    for key, values in doc_entities.iteritems():
        for ment_id1, value1 in values:
            value1 = value1.replace("'", "").replace('"', "").replace('\\', "")
            if ment_id1 not in dict_input:
                dict_input[ment_id1] = []
            dict_input[ment_id1].append(value1)

    for key, values in doc_events.iteritems():
        for ment_id1, value1 in values:
            value1 = value1.replace("'", "").replace('"', "").replace('\\', "")
            if ment_id1 not in dict_input:
                dict_input[ment_id1] = []
            dict_input[ment_id1].append(value1);

    generate_wiki_dump_from_dict(dict_input, output)


if __name__ == '__main__':
    doc_entities = {}
    doc_events = {}
    with open('data/intel_gs/ecb_entities.json', "r") as entity_file:
        doc_entities = json.load(entity_file)

    with open('data/intel_gs/ecb_events.json', "r") as event_file:
        doc_events = json.load(event_file)

    generate_wiki_dump_from_gs(doc_entities, doc_events, 'data/wikidumps/ecb_full_dump.json')

    print '--- Done Creating Dump Successfully! ---'
