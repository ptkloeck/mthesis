'''
Created on 19.11.2015

@author: Peter
'''
from collections import defaultdict, Counter
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))

from anton import config
from anton.util import jobim_reader
from anton.feature_extraction import base
from anton.util import util

WORD_PATTERN_COUNT_FILE = "word_pattern_count.tsv"
INSTANCE_PATTERN_COUNT_FILE = "instance_pattern_count.tsv"

EITHER_OR_PATTERN_ID = "either_or"
FROM_TO_PATTERN_ID = "from_to"

WORD_1_ID = "word_1"
WORD_2_ID = "word_2"

class LinPattern:
    
    def __init__(self, regex, identifier):
        self.__pattern = re.compile(regex)
        self.identifier = identifier
        
    def check_sentence(self, sentence):

        sentence = sentence.lower()
        
        relations = []

        for match in self.__pattern.finditer(sentence):
        
            pattern = match.group(0)
            words = pattern.split()
        
            word_1 = words[1]
            word_2 = words[3]
            
            relations.append((word_1, word_2))
            
        return relations  

either_or_pattern = LinPattern("either\s[\w]+\sor\s[\w]+", EITHER_OR_PATTERN_ID)
from_to_pattern = LinPattern("from\s[\w]+\sto\s[\w]+", FROM_TO_PATTERN_ID)

all_patterns = [either_or_pattern, from_to_pattern]

class PatternCount:

    def __init__(self):        
        self.word_to_count = defaultdict(lambda: Counter())
        self.instance_to_count = defaultdict(lambda: Counter())
        
    @classmethod
    def from_files(cls, word_filename, instances_filename):
        pattern_count = cls()

        def read_tsv(filename, pattern_count, write_fun):
            
            with open(filename, 'r') as file:
                header = next(file)
                header_parts = header.replace('\n', "").split('\t')
                  
                for line in file:
                    parts = line.replace('\n', "").split('\t')
                    iterparts = iter(parts)
                    item = next(iterparts)
                    i = 1
                    for part in iterparts: 
                        write_fun(pattern_count, item, header_parts[i], int(part))
                        i += 1     
        
        def write_word_count(pattern_count, word, count_id, count):
            pattern_count.word_to_count[word][count_id] = count
                                 
        read_tsv(word_filename, pattern_count, write_word_count)
        
        def write_instance_count(pattern_count, instance, pattern_id, count):
            words = instance.split()
            instance = words[0], words[1]
            pattern_count.instance_to_count[instance][pattern_id] = count
            
        read_tsv(instances_filename, pattern_count, write_instance_count)
        
        return pattern_count

    def inc_word_1_count(self, word_1, pattern_id):
        self.__inc_word_count(word_1, pattern_id + "_" + WORD_1_ID)
        
    def inc_word_2_count(self, word_2, pattern_id):
        self.__inc_word_count(word_2, pattern_id + "_" + WORD_2_ID)
        
    def __inc_word_count(self, word, key):
        self.word_to_count[word][key] += 1
        
    def inc_instance_count(self, instance, pattern_id):

        if not instance in self.instance_to_count:
            instance = (instance[1], instance[0])
            
        self.instance_to_count[instance][pattern_id] += 1
    
    def get_word_1_count(self, word_1, pattern_id):
        return self.__get_word_count(word_1, pattern_id + "_" + WORD_1_ID)
        
    def get_word_2_count(self, word_2, pattern_id):
        return self.__get_word_count(word_2, pattern_id + "_" + WORD_2_ID)
        
    def __get_word_count(self, word, key):
        return self.word_to_count[word][key]   
    
    def get_instance_count(self, instance, pattern_id):
        
        if not instance in self.instance_to_count:
            instance = (instance[1], instance[0])
            
        return self.instance_to_count[instance][pattern_id]
            
    def get_rel_freq(self, instance, pattern_id):
        
        instance_count = self.get_instance_count(instance, pattern_id)
        
        word_1_count = self.get_word_1_count(instance[0], pattern_id)
        word_2_count = self.get_word_2_count(instance[1], pattern_id)
        
        if word_1_count == 0 and word_2_count == 0:
            return 0
        
        return instance_count / float(word_1_count + word_2_count) 
        
    def to_files(self, word_filename, instances_filename, pattern_ids):
        
        with open(word_filename, 'w') as file:

            file.write("word")

            for pattern_id in pattern_ids:
                file.write('\t' + pattern_id + "_" + WORD_1_ID + '\t' + pattern_id + "_" + WORD_2_ID)
            file.write('\n')
            
            for word in self.word_to_count:
                file.write(word)
                for pattern_id in pattern_ids:
                    file.write('\t')
                    file.write(str(self.word_to_count[word][pattern_id + "_" + WORD_1_ID]))
                    file.write('\t')
                    file.write(str(self.word_to_count[word][pattern_id + "_" + WORD_2_ID]))
                file.write('\n')
                
        with open(instances_filename, 'w') as file:
            
            file.write("instance")
            
            for pattern_id in pattern_ids:
                file.write('\t' + pattern_id)
            file.write('\n')
            
            for instance in self.instance_to_count:
                file.write(instance[0] + " " + instance[1])
                for pattern_id in pattern_ids:
                    file.write('\t' + str(self.instance_to_count[instance][pattern_id]))
                file.write('\n')
                    
def search_files():
    
    pattern_count = PatternCount()

    for line in jobim_reader.readlines(config.path_to_res("corpus_dir"), config.is_linux()):
        
        sentence = line.split('\t')[0]

        for lin_pattern in all_patterns:
            
            relations = lin_pattern.check_sentence(sentence)
            
            for relation in relations:
                
                pattern_count.inc_word_1_count(relation[0], lin_pattern.identifier)
                pattern_count.inc_word_2_count(relation[1], lin_pattern.identifier)
                pattern_count.inc_instance_count(relation, lin_pattern.identifier)
    
    lin_path = config.path_to_res("lin_count")
    pattern_count.to_files(lin_path + WORD_PATTERN_COUNT_FILE, lin_path + INSTANCE_PATTERN_COUNT_FILE, [EITHER_OR_PATTERN_ID, FROM_TO_PATTERN_ID])

class LinPatternFeatureExtractor(base.FeatureExtractor):

    def title(self):
        return "Lin patterns"
    
    def feature_col_headers(self):
        return self.col_headers()
    
    def col_headers(self):
        return [EITHER_OR_PATTERN_ID, FROM_TO_PATTERN_ID]

    def init(self, pos_to_df):
        return

    def extract_features_pos(self, pos_to_df):
        
        lin_path = config.path_to_res("lin_count")
        lin_count = PatternCount.from_files(lin_path + WORD_PATTERN_COUNT_FILE, lin_path + INSTANCE_PATTERN_COUNT_FILE)

        def get_rel_freq(instance, pattern_id):
            words = instance.split()
            instance = words[0], words[1]
            return lin_count.get_rel_freq(instance, pattern_id)

        for pos in util.POS:
            
            df = pos_to_df[pos]
            df[EITHER_OR_PATTERN_ID] = df.index.map(lambda x: get_rel_freq(x, EITHER_OR_PATTERN_ID))
            df[FROM_TO_PATTERN_ID] = df.index.map(lambda x: get_rel_freq(x, FROM_TO_PATTERN_ID))

    def finish(self, df):
        return        

if __name__ == "__main__":
    
    search_files()
