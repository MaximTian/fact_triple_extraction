#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd
from pprint import pprint
from pyltp import Segmentor, Postagger

segmentor = Segmentor()
segmentor.load_with_lexicon("../ltp_data/cws.model", '../construct_dict.txt')
postagger = Postagger()
postagger.load("../ltp_data/pos.model")  # 词性标注


def is_valid(words, index, train_data):
    train_line = train_data[index]
    e1 = train_line[0]
    e2 = train_line[1]
    if e1 in words and e2 in words:
        return True
    else:
        return False


df = pd.read_csv("../data_process/train_data.csv")
output_data = open("../output.txt", 'r', encoding="utf-8")
test_data = open("../my_test.txt", 'w+', encoding="utf-8")

train_data = []
for index, row in df.iterrows():
    e1 = row['Entity1']
    e2 = row['Entity2']
    relation = row['Relation']
    train_data.append([e1, e2, relation])

triple_list = {}
for line in output_data:
    line_split = line.strip().split('\t')
    triple_type = line_split[0]
    if triple_type in ['主语谓语宾语关系', '定语后置动宾关系', '介宾关系主谓动补']:
        index = int(line_split[-1])
        triple = line_split[1][1:-1]
        words = segmentor.segment(triple)
        postags = postagger.postag(words)
        if is_valid(words, index, train_data):
            relation = train_data[index][2]
            if relation not in triple_list:
                triple_list[relation] = []
            triple_list[relation].append((triple, index))
            test_data.write(triple + " -> " + " ".join(train_data[index]) + "\n")

word_count = {}
for triple, index in triple_list['company/company/cooperate']:
    words = segmentor.segment(triple)
    postags = postagger.postag(words)

    e1 = train_data[index][0]
    e2 = train_data[index][1]
    for word_index, word in enumerate(words):
        postag = postags[word_index]
        if postag in ['v'] and word not in [e1, e2, '\xa0', '|']:
            if word not in word_count:
                word_count[word] = 0
            word_count[word] += 1

word_rank = sorted(word_count.items(), key=lambda item: item[1], reverse=True)
pprint(word_rank)
