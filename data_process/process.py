#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split


def split_data():
    data = pd.read_csv("./news.csv")
    data = data.dropna(axis=[0, 1], how='all')

    print(set(data['Relation']))

    train, test = train_test_split(data, test_size=0.2, random_state=123)
    train = train.sort_values(by=['Relation'], ascending='False')
    train.to_csv("train.csv", encoding="utf-8", index=None)
    test.to_csv("test.csv", encoding="utf-8", index=None)


def select_data():
    data = pd.read_csv("./train_data.csv")
    f = open('sample.txt', 'w+', encoding='utf-8')
    for i, row in data.iterrows():
        content = row['Example']
        relation = row['Relation']
        if relation != 'company/person/chairman':
            f.write(content.strip())
            f.write('\n')


def judge_pure_english(keyword):
    return all(ord(c) < 128 for c in keyword)


def generate_dict():
    data = pd.read_csv("./train_data.csv")
    my_dict = open('construct_dict.txt', 'w+', encoding='utf-8')
    cur_dict = []
    for word in set(data['Entity1']):
        if word not in cur_dict:
            cur_dict.append(word)
            my_dict.write(word + '\n')

    for word in set(data['Entity2']):
        if word not in cur_dict:
            cur_dict.append(word)
            my_dict.write(word + '\n')
    my_dict.close()

select_data()
generate_dict()
