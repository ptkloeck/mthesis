'''
Created on 05.01.2016

@author: Peter
'''
import numpy
import pandas
from collections import Counter
from nltk import tokenize

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))

from anton import config
from anton.util import jobim_reader
from anton.util import util
from anton.feature_extraction import base

PARA_SENTENCE_LENGTH = 3

IN_SEN_COOC_COL_HEADER = "in_sen_cooc"
IN_SEN_COOC_LMI_COL_HEADER = "in_sen_cooc_lmi" 

PARA_FREQ_WORD_1_COL_HEADER = "para_freq_1"
PARA_FREQ_WORD_2_COL_HEADER = "para_freq_2"
IN_PARA_COOC_COL_HEADER = "in_para_cooc"
IN_PARA_COOC_LMI_COL_HEADER = "in_para_cooc_lmi"

class PairCoocFeatureExtractor(base.JBCorpusFeatureExtractor):

    def __init__(self):
        self.pos_to_pair_to_count = {}
        
    def title(self):
        return "Intra-sentence co-occurence"

    def feature_col_headers(self):
        return [IN_SEN_COOC_LMI_COL_HEADER]
        
    def col_headers(self):
        return [IN_SEN_COOC_COL_HEADER, IN_SEN_COOC_LMI_COL_HEADER]

    def init(self, pos_to_df):
        
        for pos in util.POS:
            
            instances = pos_to_df[pos].index.values
    
            self.pos_to_pair_to_count[pos] = {}
            for instance in instances:
                words = instance.split()
                pair = (words[0], words[1])
                key = util.pair_to_index_key(pair)
                self.pos_to_pair_to_count[pos][key] = 0

    def extract_features_line(self, pos_to_df, line): 
        
        parts = line.split('\t')    
        tagged_sen = parts[1].lower()        
        
        for pos in util.POS:
            self.in_sentence_cooc_pos(self.pos_to_pair_to_count[pos], pos, tagged_sen)
    
    def in_sentence_cooc_pos(self, pair_to_count, pos, tagged_sen):
    
        if len(jobim_reader.jb_pos(pos).pattern.findall(tagged_sen)) < 2:
            return
        
        tokens_with_pos = jobim_reader.extract_tokens_with_pos(tagged_sen, pos)
    
        num_tokens = len(tokens_with_pos)
    
        if num_tokens < 2:
            return

        token_pairs = util.create_pairs(tokens_with_pos)
        
        for token_pair in token_pairs:
             
            key = util.pair_to_index_key(token_pair)
            if key in pair_to_count:
                pair_to_count[key] += 1
    
    def finish(self, pos_to_df):
        
        num_sen_corpus = float(config.config["num_sen_corpus"])
        
        for pos in util.POS:
            
            df = pos_to_df[pos]
            pair_to_count = self.pos_to_pair_to_count[pos]
            
            def get_count(instance):
                words = instance.split()
                key = util.pair_to_index_key((words[0], words[1]))
                return pair_to_count[key]
               
            df[IN_SEN_COOC_COL_HEADER] = df.index.map(lambda x: get_count(x))
    
            #jobim_query.FREQ_WORD_1_COL_HEADER
            freq_a = df["freq1"]
            #jobim_query.FREQ_WORD_2_COL_HEADER
            freq_b = df["freq2"]
            joint_freq = pandas.Series(pair_to_count, name="cooc_count")
            total = num_sen_corpus  
            lmi(df, IN_SEN_COOC_LMI_COL_HEADER, freq_a, freq_b, joint_freq, total)

class PairContextCoocFeatureExtractor(base.JBCorpusFeatureExtractor):
    
    CONTEXT_WORD_COOC_LMI_SUFFIX = "_cooc_lmi"
    
    def __init__(self):
        
        self.context_word_to_count = {}
        with open(config.path_to_res("google_most_freq_words"), 'r') as file:
            next(file)
            for line in file:
                parts = line.strip().split('\t')
                self.context_word_to_count[parts[0]] = float(parts[1])
        
    def title(self):
        return "Intra-sentence context co-occurence"

    def feature_col_headers(self):
        return self.col_headers()
        
    def col_headers(self):
        return [context_word + self.CONTEXT_WORD_COOC_LMI_SUFFIX for context_word in ["and", "or", "between", "both", "neither", "nor", "either", "from", "to", "too", "not"]]
        return [context_word + self.CONTEXT_WORD_COOC_LMI_SUFFIX for context_word in self.context_word_to_count]

    def init(self, pos_to_df):
        return
        
    def extract_features_line(self, pos_to_df, line): 
        
        parts = line.split('\t')    
        tagged_sen = parts[1].lower()        
        
        for pos in util.POS:
            self.in_sentence_context_cooc(pos_to_df[pos], pos, tagged_sen)
    
    def in_sentence_context_cooc(self, df, pos, tagged_sen):
    
        tokens_with_pos = jobim_reader.extract_tokens_with_pos(tagged_sen, pos)
        token_pairs = util.create_pairs(tokens_with_pos)
    
        tokens = jobim_reader.extract_tokens(tagged_sen)
        
        for token_pair in token_pairs:

            key = util.pair_to_index_key(token_pair)

            if not key in df.index:
                continue
        
            token_1, token_2 = token_pair[0], token_pair[1]

            token_1_seen = False
            token_2_seen = False
            
            for token in tokens:
            
                if not token in self.context_word_to_count:
                    continue
                
                if not token_1_seen and token == token_1:
                    token_1_seen = True
                elif not token_2_seen and token == token_2:
                    token_2_seen = True
                else:
                    self.__inc_entry(df, key, token + self.CONTEXT_WORD_COOC_LMI_SUFFIX)

    def __inc_entry(self, df, index_key, column):
    
        if not column in df.columns:
            df[column] = 0
    
        df.set_value(index_key, column, df.at[index_key, column] + 1)
    
    def finish(self, pos_to_df):
        
        num_sen_corpus = float(config.config["num_sen_corpus"])
        
        for pos in util.POS:
            
            df = pos_to_df[pos]
            
            for context_word in self.context_word_to_count.keys():
                col_name = context_word + self.CONTEXT_WORD_COOC_LMI_SUFFIX
                if not col_name in df.columns:
                    df[col_name] = 0
                else:
                    freq_a = df[IN_SEN_COOC_COL_HEADER]
                    freq_b = self.context_word_to_count[context_word]
                    joint_freq = df[col_name]
                    total = num_sen_corpus  
                    lmi(df, col_name, freq_a, freq_b, joint_freq, total)

class ParagraphCoocExtractor(base.FeatureExtractor):

    def title(self):
        return "Paragraph co-occurence"
    
    def feature_col_headers(self):
        return [IN_PARA_COOC_LMI_COL_HEADER]
    
    def col_headers(self):
        return [PARA_FREQ_WORD_1_COL_HEADER, PARA_FREQ_WORD_2_COL_HEADER, IN_PARA_COOC_COL_HEADER, IN_PARA_COOC_LMI_COL_HEADER] 

    def init(self, pos_to_df):
        return

    def extract_features_pos(self, pos_to_df):
        
        corpus_dir = config.path_to_res("corpus_dir_aquaint")
        
        pos_to_pair_to_count = {}
        pos_to_word_1_to_count = {}
        pos_to_word_2_to_count = {}
        
        for pos in util.POS:
            
            pos_to_pair_to_count[pos] = Counter()
            pos_to_word_1_to_count[pos] = Counter()
            pos_to_word_2_to_count[pos] = Counter()
            
            for instance, _ in pos_to_df[pos].iterrows(): 
                
                parts = instance.split()
                word_1, word_2 = parts[0], parts[1]
                pair = (parts[0], parts[1])
                
                pos_to_pair_to_count[pos][pair] = 0
                pos_to_word_1_to_count[pos][word_1] = 0
                pos_to_word_2_to_count[pos][word_2] = 0
        
        num_sents = 0          
        for filename in os.listdir(corpus_dir):            
            with open(corpus_dir + '/' + filename, 'r') as file: 
                print("Processing " + filename)              
                for line in file:
                    
                    #list of sets of tokens (one token set per sentence in article)
                    tokens = []
                    
                    sentences = tokenize.sent_tokenize(line)
                    num_sents += len(sentences)
                    for sentence in sentences:
                        tokens.append(set(tokenize.word_tokenize(sentence)))
                    
                    for i in range(len(tokens) - PARA_SENTENCE_LENGTH):
                        
                        #list of sets of tokens (one token set per sentence in the paragraph)
                        para_tokens = tokens[i:i + PARA_SENTENCE_LENGTH]
                        
                        for pos in util.POS:                                                 
                            
                            self.count_in_para_pairs(para_tokens, pos_to_pair_to_count[pos])  
   
                            self.count_in_para_words(para_tokens, pos_to_word_1_to_count[pos]) 
                            self.count_in_para_words(para_tokens, pos_to_word_2_to_count[pos]) 
        
        for pos in util.POS:
            df = pos_to_df[pos]
            
            def para_freq_word(instance, word_to_count, word_index):
                return word_to_count[instance.split()[word_index]]
            
            word_1_to_count = pos_to_word_1_to_count[pos]
            df[PARA_FREQ_WORD_1_COL_HEADER] = df.index.map(lambda instance: para_freq_word(instance, word_1_to_count, 0))
            
            word_2_to_count = pos_to_word_2_to_count[pos]
            df[PARA_FREQ_WORD_2_COL_HEADER] = df.index.map(lambda instance: para_freq_word(instance, word_2_to_count, 1))
            
            pair_to_count = pos_to_pair_to_count[pos]
            def para_freq_pair(instance):
                parts = instance.split()
                pair = (parts[0], parts[1])
                return pair_to_count[pair]
            
            df[IN_PARA_COOC_COL_HEADER] = df.index.map(lambda instance: para_freq_pair(instance))

            lmi(df, IN_PARA_COOC_LMI_COL_HEADER, df[PARA_FREQ_WORD_1_COL_HEADER], df[PARA_FREQ_WORD_2_COL_HEADER], df[IN_PARA_COOC_COL_HEADER], num_sents - PARA_SENTENCE_LENGTH + 1)
    
    def count_in_para_words(self, para_tokens, word_to_count):
        for word in word_to_count:
            for sentence_tokens in para_tokens:
                if word in sentence_tokens:
                    word_to_count[word] += 1
                    break
    
    def count_in_para_pairs(self, para_tokens, pair_to_count):
        for pair in pair_to_count:                                                                                    
            if self.is_in_distinct_sents(para_tokens, pair):
                pair_to_count[pair] += 1 
                            
    def is_in_distinct_sents(self, para_tokens, pair):
        
        def check_from_sen(i, target_word, other_word):
            return target_word in para_tokens[i] and (self.list_of_collection_contains(para_tokens[:i], other_word) or self.list_of_collection_contains(para_tokens[i+1:], other_word))
        
        word_1 = pair[0]
        word_2 = pair[1]
                    
        for i in range(len(para_tokens)):    
            if check_from_sen(i, word_1, word_2) or check_from_sen(i, word_2, word_1):
                return True
            
        return False
                                                                 
    def list_of_collection_contains(self, list_of_collection, element):   
        for collection in list_of_collection:
            if element in collection:
                return True
        return False             
                    
    def finish(self, df):
        return
    
def lmi(df, lmi_col_header, freq_a, freq_b, joint_freq, total):       
    # vectorized lmi calculation
    df[lmi_col_header] = joint_freq * numpy.log((joint_freq * total) / (freq_a * freq_b))
    df[lmi_col_header].fillna(0, inplace=True)  
    