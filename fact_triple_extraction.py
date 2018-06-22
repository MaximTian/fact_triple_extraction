#!/usr/bin/env python
# coding=utf-8

from pyltp import Segmentor, Postagger, Parser, NamedEntityRecognizer
from pprint import pprint

segmentor = Segmentor()
segmentor.load_with_lexicon("./ltp_data/cws.model", './construct_dict.txt')
# segmentor.load("./ltp_data/cws.model")  # 分词模型
postagger = Postagger()
postagger.load("./ltp_data/pos.model")  # 词性标注
parser = Parser()
parser.load("./ltp_data/parser.model")  # 依存句法分析
recognizer = NamedEntityRecognizer()
recognizer.load("./ltp_data/ner.model")  # 命名实体识别

in_file_name = "input_test"
out_file_name = "output.txt"
in_file = open(in_file_name, 'r', encoding="utf-8")
out_file = open(out_file_name, 'w+', encoding="utf-8")

construct_list = []


def get_contruct_list():
    f = open('construct_dict.txt', 'r', encoding="utf-8")
    for line in f:
        construct = line.strip()
        if construct not in construct_list:
            construct_list.append(construct)


def map_WordList_ConstructList(word_list):
    for word in word_list:
        if word in construct_list:
            return True
    return False


def extraction_start():
    """
    事实三元组抽取的总控程序
    """
    for sentence_index, text_line in enumerate(in_file):
        sentence = text_line.strip()
        if len(sentence) == 0:
            continue
        fact_triple_extract(sentence, sentence_index)
    in_file.close()
    out_file.close()


def fact_triple_extract(sentence, sentence_index):
    """
    对于给定的句子进行事实三元组抽取
    Args:
        sentence: 要处理的语句
    """
    words = segmentor.segment(sentence)
    postags = postagger.postag(words)
    netags = recognizer.recognize(words, postags)
    arcs = parser.parse(words, postags)

    child_dict_list = build_parse_child_dict(words, postags, arcs)

    print("\t".join(words))
    print("\t".join(postags))
    print("\t".join("%d:%s" % (arc.head, arc.relation) for arc in arcs))
    print('\t'.join(netags))
    pprint(child_dict_list)

    for index in range(len(postags)):
        # 抽取以谓词为中心的事实三元组
        if postags[index] == 'v':
            child_dict = child_dict_list[index]
            # 主谓宾
            if 'SBV' in child_dict and 'VOB' in child_dict:
                # print(index, words[index])
                cur_wordlist = []
                e1 = complete_entity(words, postags, child_dict_list, child_dict['SBV'][0], cur_wordlist)
                r = words[index]
                e2 = complete_entity(words, postags, child_dict_list, child_dict['VOB'][0], cur_wordlist)
                if (map_WordList_ConstructList(cur_wordlist)):
                    out_file.write("主语谓语宾语关系\t({}, {}, {})\t{}\n".format(e1, r, e2, sentence_index))

                if 'COO' in child_dict:  # 寻找并列关系
                    tie_index = child_dict['COO'][0]
                    new_child_dict = child_dict_list[tie_index]
                    if 'VOB' in new_child_dict:
                        cur_wordlist = []
                        e1 = complete_entity(words, postags, child_dict_list, child_dict['SBV'][0], cur_wordlist)
                        r = words[tie_index]
                        e2 = complete_entity(words, postags, child_dict_list, new_child_dict['VOB'][0], cur_wordlist)
                        if (map_WordList_ConstructList(cur_wordlist)):
                            out_file.write("主语谓语宾语关系\t({}, {}, {})\t{}\n".format(e1, r, e2, sentence_index))

            # 定语后置，动宾关系
            if arcs[index].relation == 'ATT':
                if 'VOB' in child_dict:
                    cur_wordlist = []
                    e1 = complete_entity(words, postags, child_dict_list, arcs[index].head - 1, cur_wordlist)
                    r = words[index]
                    e2 = complete_entity(words, postags, child_dict_list, child_dict['VOB'][0], cur_wordlist)
                    temp_string = r+e2
                    if temp_string == e1[:len(temp_string)]:
                        e1 = e1[len(temp_string):]
                    if temp_string not in e1:
                        if (map_WordList_ConstructList(cur_wordlist)):
                            out_file.write("定语后置动宾关系\t({}, {}, {})\t{}\n".format(e1, r, e2, sentence_index))
            # 含有介宾关系的主谓动补关系
            if 'SBV' in child_dict and 'CMP' in child_dict:
                cur_wordlist = []
                e1 = complete_entity(words, postags, child_dict_list, child_dict['SBV'][0], cur_wordlist)
                cmp_index = child_dict['CMP'][0]
                r = words[index] + words[cmp_index]
                if 'POB' in child_dict_list[cmp_index]:
                    e2 = complete_entity(words, postags, child_dict_list, child_dict_list[cmp_index]['POB'][0], cur_wordlist)
                    if (map_WordList_ConstructList(cur_wordlist)):
                        out_file.write("介宾关系主谓动补\t({}, {}, {})\t{}\n".format(e1, r, e2, sentence_index))

        # 尝试抽取命名实体有关的三元组
        # if netags[index][0] == 'S' or netags[index][0] == 'B':
        #     ni = index
        #     if netags[ni][0] == 'B':
        #         while netags[ni][0] != 'E':
        #             ni += 1
        #         e1 = ''.join(words[index:ni+1])
        #     else:
        #         e1 = words[ni]
        #     if arcs[ni].relation == 'ATT' and postags[arcs[ni].head-1] == 'n' and netags[arcs[ni].head-1] == 'O':
        #         cur_wordlist = []
        #         r = complete_entity(words, postags, child_dict_list, arcs[ni].head-1, cur_wordlist)
        #         if e1 in r:
        #             r = r[(r.index(e1)+len(e1)):]
        #         if arcs[arcs[ni].head-1].relation == 'ATT' and netags[arcs[arcs[ni].head-1].head-1] != 'O':
        #             e2 = complete_entity(words, postags, child_dict_list, arcs[arcs[ni].head-1].head-1, cur_wordlist)
        #             mi = arcs[arcs[ni].head-1].head-1
        #             li = mi
        #             if netags[mi][0] == 'B':
        #                 while netags[mi][0] != 'E':
        #                     mi += 1
        #                 e = ''.join(words[li+1:mi+1])
        #                 e2 += e
        #             if r in e2:
        #                 e2 = e2[(e2.index(r)+len(r)):]
        #             if r+e2 in sentence:
        #                 out_file.write("人名//地名//机构\t(%s, %s, %s)\n" % (e1, r, e2))

    # extract_person_construction(words, postags, netags, arcs)


def extract_person_construction(words, postags, netags, arcs):
    child_dict_list = build_parse_child_dict(words, postags, arcs)
    for index in range(len(postags)):
        if netags[index][0] == 'S':
            pre_child_dict = child_dict_list[index - 1]
            if 'ATT' in pre_child_dict:
                first_entity_index = pre_child_dict['ATT'][0]
                if 'ATT' in child_dict_list[first_entity_index]:
                    e1_index = child_dict_list[first_entity_index]['ATT'][0]
                    e1 = complete_construction(words, child_dict_list, e1_index, True) + words[first_entity_index]
                    relation = complete_construction(words, child_dict_list, index - 1, False)
                    e2 = words[index]
                    out_file.write("人名//职位//机构\t(%s, %s, %s)\n" % (e1, relation, e2))

                if 'LAD' in pre_child_dict:  # 并列结构
                    for lad_entity_index in pre_child_dict['LAD']:
                        tie_entity_index = lad_entity_index - 1
                        if 'ATT' in child_dict_list[tie_entity_index]:
                            e1_index = child_dict_list[tie_entity_index]['ATT'][0]
                            e1 = complete_construction(words, child_dict_list, e1_index, True)
                            relation = complete_construction(words, child_dict_list, tie_entity_index, False)
                            e2 = words[index]
                            out_file.write("人名//职位//机构\t(%s, %s, %s)\n" % (e1, relation, e2))


def complete_construction(words, child_dict_list, word_index, is_head):
    child_dict = child_dict_list[word_index]
    prefix = ''
    if 'ATT' in child_dict:
        if is_head:
            for i in child_dict['ATT']:
                prefix += words[i]
        else:
            for i in child_dict['ATT'][1:]:
                prefix += words[i]
    return prefix + words[word_index]


def build_parse_child_dict(words, postags, arcs):
    """
    为句子中的每个词语维护一个保存句法依存儿子节点的字典
    Args:
        words: 分词列表
        postags: 词性列表
        arcs: 句法依存列表, head表示父节点索引，relation表示依存弧的关系
    """
    child_dict_list = []
    for index in range(len(words)):
        child_dict = {}
        for arc_index in range(len(arcs)):
            if arcs[arc_index].head == index + 1:
                relation = arcs[arc_index].relation
                if relation not in child_dict:
                    child_dict[relation] = []
                child_dict[relation].append(arc_index)
        child_dict_list.append(child_dict)
    return child_dict_list


def complete_entity(words, postags, child_dict_list, word_index, wordlist):
    """
    完善识别的部分实体
    """

    child_dict = child_dict_list[word_index]
    prefix = ''
    if 'ATT' in child_dict:
        for i in range(len(child_dict['ATT'])):
            prefix += complete_entity(words, postags, child_dict_list, child_dict['ATT'][i], wordlist)
    postfix = ''
    if postags[word_index] == 'v':
        if 'VOB' in child_dict:
            postfix += complete_entity(words, postags, child_dict_list, child_dict['VOB'][0], wordlist)
        if 'SBV' in child_dict:
            prefix = complete_entity(words, postags, child_dict_list, child_dict['SBV'][0], wordlist) + prefix
        if 'FOB' in child_dict:
            prefix += complete_entity(words, postags, child_dict_list, child_dict['FOB'][0], wordlist)

    tie_entity = ''
    if 'COO' in child_dict:
        for i in range(len(child_dict['COO'])):
            tie_entity += complete_entity(words, postags, child_dict_list, child_dict['COO'][i], wordlist)
        if len(tie_entity) > 0:
            tie_entity = '|' + tie_entity
    wordlist.append(words[word_index])
    return prefix + words[word_index] + postfix + tie_entity


if __name__ == "__main__":
    get_contruct_list()
    extraction_start()
