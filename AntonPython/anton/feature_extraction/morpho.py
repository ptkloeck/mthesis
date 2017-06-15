'''
Created on May 7, 2016

@author: peter
'''
import Levenshtein
from hyphen import Hyphenator

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))

from anton import config
from anton.feature_extraction import base
from anton.util import util

IS_AFFIX = "is_affix"
IS_AFFIX_RULES = "is_affix_rules"
NORM_LEVENSHTEIN = "norm_levenshtein"
JACCARD_SYLLABLES = "jaccard_syllables" 

AFFIX_RULES = [("X", "antiX"), ("X", "disX"), ("X", "imX"), ("X", "inX"), ("X", "malX"), ("X", "misX"),
               ("X", "nonX"), ("X", "unX"), ("lX", "illX"), ("rX", "irrX"), ("imX", "exX"), ("inX", "exX"),
               ("upX", "downX"), ("overX", "underX"), ("Xless", "Xful"), ("X", "aX")]

class PairMorphFeatureExtractor(base.FeatureExtractor):

    def __init__(self):
        self.h_en = Hyphenator(language = "en_GB", directory = config.path_to_res("hyphen_dir"))

    def title(self):
        return "Morphological features"
    
    def feature_col_headers(self):
        return self.col_headers()
    
    def col_headers(self):
        return [IS_AFFIX, IS_AFFIX_RULES, NORM_LEVENSHTEIN, JACCARD_SYLLABLES]

    def init(self, pos_to_df):
        return

    def extract_features_pos(self, pos_to_df):
        
        for pos in util.POS:
            
            df = pos_to_df[pos]
            df[IS_AFFIX] = df.index.map(lambda x: is_affix_pair(x))
            df[IS_AFFIX_RULES] = df.index.map(lambda x: is_affix_rules(x))
            df[NORM_LEVENSHTEIN] = df.index.map(lambda x: norm_levenshtein(x))
            df[JACCARD_SYLLABLES] = df.index.map(lambda x: self.jaccard_syllables(x))    

    def jaccard_syllables(self, instance):
        words = instance.split()
        word_1, word_2 = words[0], words[1]
        w1_syls = set(self.h_en.syllables(word_1))
        w2_syls = set(self.h_en.syllables(word_2))

        intersection_syls = w1_syls.intersection(w2_syls)
        union_syls = w1_syls.union(w2_syls)
        len_union = len(union_syls)
        if len_union == 0:
            return 0
        return len(intersection_syls) / float(len(union_syls))

    def finish(self, df):
        return  

def is_affix_pair(instance):
    words = instance.split()
    word_1, word_2 = words[0], words[1]

    if word_1 in word_2 or word_2 in word_1:
        return 1
    else:
        return 0

def check_rule(rule, word_1, word_2):
                
        w1_rule = rule[0].split("X")
        w2_rule = rule[1].split("X")
                
        w1_len = len(word_1)
        w2_len = len(word_2)
                
        w1_prefix = w1_rule[0]
        w1_suffix = w1_rule[1]
        
        w2_prefix = w2_rule[0]
        w2_suffix = w2_rule[1]
                
        w1_prefix_len = len(w1_prefix)
        w1_suffix_len = len(w1_suffix)
        w2_prefix_len = len(w2_prefix)
        w2_suffix_len = len(w2_suffix)
                
        if w1_len < w1_prefix_len + w1_suffix_len or w2_len < w2_prefix_len + w2_suffix_len:
            return False
                
        w1_X = word_1[w1_prefix_len: w1_len - w1_suffix_len]
        w2_X = word_2[w2_prefix_len: w2_len - w2_suffix_len]
                
        return w1_X == w2_X and word_1.startswith(w1_prefix) and word_1.endswith(w1_suffix) and word_2.startswith(w2_prefix) and word_2.endswith(w2_suffix)
    
def is_affix_rules(instance):
    words = instance.split()
    word_1, word_2 = words[0], words[1]
                
    for rule in AFFIX_RULES:
                
        if check_rule(rule, word_1, word_2) or check_rule(rule, word_2, word_1):
            return 1    
                
    return 0

def norm_levenshtein(instance):
    words = instance.split()
    word_1, word_2 = words[0], words[1]

    return Levenshtein.distance(word_1, word_2) / float(max(len(word_1), len(word_2)))
    