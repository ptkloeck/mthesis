'''
Created on 24.11.2015

@author: Peter
'''
import json
import urllib.request
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))

from anton.util import util as util
from anton.feature_extraction import base

BASE_URL = "http://maggie.lt.informatik.tu-darmstadt.de:10080/jobim/ws/api/stanford/"
FREQS_FILE_SUFFIX = "_freqs"
JB_ADJ_TAG = "JJ"
JB_NOUN_TAG = "NN"
JB_VERB_TAG = "VB"

FREQ_WORD_1_COL_HEADER = "freq1"
FREQ_WORD_2_COL_HEADER = "freq2"

def pos_to_jo_bim_tag(pos):
    
    if pos == util.POS.ADJ:
        return JB_ADJ_TAG
    elif pos == util.POS.NOUN:
        return JB_NOUN_TAG
    elif pos == util.POS.VERB:
        return JB_VERB_TAG

def get_count_web(word, pos_tag):

    response = urllib.request.urlopen(BASE_URL + "jo/count/" + word + "%23" + pos_tag).read()
    
    data = json.loads(response.decode())
    
    return data["result"]["count"]

def freqs_instances_file(instances_filename, output_filename, pos):
    
    pos_tag = pos_to_jo_bim_tag(pos)
    
    with open(instances_filename, 'r') as instances_file:
        with open(output_filename, 'w') as count_file:
            
            count_file.write('\t' + FREQ_WORD_1_COL_HEADER + '\t' + FREQ_WORD_2_COL_HEADER + '\n')
            for line in instances_file:
        
                words = line.split()
                word_0 = words[0]
                word_1 = words[1]

                count_0 = get_count_web(word_0, pos_tag)
                count_1 = get_count_web(word_1, pos_tag)

                count_file.write(word_0 + ' ' + word_1 + '\t' + str(count_0) + '\t' + str(count_1) + '\n')

def get_freqs(instance, pos):
    
    pos_tag = pos_to_jo_bim_tag(pos)
    
    words = instance.split()
    word_0 = words[0]
    word_1 = words[1]

    count_0 = get_count_web(word_0, pos_tag)
    count_1 = get_count_web(word_1, pos_tag)
    
    print("Received frequencies for " + instance)
    
    return (count_0, count_1)
                
def add_freqs(df, pos):

    if FREQ_WORD_1_COL_HEADER in df and FREQ_WORD_2_COL_HEADER in df:
        return
    df[FREQ_WORD_1_COL_HEADER], df[FREQ_WORD_2_COL_HEADER] = zip(*df.index.map(lambda x: get_freqs(x, pos)))

def is_top_sim(instance, second_in_first, pos):
    """
    :param second_in_first: if True, checks if the second word (word_1) is in the top similar words of the first word (word_0), otherwise the other way round
    :type second_in_first: boolean
    :param instance: the pair as as string with a space in the middle
    :type str
    :returns: a tuple indicating whether word_1 (or word_2) is in the top1, top3, top5, top10, top20 most similar words of word_2 (or word_1)
    :rtype: tuple with five ints (0 -> False or 1 -> True)
    """
    
    pos_tag = pos_to_jo_bim_tag(pos)
    
    words = instance.split()
    word_1 = words[0]
    word_2 = words[1]

    if not second_in_first:
        word_2, word_1 = word_1, word_2 
        
    response = urllib.request.urlopen(BASE_URL + "jo/similar/" + word_1 + "%23" + pos_tag).read()
    
    data = json.loads(response.decode())

    index = 0
    for sim_word_json in data["results"][1:20]:
        if sim_word_json["key"].split('#')[0] == word_2:
            if index < 1:
                return (1, 1, 1, 1, 1)
            elif index < 3:
                return (0, 1, 1, 1, 1)
            elif index < 5:
                return (0, 0, 1, 1, 1)
            elif index < 10:
                return (0, 0, 0, 1, 1)
            elif index < 20:
                return (0, 0, 0, 0, 1)                
        index += 1
    
    print("Received is_top_sim for " + instance)
        
    return (0, 0, 0, 0, 0)

class JBSimFeatureExtractor(base.FeatureExtractor):
    
    TOP1_SIM_SF = "top1_sim_sf" 
    TOP3_SIM_SF = "top3_sim_sf"
    TOP5_SIM_SF = "top5_sim_sf" 
    TOP10_SIM_SF = "top10_sim_sf" 
    TOP20_SIM_SF = "top20_sim_sf"
    
    TOP1_SIM_FS = "top1_sim_fs" 
    TOP3_SIM_FS = "top3_sim_fs"
    TOP5_SIM_FS = "top5_sim_fs" 
    TOP10_SIM_FS = "top10_sim_fs" 
    TOP20_SIM_FS = "top20_sim_fs"
    
    def title(self):
        return "JoBim similarity"
    
    def feature_col_headers(self):
        return self.col_headers()
    
    def col_headers(self):
        return [self.TOP1_SIM_SF, self.TOP3_SIM_SF, self.TOP5_SIM_SF, self.TOP10_SIM_SF, self.TOP20_SIM_SF, self.TOP1_SIM_FS, self.TOP3_SIM_FS, self.TOP5_SIM_FS, self.TOP10_SIM_FS, self.TOP20_SIM_FS]

    def init(self, pos_to_df):
        return

    def extract_features_pos(self, pos_to_df):

        for pos in util.POS:
            
            df = pos_to_df[pos]
            
            df[self.TOP1_SIM_SF], df[self.TOP3_SIM_SF], df[self.TOP5_SIM_SF], df[self.TOP10_SIM_SF], df[self.TOP20_SIM_SF] = zip(*df.index.map(lambda x: is_top_sim(x, True, pos)))
            df[self.TOP1_SIM_FS], df[self.TOP3_SIM_FS], df[self.TOP5_SIM_FS], df[self.TOP10_SIM_FS], df[self.TOP20_SIM_FS] = zip(*df.index.map(lambda x: is_top_sim(x, False, pos)))

    def finish(self, df):
        return    
