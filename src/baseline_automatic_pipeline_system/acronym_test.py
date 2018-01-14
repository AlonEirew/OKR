import os, sys
import pandas as pd

for pack in os.listdir("src"):
    sys.path.append(os.path.join("src", pack))

from src.baseline_system.eval_entity_coref import wikidata_check
from src.baseline_system.data.result_object import ResultObject


def main():
    dataframes = pd.read_csv("./data/intel_gs/Acronym_all_news.csv")
    result_objs = []
    for index, row in dataframes.iterrows():
        group1 = row[1].replace('[', '').replace(']', '').split(',')
        group2 = row[2].replace('[', '').replace(']', '').split(',')
        if row[3] == 'Y':
            expected = True
        else:
            expected = False

        if len(group2) != 1:
            print group1

        for word1 in group1:
            wiki_result = wikidata_check(word1, group2[0])
            result_objs.append(ResultObject(word1, group2[0], wiki_result, expected))

    with open("./data/intel_gs/result.csv", 'w') as acronyms_out:
        for result in result_objs:
            acronyms_out.write(result.to_string() + '\n')


if __name__ == '__main__':
    main()