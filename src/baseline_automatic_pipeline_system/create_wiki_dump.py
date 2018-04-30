"""
Creates Wiki dumps for a corpus input.
input: comma separated file (TBD-Need to add method to pull the mentions from GS format file)
output: pickled file that represent for each mention the wiki page presented by mention title
        page redirect (if exist) & aliases (if exist)

data is pickled to a file, examples can be found in data/wiki_dumps

Usage: create_wiki_dump --input=INPUT_FILE_PATH --output=OUTPUT_FILE_PATH

Usage example: create_wiki_dump --input=data/baseline/dev --output=data/wiki_dumps/dev.json

"""

import sys
import os
from phrases_similarity.create_wiki_dump import generate_wiki_dump_from_dict


for pack in os.listdir("src"):
    sys.path.append(os.path.join("src", pack))

from src.common.okr import load_graphs_from_folder, load_graph_from_file
from docopt import docopt, printable_usage


def generate_wiki_dump_from_gs(input, output):
    if os.path.isdir(input):
        gold_graphs = load_graphs_from_folder(input)
    else:  # single gold file
        gold_graphs = [load_graph_from_file(input)]

    dict_input = {}
    for gold_val in gold_graphs:
        for key, val in gold_val.ent_mentions_by_key.iteritems():
            if key not in dict_input:
                dict_input[key] = []
            dict_input[key].append(val.terms)

    generate_wiki_dump_from_dict(dict_input, output)


if __name__ == '__main__':
    args = docopt(__doc__)
    if len(args) != 2:
        print 'need provide input and output arguments'
        print printable_usage(__doc__)
        sys.exit()

    input = args['--input']
    output = args['--output']
    generate_wiki_dump_from_gs(input, output)

    print '--- Done Creating Dump Successfully! ---'
