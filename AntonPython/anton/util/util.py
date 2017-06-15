'''
Created on 22.11.2015

@author: Peter
'''
import pandas as pd
from enum import Enum
import math
import re
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))

from anton import config

TRESH_SUFFIX = "_thresh" 
 
class POS(Enum):
    ADJ = ("adj")
    NOUN = ("noun")
    VERB = ("verb")
    
    def __init__(self, tag):
        self.tag = tag
    
def order_pair(pair):
    
    word_1 = pair[0]
    word_2 = pair[1]
        
    if word_1 > word_2:
        word_1, word_2 = word_2, word_1
        
    return (word_1, word_2)

def ordered_pair_to_index_key(pair):
    
    return pair[0] + " " + pair[1]

def pair_to_index_key(pair):
    
    return ordered_pair_to_index_key(order_pair(pair))

def begins_with_capital(word):
    if len(word) == 0:
        return False
    return word[0].isupper()

def create_pairs(items):
    
    num_items = len(items)
    
    item_pairs = []
    
    for i, item_1 in enumerate(items):
        for j in range(i + 1, num_items):
            
            item_2 = items[j]
            
            item_pairs.append((item_1, item_2))
            
    return item_pairs

def deduplicate_pairs(filename):
    
    outfilename = filename + "_deduplicated"
    
    lines_seen = set() 
    outfile = open(outfilename, "w")
    
    for line in open(filename, "r"):
        
        words = line.split()
        word_1 = words[0]
        word_2 = words[1]
        
        reverted_line = word_2 + ' ' + word_1 + '\n'

        if line not in lines_seen and reverted_line not in lines_seen:
            
            outfile.write(line)
            lines_seen.add(line)

    outfile.close()

def filter_by_freq(instances_filename, threshold):
    
    df = pd.read_csv(instances_filename, sep='\t', index_col=0)
    df = df[(df.freq1 >= threshold) & (df.freq2 >= threshold)]

    df.to_csv(instances_filename.replace(".tsv", TRESH_SUFFIX + str(threshold) + ".tsv"), sep='\t')

def lmi(freq_a, freq_b, joint_freq, total):

    if freq_a == 0 or freq_b == 0 or joint_freq == 0 or total == 0:
        return 0
    else:
        return joint_freq * math.log((total * joint_freq) / float(freq_a * freq_b))

def swap_columns(col1, col2):
    
    df = pd.read_csv("../res/data.tsv", sep='\t', index_col=0) 
    cols = list(df)
    cols[col1], cols[col2] = cols[col2], cols[col1]
    df.columns = cols
    df.to_csv("../res/data.tsv", sep='\t')
    
def pattern_id_to_pattern(web1t, pos=POS.ADJ):
    
    if web1t:
        pattern_file = "webt1_pattern_count.txt"
    else:
        pattern_file = pattern_ranking_file(pos) 
    
    pattern_id_to_pattern = {}
    line_number = 0
    
    for line in open(config.ws_path + "/AntonSpk/" + pattern_file):
        line_number += 1
        parts = line.split('\t')
        pattern = parts[0]
        if web1t:
            pattern_id = "web1t_pattern_" + str(line_number) + "_lmi"
        else:
            pattern_id = "bestPattern" + str(line_number)
        pattern_id_to_pattern[pattern_id] = pattern
        
    return pattern_id_to_pattern  

def pattern_ranking_file(pos):
    
    if pos == POS.ADJ:
        pattern_file = "adj_pattern_ranking.txt"
    elif pos == POS.NOUN:
        pattern_file = "noun_pattern_ranking.txt"
    elif pos == POS.VERB:
        pattern_file = "verb_pattern_ranking.txt" 
        
    return pattern_file

def pattern_to_score(pos):
    
    pattern_to_score = {}
    
    ranking_file = pattern_ranking_file(pos)
    
    for line in open(config.ws_path + "/AntonSpk/" + ranking_file):
        parts = line.rstrip('\n').split('\t')
        
        raw_pattern = parts[0]
        pattern = re.sub(r"/[^ ]*", "", raw_pattern)
        
        score = float(parts[3])
        
        pattern_to_score[pattern] = score
        
    return pattern_to_score
        
def web1t_pattern_to_scores():
    
    web1t_pattern_to_score = {}
    
    web1t_pattern_id_to_pattern = pattern_id_to_pattern(True)
    
    adj_pattern_to_score = pattern_to_score(POS.ADJ)
    noun_pattern_to_score = pattern_to_score(POS.NOUN)
    verb_pattern_to_score = pattern_to_score(POS.VERB)
    
    for _, pattern in web1t_pattern_id_to_pattern.items():
        
        if pattern in adj_pattern_to_score:
            web1t_pattern_to_score[pattern] = adj_pattern_to_score[pattern]
        elif pattern in noun_pattern_to_score:
            web1t_pattern_to_score[pattern] = noun_pattern_to_score[pattern]
        elif pattern in verb_pattern_to_score:
            web1t_pattern_to_score[pattern] = verb_pattern_to_score[pattern]
            
    return web1t_pattern_to_score

def feature_category_to_latex(feature_category):
    
    from anton.feature_extraction.base import FeatureCategory
    
    return {FeatureCategory.COOC_PAIR: "\textit{sen-cooc}",
     FeatureCategory.COOC_CONTEXT: "\textit{news105-context-words}",
     FeatureCategory.LIN: "\textit{news105-lin}",
     FeatureCategory.JB_SIM: "\textit{jb-sim}",
     FeatureCategory.MORPH: "\textit{morpho}",
     FeatureCategory.WORD_EMBED: "\textit{word-embed}",
     FeatureCategory.PATTERNS: "\textit{news105-patterns}",
     FeatureCategory.PARA_COOC_PAIR: "\textit{para-cooc}",
     FeatureCategory.WEB1T_PATTERNS: "\textit{web1t-patterns}"}[feature_category]
