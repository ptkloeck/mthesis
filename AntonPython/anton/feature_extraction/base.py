'''
Created on Apr 29, 2016

@author: peter
'''
import abc
from enum import Enum

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))

from anton.util import util

class FeatureExtractor(abc.ABC):

    @abc.abstractmethod
    def title(self):
        return
    
    @abc.abstractmethod    
    def feature_col_headers(self):
        return
    
    @abc.abstractmethod    
    def col_headers(self):
        return
    
    def covered_pos(self):
        return [pos for pos in util.POS]
    
    @abc.abstractmethod
    def init(self, pos_to_df):
        return
    
    def extract_features(self, pos_to_df):
        print("Starting to extract features: " + self.title())
        self.extract_features_pos(pos_to_df)
        print("Finished to extract features: " + self.title())
    
    @abc.abstractmethod 
    def extract_features_pos(self, pos_to_df):
        return
    
    @abc.abstractmethod
    def finish(self, pos_to_df):
        return            
        
    def remove_all_features(self, pos_to_df):
        for df in pos_to_df.values():
            df.drop(self.col_headers(), inplace=True, axis=1)

class JBCorpusFeatureExtractor(FeatureExtractor):
    
    def extract_features_pos(self, pos_to_df, pos_to_extract):
        print("Do not use this method, use extract_features_line(...) instead")
    
    @abc.abstractmethod  
    def extract_features_line(self, pos_to_df, line): 
        return

class FeatureCategory(Enum):
    COOC_PAIR = 1
    COOC_CONTEXT = 2
    LIN = 3
    JB_SIM = 4
    MORPH = 5 
    WORD_EMBED = 6
    PATTERNS = 7
    PARA_COOC_PAIR = 8
    WEB1T_PATTERNS = 9  

class ExtractorCategory(Enum):
    JO_BIM = 1
    REST = 2
 
def get_feature_categories(extractor_category):
    return {ExtractorCategory.JO_BIM: [FeatureCategory.COOC_PAIR, FeatureCategory.COOC_CONTEXT],
            ExtractorCategory.REST: [FeatureCategory.LIN, FeatureCategory.MORPH, FeatureCategory.JB_SIM, FeatureCategory.WORD_EMBED, FeatureCategory.PATTERNS, FeatureCategory.PARA_COOC_PAIR, FeatureCategory.WEB1T_PATTERNS]}[extractor_category]
           
def make_feature_extractor(feature_category):
    
    from anton.feature_extraction import cooc
    from anton.feature_extraction import lin_count
    from anton.feature_extraction import jobim_query
    from anton.feature_extraction import morpho
    from anton.feature_extraction import embed
    from anton.feature_extraction import patterns

    return {FeatureCategory.COOC_PAIR: cooc.PairCoocFeatureExtractor(),
     FeatureCategory.COOC_CONTEXT: cooc.PairContextCoocFeatureExtractor(),
     FeatureCategory.LIN: lin_count.LinPatternFeatureExtractor(),
     FeatureCategory.JB_SIM: jobim_query.JBSimFeatureExtractor(),
     FeatureCategory.MORPH: morpho.PairMorphFeatureExtractor(),
     FeatureCategory.WORD_EMBED: embed.WordEmbedddingSimExtractor(),
     FeatureCategory.PATTERNS: patterns.PosPatternsExtractor(),
     FeatureCategory.PARA_COOC_PAIR: cooc.ParagraphCoocExtractor(),
     FeatureCategory.WEB1T_PATTERNS: patterns.GoogleNGramPatternExtractor()}[feature_category]
    