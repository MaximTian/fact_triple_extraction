#!/usr/bin/env python
# -*- coding: utf-8 -*-


import pandas as pd
from pyltp import Segmentor, Postagger

segmentor = Segmentor()
segmentor.load_with_lexicon("../ltp_data/cws.model", '../construct_dict.txt')
postagger = Postagger()
postagger.load("../ltp_data/pos.model")  # 词性标注


df = pd.read_csv("../data_process/train_data.csv")
df = df[df['Relation'] != 'company/person/chairman']
output_data = open("../output.txt", encoding="utf-8")

train_data = []
for index, row in df.iterrows():
    e1 = row['Entity1']
    e2 = row['Entity2']
    relation = row['Relation']
    if relation != 'company/person/chairman':
        train_data.append([e1, e2, relation])


def is_valid(words, index, train_data):
    train_line = train_data[index]
    e1 = train_line[0]
    e2 = train_line[1]
    if e1 in words and e2 in words:
        return True
    else:
        return False


output_data = open("../output.txt", 'r', encoding="utf-8")
triple_list = {}
confirm_list = set([])

invest = 0
compete = 0
cooperate = 0
acquisition = 0


for line in output_data:
    line_split = line.strip().split('\t')
    triple_type = line_split[0]
    if triple_type in ['主语谓语宾语关系', '定语后置动宾关系', '介宾关系主谓动补']:
        index = int(line_split[-1])
        triple = line_split[1][1:-1]
        words = segmentor.segment(triple)
        if is_valid(words, index, train_data):
            relation = train_data[index][2]
            for word in words:
                if word in ['投资', '融资', '领投', '入股', '抛售']:
                    if relation == 'company/company/invest':
                        invest += 1
                        confirm_list.add(index)
                        break
                elif word in ['竞争', '超越', '超过', '击败', '对抗', '争夺', '竞购']:
                    if relation == 'company/company/compete':
                        confirm_list.add(index)
                        compete += 1
                        break
                elif word in ['合作', '达成', '联合', '联手', '互利', '牵手', '共享', '伙伴']:
                    if relation == 'company/company/cooperate':
                        confirm_list.add(index)
                        cooperate += 1
                        break
                elif word in ['收购', '并购', '控股', '掌控', '并入']:
                    if relation == 'company/company/acquisition':
                        confirm_list.add(index)
                        acquisition += 1
                        break


print("invest = %d, total = %d" % (invest, df[df['Relation'] == 'company/company/invest'].shape[0]))
print("compete = %d, total = %d" % (compete, df[df['Relation'] == 'company/company/compete'].shape[0]))
print("cooperate = %d, total = %d" % (cooperate, df[df['Relation'] == 'company/company/cooperate'].shape[0]))
print("acquisition = %d, total = %d" % (acquisition, df[df['Relation'] == 'company/company/acquisition'].shape[0]))
count = len(confirm_list) * 1.0
print(count)
print(count / df.shape[0])
