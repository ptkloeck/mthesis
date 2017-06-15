'''
Created on 07.11.2015

@author: Peter
'''
from _collections import defaultdict
import math
from random import shuffle
from nltk.corpus import wordnet as wn
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))

from anton import config
from anton.feature_extraction import jobim_query
from anton.util import util
import pandas

MAX_RELATION_PAIRS = 10000

JO_BIM_OCCURENCE_TRESH = 100

WN_ADJ_TAGS = [wn.ADJ, wn.ADJ_SAT]
WN_NOUN_TAGS = [wn.NOUN]
WN_VERB_TAGS = [wn.VERB]

PURE_RELATION_FILE_SUFFIX = ".txt"

ANTONYM_FILE = "antonyms" + PURE_RELATION_FILE_SUFFIX
SYNONYM_FILE = "synonyms" + PURE_RELATION_FILE_SUFFIX
HYPONYM_FILE = "hyponyms" + PURE_RELATION_FILE_SUFFIX
CO_HYPONYM_FILE = "cohyponyms" + PURE_RELATION_FILE_SUFFIX
MERONYM_FILE = "meronyms" + PURE_RELATION_FILE_SUFFIX
UNRELATED_FILE = "unrelated" + PURE_RELATION_FILE_SUFFIX

ADJ_CREATION_PATH = config.ws_path + "/res/adj/dataset_creation/"
NOUN_CREATION_PATH = config.ws_path + "/res/noun/dataset_creation/"
VERB_CREATION_PATH = config.ws_path + "/res/verb/dataset_creation/"

ADJ_CREATION_FILES = [ADJ_CREATION_PATH + file for file in [ANTONYM_FILE, SYNONYM_FILE, UNRELATED_FILE]]
NOUN_CREATION_FILES = [NOUN_CREATION_PATH + file for file in [ANTONYM_FILE, SYNONYM_FILE, HYPONYM_FILE, CO_HYPONYM_FILE, MERONYM_FILE, UNRELATED_FILE]]
VERB_CREATION_FILES = [VERB_CREATION_PATH + file for file in [ANTONYM_FILE, SYNONYM_FILE, UNRELATED_FILE]]

DATA_FILE = "data_all.tsv"
ANT_SYN_DATA_FILE = "data_ant_syn.tsv"

class RelationBucket:
    
    def __init__(self):
        self.__pairs = set()
        self.__word_to_pair = defaultdict(list)
     
    @classmethod
    def from_freqs_thresh_file(cls, file):
        bucket = cls()
        df = pandas.read_csv(file, sep='\t', index_col=0)
        for index, _ in df.iterrows():
            words = index.split(" ")
            pair = words[0], words[1]
            bucket.add_pair(pair)
        return bucket
    
    def pairs(self):
        for pair in self.__pairs:
            yield pair
           
    def add_pair(self, pair):
        pair = util.order_pair(pair)
        if not pair in self.__pairs:
            self.__pairs.add(pair)
            self.__word_to_pair[pair[0]].append(pair)
            self.__word_to_pair[pair[1]].append(pair)
            
    def __delete_word(self, word):
        for pair in self.__word_to_pair[word]:
            if pair in self.__pairs:
                self.__pairs.remove(pair)
        self.__word_to_pair.pop(word)
        
    def delete_pair(self, pair):
        self.__delete_word(pair[0])
        self.__delete_word(pair[1])
        
    def num_pairs(self):
        return len(self.__pairs)

    def pop(self):
        pair = self.__pairs.pop()
        self.delete_pair(pair)
        return pair
        
def synset_pos_is_one_of(synset, pos_tags):
    return synset.pos() in pos_tags

def is_wn_multi_word(word):
    return '_' in word

def antonym_synsets(synset_1, synset_2):

    for lemma in synset_1.lemmas(): 
        for antonym in lemma.antonyms():
            if antonym.synset() == synset_2:
                return True
            
    return False
                        
def pointers_between_synsets(synset_1, synset_2):
    
    """
    possible pointers:
    - hypernyms, instance_hypernyms
    - hyponyms, instance_hyponyms
    - member_holonyms, substance_holonyms, part_holonyms
    - member_meronyms, substance_meronyms, part_meronyms
    - attributes
    - entailments
    - causes
    - also_sees
    - verb_groups
    - similar_tos
    """   
    
    if synset_1 in synset_2.hypernyms():
        return True
    
    if synset_1 in synset_2.instance_hypernyms():
        return True
    
    if synset_1 in synset_2.hyponyms():
        return True
    
    if synset_1 in synset_2.instance_hyponyms():
        return True
    
    if synset_1 in synset_2.part_meronyms():
        return True
    
    if synset_1 in synset_2.substance_meronyms():
        return True

    if synset_1 in synset_2.member_meronyms():
        return True
    
    if synset_1 in synset_2.part_holonyms():
        return True
    
    if synset_1 in synset_2.substance_holonyms():
        return True

    if synset_1 in synset_2.member_holonyms():
        return True
    
    if synset_1 in synset_2.attributes():
        return True
    
    if synset_1 in synset_2.entailments():
        return True
    
    if synset_2 in synset_1.attributes():
        return True
    
    if synset_2 in synset_1.entailments():
        return True
    
    return False 

def extract_pairs(synset_1, synset_2):
    
    pairs = []
    for lemma_1 in synset_1.lemmas():
        for lemma_2 in synset_2.lemmas():
                    
            lemma_1_name = lemma_1.name()
            lemma_2_name = lemma_2.name()
            
            __append_ordered_if_not_mw_or_capital(pairs, (lemma_1_name, lemma_2_name))       
    
    return pairs

def __append_ordered_if_not_mw_or_capital(pairs, pair):
    
    word_1 = pair[0]
    word_2 = pair[1]
    if is_wn_multi_word(word_1):
        return
    if is_wn_multi_word(word_2):
        return 
    if util.begins_with_capital(word_1):
        return
    if util.begins_with_capital(word_2):
        return

    pairs.append(util.order_pair(pair))

def save_pairs(output_file, pairs):
    
    file = open(output_file, 'w')
    for pair in pairs:
        file.write(pair[0] + ' ' + pair[1] + '\n')
    file.close()
    
def query_from_single_synsets(pos_tags, output_file, pair_extract_fun):

    pairs = set()
    
    for synset in wn.all_synsets():
        if not synset_pos_is_one_of(synset, pos_tags):
            continue
        
        pairs.update(pair_extract_fun(synset))
        
        if len(pairs) > MAX_RELATION_PAIRS:
            break;
    
    save_pairs(output_file, pairs)

def antonym_extract_fun(synset):
    
    pairs = []
    for lemma in synset.lemmas(): 
        for antonym in lemma.antonyms():
            ant_pair = (lemma.name(), antonym.name())
            __append_ordered_if_not_mw_or_capital(pairs, ant_pair) 
    
    return pairs
            
def query_antonyms(pos_tags, output_file): 
       
    query_from_single_synsets(pos_tags, output_file, antonym_extract_fun)

def synonym_extract_fun(synset):
     
    pairs = []
       
    lemmas = synset.lemmas()
    num_lemmas = len(lemmas)
    for i in range(num_lemmas):
        for j in range(i + 1, num_lemmas):
            syn_pair = (lemmas[i].name(), lemmas[j].name())
            __append_ordered_if_not_mw_or_capital(pairs, syn_pair)

    return pairs
    
def query_synonyms(pos_tags, output_file):

    query_from_single_synsets(pos_tags, output_file, synonym_extract_fun)
    
def query_from_double_synsets(pos_tags, output_file, synset_restrict_fun, related_synset_fun):    
    """
    :param synset_restrict_fun: 
        function which defines whether to look for related synsets of a synset 
        with related_synset_fun or not (e.g. for hypernym/hyponym extraction: 
        do not consider hypernym synsets which are top level concepts 
        like entity or abstract entity. 
    :type synset_restrict_fun: function with contract Synset -> boolean
    :param related_synset_fun: function which retrieves the related synsets for a synset
    :type related_synset_fun: function with contract Synset -> Synset*
    """
    pairs = set()
    
    for synset in wn.all_synsets():
        
        if not synset_pos_is_one_of(synset, pos_tags):
            continue
        
        if not synset_restrict_fun(synset):
            continue

        for other_synset in related_synset_fun(synset): 
            new_pairs = extract_pairs(synset, other_synset)
            pairs.update(new_pairs)
         
        if len(pairs) > MAX_RELATION_PAIRS:
            break;
           
    save_pairs(output_file, pairs)

def hyponym_related_synsets(synset):
    return synset.hyponyms()

def hyponym_restrict_fun(synset):
    
    # only extract hypernym/hyponym pairs where the hypernym 
    # is at least 2 "is_a" steps distant to the root concept
    # to not extract pairs like entity, physical entity        
    return len(synset.hypernym_paths()) > 2
    
def query_hyponyms(pos_tags, output_file):
    
    query_from_double_synsets(pos_tags, output_file, hyponym_restrict_fun, hyponym_related_synsets)

def meronym_related_synsets(synset):
    # try also: part_meronyms(), member_meronyms() and substance_meronyms()
    return synset.part_meronyms()

def no_restrict_fun(synset):
    return True
                
def query_meronyms(pos_tags, output_file):
    
    query_from_double_synsets(pos_tags, output_file, no_restrict_fun, meronym_related_synsets)
         
def co_hyponym_related_synsets(synset):
    
    related_synsets = []
    for hyper_synset in synset.hypernyms():
            
        if len(hyper_synset.hypernym_paths()) <= 2:
            continue
           
        for co_hyponym_2_synset in hyper_synset.hyponyms():
            if co_hyponym_2_synset == synset:
                continue
            related_synsets.append(co_hyponym_2_synset)
            
    return related_synsets   
       
def query_co_hyponyms(pos_tags, output_file):
    
    query_from_double_synsets(pos_tags, output_file, no_restrict_fun, co_hyponym_related_synsets)

def query_unrelated_restricted(pos_tags, output_file, synset_restrict_fun, other_synset_restrict_fun, pointer_restrict_fun):

    pairs = set()
    
    synsets = [synset for synset in wn.all_synsets()]
    shuffle(synsets)
    num_synsets = len(synsets)

    for i in range(num_synsets):
        
        synset = synsets[i]
        
        if not synset_pos_is_one_of(synset, pos_tags):              
            continue

        if not synset_restrict_fun(synset):
            continue

        for j in range(i + 1, num_synsets):
        
            other_synset = synsets[j]
            if not synset_pos_is_one_of(other_synset, pos_tags):
                continue
            
            if not other_synset_restrict_fun(synset):
                continue

            if not pointer_restrict_fun(synset, other_synset):
                continue

            new_pairs = extract_pairs(synset, other_synset)
            pairs.update(new_pairs)
            break;
    
        if len(pairs) > MAX_RELATION_PAIRS:
            break;
        
    save_pairs(output_file, pairs)

def query_unrelated(pos_tags, output_file):
    
    if pos_tags == set(WN_ADJ_TAGS) or pos_tags == set(WN_VERB_TAGS):
        return query_unrelated_restricted(pos_tags, output_file, no_restrict_fun, no_restrict_fun, verb_adj_pointer_restrict_fun) 
     
    return query_unrelated_restricted(pos_tags, output_file, hyponym_restrict_fun, hyponym_restrict_fun, noun_pointer_restrict_fun)

def noun_pointer_restrict_fun(synset, other_synset):
    """
    :returns: True, if two noun synsets are considered unrelated. False, otherwise.
    :rtype: boolean 
    """
    if pointers_between_synsets(synset, other_synset):
        return False
    
    if synset.shortest_path_distance(other_synset) <= 2:
        return False
    
    return True

def verb_adj_pointer_restrict_fun(synset, other_synset):
    
    if other_synset in synset.similar_tos():
        return False
            
    if antonym_synsets(synset, other_synset):
        return False
    
    return True

def query_all(pos):

    if pos == util.POS.ADJ:        
        wn_tags = set(WN_ADJ_TAGS)
        query_antonyms(wn_tags, ADJ_CREATION_PATH + ANTONYM_FILE)  
        query_synonyms(wn_tags, ADJ_CREATION_PATH + SYNONYM_FILE)  
        query_unrelated(wn_tags, ADJ_CREATION_PATH + UNRELATED_FILE)   
             
    elif pos == util.POS.NOUN:       
        wn_tags = set(WN_NOUN_TAGS)
        query_antonyms(wn_tags, NOUN_CREATION_PATH + ANTONYM_FILE)  
        query_synonyms(wn_tags, NOUN_CREATION_PATH + SYNONYM_FILE)  
        query_hyponyms(wn_tags, NOUN_CREATION_PATH + HYPONYM_FILE)
        query_co_hyponyms(wn_tags, NOUN_CREATION_PATH + CO_HYPONYM_FILE)
        query_meronyms(wn_tags, NOUN_CREATION_PATH + MERONYM_FILE)
        query_unrelated(wn_tags, NOUN_CREATION_PATH + UNRELATED_FILE)
    
    elif pos == util.POS.VERB:
        wn_tags = set(WN_VERB_TAGS)
        query_antonyms(wn_tags, VERB_CREATION_PATH + ANTONYM_FILE)  
        query_synonyms(wn_tags, VERB_CREATION_PATH + SYNONYM_FILE)  
        query_unrelated(wn_tags, VERB_CREATION_PATH + UNRELATED_FILE)
           
    else:       
        print("Cannot query " + str(pos))

def freq_files(files, pos):
    
    for file in files:
        jobim_query.freqs_instances_file(file, pure_name_to_freqs_name(file), pos)

def pure_name_to_freqs_name(file):
    return file.replace(PURE_RELATION_FILE_SUFFIX, jobim_query.FREQS_FILE_SUFFIX + ".tsv")

def creation_files(pos):
    
    if pos == util.POS.ADJ: 
        return ADJ_CREATION_FILES 
    elif pos == util.POS.NOUN:
        return NOUN_CREATION_FILES
    elif pos == util.POS.VERB:
        return VERB_CREATION_FILES

def creation_path(pos):
    
    if pos == util.POS.ADJ: 
        return ADJ_CREATION_PATH 
    elif pos == util.POS.NOUN:
        return NOUN_CREATION_PATH
    elif pos == util.POS.VERB:
        return VERB_CREATION_PATH

def freq(pos):
    freq_files(creation_files(pos), pos)
          
def pure_name_to_freqs_thresh_name(file):
    return pure_name_to_freqs_name(file).replace(".tsv", util.TRESH_SUFFIX + str(JO_BIM_OCCURENCE_TRESH) + ".tsv")

def freq_filter_files(files):
    for file in files:
        util.filter_by_freq(pure_name_to_freqs_name(file), JO_BIM_OCCURENCE_TRESH)

def freq_filter(pos):
    freq_filter_files(creation_files(pos))

def tresh_df_bucket(pure_file):

    file = pure_name_to_freqs_thresh_name(pure_file)
    df = pandas.read_csv(file, sep='\t', index_col=0)  
    bucket = RelationBucket.from_freqs_thresh_file(file)
    
    return df, bucket

def make_wn_data_set(pos, ant_syn):
    
    creat_path = creation_path(pos)
    ant_df, ant_bucket = tresh_df_bucket(creat_path + ANTONYM_FILE)
    ant_df["rel_class"] = 1

    buckets = []
    dfs = []
    files = creation_files(pos)[1:]
    if ant_syn:
        files = files[0:1]
    for creation_file in files:
        rel_df, rel_bucket = tresh_df_bucket(creation_file)
        dfs.append(rel_df)
        buckets.append(rel_bucket)
        
    ant_pairs = []
    rel_pairs = []
    for i in range(len(buckets)):
        rel_pairs.append([])

    for pair in ant_bucket.pairs():
        ant_pairs.append(pair)       
        for bucket in buckets:
            bucket.delete_pair(pair)
    
    num_ants = ant_bucket.num_pairs()
    num_rels = [0] * len(buckets)

    num_rel_max_stratified = math.ceil(num_ants / len(buckets))
    print(num_rel_max_stratified)

    def dataset_full():
        return num_ants <= sum(num_rels)

    def buckets_empty():
        for bucket in buckets:
            if bucket.num_pairs() > 0:
                return False
        return True 

    while not buckets_empty():
        
        min_num_pairs = float('inf')
        smallest_bucket = buckets[0]
        smallest_bucket_index = 0    
        for i, bucket in enumerate(buckets):
            num_pairs = bucket.num_pairs()
            if num_pairs < min_num_pairs and num_pairs != 0:
                min_num_pairs = num_pairs
                smallest_bucket = bucket
                smallest_bucket_index = i
                
        pair = smallest_bucket.pop()
        for j, bucket in enumerate(buckets):
            if not smallest_bucket_index == j:
                bucket.delete_pair(pair)
        rel_pairs[smallest_bucket_index].append(pair)
        num_rels[smallest_bucket_index] += 1

    for pairs in rel_pairs:
        print(pairs)
        print(len(pairs))
        
    for i, pairs in enumerate(rel_pairs):
        for pair in pairs[:num_rel_max_stratified]:
            index_key = util.ordered_pair_to_index_key(pair) 
            row = dfs[i].loc[index_key]
            row["rel_class"] = i + 2             
            ant_df.loc[index_key] = row
    
    datafile = ANT_SYN_DATA_FILE if ant_syn  else DATA_FILE
    ant_df["pos_tag"] = pos.tag    
    ant_df.to_csv(creat_path + "../" + datafile, sep='\t')
                  
if __name__ == "__main__":

    for pos in util.POS:
        query_all(pos)
        freq(pos)
        freq_filter(pos)
        make_wn_data_set(pos, False)
        make_wn_data_set(pos, True)
    