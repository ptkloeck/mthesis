'''
Created on May 8, 2016

@author: peter
'''

from gensim.models.word2vec import Word2Vec

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))

from anton import config
from anton.util import util
from anton.feature_extraction import base

WORD_EMBED_SIM = "word_embed_sim"

class WordEmbedddingSimExtractor(base.FeatureExtractor):

    def title(self):
        return "Word embedding similarity"
    
    def feature_col_headers(self):
        return self.col_headers()
    
    def col_headers(self):
        return [WORD_EMBED_SIM]

    def init(self, pos_to_df):
        return

    def extract_features_pos(self, pos_to_df):

        model = Word2Vec.load_word2vec_format(config.ws_path + "/../Word2Vec/GoogleNews-vectors-negative300.bin", binary=True)
    
        def word_embed_sim(instance):
            words = instance.split()
            word_1, word_2 = words[0], words[1]
        
            try:
                sim = model.similarity(word_1, word_2)
            except KeyError:
                sim = 0
            
                return sim 
        
        for pos in util.POS:
            
            df = pos_to_df[pos]
            df[WORD_EMBED_SIM] = df.index.map(lambda x: word_embed_sim(x))

    def finish(self, df):
        return  
    